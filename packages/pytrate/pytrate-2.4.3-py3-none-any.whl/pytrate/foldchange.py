"""
Fold change models work by decomposing differences in titers between mutants and their
parent (or _root_) viruses as a linear additive combination of the mutant's amino acid
substitutions.

$$T_{m,s} = X \\beta + T_{r_m,s}$$

where:

- $T_{m,s}$ is the titer between a mutant ($m$) and serum ($s$).
- $T_{r_m,s}$ is the titer between the root used to make mutant $m$ ($r_m$) and serum
    ($s$).
- $X \\beta$ captures the linear additive combination of the substitutions ($X$) and the
    effect sizes of each substitution ($\\beta$).
"""

import re

import numpy as np
import pandas as pd
import pymc as pm

from pytensor import sparse, tensor

from . import helper


class FoldChangeModel:

    def __init__(
        self,
        df_root: pd.DataFrame,
        df_mut: pd.DataFrame,
        mutant_subs: dict[str, list[str]],
    ) -> None:
        """
        Args:
            df_root: DataFrame containing root titers. Index must be `'antigen'`. Columns
                must contain `"serum"` and `"log_titer"`. `"root"` must be present in the
                `df_root` index.
            df_mut: DataFrame containing root titers. Index must be `'antigen'`. Columns
                must contain `"serum"`, `"log_titer"` and `"root"`. Value of `"root"`
                must be present in the `df_root` index.
            mutant_subs: Dict that maps a mutant to its substitutions.
        """
        if df_mut.index.name != "antigen":
            raise ValueError("df_mut index must be named 'antigen'")

        if df_root.index.name != "antigen":
            raise ValueError("df_root index must be named 'antigen'")

        if missing := set(mutant_subs) - set(df_mut.index):
            raise ValueError(f"mutant(s) {missing} in mutant_subs missing from df_mut")

        if missing := set(df_mut.index) - set(mutant_subs):
            raise ValueError(f"mutant(s) {missing} in df_mut missing from mutant_subs")

        ##############
        # DataFrames #
        ##############

        #: DataFrame containing root titers.
        self.df_root = df_root

        #: DataFrame containing mutant titers.
        self.df_mut = df_mut

        ###########
        # Factors #
        ###########

        #: All root viruses.
        self.roots = sorted(set(df_root.index))

        #: All individual mutants.
        self.mutants = sorted(set(df_mut.index))

        #: All antigens.
        self.antigens = sorted(set(self.roots + self.mutants))

        #: All (serum, root) combinations.
        self.root_sr_pairs = helper.NDFactor(df_root["serum"].items())

        #: All individual sera.
        self.sera = tuple(sorted(set(serum for _, serum in self.root_sr_pairs.values)))

        #: Tables
        self.tables = sorted(set(df_root["table_id"]) | set(df_mut["table_id"]))

        #################
        # Substitutions #
        #################

        #: Dictionary that maps each mutant to its substitutions
        self.mutant_subs = mutant_subs

        #: Substitutions for each mutant merged such that any set of substitutions that
        #: always appear together are grouped. See `helper.merge_maximal_subgroup_subs`
        #: for details.
        self.mutant_subs_merged = helper.merge_maximal_subgroup_subs(mutant_subs)

        if missing_after_merge := set(self.mutant_subs) - set(self.mutant_subs_merged):
            raise ValueError(
                f"`merge_maximal_subgroup_subs` dropped antigens: {missing_after_merge}"
            )

        if introduced_by_merge := set(self.mutant_subs_merged) - set(self.mutant_subs):
            raise ValueError(
                f"`merge_maximal_subgroup_subs` introduced antigens: {introduced_by_merge}"
            )

        #: All individual substitutions.
        self.subs = tuple(sorted(set(helper.unpack(self.mutant_subs_merged.values()))))

        def gen_sub_serums():
            for ag, sr in (
                self.df_mut.reset_index()[["antigen", "serum"]].drop_duplicates().values
            ):
                yield from ((sub, sr) for sub in self.mutant_subs_merged[ag])

        self.sub_serum = helper.NDFactor(list(gen_sub_serums()))

        #: `np.ndarray` (n. mutant titrations, n. (sub, serum) combinations) encoding the
        #: substitutions this mutant has, and the sera that they are titrated against in
        #: each row of `df_mut`.
        self.X = np.zeros((len(df_mut), len(self.sub_serum)))
        for i, row in enumerate(df_mut.itertuples()):
            mutant = row.Index
            for sub in self.mutant_subs_merged[mutant]:
                j = self.sub_serum.index((sub, row.serum))
                self.X[i, j] = 1.0
        self.X = self.X.astype(int)

        #: Sparse representation of `X`.
        self.X_sparse = sparse.csr_from_dense(tensor.as_tensor(self.X))

        #: DataFrame version of `X`, with appropriate column and index.
        self.df_X = pd.DataFrame(
            self.X,
            index=self.df_mut.set_index("serum", append=True).index,
            columns=self.sub_serum.values,
        )

        ###########
        # Indexes #
        ###########

        #: Index mapping table to `df_root`
        self.table_root_idx = df_root["table_id"].apply(self.tables.index).values

        #: Index mapping table to `df_mut`
        self.table_mut_idx = df_mut["table_id"].apply(self.tables.index).values

        #: Index mapping (root, serum) pairs to `df_root`.
        self.root_sr_idx = self.root_sr_pairs.make_index(
            df_root.reset_index()[["antigen", "serum"]]
        )

        #: Index mapping (serum,) to `df_root`.
        self.root_per_sr_idx = df_root["serum"].apply(self.sera.index).values

        #: Index mapping (antigen,) to `df_root`.
        self.root_per_ag_idx = np.array(
            [self.roots.index(root) for root in df_root.index]
        )

        #: Index mapping (serum,) to `df_mut`.
        self.mut_per_sr_idx = df_mut["serum"].apply(self.sera.index).values

        #: Index mapping (antigen,) to `df_mut`.
        self.mut_per_ag_idx = np.array([self.mutants.index(mut) for mut in df_mut.index])

        #: Index mapping (root, serum) pairs to `df_mut`.
        self.root_idx = self.root_sr_pairs.make_index(df_mut[["root", "serum"]])

        #: Index mapping (sub, serum) pairs to substitutions in `subs`.
        self.sub_idx = [self.subs.index(sub) for sub, _ in self.sub_serum.values]

        independent_subs = set([sub for sub in self.subs if "+" not in sub])

        def site_from_sub(sub: str) -> int:
            return int(re.search(r"\w(\d+)\w", sub).groups()[0])

        #: All sites that occur in substitutions.
        self.sites = sorted(set(site_from_sub(sub) for sub in independent_subs)) + ["+"]

        #: Index mapping substitution sites to substitutions. If `sites_in_hierarchy` is
        #: used. All groups of substitutions that always occur together share a
        #: hyperprior. E.g. 'A127S', 'A127T', 'A127V', all share one prior distribution
        #: because they all occur at site 127. 'D124H+R145G', 'D124N+A263E',
        #: 'D237N+N273S' (and all other "subs" that are actually multiple substitutions
        #: that always occur together) also share one single (hyper) prior.
        self.site_idx = [
            (
                self.sites.index("+")
                if "+" in sub
                else self.sites.index(site_from_sub(sub))
            )
            for sub in self.subs
        ]

    def __repr__(self) -> str:
        return (
            f"FoldChangeModel(df_root={self.df_root}, df_mut={self.df_mut}, "
            f"mutant_subs={self.mutant_subs})"
        )

    def model(
        self,
        use_noncentered: bool = True,
        site_in_hierarchy: bool = False,
        student_t_b_sub_serum: bool = False,
        student_t_b_sub: bool = False,
        student_t_lik: bool = False,
    ) -> pm.Model:
        """
        PyMC model representation of the fold change model.

        Args:
            use_noncentered: Use non-centered parametrisations for normal distributions
                with hierarchical priors.
            site_in_hierarchy: Include sites in the model hierarchy.
            student_t_b_sub_serum: Use a Student-T distribution as the prior for
                b_sub_serum. If False, use a Normal.
            student_t_b_sub: Use a Student-T distribution as the prior for b_sub.
            student_t_lik: Use a Student-T distribution for the likelihood.
        """

        hier_normal = (
            helper.hierarchical_noncentered_normal
            if use_noncentered
            else helper.hierarchical_normal
        )

        coords = dict(
            root_sr=self.root_sr_pairs.labels,
            sub=self.subs,
            serum=self.sera,
            sub_serum=self.sub_serum.labels,
            site=self.sites,
            table=self.tables,
        )

        with pm.Model(coords=coords) as model:

            #################
            # Table effects #
            #################

            T_table = hier_normal(
                "T_table", dims="table", hyper_mu=0.0, hyper_sigma=1.0, hyper_lam=2.0
            )

            ###############
            # Root titers #
            ###############

            # Per-serum effect
            serum = hier_normal("b_serum", dims="serum")

            T_root = hier_normal("T_root", dims="root_sr")
            T_root_mu = (
                T_root[self.root_sr_idx]
                + serum[self.root_per_sr_idx]
                + T_table[self.table_root_idx]
            )

            T_root_sd = pm.Exponential("T_root_obs_sd", 2.0)

            T_latent_root = (
                pm.StudentT.dist(
                    mu=T_root_mu,
                    sigma=T_root_sd,
                    nu=pm.Exponential("T_root_obs_nu", 2.0),
                )
                if student_t_lik
                else pm.Normal.dist(mu=T_root_mu, sigma=T_root_sd)
            )

            # Root titer likelihood
            pm.Censored(
                "T_root_obs",
                T_latent_root,
                observed=self.df_root["log_titer"].values,
                lower=-1.0,
                upper=None,
            )

            ################
            # Delta titers #
            ################

            # Substitution effects
            if student_t_b_sub and site_in_hierarchy:
                raise NotImplementedError

            elif student_t_b_sub:
                b_sub = pm.StudentT(
                    "b_sub",
                    mu=pm.Normal("b_sub_mu", 0.0, 0.5),
                    sigma=pm.Exponential("b_sub_sigma", 2.0),
                    nu=pm.Exponential("b_sub_nu", 1.0),
                    dims="sub",
                )

            elif site_in_hierarchy:
                site = hier_normal("b_site", dims="site")
                b_sub = hier_normal("b_sub", dims="sub", hyper_mu=site[self.site_idx])

            else:
                b_sub = hier_normal("b_sub", dims="sub")

            # Individual effects of each substitution in each serum
            b_sub_serum_kwds = dict(
                name="b_sub_serum",
                mu=b_sub[self.sub_idx],
                sigma=pm.Exponential("b_sub_serum_sd", 2.0),
                dims="sub_serum",
            )

            b_sub_serum = (
                pm.StudentT(nu=pm.Exponential("b_sub_serum_nu", 1.0), **b_sub_serum_kwds)
                if student_t_b_sub_serum
                else pm.Normal(**b_sub_serum_kwds)
            )

            # Titer difference (delta titer) is linear sum of each mutant's substitutions
            T_delta = sparse.dot(self.X_sparse, b_sub_serum[:, None]).flatten()

            #################
            # Mutant titers #
            #################

            # Mutant titers are simply: root titer + delta titer
            T_mut_mu = T_root[self.root_idx] + T_delta + T_table[self.table_mut_idx]

            # Mutant titer observation error
            T_mut_sd = pm.Exponential("T_mut_obs_sd", 2.0)

            # Likelihood
            if student_t_lik:
                T_mut_nu = pm.Exponential("T_mut_obs_nu", 2.0)
                T_latent_mut = pm.StudentT.dist(mu=T_mut_mu, sigma=T_mut_sd, nu=T_mut_nu)

            else:
                T_latent_mut = pm.Normal.dist(mu=T_mut_mu, sigma=T_mut_sd)

            pm.Censored(
                "T_mut_obs",
                T_latent_mut,
                observed=self.df_mut["log_titer"].values,
                lower=-1.0,
                upper=None,
            )

        return model

    def model_per_ag_sr_sd(
        self,
        use_noncentered: bool = True,
        student_t_lik: bool = False,
    ) -> pm.Model:
        """
        Fold change model with per-antigen and per-serum measurement SD.

        Args:
            use_noncentered: Use non-centered parametrisations for normal distributions
                with hierarchical priors.
            student_t_lik: Use a Student-T distribution for the likelihood.
        """

        hier_normal = (
            helper.hierarchical_noncentered_normal
            if use_noncentered
            else helper.hierarchical_normal
        )

        coords = dict(
            sub=self.subs,
            serum=self.sera,
            root=self.roots,
            mutant=self.mutants,
            root_sr=self.root_sr_pairs.labels,
            sub_serum=self.sub_serum.labels,
            antigen=self.antigens,
            table=self.tables,
        )

        with pm.Model(coords=coords) as model:

            #################
            # Table effects #
            #################

            T_table = hier_normal(
                "T_table", dims="table", hyper_mu=0.0, hyper_sigma=1.0, hyper_lam=2.0
            )

            #############################
            # Per antigen, per serum SD #
            #############################

            log_sd_intercept = pm.Normal("log_sd_intercept", 0.0, 0.5)

            # These hyper priors were selected such that the prior sd of any individual
            # measurement is approximately Exponential(1)

            # Antigens and sera hierarchies will both share this single, overarching,
            # hyper parameter so that there can be some partial pooling among sera and
            # antigen SD variables.
            hyper_mu = pm.Normal("log_sd_hyper_mu", 0.0, 0.5)

            sd_hyper = dict(hyper_mu=hyper_mu, hyper_sigma=0.25, hyper_lam=5.0)

            log_sd_ag = hier_normal("log_sd_ag", dims="antigen", **sd_hyper)
            log_sd_sr = hier_normal("log_sd_sr", dims="serum", **sd_hyper)

            ###############
            # Root titers #
            ###############

            # Per-serum effect
            serum = hier_normal("b_serum", dims="serum")

            T_root = hier_normal("T_root", dims="root_sr")
            T_root_mu = (
                T_root[self.root_sr_idx]
                + serum[self.root_per_sr_idx]
                + T_table[self.table_root_idx]
            )

            # Observation SD
            sd_root = tensor.exp(
                log_sd_intercept
                + log_sd_ag[self.root_per_ag_idx]
                + log_sd_sr[self.root_per_sr_idx]
            )

            # Likelihood
            if student_t_lik:
                T_obs_nu = pm.Exponential("T_root_obs_nu", 2.0)
                T_latent_root = pm.StudentT.dist(
                    mu=T_root_mu, sigma=sd_root, nu=T_obs_nu
                )

            else:
                T_latent_root = pm.Normal.dist(mu=T_root_mu, sigma=sd_root)

            pm.Censored(
                "T_root_obs",
                T_latent_root,
                observed=self.df_root["log_titer"].values,
                lower=-1.0,
                upper=None,
            )

            ################
            # Delta titers #
            ################

            # Substitution effects
            b_sub = hier_normal("b_sub", dims="sub")

            # Individual effects of substitutions in each serum
            b_sub_serum = pm.Normal(
                name="b_sub_serum",
                mu=b_sub[self.sub_idx],
                sigma=pm.Exponential("b_sub_serum_sd", 2.0),
                dims="sub_serum",
            )

            # Titer difference (delta titer) is linear sum of each mutant's substitutions
            T_delta = sparse.dot(self.X_sparse, b_sub_serum[:, None]).flatten()

            #################
            # Mutant titers #
            #################

            # Mutant titers are simply: root titer + delta titer
            T_mut_mu = T_root[self.root_idx] + T_delta + T_table[self.table_mut_idx]

            # Observation error
            sd_mut = tensor.exp(
                log_sd_intercept
                + log_sd_ag[self.mut_per_ag_idx]
                + log_sd_sr[self.mut_per_sr_idx]
            )

            # Likelihood
            if student_t_lik:
                T_latent_mut = pm.StudentT.dist(mu=T_mut_mu, sigma=sd_mut, nu=T_obs_nu)

            else:
                T_latent_mut = pm.Normal.dist(mu=T_mut_mu, sigma=sd_mut)

            pm.Censored(
                "T_mut_obs",
                T_latent_mut,
                observed=self.df_mut["log_titer"].values,
                lower=-1.0,
                upper=None,
            )

        return model
