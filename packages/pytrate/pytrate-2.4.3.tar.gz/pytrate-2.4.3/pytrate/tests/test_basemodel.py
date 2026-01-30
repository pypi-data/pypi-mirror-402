import pytest
import numpy as np
import pandas as pd

import pytrate as pt


class TestBaseModel:
    def test_passing_dataframe_raises_value_error(self, seqdf):
        """Titers should only be allowed to be a pandas series."""
        with pytest.raises(ValueError):
            pt.modelbase.TiterModelBase(sequences=seqdf, titers=pd.DataFrame())

    def test_raises_error_with_missing_seqs(self):
        """
        Test that a ValueError is raised if there is a sequence in titers that is not
        present in sequences.
        """
        sequences = pd.DataFrame(
            {
                1: ["N", "K", "S", "A"],
                2: ["N", "K", "S", "C"],
                3: ["N", "K", "S", "A"],
            },
            index="a b c d".split(),
        )
        titer_index = pd.MultiIndex.from_tuples(
            [("a", "b"), ("c", "e")], names=["antigen", "serum"]
        )
        titers = pd.Series([10, 20], index=titer_index)

        with pytest.raises(ValueError):
            pt.modelbase.TiterModelBase(sequences=sequences, titers=titers)

    def test_covariates_different_length(self, seqdf, titers):
        """If covariates is not None and is a different length to titers, raise an error."""
        covariates = pd.DataFrame(
            np.random.randn(4, 3),
            columns=["cov1", "cov2", "cov3"],
            index=pd.MultiIndex.from_tuples(
                [("a", "b"), ("a", "c"), ("a", "d"), ("a", "e")]
            ),
        )

        msg = "covariates and titers have different length"
        with pytest.raises(ValueError, match=msg):
            pt.modelbase.TiterModelBase(
                sequences=seqdf, titers=titers, covariates=covariates
            )

    def test_grouped_train_test_uncensored_splits(self, titer_reg_obj, subtests):
        """The uncensored train and test splits should combine to be the uncensored data."""
        for train, test in titer_reg_obj.grouped_train_test_sets(n_splits=3):
            with subtests.test():
                assert all(train.uncensored ^ test.uncensored == titer_reg_obj.u)

    def test_grouped_train_test_censored_splits(self, titer_reg_obj, subtests):
        """The censored train and test splits should combine to be the censored data."""
        for train, test in titer_reg_obj.grouped_train_test_sets(n_splits=3):
            with subtests.test():
                assert all(train.censored ^ test.censored == titer_reg_obj.c)

    def test_grouped_train_test_splits_uncensored_censored(
        self, titer_reg_obj, subtests
    ):
        """
        The logical and of all masks in a single train/test fold should be an array of
        True.
        """
        for train, test in titer_reg_obj.grouped_train_test_sets(n_splits=3):
            with subtests.test():
                combined_mask = (
                    train.censored ^ train.uncensored ^ test.censored ^ test.uncensored
                )
                expect = np.full(titer_reg_obj.n_titers, True)
                assert (combined_mask == expect).all()
