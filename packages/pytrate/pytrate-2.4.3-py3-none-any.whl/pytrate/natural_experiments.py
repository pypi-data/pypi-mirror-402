from functools import cache, cached_property
from itertools import zip_longest
from math import ceil
from typing import Optional
import warnings

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import xarray as xr

from . import helper
from .seqdf import SeqDf
from .modelbase import ModelBase

POSTCOORDS_REPR = """PosteriorAgCoords(

idata=
{},

chain=
{},

draw=
{},

data=
{}
)"""


class PosteriorAgCoords:
    def __init__(
        self,
        idata: az.InferenceData,
        coords_data: pd.DataFrame,
        sequences: Optional[SeqDf] = None,
    ) -> None:
        self.idata = idata
        self.chain = idata.posterior.coords["chain"]
        self.draw = idata.posterior.coords["draw"]
        self.data = coords_data
        self.sequences = sequences

    def __repr__(self) -> str:
        return POSTCOORDS_REPR.format(self.idata, self.chain, self.draw, self.data)

    def coords(self, name: str, stack: bool = False, center: bool = False):
        arr = self.idata.posterior.sel(name=name)["ag_coords"]
        if center:
            arr = arr - arr.mean(dim=["chain", "draw"])
        return arr.stack({"sample": ["chain", "draw"]}) if stack else arr

    def plot_posterior(self, name: str, draw_skip: int = 5, ax=None, **kwds):
        ax = ax or plt.gca()
        kwds = {**kwds, **dict(lw=0, alpha=0.5)}
        coords = self.coords(name)[:, ::draw_skip]
        return ax.scatter(coords.sel(ag_dim="x"), coords.sel(ag_dim="y"), **kwds)

    def plot_hdi_contour(
        self, name: str, hdi_probs: list[float] = None, lc="black", lw=0.5, ax=None
    ):
        ax = ax or plt.gca()
        hdi_probs = hdi_probs or [0.95]
        arr = self.coords(name)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            az.plot_kde(
                arr.sel(ag_dim="x"),
                arr.sel(ag_dim="y"),
                hdi_probs=hdi_probs,
                contour_kwargs=dict(colors=lc, zorder=15, linewidths=lw),
                contourf_kwargs=dict(colors="white", alpha=0, zorder=0),
                ax=ax,
            )

    @cache
    def dist_between_pair(
        self, a: str, b: str, center_coords: bool = False
    ) -> xr.DataArray:
        diff = self.coords(b, center=center_coords) - self.coords(
            a, center=center_coords
        )
        return xr.DataArray(
            np.linalg.norm(diff, axis=-1),
            coords=dict(chain=self.chain, draw=self.draw),
            dims=["chain", "draw"],
            name="dist",
        )

    def dist_between_pair_corrected(self, a: str, b: str) -> xr.DataArray:
        null = self.dist_between_pair(a, b, center_coords=True)
        return self.dist_between_pair(a, b, center_coords=False) - null

    def plot_dist_between_pair(
        self, a: str, b: str, ax=None, center_coords: bool = False, **kwds
    ):
        kwds = {**kwds, **dict(bins=np.arange(0, 8, 0.5))}
        ax = ax or plt.gca()
        return ax.hist(
            self.dist_between_pair(a, b, center_coords=center_coords).to_numpy().ravel(),
            **kwds,
        )

    def plot_data(self, name, ax=None, **kwds):
        ax = ax or plt.gca()
        x = self.data.loc[name, "x"]
        y = self.data.loc[name, "y"]
        return ax.scatter(x, y, **kwds)

    def plot_coords_pair(
        self, a, b, post_cloud: bool = False, post_contour: bool = False, ax=None
    ):
        ax = ax or plt.gca()

        if post_cloud:
            posterior_kwds = dict(s=4, alpha=1, zorder=5, ax=ax)
            self.plot_posterior(a, c="#fd8d3c", **posterior_kwds)
            self.plot_posterior(b, c="#31a354", **posterior_kwds)

        if post_contour:
            self.plot_hdi_contour(a, ax=ax)
            self.plot_hdi_contour(b, ax=ax)

        # a, b data
        data_kwds = dict(zorder=10, lw=0.5, ec="white", ax=ax, s=20)

        c_aa0 = "#AF0A0A"
        c_aa1 = "#131F9E"
        aa0 = None
        aa1 = None

        # if sequences are known then can plot coordinates according to amino
        # acids that the antigens differ by
        if self.sequences is not None:
            subs = list(
                helper.find_substitutions(
                    a,
                    b,
                    numbering_start=self.sequences.numbering_start,
                    yield_tuples=True,
                )
            )
            if len(subs) == 1:
                aa0, _, aa1 = subs[0]
                c_aa0 = helper.amino_acid_colors[aa0]
                c_aa1 = helper.amino_acid_colors[aa1]

        self.plot_data(a, c=c_aa0, label=aa0, **data_kwds)
        self.plot_data(b, c=c_aa1, label=aa1, **data_kwds)

        # raw coordinates
        self.data.plot.scatter("x", "y", ax=ax, zorder=0, c="lightgrey")

        helper.make_ax_a_map(ax)

        return ax

    def plot_groups_of_pairs(
        self,
        groups: list[list[str] | tuple[str, str]],
        ncols=8,
        figsize: Optional[tuple[int, int]] = None,
        **kwds,
    ) -> np.ndarray:
        """
        Plot summaries of groups of pairs of strains that differ by single substitutions.

        Args:
            groups: List of lists / 2-tuples. Each sublist contains a group of strains to plot.
            ncols: Number of columns in the figure.
            figsize: Figure size (width, height). If None, calculated from ncols.
            **kwds: Passed to self.plot_coords_pair

        Returns:
            numpy array containing matplotlib axes
        """
        nrows = ceil(len(groups) / ncols)
        ncols = len(groups) if ncols >= len(groups) else ncols

        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            sharex=True,
            sharey=True,
            figsize=(ncols * 1.2, nrows * 1.5) if figsize is None else figsize,
        )

        for i, (ax, pair) in enumerate(zip_longest(fig.axes, groups)):

            if pair is None:
                ax.axis("off")

            elif len(pair) != 2:
                raise ValueError("groups should contain a list of pairs")

            else:
                self.plot_coords_pair(*pair, ax=ax, **kwds)
                dist = self.dist_between_pair(*pair)
                lo, hi = az.hdi(dist)["dist"]
                label = (
                    f"[{i}] {float(dist.mean()):.1f} ({float(lo):.1f}, {float(hi):.1f})"
                )

                ax.text(0, 1.01, label, transform=ax.transAxes, fontsize=6)

        return axes

    def summarise_pair_dist_hdi(
        self,
        groups: list[list[str] | tuple[str, str]],
        show_null: bool = True,
        show_corrected: bool = False,
        **kwds,
    ) -> np.ndarray:
        """
        Show HDI of distances between groups of pairs of strains.

        - The unmodified distribution (labelled 'Data') is the difference in the
          posterior distributions of items in a pair.
        - The null distribution subtracts the mean of each posterior distribution (i.e.
          centers) before subtracting one from another. The result is the distribution
          that results from the multidimensional nature of the coordinates, and from the
          uncertainty in the posterior.
        - The 'corrected' distribution subtracts the null from the unmodified.

        Args:
            groups: List of lists / 2-tuples. Each sublist contains a group of strains to plot.
            show_null: Show posterior distribution of distances between the groups after centering
                the point clouds.
            show_corrected:
            **kwds: Passed to arviz.plot_forest.
        """

        def concat_dists(fun=self.dist_between_pair, **kwds) -> xr.DataArray:
            return xr.concat([fun(*pair, **kwds) for pair in groups], dim="dist")

        data = [concat_dists(center_coords=False)]
        colors = [kwds.pop("colors", "black")]
        names = ["Data"]

        if show_null:
            data.append(concat_dists(center_coords=True))
            colors.append("#A2A2A2")
            names.append("Null")

        if show_corrected:
            data.append(concat_dists(fun=self.dist_between_pair_corrected))
            colors.append("#C33F3F")
            names.append("Corrected")

        defaults = dict(
            combined=True, hdi_prob=0.95, figsize=(6, 0.3 * len(groups) + 0.25)
        )
        axes = az.plot_forest(
            data, model_names=names, colors=colors, **{**kwds, **defaults}
        )

        leg = axes[0].get_legend()
        leg.set_loc("upper left")
        leg.set_bbox_to_anchor((1, 1))

        return axes


class MapCoordModel(ModelBase):
    def __init__(self, coords: pd.DataFrame, sigma_lam: float = 1.0) -> None:
        """
        A Bayesian model for antigenic coordinates.

        Args:
            coords: DataFrame containing antigenic coordinates. Index can
                contain antigens or sera. Posterior distribution is inferred for
                every unique item in the index.
            sigma_lam: Error rate parameter prior.
        """
        self.coords = coords
        self.ndim = self.coords.shape[1]
        self.sigma_lam = sigma_lam

    def __repr__(self):
        return f"MapCoordModel(coords={repr(self.coords)}, sigma_lam={self.sigma_lam})"

    @cached_property
    def model(self) -> pm.Model:

        name = pd.Categorical(self.coords.index)

        model_coords = dict(name=name.categories, ag_dim=self.coords.columns)

        # Prior upper and lower limits
        lower = self.coords.min().values - 5
        upper = self.coords.max().values + 5

        with pm.Model(coords=model_coords) as model:
            xyz = pm.Uniform(
                "ag_coords", lower=lower, upper=upper, dims=["name", "ag_dim"]
            )
            sigma = pm.Exponential("sigma", lam=self.sigma_lam, dims="ag_dim")
            pm.Normal("obs", xyz[name.codes], sigma=sigma, observed=self.coords)

        return model

    def sample(self, *args, **kwargs) -> PosteriorAgCoords:
        idata = super().sample(*args, **kwargs)
        return PosteriorAgCoords(idata, coords_data=self.coords)
