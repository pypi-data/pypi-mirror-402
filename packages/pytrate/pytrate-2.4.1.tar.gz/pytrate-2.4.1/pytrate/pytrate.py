"""
Titer models aim to decompose the titer between a particular serum and antigen as a combination of
the effects of the amino acid sequences the antigen and antigen used to generate the serum. Amino
 acid effects are inferred for all pairs of amino acids at sites between sera and
antigens in the data. For example if a serum and antigen have the following sequences:

```
Serum:   EKIRH
Antigen: EHVRK
```

then effects for `EE`, `HK`, `IR` and `RR` would be inferred. `HK` and `IR` are typical
'substitutions' in that they refer to a difference in the amino acid in the serum and
antigen, whereas `EE` and `RR` are 'congruences' because the amino acids are the same in
the serum and antigen. Note that at the second site the serum and antigen have `K` and
`H` respectively but at the fifth site they have `H` and `K` respectively. In these cases
a single term is used to capture both of these pairs, even though the amino acids are
swapped between the antigen and serum. Generally, it is expected that sequence
congruences would tend to increase a serum and antigen's titer, whereas substitutions
would tend to decrease it. Amino acid substitutions and congruences (pairs of amino
acids) are modelled as:

$$
\\beta_\\text{pair} \\sim \\text{Normal}(\\mu_\\text{pair}, \\sigma_\\text{pair})
$$

so that they can affect a titer either positively or negatively. The hyperpriors
$\\mu_\\text{pair}$ and $\\sigma_\\text{pair}$ control the degree of partial pooling among
amino acid pairs and have the priors:

$$
\\begin{align}
    \\mu_\\text{pair} &\\sim \\text{Normal}(0, 0.5) \\\\
    \\sigma_\\text{pair} &\\sim \\text{Exponential}(1)
\\end{align}
$$

**Sequence site effects**

The sequence location of amino acid substitutions or congruences affects titers. We model
this by assigning each sequence location a value between 0 and 1, where 0 effectively
'turns off' the effects of amino acid pairs at that location, 1 'turns them on', and
intermediate values modulate them. Concretely:

$$
\\begin{align}
    \\mu_{\\text{site}} &\\sim \\text{Normal(-2, 0.5)} \\\\
    \\sigma_{\\text{site}} &\\sim \\text{Exponential(1)} \\\\
    \\beta_\\text{site} &\\sim \\text{invlogit}(\\text{Normal}(\\mu_{\\text{site}}, \\sigma_{\\text{site}}))
\\end{align}
$$

where invlogit is the inverse logit function: $\\text{invlogit}(x) =1 / (1 +
\\text{exp}(-x))$. These priors weakly reflect the assumption that amino acid pairs at
most sites would have a negligible effect on titer.

**Per-serum, per-antigen  and covariates**

It is common for particular sera or antigens to consistently generate generally high or
low titers, and for these effect sizes to be variable. These antigen and serum effects
are captured as:

$$
\\begin{align}
    \\beta_\\text{ag} &\\sim \\text{Normal}(\\mu_\\text{ag}, \\sigma_\\text{ag}) \\\\
    \\beta_\\text{sr} &\\sim \\text{Normal}(\\mu_\\text{sr}, \\sigma_\\text{sr})
\\end{align}
$$

where again, the degree of partial pooling among effect sizes are captured by the
hyperpriors:

$$
\\begin{align}
    \\mu_\\text{ag} &\\sim \\text{Normal}(0, 0.5) \\\\
    \\mu_\\text{sr} &\\sim \\text{Normal}(0, 0.5) \\\\
    \\sigma_\\text{ag} &\\sim \\text{Exponential}(1) \\\\
    \\sigma_\\text{sr} &\\sim \\text{Exponential}(1)
\\end{align}
$$

Finally any other general covariates associated with a titration are captured as:

$$
\\beta_\\text{cov} \\sim \\text{Normal}(0, 1)
$$

**Titer model**

The effects of amino acid pairs ($\\beta_\\text{pair}$), sequence sites
($\\beta_\\text{site}$), antigens ($\\beta_\\text{ag}$), sera ($\\beta_\\text{sr}$) and
covariates ($\\beta_\\text{cov}$) are combined to model the log titers measured between
sera and antigens. If $T$ titers are measured and there are $S$ sequence sites then $aa$
is an $(T, S)$ index constructed such that $aa_{t,s}$ indexes the amino acid substitution
or congruence at site $s$ for the serum and antigen used to measure titer $t$. $a$ and
$s$ index the antigen and serum used in each titration. $X$ is an $(T, n)$ array of $n$
covariates associated with each titration, and $c$ is a constant term with prior
$\\text{Normal}(0, 1)$. Log-titers, $l$, are computed as $\\text{log}_2(\\text{titer}/10)$
and are modelled as:

$$
\\begin{align}
    \\mu_\\text{titer} &= \\beta_{\\text{pair},aa} \\times \\beta_\\text{site} +
    \\beta_{\\text{ag},a} + \\beta_{\\text{sr},s} + X \\times \\beta_\\text{cov} + c \\\\
    \\sigma_\\text{titer} &\\sim \\text{Exponential}(1) \\\\
    l &\\sim \\text{Normal}(\\mu_\\text{titer}, \\sigma_\\text{titer})
\\end{align}
$$

Importantly, because $aa$ is a 2D index, the term $\\beta_{\\text{pair},aa}$ generates a
$(T, S)$ array.

**Threshold titers**

A titer of 10 corresponds to a log-titer of 0 and it is assumed that any log-titer
between -0.5 and 0.5 would result in a titer of 10 (ignoring measurement error).
Therefore a log-titer below -0.5 would result in a below threshold titer (<10). The
likelihood of <10 titers can therefore be captured using the Normal cumulative
distribution function with mean $\\mu_\\text{titer}$ and standard deviation
$\\sigma_\\text{titer}$ at a value of -0.5:

$$
m \\sim \\text{NormalCDF}(\\mu_\\text{titer}, \\sigma_\\text{titer}, x=-0.5)
$$
"""

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm
import pytensor
import xarray as xr

from operator import attrgetter
from typing import Optional, Literal, Iterable

from . import helper
from .modelbase import TiterModelBase
from .seqdf import SeqDf, Substitution


class CrossedSiteAaModel(TiterModelBase):
    def __init__(
        self,
        sequences: pd.DataFrame | SeqDf,
        titers: pd.Series,
        constrain_aa_effects: bool,
        symmetric_aas: bool,
        covariates: Optional[pd.DataFrame] = None,
        allow_unknown_aa: bool = False,
    ) -> None:
        """
        Holds data and constructs a Bayesian model for conducting a crossed amino acid
        change, site titer regression.

        Args:
            sequences: DataFrame containing sequences for all antigens and sera. Columns
                are sequence sites, rows are names of antigens and sera. The
                'sequence' of a serum is the sequence of the antigen used to raise that
                serum.
            titers: Series that has a multilevel index of (antigen, serum) and values are
                titers.
            constrain_aa_effects: Force the effects of substitutions to be negative and
                congruences to be positive. A substitution is an amino acid pair where
                the amino acids do not match (e.g. "NK" and "HS"). A congruence is a pair
                where the amino acids do match (e.g. "NN", "SS").
            symmetric_aas: If False, then estimate separate effects for "NK" and "KN".
            covariates: Optional DataFrame containing additional covariates to include in
                the regression for each (antigen, serum) pair. Rows correspond to
                (antigen, serum) pairs. Columns contain the covariates. Must be the same
                length as titers and have an identical index.
            allow_unknown_aa: Set to True to estimate effects for amino acid pairs
                involving "X".

        Attributes:
            n_titers: (int) number of titrations, (i.e. 'pairs' of antigens and sera).
            n_sites: (int) number of sites to estimate effects for. Only
                sites that are variable in `sequences` are considered.
            titers: (n_titers,) pd.Series of the raw titer values. Multilevel index of
                (antigen, serum).
            Y: (n_titers,) array of log2(titer/10) titer values. <10 is represented as -1,
                although threshold values are handled by the model as < 0 on the log
                scale.
            aa_uniq: tuple[str] of all unique pairs of amino acids (including pairs where
                the amino acids match such as 'NN') between sera and antigens in sequences.
            aa: (n_titers, n_site) array containing the index of the substitution for this
                serum-antigen combination at this site.
            ags,srs: (n_titers,) pd.Categorical of the antigens or sera used in each
                titration.
            c: (n_titers,) boolean array. True in this array means the titer is 'censored'
                (i.e. threshold titers).
            n: (n_titers,) boolean array. False corresponds to regular/numeric titers.
        """
        super().__init__(
            sequences=sequences,
            titers=titers,
            covariates=covariates,
            allow_unknown_aa=allow_unknown_aa,
        )

        self.constrain_aa_effects = constrain_aa_effects
        self.symmetric_aas = symmetric_aas

        # All amino acid changes in the alignment
        self.aa_uniq = tuple(
            sorted(
                str(aa)
                for aa in self.seqdf.amino_acid_changes_sequence_pairs(
                    self.titers.index, symmetric=symmetric_aas
                )
            )
        )

        # List where 0 indicates a substitution and 1 indicates a congruence
        self.aa_sign = np.array([-1.0 if aa[0] != aa[1] else 1.0 for aa in self.aa_uniq])

        # aa is an array that for each pair at each site indexes into the aa
        # parameter vector
        self.aa = np.empty((self.n_titers, self.n_sites), dtype=np.int32)
        for i, (ag, sr) in enumerate(self.titers.index):
            if not symmetric_aas:
                aa_pairs = self.seqdf.df.loc[[ag, sr]].apply("".join)
            else:
                aa_pairs = self.seqdf.df.loc[[ag, sr]].apply(sorted).apply("".join)

            for j, aa_pair in enumerate(aa_pairs):
                self.aa[i, j] = self.aa_uniq.index(aa_pair)

    def __repr__(self):
        return (
            f"CrossedSiteAaModel(sequences={self.seqdf}, titers={self.titers}, "
            f"constrain_aa_effects={self.constrain_aa_effects} "
            f"symmetric_aas={self.symmetric_aas} "
            f"covariates={self.covs})"
        )

    @property
    def coords(self) -> dict[str, Iterable[str | int]]:
        """
        Model coordinates.
        """
        coords = {
            "aa": self.aa_uniq,
            "site": self.seqdf.df.columns,
            "ag": self.ags.categories,
            "sr": self.srs.categories,
        }

        if self.covs is not None:
            coords["covs"] = self.cov_names

        return coords

    def calculate_titer(
        self,
        b_site: "pytensor.tensor.TensorVariable",
        b_aa: "pytensor.tensor.TensorVariable",
        b_ag: "pytensor.tensor.TensorVariable",
        b_sr: "pytensor.tensor.TensorVariable",
        b_cov: "pytensor.tensor.TensorVariable",
        b_const: "pytensor.tensor.TensorVariable",
        suffix: Literal["u", "c"],
        mask: Optional[np.ndarray] = None,
    ):
        """
        Compute titers.

        Args:
            suffix: "u" uncensored, or "c" censored titers.
            mask: (n_titers,) boolean array. Include only these antigen-serum pairs.
        """
        if mask is None:
            mask = np.repeat(True, self.n_titers)

        aa = pm.Data(f"aa_{suffix}", self.aa[mask])
        ags = pm.Data(f"ags_{suffix}", self.ags.codes[mask])
        srs = pm.Data(f"srs_{suffix}", self.srs.codes[mask])

        if self.covs is None:
            return b_aa[aa] @ b_site + b_ag[ags] + b_sr[srs] + b_const

        else:
            covs = pm.Data(f"covs_{suffix}", self.covs[mask])
            return b_aa[aa] @ b_site + b_ag[ags] + b_sr[srs] + covs @ b_cov + b_const

    def make_variables(self) -> dict[str, "pytensor.tensor.TensorVariable"]:
        # sites
        # 0-1 values that 'turn on/off' the effect of amino acid pairs
        b_site_raw = helper.hierarchical_noncentered_normal(
            "b_site_raw", hyper_mu=-2.0, hyper_sigma=1.0, dims="site"
        )
        b_site = pm.Deterministic("b_site", pm.math.invlogit(b_site_raw), dims="site")

        # Amino acids
        if self.constrain_aa_effects:
            # Positive effects for congruences
            # Negative effects for substitutions
            raw_b_aa = helper.hierarchical_noncentered_normal(
                "_raw_b_aa", dims="aa", lognormal=True
            )
            b_aa = pm.Deterministic("b_aa", self.aa_sign * raw_b_aa, dims="aa")
        else:
            b_aa = helper.hierarchical_noncentered_normal("b_aa", dims="aa")

        # Per-antigen / per-serum effects
        b_ag = helper.hierarchical_noncentered_normal("b_ag", dims="ag")
        b_sr = helper.hierarchical_noncentered_normal("b_sr", dims="sr")

        # Covariates
        b_cov = (
            pm.Normal("b_cov", 0.0, 1.0, dims="covs") if self.covs is not None else None
        )

        # Intercept and error
        b_const = pm.Normal("b_const", 0.0, 1.0)

        return dict(
            b_site=b_site,
            b_aa=b_aa,
            b_ag=b_ag,
            b_sr=b_sr,
            b_cov=b_cov,
            b_const=b_const,
        )

    def set_data(self, mask: np.ndarray, suffix: Literal["u", "c"]) -> None:
        """
        Set data in a pymc model context.

        Args:
            mask: (n_titers,) boolean array with True for titers to include.
            suffix: "u" for uncensored data or "c" for censored data.
        """
        data = {
            f"aa_{suffix}": self.aa[mask],
            f"ags_{suffix}": self.ags.codes[mask],
            f"srs_{suffix}": self.srs.codes[mask],
            f"Y_{suffix}": self.Y[mask],
        }

        if self.covs is not None:
            data[f"covs_{suffix}"] = self.covs[mask]

        pm.set_data(data)

    def combined_site_aa_effects(self, idata: az.InferenceData) -> xr.DataArray:
        """
        DataArray containing all amino acid x site effects. Amino acid effects just
        report the effects of an amino acid pair (e.g. 'NK'). site effects just
        report the effects of a site (e.g. 145). This array contains the product of
        amino acid and site effects (e.g. 'NK145') for all combinations of amino
        acids found at sites in the dataset.

        Args:
            idata: InferenceData object containing posterior samples. (Must contain
                b_aa and b_site with 'aa' and 'site' coords.)
        """
        site_aa_combined = sorted(
            set(
                self.seqdf.site_aa_combinations(
                    symmetric_aa=self.symmetric_aas, sequence_pairs=self.titers.index
                )
            )
        )
        sites, aa_pairs = zip(*site_aa_combined)
        b_site = idata.posterior.sel(site=list(sites))["b_site"]
        b_aa = idata.posterior.sel(aa=list(aa_pairs))["b_aa"]

        if b_site.dims[:-1] != b_aa.dims[:-1]:
            raise ValueError("b_site and b_aa have different leading dims")

        return xr.DataArray(
            b_site.values * b_aa.values,
            dims=(*b_site.dims[:-1], "aa_site"),
            name="b_aa_site",
            coords=dict(
                aa_site=[
                    f"{aa}{site}"
                    for aa, site in zip(b_aa.indexes["aa"], b_site.indexes["site"])
                ]
            ),
        )


class CombinedSiteAaModel(TiterModelBase):
    def __init__(
        self,
        sequences: pd.DataFrame | SeqDf,
        titers: pd.Series,
        covariates: Optional[pd.DataFrame] = None,
        allow_unknown_aa: bool = False,
    ):
        """
        Holds data and constructs a Bayesian model for conducting a combined amino acid
        change, site titer regression.

        Args:
            sequences: DataFrame containing sequences for all antigens and sera. Columns
                are sequence sites, rows are names of antigens and sera. The
                'sequence' of a serum is the sequence of the antigen used to raise that
                serum.
            titers: Series that has a multilevel index of (antigen, serum) and values are
                titers.
            covariates: Optional DataFrame containing additional covariates to include in
                the regression for each (antigen, serum) pair. Rows correspond to
                (antigen, serum) pairs. Columns contain the covariates. Must be the same
                length as titers and have an identical index.
            allow_unknown_aa: Set to True to estimate effects for amino acid pairs
                involving "X".

        Attributes:
            n_titers: (int) number of titrations, (i.e. 'pairs' of antigens and sera).
            n_sites: (int) number of sites to estimate effects for. Only
                sites that are variable in `sequences` are considered.
            titers: (n_titers,) pd.Series of the raw titer values. Multilevel index of
                (antigen, serum).
            Y: (n_titers,) array of log2(titer/10) titer values. <10 is represented as -1,
                although threshold values are handled by the model as < 0 on the log
                scale.
            site_aa_uniq: tuple[str] of all unique site-amino acid combinations, e.g. N145K.
            site_aa: (n_titers, n_sites) array containing the index of the site-amino
                acid combination for this serum-antigen pair at this site.
            ags,srs: (n_titers,) pd.Categorical of the antigens or sera used in each
                titration.
            c: (n_titers,) boolean array. True in this array means the titer is 'censored'
                (i.e. threshold titers).
            n: (n_titers,) boolean array. False corresponds to regular/numeric titers.
        """

        super().__init__(
            sequences=sequences,
            titers=titers,
            covariates=covariates,
            allow_unknown_aa=allow_unknown_aa,
        )

        #: Unique site - amino acid changes in the alignment.
        self.site_aa_uniq = tuple(
            str(site_aa)
            for site_aa in sorted(
                self.seqdf.site_amino_acid_changes_sequence_pairs(self.titers.index),
                key=attrgetter("site", "aa_lost", "aa_gained"),
            )
        )

        #: np.ndarray containing the index of the site_aa combination
        self.site_aa = np.empty((self.n_titers, self.n_sites), dtype=np.int32)
        for i, (ag, sr) in enumerate(self.titers.index):
            for j, site in enumerate(self.seqdf.df.columns):
                a, b = self.seqdf.df.loc[[ag, sr], site]
                a_site_b = str(Substitution(a, site, b))
                self.site_aa[i, j] = self.site_aa_uniq.index(a_site_b)

    def __repr__(self):
        return (
            f"CombinedSiteAaModel(sequences={self.seqdf}, titers={self.titers}, "
            f"covariates={self.covs})"
        )

    @property
    def coords(self) -> dict[str, Iterable[str | int]]:
        """
        Model coordinates.
        """
        coords = {
            "site_aa": self.site_aa_uniq,
            "site": self.seqdf.df.columns,
            "ag": self.ags.categories,
            "sr": self.srs.categories,
        }

        if self.covs is not None:
            coords["covs"] = self.cov_names

        return coords

    def calculate_titer(
        self,
        b_site_aa: "pytensor.tensor.TensorVariable",
        b_ag: "pytensor.tensor.TensorVariable",
        b_sr: "pytensor.tensor.TensorVariable",
        b_cov: "pytensor.tensor.TensorVariable",
        b_const: "pytensor.tensor.TensorVariable",
        suffix: Literal["u", "c"],
        mask: Optional[np.ndarray] = None,
    ):
        """
        Compute titers.

        Args:
            suffix: "u" uncensored, or "c" censored titers.
            mask: (n_titers,) boolean array. Include only these antigen-serum pairs.
        """
        if mask is None:
            mask = np.repeat(True, self.n_titers)

        site_aa = pm.Data(f"site_aa_{suffix}", self.site_aa[mask])
        ags = pm.Data(f"ags_{suffix}", self.ags.codes[mask])
        srs = pm.Data(f"srs_{suffix}", self.srs.codes[mask])

        if self.covs is None:
            return b_site_aa[site_aa].sum(axis=1) + b_ag[ags] + b_sr[srs] + b_const

        else:
            covs = pm.Data(f"covs_{suffix}", self.covs[mask])
            return (
                b_site_aa[site_aa].sum(axis=1)
                + b_ag[ags]
                + b_sr[srs]
                + covs @ b_cov
                + b_const
            )

    def make_variables(self) -> dict[str, "pytensor.tensor.TensorVariable"]:
        # Site - amino acid combined effects
        b_site_aa = helper.hierarchical_noncentered_normal("b_site_aa", dims="site_aa")

        # Per-antigen / per-serum effects
        b_ag = helper.hierarchical_noncentered_normal("b_ag", dims="ag")
        b_sr = helper.hierarchical_noncentered_normal("b_sr", dims="sr")

        # Covariates
        b_cov = (
            pm.Normal("b_cov", 0.0, 1.0, dims="covs") if self.covs is not None else None
        )

        # Intercept and error
        b_const = pm.Normal("b_const", 0.0, 1.0)

        return dict(
            b_site_aa=b_site_aa, b_ag=b_ag, b_sr=b_sr, b_cov=b_cov, b_const=b_const
        )

    def set_data(self, mask: np.ndarray, suffix: Literal["u", "c"]) -> None:
        """
        Set data in a pymc model context.

        Args:
            mask: (n_titers,) boolean array with True for titers to include.
            suffix: "u" for uncensored data or "c" for censored data.
        """
        data = {
            f"site_aa_{suffix}": self.site_aa[mask],
            f"ags_{suffix}": self.ags.codes[mask],
            f"srs_{suffix}": self.srs.codes[mask],
            f"Y_{suffix}": self.Y[mask],
        }

        if self.covs is not None:
            data[f"covs_{suffix}"] = self.covs[mask]

        pm.set_data(data)

    @staticmethod
    def data_shape(model: pm.Model) -> dict[str, tuple]:
        """The shape of data currently set on the model."""
        shapes = {}
        for suffix in "u", "c":
            for variable in "site_aa", "ags", "srs", "Y":
                key = f"{variable}_{suffix}"
                try:
                    shapes[key] = model[key].eval().shape
                except KeyError:
                    continue
        return shapes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run either the combined or crossed model."
    )
    parser.add_argument("titer_file", type=str, help="CSV file containing titer data")
    parser.add_argument(
        "sequence_file", type=str, help="CSV file containing sequence data"
    )
    parser.add_argument(
        "--model",
        choices=["combined", "crossed"],
        required=True,
        help="Which model to run",
    )
    parser.add_argument("netcdf_path", type=str, help="Path to the netCDF file to write")
    parser.add_argument(
        "--chains", type=int, default=10, help="Number of chains (default: 10)"
    )

    args = parser.parse_args()

    titers = pd.read_csv(args.titer_file, index_col=[0, 1]).squeeze()
    sequences = pd.read_csv(args.sequence_file, index_col=0)

    if args.model == "combined":
        model = CombinedSiteAaModel(
            sequences=sequences, titers=titers, allow_unknown_aa=True
        )

    elif args.model == "crossed":
        model = CrossedSiteAaModel(
            sequences=sequences,
            titers=titers,
            constrain_aa_effects=False,
            symmetric_aas=False,
            allow_unknown_aa=True,
        )

    else:
        raise ValueError(f"Unknown model: {args.model}")

    model.sample(netcdf_path=args.netcdf_path, use_nutpie=True, chains=args.chains)
