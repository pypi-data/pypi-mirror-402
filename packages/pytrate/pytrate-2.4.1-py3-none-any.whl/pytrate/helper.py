from collections import namedtuple, defaultdict
from itertools import product, combinations
from pathlib import Path
from typing import Callable, Generator, Iterable, Literal, Optional, Any, Union
import math
import re
import warnings

from adjustText import adjust_text
from Bio import SeqIO
from scipy import odr
from scipy.stats import pearsonr
import arviz as az
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import xarray as xr


"""
1 letter amino acid codes, sorted by biophysical property.
"""
aminoAcidsByProperty = (
    # Hydrophobic
    "W",
    "Y",
    "F",
    "M",
    "L",
    "I",
    "V",
    "A",
    # Special
    "P",
    "G",
    "C",
    # Polar uncharged
    "Q",
    "N",
    "T",
    "S",
    # Charged (-)
    "E",
    "D",
    # Charged (+)
    "H",
    "K",
    "R",
)

"""
1 letter amino acid codes, sorted alphabetically.
"""
aminoAcids = (
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "Y",
)

"""
1 letter amino acid codes, sorted alphabetically, including a gap character.
"""
aminoAcidsAndGap = (
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "Y",
    "-",
)

"""
1 letter amino acid codes, sorted alphabetically, including gap and unknown amino acid
character.
"""
aminoAcidsAndGapAndUnknown = (
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "Y",
    "X",
    "-",
)

amino_acid_colors = {
    "A": "#F76A05",
    "C": "#dde8cf",
    "D": "#a020f0",
    "E": "#9e806e",
    "F": "#f1b066",
    "G": "#675b2c",
    "H": "#ffc808",
    "I": "#8b8989",
    "K": "#03569b",
    "L": "#9B84AD",
    "M": "#93EDC3",
    "N": "#a2b324",
    "P": "#e9a390",
    "Q": "#742f32",
    "R": "#75ada9",
    "S": "#e72f27",
    "T": "#049457",
    "V": "#00939f",
    "W": "#ED93BD",
    "X": "#777777",  # Unknown AA
    "Y": "#a5b8c7",
    "-": "#000000",  # Gap / insertion
}


_KNOWN_AMINO_ACIDS = frozenset(aminoAcidsAndGapAndUnknown)

normal_lcdf = pm.distributions.dist_math.normal_lcdf
UncensoredCensoredTuple = namedtuple(
    "UncensoredCensoredTuple", ("uncensored", "censored", "combined")
)
TrainTestTuple = namedtuple("TrainTestTuple", ("train", "test"))


def string_to_series(string: str) -> pd.Series:
    """
    Expand characters in a string to individual items in a series.
    """
    return pd.Series(list(string))


def expand_sequences(series: pd.Series) -> pd.DataFrame:
    """
    Expand Series containing sequences into DataFrame.

    Args:
        series (pd.Series)

    Returns:
        pd.DataFrame: Columns are sequence sites, indexes match the series index.
    """
    if series.empty:
        return pd.DataFrame()
    else:

        sequence_lengths = set(len(s) for s in series)
        if len(sequence_lengths) > 1:
            warnings.warn(
                UserWarning(
                    "sequences have different lengths, '-' characters have been "
                    "appended to shorter sequences"
                )
            )

        df = series.apply(string_to_series)
        df.columns = list(range(1, df.shape[1] + 1))
        return df.fillna("-")


def df_from_fasta(path: str, sites: Optional[list[int]] = None) -> pd.DataFrame:
    """
    Read a fasta file.

    Args:
        path: Path to fasta file.
        sites: Optional 1-indexed list of sites to include.

    Returns:
        DataFrame. Indexes are record IDs in upper case, columns are sites.
    """
    with open(path, "r") as handle:
        data = {record.id: record.seq for record in SeqIO.parse(handle, "fasta")}

    df = pd.DataFrame.from_dict(data, orient="index")
    df.columns = list(range(1, df.shape[1] + 1))

    if sites is not None:
        df = df[list(sites)]

    return df


def df_to_dict(df: pd.DataFrame) -> dict:
    """
    Convert a DataFrame to a nested dictionary, excluding NaN values.

    Args:
        df: DataFrame to convert.

    Returns:
        dict: Nested dictionary where outer keys are column names and inner keys are
            row indices with non-NaN values.
    """
    if len(df.columns) != len(set(df.columns)):
        raise ValueError(
            "DataFrame contains duplicate column names, dict would lose data"
        )

    if len(df.index) != len(set(df.index)):
        raise ValueError("DataFrame contains duplicate row names, dict would lose data")

    return {
        column_name: {
            row_name: row_value
            for row_name, row_value in sorted(
                column_values.items(), key=lambda item: item[1], reverse=True
            )
            if not pd.isnull(row_value)
        }
        for column_name, column_values in df.to_dict().items()
    }


def test_known_aa(aa: str) -> None:
    """
    Test if a string is a known amino acid.
    """
    if aa not in _KNOWN_AMINO_ACIDS:
        raise ValueError(f"unrecognized amino acid: {aa}")


class GlycosylationChange:
    def __init__(
        self,
        gain_or_loss: Literal["gain", "loss"],
        site: int,
        subs: list[str],
        root_motif: str,
        mut_motif: str,
    ):
        self.gain_or_loss = gain_or_loss
        self.site = site
        self.subs = subs
        self.root_motif = root_motif
        self.mut_motif = mut_motif
        try:
            self.sign = {"gain": "+", "loss": "-"}[self.gain_or_loss]
        except KeyError:
            raise ValueError("gain_or_loss must be 'gain' or 'loss'")

    def __str__(self) -> str:
        return f"{self.site}{self.sign}g"

    def __eq__(self, other) -> bool:
        """
        Glycosylation changes are equivalent if they occur at the same site and are both
        losses / gains.
        """
        return (self.site == other.site) and (self.gain_or_loss == other.gain_or_loss)


def plot_forest_sorted(
    data: az.InferenceData | xr.DataArray,
    var_name: str,
    sortby: Literal["mean", "median"] = "median",
    dim: str = None,
    tail: Optional[int] = None,
    head: Optional[int] = None,
    ax: mpl.axes.Axes = None,
    **kwds,
) -> mpl.axes.Axes:
    """
    Plot parameters of an inference data object sorted by their median value.

    Args:
        data: Any object that can be converted to arviz.InferenceData.
        var_name: The variable to plot.
        sortby: Criterion to sort by, either "mean" or "median" (default: "median").
        dim: The dimension to use for labelling. This is necessary when the variable has
            multiple dimensions (not including 'sample'), so that the correct dimension
            is used for labelling. Only used when there are multiple (non-sample)
            dimensions.
        tail: If provided, plot only this many of the lowest values.
        head: If provided, plot only this many of the highest values.
        ax: Optional matplotlib axes to plot on.
        **kwds: Passed to arviz.plot_forest

    Returns:
        mpl.axes.Axes
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")

    ax = ax or plt.gca()

    post = az.extract(data)
    values = post[var_name]

    non_sample_dims = set(values.dims) - {"sample"}
    if len(non_sample_dims) == 1:
        (dim,) = non_sample_dims
    else:
        raise ValueError("multiple dims present, pass a dim for labelling")

    if sortby == "mean":
        sort_param = values.mean(dim="sample")
    elif sortby == "median":
        sort_param = values.median(dim="sample")
    else:
        raise ValueError("sortby must be either 'mean' or 'median'")

    sorted_values = values.sortby(sort_param)

    if tail is not None and head is not None:
        raise ValueError("at least one of head and tail must be None")
    elif tail is not None:
        sorted_values = sorted_values[:tail]
    elif head is not None:
        sorted_values = sorted_values[len(sorted_values) - head :]

    az.plot_forest(
        data,
        var_names=var_name,
        coords={dim: sorted_values[dim]},
        combined=kwds.pop("combined", True),
        ax=ax,
        **kwds,
    )

    return ax


def plot_aa_matrix(
    idata: az.InferenceData,
    ax: Optional[mpl.axes.Axes] = None,
    force_upper_left: bool = False,
    vmin: float = -3.0,
    vmax: float = 3.0,
    include_unknown_aa: bool = False,
) -> tuple[mpl.axes.Axes, mpl.cm.ScalarMappable]:
    """
    Show the amino acid parameters as a matrix.

    Args:
        idata: Inference data containing b_aa variable.
        ax: Plot on this axes.
        force_upper_left: Push all the coloured squares in to the upper left corner of
            the plot. (Implementation note: this would happen by default if amino acids
            were sorted by their site in the aminoAcidsByProperty tuple, rather than
            alphabetically when amino acid pairs get defined in
            CrossedSiteAaModel.aa_uniq.)
        vmin: Colormap boundary.
        vmax: Colormap boundary.
        include_unknown_aa: Include 'X' as an amino acid.
    """
    aas = list(reversed(aminoAcidsByProperty))
    if include_unknown_aa:
        aas.append("X")
    aas.append("-")

    post = az.extract(idata)
    b_aa_med = post["b_aa"].mean("sample").to_dataframe().squeeze()

    norm = mpl.colors.Normalize(vmin, vmax)
    mappable = mpl.cm.ScalarMappable(norm=norm, cmap=mpl.cm.RdBu)

    ax = ax or plt.gca()

    seen = set()

    rect_kwds = dict(width=1.0, height=1.0, clip_on=False)

    for aa_pair, _b_aa in b_aa_med.items():

        if (aa_pair[0] == "X" or aa_pair[1] == "X") and not include_unknown_aa:
            continue

        j, i = aas.index(aa_pair[0]), aas.index(aa_pair[1])

        if force_upper_left:
            i, j = sorted((i, j))
            if (i, j) in seen:
                raise ValueError(
                    "forcing values in upper left would over write (maybe you are using "
                    "force_upper_left with asymmetric amino acids)"
                )

        congruence = j == i
        ax.add_artist(
            mpl.patches.Rectangle(
                (i, j),
                facecolor=mpl.cm.RdBu(norm(_b_aa)),
                lw=0.5 if congruence else 0,
                zorder=15 if congruence else 10,
                edgecolor="black",
                **rect_kwds,
            )
        )
        seen.add((i, j))

    for ij in product(range(len(aas)), range(len(aas))):
        if ij not in seen:
            ax.add_artist(
                mpl.patches.Rectangle(ij, facecolor="lightgrey", zorder=5, **rect_kwds)
            )

    lim = 0, len(aas)
    ticks = np.arange(0.5, len(aas) + 0.5)
    ax.set(
        xlim=lim,
        ylim=lim,
        aspect=1,
        xticks=ticks,
        yticks=ticks,
        xticklabels=aas,
        yticklabels=aas,
    )
    ax.grid(False, "major", "both")

    kwds = dict(c="white", zorder=12)
    for x in 3, 5, 9, 12, 17, 20:
        ax.axvline(x, **kwds)
        ax.axhline(x, **kwds)

    return ax, mappable


def plot_aa_matrix_error_bars(
    idata: az.InferenceData,
    ax: Optional[mpl.axes.Axes] = None,
    include_unknown_aa: bool = False,
):
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))

    post = az.extract(idata)

    hdi = az.hdi(idata)

    aa_terms = post["aa"]

    aas = list(reversed(aminoAcidsByProperty))
    if include_unknown_aa:
        aas.append("X")
    aas.append("-")

    half_y_range = max(abs(hdi["b_aa"].min()), hdi["b_aa"].max())
    y_range = (half_y_range * 2).values
    yticks = np.arange(len(aas)) * y_range
    xticks = np.arange(len(aas))

    norm = mpl.colors.Normalize(vmin=-half_y_range, vmax=half_y_range)

    def plot_errorbar(x: float, y: float, hdi: tuple[float, float], c: str, **kwds):
        ax.plot((x, x), hdi, c=c, zorder=10, solid_capstyle="butt", **kwds)
        ax.plot(
            (x, x),
            (y - 0.05, y + 0.05),
            c="black",
            zorder=15,
            solid_capstyle="butt",
            **kwds,
        )

    for y, aa_y in zip(yticks, aas):
        for x, aa_x in enumerate(aas):
            if aa_y != aa_x:
                # Small bar for each term that's present
                terms = aa_y + aa_x, aa_x + aa_y  # E.g. "XY", "YX"
                for term, xoffset in zip(terms, (-0.25, 0.25)):
                    if term in aa_terms:
                        mean = post["b_aa"].sel(aa=term).mean()
                        plot_errorbar(
                            x=x + xoffset,
                            y=mean + y,
                            hdi=hdi["b_aa"].sel(aa=term) + y,
                            c=mpl.cm.RdBu(norm(mean)),
                            lw=6,
                        )

            else:
                # Single wider bar for matching amino acids
                term = aa_y + aa_x
                if term in aa_terms:
                    mean = post["b_aa"].sel(aa=term).mean()
                    plot_errorbar(
                        x=x,
                        y=mean + y,
                        hdi=hdi["b_aa"].sel(aa=term) + y,
                        c=mpl.cm.RdBu(norm(mean)),
                        lw=12,
                    )

                # Grey box surrounding matching amino acids
                ax.add_artist(
                    mpl.patches.Rectangle(
                        xy=(x - 0.5, y - half_y_range),
                        width=1,
                        height=y_range,
                        facecolor="darkgrey",
                        edgecolor=None,
                        zorder=5,
                        clip_on=False,
                        linewidth=0.5,
                    ),
                )

    ax.set_facecolor("lightgrey")
    ax.grid(False, axis="both", which="both")
    kwds = dict(c="white", lw=0.5, zorder=6)
    for ytick in yticks:
        ax.axhline(ytick - half_y_range, **kwds)
        ax.axhline(ytick, c="darkgrey", lw=0.25, linestyle="--")
    for xtick in xticks:
        ax.axvline(xtick - 0.5, **kwds)

    # Thicker lines to demark amino acid groups
    kwds = dict(c="white", zorder=12)
    for x in 3, 5, 9, 12, 17, 20:
        ax.axvline(x - 0.5, **kwds)
        ax.axhline(x * y_range - half_y_range, **kwds)

    plt.yticks(yticks, aas)
    plt.xticks(xticks, aas)
    plt.xlim(-0.5, len(aas) - 0.5)
    plt.ylim(-half_y_range, yticks[-1] + half_y_range)


def hdi_scatter_data(
    data: az.InferenceData | xr.DataArray,
    varname: Optional[str] = None,
    hdi_prob: float = 0.95,
    sort: Optional[Literal["ascending", "descending"]] = None,
    sortby: Literal["mean", "lower", "higher"] = "mean",
    head: Optional[int] = None,
    tail: Optional[int] = None,
) -> tuple[xr.DataArray, np.ndarray]:
    """
    Calculate mean and HDI error bars for a variable in an InferenceData object.

    Args:
        idata: az.InferenceData. InferenceData object to extract from.
        varname: str. Name of the variable to extract. Required if data is az.InferenceData.
        hdi_prob: float, optional. Probability to use for the HDI calculation (default=0.95).
        sort: str, optional. If 'ascending' or 'descending', sort the values by their mean.
        sortby: str. How should values be sorted? 'lower' and 'upper' refer to the lower and upper
            bounds of the HDI. Only relevant is sort is not None.
        head: int, optional. Show only this many of the highest values.
        tail: int, optional. Show only this many of the lowest values.

    Returns:
        2-tuple containing:
            mean: xr.DataArray. Mean of the variable.
            hdi_err: np.ndarray. Shape (2, len(variable)) containing the HDI error bars
                as (lower, upper).
    """
    if isinstance(data, az.InferenceData):
        hdi = az.hdi(data, hdi_prob=hdi_prob)[varname]
        mean = az.extract(data)[varname].mean("sample")

    else:
        hdi = az.hdi(data, hdi_prob=hdi_prob)[data.name]

        try:
            mean = data.mean("sample")
        except ValueError:
            mean = data.stack({"sample": ["chain", "draw"]}).mean("sample")

    if sort is not None:

        # Get values to sort by
        if sortby == "mean":
            values = mean
        elif sortby == "lower":
            values = hdi.sel(hdi="lower")
        elif sortby == "higher":
            values = hdi.sel(hdi="higher")
        else:
            raise ValueError("sortby should be one of 'mean', 'lower', 'higher'")

        # Get index that sorts
        if sort == "ascending":
            idx = np.argsort(values).values

        elif sort == "descending":
            idx = np.argsort(-values).values

        else:
            raise ValueError("sort must be 'ascending' or 'descending'")

        if head is not None and tail is not None:
            raise ValueError("pass either head or tail, not both")

        elif head is not None:
            if sort == "ascending":
                idx = idx[-head:]
            elif sort == "descending":
                idx = idx[:head]

        elif tail is not None:
            if sort == "ascending":
                idx = idx[:tail]
            elif sort == "descending":
                idx = idx[-tail:]

        mean = mean[idx]
        hdi = hdi.isel(site=idx)

    return mean, np.stack([(mean - hdi[..., 0]).values, (hdi[..., 1] - mean.values)])


def plot_hdi_scatter(
    y_data: az.InferenceData | xr.DataArray,
    var_name: Optional[str] = None,
    x_data: Optional[az.InferenceData | xr.DataArray] = None,
    var_name_x: Optional[str] = None,
    ax: Optional[mpl.axes.Axes] = None,
    highlight_site: Optional[int] = None,
    highlight_kwds: Optional[dict[str, Any]] = None,
    hdi_as_area: bool = False,
    area_kwds: Optional[dict] = None,
    xtick_skip: Optional[int] = None,
    data_kwds: Optional[dict] = None,
    **kwds,
) -> mpl.axes.Axes:
    """
    Plot two variables in an InferenceData object against each other, using HDI error bars.

    Args:
        y_data: az.InferenceData or xr.DataArray. The y data to plot.
        var_name: str. Name of the variable to plot. Must be passed for az.InferenceData objects.
        x_data: az.InferenceData or xr.DataArray. The x data to plot. If not provided, then
            y data is plotted with uniformly spaced x data.
        var_name_x: str. Name of the variable to plot on the x-axis (if different from var_name).
        ax: Optional[mpl.axes.Axes], optional. Axes to plot on. If None, a new figure
            is created (default).
        highlight_site: int, optional. If provided, highlight this site in red.
        highlight_kwds: dict, optional. Passed to plt.scatter for the highlighted point.
        hdi_as_area: bool. Plot the width of the HDIs as an area rather than individual lines. Only
            applies when x_data is None. Only applies when x_data is not provided.
        area_kwds: dict. Passed to axes.Axes.fill_between.
        xtick_skip: Use this to add xticklabels if only y_data is passed. This integer defines how
            frequently to plot xticks. I.e. set to 1 to show all xticklabels, or 10 to show every
            tenth, say.
        data_kwds: dict, optional. Passed to `hdi_scatter_data`. Keys include `hdi_prob`, `sort`,
            `sortby`, `head`, `tail`. See `hdi_scatter_data` for more details.
        **kwds: Passed to ax.errorbar.

    Returns:
        `mpl.axes.Axes`
    """
    # Data
    data_kwds = {} if data_kwds is None else data_kwds
    y, yerr = hdi_scatter_data(y_data, var_name, **data_kwds)

    if isinstance(x_data, np.ndarray) and x_data.ndim == 1 and len(x_data) == len(y):
        # Assume that we've been passed an array of scalar x values to plot the posterior
        # y values at
        x_data = xr.DataArray(x_data.reshape(1, 1, -1), dims=("draw", "chain", "_"))
        xerr = None

    elif x_data is None:
        # Uniformly spaced x data
        x = xr.DataArray(np.arange(len(y)), coords=dict(site=y.coords["site"]))
        xerr = None

    else:
        # TODO 'site' shouldn't be hardcoded here!
        x, xerr = hdi_scatter_data(x_data, var_name_x or var_name, **data_kwds)

    # Plotting
    ax = ax or plt.gca()

    if hdi_as_area:
        if x_data is not None:
            raise ValueError("hdi_as_area only applies when x_data not provided")

        area_defaults = dict(color="lightgrey", linewidth=0, zorder=5)
        area_kwds = area_kwds or {}
        ax.fill_between(
            x, y1=y - yerr[0], y2=y + yerr[1], **{**area_defaults, **area_kwds}
        )
        ax.plot(x, y, c="black", lw=0.5, zorder=10)

    else:
        errorbar_defaults = dict(
            c="black",
            ecolor="grey",
            elinewidth=0.75,
            fmt="o",
            markeredgecolor="white",
            zorder=10,
        )
        ax.errorbar(x, y, yerr, xerr, **{**errorbar_defaults, **kwds})

    highlight_defaults = dict(c="red", s=50, zorder=15)
    highlight_kwds = {**highlight_defaults, **(highlight_kwds or {})}

    if highlight_site is not None:
        if isinstance(highlight_site, int):
            highlight_site = (highlight_site,)

        highlight_site = list(set(highlight_site) & set(y.coords["site"].values))

        ax.scatter(
            x.sel(site=highlight_site),
            y.sel(site=highlight_site),
            **highlight_kwds,
        )

    if x_data is None and xtick_skip is not None:
        ticks = x[::xtick_skip]
        labels = y.coords["site"].values[::xtick_skip]
        ax.set_xticks(ticks, labels)

    return ax


class CrossValidationFoldResult:
    def __init__(
        self,
        idata: az.InferenceData,
        y_true: np.ndarray,
        train: UncensoredCensoredTuple,
        test: UncensoredCensoredTuple,
    ) -> None:
        """
        The results of a single train/test cross validation fold.

        Args:
            idata: The inference data object. Should have a `posterior_predictive`
                attribute.
            y_true: Measured responses of the test set.
            train: Tuple of masks used to define training data.
            test: Tuple of masks used to define testing data.
        """
        self.idata = idata
        self.y_pred = (
            idata.posterior_predictive["obs_u"].mean(dim="draw").mean(dim="chain")
        )
        self.y_true = y_true
        self.err = (self.y_pred - self.y_true).values
        self.err_abs = np.absolute(self.err)
        self.err_sqr = self.err**2
        self.mean_err_sqr = np.mean(self.err_sqr)
        self.mean_err_abs = np.mean(self.err_abs)
        self.train = train
        self.test = test

    def __repr__(self) -> str:
        return f"CrossValidationFoldResult({self.idata})"

    def __str__(self) -> str:
        return (
            f"mean squared error: {self.mean_err_sqr}\n"
            f"mean absolute error: {self.mean_err_abs}"
        )

    def plot_predicted_titers(
        self, ax=None, jitter: float = 0.2, ylabel: str = "Predicted log titer"
    ) -> None:
        """
        Plot predicted vs true log titer values.

        Args:
            ax: Matplotlib ax.
            jitter: Size of jitter to add to x-axis values.
            ylabel: Y-axis label.
        """
        ax = ax or plt.gca()
        jitter = np.random.uniform(-jitter / 2, jitter / 2, len(self.y_true))
        ax.scatter(
            self.y_true + jitter,
            self.y_pred,
            lw=0.5,
            clip_on=False,
            s=15,
            edgecolor="white",
        )
        ax.set(
            aspect=1,
            xlabel="True log titer",
            ylabel=ylabel,
            xticks=np.arange(0, 10, 2),
            yticks=np.arange(0, 10, 2),
        )
        ax.axline((0, 0), slope=1, c="lightgrey", zorder=0)


class CrossValidationResults:
    def __init__(self, results: Iterable[CrossValidationFoldResult]) -> None:
        self.results = tuple(results)

    @property
    def df_error(self) -> pd.DataFrame:
        """
        DataFrame containing absolute error, squared error, raw error for each predicted
        titer in each fold.
        """
        return pd.concat(
            [
                pd.DataFrame(
                    {
                        "absolute_error": self.results[i].err_abs,
                        "squared_error": self.results[i].err_sqr,
                        "raw_error": self.results[i].err,
                    }
                ).assign(fold=i)
                for i in range(len(self.results))
            ]
        )

    def plot_predicted_titers(
        self, figsize: tuple[float, float] = (15.0, 10.0)
    ) -> np.ndarray:
        _, axes = plt.subplots(
            ncols=len(self.results), sharex=True, sharey=True, figsize=figsize
        )
        for result, ax in zip(self.results, axes):
            result.plot_predicted_titers(ax=ax, ylabel="Predicted log titer")
            ax.text(
                0,
                1,
                f"Mean abs. err={result.mean_err_abs:.2f}",
                transform=ax.transAxes,
                va="top",
                fontsize=8,
            )
            ax.label_outer()
        return axes


def geom_mean(a: float | int, b: float | int) -> float:
    """
    Calculate the geometric mean of two numbers.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        float: The geometric mean of a and b.
    """
    return np.sqrt(a * b)


def noncentered_normal(*args, **kwargs) -> None:
    raise NameError(
        "this function is now pytrate.helper.hierarchical_noncentered_normal"
    )


def hierarchical_noncentered_normal(
    name: str,
    dims: str,
    hyper_mu: Union[float, "pytensor.tensor.variable.TensorVariable"] = 0.0,
    hyper_sigma: Union[float, "pytensor.tensor.variable.TensorVariable"] = 0.5,
    hyper_lam: Union[float, "pytensor.tensor.variable.TensorVariable"] = 2.0,
    lognormal: bool = False,
) -> "pytensor.tensor.variable.TensorVariable":
    """
    Construct a non-centered hierarchical normal distribution. Equivalent to:

        mu = Normal('name'_mu, hyper_mu, hyper_sigma)
        sigma = Exponential('name'_sigma, hyper_lam)
        Normal(name, mu, sigma, dims=dims)

    See also `pytrate.hierarchical_normal`.

    Args:
        name: Variable name.
        dims: Dimensions of the model for the variable.
        hyper_mu: Hyperpriors.
        hyper_sigma: Hyperprior.
        hyper_lam: Hyperprior.
        lognormal: Make this a lognormal variable.

    Returns:
        pytensor.tensor.variable.TensorVariable
    """
    mu = pm.Normal(f"{name}_mu", mu=hyper_mu, sigma=hyper_sigma)
    sigma = pm.Exponential(f"{name}_sigma", lam=hyper_lam)
    z = pm.Normal(f"_{name}_z", mu=0.0, sigma=1.0, dims=dims)
    return (
        pm.Deterministic(name, np.exp(z * sigma + mu), dims=dims)
        if lognormal
        else pm.Deterministic(name, z * sigma + mu, dims=dims)
    )


def hierarchical_normal(
    name: str,
    dims: str,
    hyper_mu: Union[float, "pytensor.tensor.variable.TensorVariable"] = 0.0,
    hyper_sigma: Union[float, "pytensor.tensor.variable.TensorVariable"] = 0.5,
    hyper_lam: Union[float, "pytensor.tensor.variable.TensorVariable"] = 2.0,
) -> "pytensor.tensor.variable.TensorVariable":
    """
    Hierarchical normal distribution. Equivalent to:

        Normal(
            name,
            mu=Normal(<name>_mu, mu=hyper_mu, sigma=hyper_sigma),
            sigma=Exponential(<name>_sigma, lam=hyper_lam),
            dims=dims
        )

    See also `pytrate.hierarchical_noncentered_normal`.

    Args:
        name: Variable name.
        dims: Dimensions of the model for the variable.
        hyper_mu: Hyperpriors.
        hyper_sigma: Hyperprior.
        hyper_lam: Hyperprior.

    Returns:
        pytensor.tensor.variable.TensorVariable
    """
    mu = pm.Normal(f"{name}_mu", mu=hyper_mu, sigma=hyper_sigma)
    sigma = pm.Exponential(f"{name}_sigma", lam=hyper_lam)
    return pm.Normal(name, mu=mu, sigma=sigma, dims=dims)


class NDFactor:
    """
    Multi-dimensional factors.
    """

    def __init__(self, values: list[tuple]):

        self.values = tuple(sorted(set(values)))
        self._indexes = dict((value, i) for i, value in enumerate(self.values))
        self.labels = ["-".join(map(str, items)) for items in self.values]

    def __repr__(self) -> str:
        return f"Factor({self.values})"

    def __len__(self):
        return len(self.values)

    def make_index(self, df: pd.DataFrame) -> list[int]:
        """
        Returns the index for each row in the given DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame for which to generate indices.

        Returns:
            list[int]: A list of indices corresponding to each row in the DataFrame.
        """

        return [self.index(tuple(row)) for row in df.values]

    def index(self, value) -> int:
        return self._indexes[value]


def merge_maximal_subgroup_subs(
    ag_subs: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Finds maximal subgroups of antigens based on their unique substitutions.

    Args:
        ag_subs (dict[str, list[str]]): A dictionary mapping antigen IDs to
            lists of substitutions.

    Returns:
        dict[str, list[str]]: A dictionary mapping antigen IDs to lists of
            maximal subgroups of substitutions. Each maximal subgroup is
            represented as a string joined by '+' characters. The subgroups are
            sorted lexicographically based on the components of each
            substitution.
    """

    maximal_subsets = find_maximal_subsets(ag_subs.values())

    d = defaultdict(list)

    for ag, subs in ag_subs.items():

        unique_subs = set(subs)

        # Loop through all maximal subsets, if the maximal subset is present in this antigens unique
        # substitutions, then add this maximal subset to this antigen.
        for maximal_subset in maximal_subsets:
            if maximal_subset.issubset(unique_subs):
                d[ag].append(
                    "+".join(
                        sorted(
                            maximal_subset,
                            key=lambda x: int(re.search(r"(\d+)", x).groups()[0]),
                        )
                    )
                )

    return {k: sorted(v) for k, v in d.items()}


def find_maximal_subsets(sets: list[set]) -> set[frozenset]:
    """
    Find the maximal subsets of items that always appear together in a group of sets.

    Args:
        sets (list[set]): Group of sets.

    Returns:
        set[frozenset]: A set of frozensets representing the maximal subsets of items
            that always appear together.
    """
    if not sets:
        return set()

    frozen_sets = [frozenset(s) for s in sets]

    # dictionary that maps each item to the sets it appears in
    item_to_sets = defaultdict(set)
    all_items = set()
    for i, s in enumerate(frozen_sets):
        for item in s:
            item_to_sets[item].add(i)
            all_items.add(item)

    # group items that appear in exactly the same sets
    signature_to_items = defaultdict(set)
    for item in all_items:
        signature = frozenset(item_to_sets[item])
        signature_to_items[signature].add(item)

    # each group of items with the same signature forms a maximal subset
    maximal_subsets = set()
    for items in signature_to_items.values():
        if items:  # skip empty sets
            maximal_subsets.add(frozenset(items))

    return maximal_subsets


def sub_components(sub: str) -> tuple[int, str, str]:
    """Components of a substitution."""
    return sub_pos(sub), sub_aa0(sub), sub_aa1(sub)


def sub_pos(sub: str) -> int:
    """A substitution's position."""
    return int(re.match(r"^[A-Z](\d+)[A-Z](\(g[+-]\))?$", sub).groups()[0])


def sub_aa0(sub: str) -> str:
    """A substitution's amino acid lost."""
    return re.match(r"^([A-Z])\d+[A-Z](\(g[+-]\))?$", sub).groups()[0]


def sub_aa1(sub: str) -> str:
    """A substitution's amino acid gained."""
    return re.match(r"^[A-Z]\d+([A-Z])(\(g[+-]\))?$", sub).groups()[0]


class Titer:
    """
    A titer from a 2-fold dilution series using a 1:10 starting dilution.
    """

    def __init__(self, titer):
        self.titer = str(titer).replace(" ", "")
        if self.titer[0] == ">":
            raise NotImplementedError("gt titers not implemented")
        self.is_threshold = self.titer[0] == "<"
        self.is_inbetween = "/" in self.titer

    def __repr__(self) -> str:
        return f"Titer({self.titer})"

    def __str__(self) -> str:
        return self.titer

    @property
    def log_value(self) -> float:
        """
        Calculates the log value of the titer.

        Returns:
            float: The log value of the titer.

        Raises:
            NotImplementedError: If the titer 'greater than'.

        Note:
            If the titer is a 'less than', the log value is the log value of the titer value minus
            one. If the titer is a regular value, the log value is the log value of the titer
            divided by 10.

        Examples:
            >>> Titer("1280").log_value
            7.0
            >>> Titer("<10").log_value
            -1.0
            >>> Titer("20/40").log_value
            1.5
        """
        if self.is_inbetween:
            a, b = self.titer.split("/")
            return (Titer(a).log_value + Titer(b).log_value) / 2
        elif self.is_threshold:
            return Titer(self.titer[1:]).log_value - 1
        else:
            return np.log2(float(self.titer) / 10)


def aa_pairs_with_reversed(aa_pairs: Iterable[str]) -> set[tuple[str, str]]:
    """
    Select pairs of amino acid pairs where the reversed amino acid pair is also
    present. In this example "AN" is returned, with "NA" because both "AN" and "NA" are
    in the input:

    Args:
        aa_pairs: Amino acid pairs.

    Returns:
        set[tuple[str, str]]: A set of tuples of amino acid pairs where the reversed amino
            acid pair is also present.

    Examples:
        >>> aa_pairs_with_reversed(["QR", "AN", "TS", "ST", "KN", "NA"])
        {("AN", "NA"), ("ST", "TS")}
    """
    return set(
        tuple(sorted((pair, f"{pair[1]}{pair[0]}")))
        for pair in aa_pairs
        if f"{pair[1]}{pair[0]}" in aa_pairs and pair[0] != pair[1]
    )


def plot_reversed_amino_acid_effects_scatter(
    idata: az.InferenceData,
    ax: Optional[mpl.axes.Axes] = None,
    label_threshold: float = 1.0,
    text_kwds: Optional[dict] = None,
) -> mpl.axes.Axes:
    """
    Plot the effects of amino acid pairs and their reverse. E.g. the effect of "NK" and
    "KN" are plotted as a single point where the x-axis value represents the "KN" value
    and the y-axis value is the "NK" value.

    The regression line that is plotted is an orthogonal least squares fit (Deming
    regression). The parameters that are reported are the slope and intercept of this
    model (m and c), an a Pearson correlation coefficient (r), and p-value.

    Args:
        idata: Inference data object.
        ax: Matplotlib ax.
        label_threshold: Label amino acid pairs whose absolute difference in x and y
            values is greater than this value.
    """
    text_kwds = dict() if text_kwds is None else text_kwds
    ax = plt.gca() if ax is None else ax
    post = az.extract(idata)
    hdi = az.hdi(idata)

    kwds = dict(c="black")
    line_kwds = dict(alpha=0.5, linewidth=0.35)

    pairs_of_pairs = aa_pairs_with_reversed(post.coords["aa"].values)

    xy = np.array(
        [
            post["b_aa"].sel(aa=[pair_a, pair_b]).mean(dim="sample").values
            for pair_a, pair_b in pairs_of_pairs
        ]
    )

    labels = []
    for i, (pair_a, pair_b) in enumerate(pairs_of_pairs):
        x, y = xy[i]
        x_hdi, y_hdi = hdi["b_aa"].sel(aa=[pair_a, pair_b])

        ax.scatter(x, y, s=5, **kwds)
        ax.plot((x, x), y_hdi, **kwds, **line_kwds)
        ax.plot(x_hdi, (y, y), **kwds, **line_kwds)

        if abs(x - y) > label_threshold:
            labels.append(ax.text(x, y, f"{pair_a}/{pair_b}", **text_kwds))

    adjust_text(labels, x=xy[:, 0], y=xy[:, 1])

    ax.axline((0, 0), (1, 1), c="grey", lw=0.5)
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(base=2))
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(base=2))
    ax.set(aspect=1, xlabel="ab", ylabel="ba")

    # Deming regression
    dr = reversed_amino_acid_effects_orthogonal_least_squares_regression(idata)
    text = f"r={dr['r']:.2f}\nm={dr['m']:.2f}\nc={dr['c']:.2f}\np={dr['p']:.2f}"
    ax.text(1, 1, text, transform=ax.transAxes, va="top", fontsize=8)
    ax.axline((0, dr["c"]), slope=dr["m"], c="black")

    return ax


def reversed_amino_acid_effects_orthogonal_least_squares_regression(
    idata: az.InferenceData,
) -> dict[str, float]:
    """
    Orthogonal Least squares regression on the amino acid pairs that are estimated both
    ways round. (E.g. there are estimates for "NK" as well as "KN").

    Args:
        idata: Inference data object.

    Notes:
        `r` and `p` are independent of the regression. See:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html

    Returns:
        dict containing:
            `m`: Model slope.
            `c`: Model intercept.
            `r`: Pearson correlation coefficient.
            `p`: p-value of the Pearson correlation coefficient.
    """
    post = az.extract(idata)
    arr = np.array(
        [
            post["b_aa"].sel(aa=[pair_a, pair_b]).mean(dim="sample").values
            for pair_a, pair_b in aa_pairs_with_reversed(post.coords["aa"].values)
        ]
    )

    def f(p, x):
        return p[0] * x + p[1]

    od_reg = odr.ODR(odr.Data(arr[:, 0], arr[:, 1]), odr.Model(f), beta0=[1.0, 0.0])
    out = od_reg.run()

    pearsonr_result = pearsonr(arr[:, 0], arr[:, 1])
    return dict(
        m=out.beta[0],
        c=out.beta[1],
        r=pearsonr_result.statistic,
        p=pearsonr_result.pvalue,
    )


def delete_unused_variables(idata: az.InferenceData) -> az.InferenceData:
    """
    Remove variables from an InferenceData object that are from non-centered parametrisations
    and that contain log probabilities.

    Args:
        idata: Inference data object.

    Returns:
        Inference data object with unused variables removed.
    """
    for group in idata.groups():

        dataset = getattr(idata, group)

        dropped = dataset.drop_vars(
            [
                var
                for var in dataset.data_vars
                if re.match("^_.*_z$", var) or re.match(".*log__$", var)
            ]
        )

        setattr(idata, group, dropped)

    return idata


def sample_pymc(
    model: pm.Model,
    filename: Optional[str] = None,
    delete_unused: Optional[bool] = True,
    verbose: bool = True,
    **kwds,
) -> az.InferenceData:
    """
    Samples from a PyMC model and returns the inference data. At first this function tries to load
    the inference data from disk. If the file doesn't exist, then sample from the model instead, and
    save to disk using filename.

    Args:
        model (pm.Model): The PyMC model to sample from.
        filename (str | None): The path to the file where the inference data will be saved.
            Directory must exist. Must have a '.nc' suffix. Pass None to force model sampling.
        delete_unused (bool): When saving inference data objects, delete logp data and variables
            created for non-centered parametrisations.
        verbose (bool): Print messages saying if a posterior is being loaded from disk or sampled.
        **kwds: Additional keyword arguments to be passed to the `pymc.sample`.

    Returns:
        az.InferenceData: The inference data generated by PyMC.
    """
    if not isinstance(model, pm.Model):
        raise TypeError("Model should be a pymc.Model instance")

    try:
        idata = az.from_netcdf(filename)

    except FileNotFoundError:

        path = Path(filename)

        if not path.suffix == ".nc":
            raise ValueError(f"Filename should end in '.nc': {filename}")

        elif not path.parent.exists():
            raise ValueError(f"Directory doesn't exist for: {filename}")

        else:

            if verbose:
                print(f"{filename} not found, sampling from model")

            with model:
                idata = pm.sample(**kwds)

            az.to_netcdf(idata, filename)

    except TypeError:

        if filename is not None:
            raise TypeError("Filename should be None or str")

        if verbose:
            print("No filename passed, sampling from model")

        with model:
            idata = pm.sample(**kwds)

    else:
        if verbose:
            print(f"Loaded {filename}")

    return delete_unused_variables(idata) if delete_unused else idata


def rename_coordinates(
    data: xr.Dataset | az.InferenceData,
    dim: str,
    mapping: dict[str, str] | Callable[[str], str],
) -> xr.Dataset | az.InferenceData:
    """
    Renames coordinates in a given dataset or InferenceData object.

    Args:
        data (xr.Dataset | az.InferenceData): The dataset or InferenceData to rename
            coordinates in.
        dim (str): The name of the dimension to rename coordinates for.
        mapping (dict[str, str] or callable): A dictionary mapping the current coordinate
            values to the new coordinate values or a function.

    Returns:
        xr.Dataset | az.InferenceData
    """
    if isinstance(data, az.InferenceData):
        new_data = data.copy()
        for group in data.groups():
            ds = getattr(data, group)
            if dim in ds.coords:
                setattr(new_data, group, rename_coordinates(ds, dim, mapping))
        return new_data

    else:
        return data.assign_coords(
            **{
                dim: [
                    mapping(k) if callable(mapping) else mapping[k]
                    for k in data.coords[dim].values
                ]
            }
        )


def unpack(values: Iterable[Iterable[Any]]) -> Generator[Any, None, None]:
    """
    Unpacks a collection of iterables into a single iterable.

    Args:
        values: A collection of iterables to be unpacked.

    Yields:
        Elements from the unpacked iterables.
    """
    for value in values:
        yield from value


def find_glycosylation_sites(sequence: str) -> list[int]:
    """
    0-based indices of glycosylation motifs (NX{ST}) in string, where X is not proline.

    Args:
        sequence (str): The protein sequence in which to search for glycosylation motifs.

    Returns:
        list[int]: A list of indices in the protein sequence where glycosylation motifs are
            present.
    """
    return [match.start() for match in re.finditer(r"(?=(N[^P][ST]))", sequence)]


def find_substitutions(
    seq1: str,
    seq2: str,
    append_glyc_changes: bool = False,
    unify_glyc_changes: bool = False,
    ignore_chars: Optional[set] = None,
    sort_aas: bool = False,
    numbering_start: int = 1,
    yield_tuples: bool = False,
    only_sites: set[int] = None,
) -> Generator[str, None, None]:
    """
    List of substitution differences (format: 'aXb') between two protein sequences.

    Args:
        seq1 (str): The first protein sequence.
        seq2 (str): The second protein sequence.
        append_glyc_changes (bool): If a substitution is necessary to cause a
            glycosylation change, append '+g' / '-g' to the substitution if they cause a
            gain / loss of glycosylation. If multiple substitutions are required for a
            glycosylation change then they are all returned with the +/- g suffix.
            Mutually exclusive to unify_glyc_changes (default=False)
        unify_glyc_changes (bool): If a substitution is necessary to cause a
            glycosylation change, return a string representing that glycosylation change
            and not the substitution. E.g. if A156T caused a glycosylation change at site
            154 then '154+g' would be yielded. If multiple substitutions are required for
            a glycosylation change, and unify_glyc_changes=True, then the glycosylation
            change is only reported once.  Mutually exclusive to append_glyc_changes
            (default=False).
        ignore_chars (set): Don't yield substitutions that contain amino acids
            in this set.
        sort_aas (bool): Alphabetically sort the amino acids in the returned
            substitution. I.e. if the pair C and A were found, A would come
            before C in the substitution string, e.g. A14C.
        numbering_start (int): The number assigned to the first character in the
            sequence.
        yield_tuples (bool): Pass true to generate tuples (e.g. ('N', 145, 'K')),
            otherwise generate strings (e.g. 'N145K').
        only_sites (set): Only look for substitutions in these sites.

    Returns:
        list[str]: A list of strings representing the differences between the two
            sequences. Each string has the form "aXb", where "a" is the residue at the
            corresponding position in the first sequence, "X" is the 1-indexed position
            of the difference, and "b" is the residue at the corresponding position in
            the second sequence.
    """
    sites_chars = enumerate(zip(seq1.upper(), seq2.upper()), start=numbering_start)

    # filter sites if necessary
    if only_sites is not None:
        sites_chars = (
            (site, chars) for (site, chars) in sites_chars if site in only_sites
        )

    if append_glyc_changes and unify_glyc_changes:
        raise ValueError("append and unify glyc_changes can't both be True")

    elif append_glyc_changes or unify_glyc_changes:

        if sort_aas:
            raise NotImplementedError(
                "sort_aas not implemented with append_glyc_changes or unify_glyc_changes"
            )

        if yield_tuples:
            raise NotImplementedError(
                "yield_tuples not implemented with append_glyc_changes or unify_glyc_changes"
            )

        # dict mapping substitutions -> GlycosylationChange.
        # If multiple substitutions can cause a change then they will all appear in the dict
        glyc_changes = {
            sub: gc for gc in find_glycosylation_changes(seq1, seq2) for sub in gc.subs
        }

        seen = set()

        for site, (a, b) in sites_chars:

            if is_substitution(a, b, ignore_chars):

                sub = f"{a}{site}{b}"

                if sub in glyc_changes:
                    gc = glyc_changes[sub]

                    output = f"{sub}{gc.sign}g" if append_glyc_changes else str(gc)

                    if output not in seen:
                        seen.add(output)
                        yield output

                else:
                    yield sub

    else:
        for site, (a, b) in sites_chars:
            if is_substitution(a, b, ignore_chars):

                if sort_aas:
                    a, b = sorted((a, b))

                yield (a, site, b) if yield_tuples else f"{a}{site}{b}"


def sequences_differ_by_n(seq_a: Iterable, seq_b: Iterable, n: int, **kwds):
    """
    Determines if two sequences differ by exactly n substitutions.

    Args:
        seq_a: The first sequence to compare.
        seq_b: The second sequence to compare.
        n: The exact number of substitutions to check for.
        **kwds: Passed to find_substitutions.

    Returns:
        list or False: A list of n substitutions if the sequences differ by exactly
            n substitutions, or False otherwise.
    """
    subs = []

    for i, sub in enumerate(find_substitutions(seq_a, seq_b, **kwds), start=1):
        if i <= n:
            subs.append(sub)
        else:
            return False

    return subs if len(subs) == n else False


def is_substitution(a: str, b: str, ignore: Optional[set] = None):
    """
    Test if a -> b is a substitution.
    """
    return a != b and (not ignore or (a not in ignore and b not in ignore))


def find_glycosylation_changes(
    root_seq: str, mut_seq: str
) -> Generator[GlycosylationChange, None, None]:
    """
    Generate GlycosylationChange objects describing differences between glycosylation patterns of
    two protein sequences.

    Args:
        root_seq (str): The protein sequence of the root antigen.
        mut_seq (str): The protein sequence of the mutant antigen.

    Yields:
        GlycosylationChange: A named tuple describing the differences in glycosylation between the
            two sequences. The fields are:
            - gain_or_loss (str): "gain" if the glycosylation motif is present in the mutant but not
              in the root, "loss" otherwise.
            - subs (list[str]): A list of substrings representing the differences between the glycosylation
              motifs of the two sequences, e.g. "D1H".
            - root_motif (str): The motif in the root sequence.
            - mut_motif (str): The motif in the mutant sequence.
    """
    glyc_root = set(find_glycosylation_sites(root_seq))
    glyc_mut = set(find_glycosylation_sites(mut_seq))
    for index in glyc_root ^ glyc_mut:
        root_motif = root_seq[index : index + 3]
        mut_motif = mut_seq[index : index + 3]
        necessary_subs = subs_necessary_for_glyc_change(root_motif, mut_motif)
        yield GlycosylationChange(
            gain_or_loss=("loss" if find_glycosylation_sites(root_motif) else "gain"),
            site=index + 1,
            subs=[f"{a}{index + i + 1}{b}" for a, i, b in necessary_subs],
            root_motif=root_motif,
            mut_motif=mut_motif,
        )


def mutate(seq: str, diffs: Iterable[tuple[int, tuple[str, str]]]) -> str:
    """
    Apply a set of differences to a sequence to create a mutant sequence.

    Args:
        seq (str): The original sequence.
        diffs (Iterable[tuple[int, tuple[str, str]]]): An iterable of tuples where each tuple
            contains an index (0-based) and a tuple of the original and new character.
            (Only the new character is used) .

    Returns:
        str: The mutated sequence.
    """
    mutant_seq = list(seq)
    for i, (_, b) in diffs:
        mutant_seq[i] = b
    return "".join(mutant_seq)


def subs_necessary_for_glyc_change(seq_a: str, seq_b: str) -> list[tuple[str, int, str]]:
    """
    Given two 3 letter motifs return a list of substitutions that are necessary to cause the
    glycosylation difference between the root motif and the mutant motif. An error is raised if
    there is no glycosylation difference between root_motif and mut_motif.

    For instance, given the root and mutant motifs "NKT" and "NQA" the T -> A at the 3rd position is
    necessary and sufficient for the loss of glycosylation. The K -> Q at the 2nd position would not
    cause the loss of glycosylation.

    The only change at the 2nd position that could be implicated in the gain / loss would be the
    absence / presence of a proline.

    Args:
        seq_a (str): Three letter protein sequence.
        seq_b (str): Three letter protein sequence.

    Returns:
        list[tuple[str, int, str], ...]: List of tuples containing the substitutions necessary
            for the change.
    """
    seq_a = seq_a.upper()
    seq_b = seq_b.upper()

    if len(seq_a) != 3 or len(seq_b) != 3:
        raise ValueError(f"sequences not len 3: {seq_a}, {seq_b}")

    a_glyc_sites = find_glycosylation_sites(seq_a)
    b_glyc_sites = find_glycosylation_sites(seq_b)

    if a_glyc_sites == b_glyc_sites:
        raise ValueError(f"No glycosylation difference between {seq_a} and {seq_b}")

    subs = []

    diffs = [(i, (a, b)) for (i, (a, b)) in enumerate(zip(seq_a, seq_b)) if a != b]

    # Look for single amino acid changes that are sufficient to case the glyc change
    for i, (a, b) in diffs:

        mutant_seq = mutate(seq_a, [(i, (a, b))])

        if find_glycosylation_sites(mutant_seq) == b_glyc_sites:
            subs.append((a, i, b))

    # If no substitutions have been found, then no single amino acid change was
    # sufficient to cause the glycosylation difference.
    #
    # Now look for pairs of amino acid changes that could be responsible.
    if not subs:

        for pair in combinations(diffs, 2):

            mutant_seq = mutate(seq_a, pair)

            if find_glycosylation_sites(mutant_seq) == b_glyc_sites:
                for i, (a, b) in pair:
                    subs.append((a, i, b))

    # If still no subs have been found, then all three aa changes must be necessary
    if not subs:
        for i, (a, b) in diffs:
            subs.append((a, i, b))

    return subs


def make_ax_a_map(ax=None) -> mpl.axes.Axes:
    """
    Configure a matplotlib ax to be an antigenic map. Maps have integer spaced
    grids, an aspect ratio of 1, and no axis labels.

    Args:
        ax: A matplotlib axes instance.

    Returns:
        The ax.
    """
    ax = ax or plt.gca()

    ax.get_xaxis().set_major_locator(mpl.ticker.MultipleLocator(base=1.0))
    ax.get_yaxis().set_major_locator(mpl.ticker.MultipleLocator(base=1.0))

    ax.set_ylabel("")
    ax.set_xlabel("")

    xlim = ax.get_xlim()
    ax.set_xlim(math.floor(xlim[0]), math.ceil(xlim[1]))

    ylim = ax.get_ylim()
    ax.set_ylim(math.floor(ylim[0]), math.ceil(ylim[1]))

    # Can't pass a zorder to the grid, this puts the grid under everything else on the ax
    ax.set_axisbelow(True)
    ax.grid(visible=True, lw=0.5, c="lightgrey")

    ax.set_aspect(1)

    for spine in "top", "bottom", "left", "right":
        ax.spines[spine].set_visible(False)

    ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)

    return ax


def plot_legend(
    patch_colors: dict[str, str], ax: Optional[mpl.axes.Axes] = None, **kwds
) -> mpl.legend.Legend:
    """Plot a legend for the given patch colors.

    Args:
        patch_colors: Dictionary mapping label to color.
        ax: Matplotlib Axes to plot the legend on. If None, use current Axes.
        **kwds: Passed to ax.legend.

    Returns:
        The legend object.
    """
    ax = ax or plt.gca()
    handles, labels = zip(
        *((mpl.patches.Patch(color=v), k) for k, v in patch_colors.items())
    )
    return ax.legend(handles, labels, **kwds)


def get_vars_with_dims(
    dataset: xr.Dataset,
    dims: tuple[str, ...] = ("chain", "draw"),
    include_hidden: bool = False,
) -> list[str]:
    """
    Get the names of variables in a dataset that have specific dimensions.

    Args:
        dataset: The dataset to search.
        dims: The dimensions to match.
        include_hidden: Include variables that start with '_'.

    Returns:
        list[str]: A list of variable names.
    """
    return [
        name
        for name, var in dataset.data_vars.items()
        if var.dims == dims and (include_hidden or not name.startswith("_"))
    ]


def extract_arviz_summary_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    arviz.summary returns a DataFrame whose index contains values like:

        "log_sd_mut_per_sr[035X8O]"

    Here, "log_sd_mut_per_sr", refers to the variable and "035X8O" is a coordinate of
    that variable.

    This function returns a DataFrame where the variable and coordinate have been
    extracted into their own columns.

    Args:
        df: DataFrame returned by arviz.summary.

    Returns:
        A DataFrame with 'variable' and 'coordinate' columns extracted from the index.
    """
    extracted = df.index.to_series().str.extract(r"^([^\[]+)(?:\[(.+)\])?$")
    return df.assign(variable=extracted[0], coordinate=extracted[1])
