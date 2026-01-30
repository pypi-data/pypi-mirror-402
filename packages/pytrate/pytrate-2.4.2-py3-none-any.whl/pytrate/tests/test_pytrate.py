import numpy as np
import pandas as pd
import pymc as pm
import pytest

import pytrate as pt


class TestCombinedSiteAaModel:
    def test_titer_summary(self, seqdf, titers):
        model = pt.CombinedSiteAaModel(seqdf, titers)
        assert isinstance(model.titer_summary, pd.DataFrame)

    def test_passing_X_raises_value_error(self, seqdf, titers):
        edited_seqdf = seqdf.df.copy()
        edited_seqdf.iloc[0, 0] = "X"
        with pytest.raises(ValueError, match="unrecognised amino acid"):
            pt.CombinedSiteAaModel(edited_seqdf, titers)

    def test_passing_X_with_allow_unknown_aa(self, seqdf, titers):
        """
        Should be able to pass X with allow_unknown argument.
        """
        edited_seqdf = seqdf.df.copy()
        edited_seqdf.iloc[0, 0] = "X"
        pt.CombinedSiteAaModel(edited_seqdf, titers, allow_unknown_aa=True)

    @pytest.mark.slow
    def test_variables_present_no_covariates(self, seqdf, titers):
        with pt.CombinedSiteAaModel(seqdf, titers).model:
            pp = pm.sample_prior_predictive(draws=10)

        assert "b_site_aa" in pp.prior
        assert "b_ag" in pp.prior
        assert "b_sr" in pp.prior
        assert "b_const" in pp.prior
        assert "sd" in pp.prior

    @pytest.mark.slow
    def test_site_aa_terms(self, seqdf, titers):
        """
        seqdf:
                        Site
                        1 2 3 4
                    -----------
        Sequence    a   N C A A
                    b   N S A N
                    c   N S A N
                    d   A C A A
                    e   N S A N

        titers:
            [("a", "b"), ("a", "c"), ("a", "d"), ("a", "e"), ("b", "c")]
        """

        with pt.CombinedSiteAaModel(seqdf, titers).model:
            idata = pm.sample_prior_predictive(draws=10)

        # "A3A" is absent because of call to `remove_invariant`. With no variability at a
        # sequence site, all titrations would get an 'A3A' term, and these types of sites
        # would then be colinear with the intercehelper.
        expect = ["N1A", "N1N", "C2C", "C2S", "S2S", "A4A", "A4N", "N4N"]

        assert expect == list(idata.prior["b_site_aa"].coords["site_aa"].values)

    @pytest.mark.slow
    def test_passing_covariates(self, seqdf, titers, covariates):
        """
        Passing covariates should result in a 'b_cov' variable.
        """
        reg = pt.CombinedSiteAaModel(
            sequences=seqdf, titers=titers, covariates=covariates
        )

        with reg.model:
            idata = pm.sample_prior_predictive(draws=10)

        assert "b_cov" in idata.prior

    def test_covs_in_coords_when_covariates_passed(self, seqdf, titers, covariates):
        reg = pt.CombinedSiteAaModel(
            sequences=seqdf, titers=titers, covariates=covariates
        )

        assert "covs" in reg.coords

    def test_covs_not_in_coords_when_no_covariates_passed(self, seqdf, titers):
        reg = pt.CombinedSiteAaModel(sequences=seqdf, titers=titers)
        assert "covs" not in reg.coords

    @pytest.mark.slow
    def test_train_test_workflow(self, titer_reg_obj):
        titer_reg_obj.make_train_test_sets(random_seed=42, test_proportion=0.1)
        with titer_reg_obj.model:
            titer_reg_obj.set_data(mask=titer_reg_obj.mask_train_u, suffix="u")
            titer_reg_obj.set_data(mask=titer_reg_obj.mask_train_c, suffix="c")
            pm.sample(1, tune=0)


class TestCrossedSiteAaModel:
    def test_titer_summary(self, seqdf, titers):
        model = pt.CrossedSiteAaModel(
            seqdf, titers, constrain_aa_effects=False, symmetric_aas=False
        )
        assert isinstance(model.titer_summary, pd.DataFrame)

    def test_passing_X_raises_value_error(self, seqdf, titers):
        edited_seqdf = seqdf.df.copy()
        edited_seqdf.iloc[0, 0] = "X"
        with pytest.raises(ValueError, match="unrecognised amino acid"):
            pt.CrossedSiteAaModel(
                edited_seqdf, titers, constrain_aa_effects=False, symmetric_aas=False
            )

    def test_passing_X_with_allow_unknown_aa(self, seqdf, titers):
        """
        Should be able to pass X with allow_unknown argument.
        """
        edited_seqdf = seqdf.df.copy()
        edited_seqdf.iloc[0, 0] = "X"
        pt.CrossedSiteAaModel(
            edited_seqdf,
            titers,
            allow_unknown_aa=True,
            constrain_aa_effects=False,
            symmetric_aas=False,
        )

    @pytest.mark.slow
    def test_variables_present_no_covariates(self, seqdf, titers):
        reg = pt.CrossedSiteAaModel(
            seqdf, titers, constrain_aa_effects=False, symmetric_aas=True
        )

        with reg.model:
            pp = pm.sample_prior_predictive(draws=10)

        assert "b_site" in pp.prior
        assert "b_aa" in pp.prior
        assert "b_ag" in pp.prior
        assert "b_sr" in pp.prior
        assert "b_const" in pp.prior
        assert "sd" in pp.prior

    @pytest.mark.slow
    def test_passing_covariates(self, seqdf, titers, covariates):
        """
        Passing covariates should result in a 'b_cov' variable.
        """
        reg = pt.CrossedSiteAaModel(
            sequences=seqdf,
            titers=titers,
            covariates=covariates,
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        with reg.model:
            idata = pm.sample_prior_predictive(draws=10)
        assert "b_cov" in idata.prior

    @pytest.mark.slow
    def test_covariate_variable_names(self, seqdf, titers, covariates):
        reg = pt.CrossedSiteAaModel(
            sequences=seqdf,
            titers=titers,
            covariates=covariates,
            constrain_aa_effects=False,
            symmetric_aas=True,
        )

        with reg.model:
            idata = pm.sample_prior_predictive(draws=10)

        assert "cov1 cov2 cov3".split() == list(
            idata.prior["b_cov"].coords["covs"].values
        )

    def test_covs_in_coords_when_covariates_passed(self, seqdf, titers, covariates):
        reg = pt.CrossedSiteAaModel(
            sequences=seqdf,
            titers=titers,
            covariates=covariates,
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        assert "covs" in reg.coords

    def test_covs_not_in_coords_when_no_covariates_passed(self, seqdf, titers):
        reg = pt.CrossedSiteAaModel(
            sequences=seqdf,
            titers=titers,
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        assert "covs" not in reg.coords

    @pytest.mark.slow
    def test_train_test_workflow(self, titer_reg_obj):
        titer_reg_obj.make_train_test_sets(random_seed=42, test_proportion=0.1)
        with titer_reg_obj.model:
            titer_reg_obj.set_data(mask=titer_reg_obj.mask_train_u, suffix="u")
            titer_reg_obj.set_data(mask=titer_reg_obj.mask_train_c, suffix="c")
            pm.sample(1, tune=1)

    @pytest.mark.slow
    def test_substitution_effects_negative_with_constrain_aa(self, titer_reg_obj_con):
        """
        When passing constrain_aa_effects=True, b_aa effects should be negative for all
        substitutions (amino acid pairs where the amino acids don't match).
        """
        with titer_reg_obj_con.model:
            idata = pm.sample_prior_predictive(draws=10)
        subs = [aa[0] != aa[1] for aa in idata.prior.coords["aa"].values]
        assert (idata.prior["b_aa"].sel(aa=subs) < 0).all()

    @pytest.mark.slow
    def test_substitution_effects_negative_with_constrain_aa_posterior(
        self, titer_reg_obj_con
    ):
        """
        When passing constrain_aa_effects=True, b_aa effects should be negative for all
        substitutions (amino acid pairs where the amino acids don't match).

        Test when sampling a posterior.
        """
        with titer_reg_obj_con.model:
            idata = pm.sample(draws=50)
        subs = [aa[0] != aa[1] for aa in idata.posterior.coords["aa"].values]
        assert (idata.posterior["b_aa"].sel(aa=subs) < 0).all()

    @pytest.mark.slow
    def test_congruence_effects_positive_with_constrain_aa(self, titer_reg_obj_con):
        """
        When passing constrain_aa_effects=True, b_aa effects should be positive for all
        congruences (amino acid pairs where the amino acids match).
        """
        with titer_reg_obj_con.model:
            idata = pm.sample_prior_predictive(draws=10)
        cons = [aa[0] == aa[1] for aa in idata.prior.coords["aa"].values]
        assert (idata.prior["b_aa"].sel(aa=cons) > 0).all()

    @pytest.mark.slow
    def test_congruence_effects_positive_with_constrain_aa_posterior(
        self, titer_reg_obj_con
    ):
        """
        When passing constrain_aa_effects=True, b_aa effects should be positive for all
        congruences (amino acid pairs where the amino acids match).

        Test when sampling a posterior.
        """
        with titer_reg_obj_con.model:
            idata = pm.sample(draws=1, tune=0)
        cons = [aa[0] == aa[1] for aa in idata.posterior.coords["aa"].values]
        assert (idata.posterior["b_aa"].sel(aa=cons) > 0).all()

    @pytest.mark.slow
    def test_substitution_effects_unconstrained_without_constrain_aa(
        self, titer_reg_obj
    ):
        """
        When passing constrain_aa_effects=False, b_aa effects should be negative and
        positive for substitutions.
        """
        with titer_reg_obj.model:
            idata = pm.sample_prior_predictive(draws=10)
        subs = [aa[0] != aa[1] for aa in idata.prior.coords["aa"].values]
        assert (idata.prior["b_aa"].sel(aa=subs) < 0).any()
        assert (idata.prior["b_aa"].sel(aa=subs) > 0).any()

    @pytest.mark.slow
    def test_congruence_effects_unconstrained_without_constrain_aa(self, titer_reg_obj):
        """
        When passing constrain_aa_effects=False, b_aa effects should be negative and
        positive for congruences.
        """
        with titer_reg_obj.model:
            idata = pm.sample_prior_predictive(draws=10)
        cons = [aa[0] == aa[1] for aa in idata.prior.coords["aa"].values]
        assert (idata.prior["b_aa"].sel(aa=cons) < 0).any()
        assert (idata.prior["b_aa"].sel(aa=cons) > 0).any()

    def test_no_aa_terms_if_term_not_in_measured_pair(self):
        """
        It may be that amino acids at a site consist of NKTS resulting in the pairwise
        terms: (NK, NT, NS, KT, KS, TS, NN, KK, TT, SS).

        But it may be the case that only serum-antigen pairs that are titrated have NK
        and TS. So, ensure that only aa terms exist between serum-antigen pairs that are
        titrated.

        In this example only NK and SA should be in aa_uniq.
        """
        titer_reg_obj = pt.CrossedSiteAaModel(
            sequences=pd.DataFrame({1: ["N", "K", "S", "A"]}, index="a b c d".split()),
            titers=pd.Series(
                [10, 20],
                index=pd.MultiIndex.from_tuples(
                    [("a", "b"), ("c", "d")], names=("antigen", "serum")
                ),
            ),
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        assert titer_reg_obj.aa_uniq == ("AS", "KN")

    def test_no_aa_terms_if_term_not_in_measured_pair_multiple_sites(self):
        """
        Like test_no_aa_terms_if_term_not_in_measured_pair, but a test case with multiple
        sites. The additional site here includes 'NS' (between a and b), and the
        congruence 'AA' (between c and d).
        """
        titer_reg_obj = pt.CrossedSiteAaModel(
            sequences=pd.DataFrame(
                {1: ["N", "K", "S", "A"], 2: ["N", "S", "A", "A"]},
                index="a b c d".split(),
            ),
            titers=pd.Series(
                [10, 20],
                index=pd.MultiIndex.from_tuples(
                    [("a", "b"), ("c", "d")], names=("antigen", "serum")
                ),
            ),
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        assert titer_reg_obj.aa_uniq == ("AA", "AS", "KN", "NS")

    def test_aa_terms_unique(self):
        """
        Expect same as test above. Site 3 has introduced NS but the other way around.
        """
        titer_reg_obj = pt.CrossedSiteAaModel(
            sequences=pd.DataFrame(
                {
                    1: ["N", "K", "S", "A"],
                    2: ["N", "S", "A", "A"],
                    3: ["S", "N", "A", "A"],
                },
                index="a b c d".split(),
            ),
            titers=pd.Series(
                [10, 20],
                index=pd.MultiIndex.from_tuples(
                    [("a", "b"), ("c", "d")], names=("antigen", "serum")
                ),
            ),
            constrain_aa_effects=False,
            symmetric_aas=True,
        )
        assert titer_reg_obj.aa_uniq == ("AA", "AS", "KN", "NS")

    def test_antigen_serum_pairs_with_missing_covariates(self, seqdf, titers):
        """
        If covariates is not None and an (antigen, serum) pair in titers is missing from
        covariates, a ValueError should be raised.
        """
        # covariates DataFrame missing the (b, c) titer.
        covariates = pd.DataFrame(
            np.random.randn(5, 3),
            columns=["cov1", "cov2", "cov3"],
            index=pd.MultiIndex.from_tuples(
                [("a", "b"), ("a", "c"), ("a", "d"), ("a", "e"), ("a", "f")]
            ),
        )

        msg = "covariates and titers must have identical indexes"
        with pytest.raises(ValueError, match=msg):
            pt.CrossedSiteAaModel(
                sequences=seqdf,
                titers=titers,
                covariates=covariates,
                constrain_aa_effects=False,
                symmetric_aas=True,
            )
