import random
import itertools

import pytest
import pandas as pd
import numpy as np

import pytrate as pt


def make_titer_reg_obj(
    random_seed: int, strains: list[str], seq_len: int, n_covariates: int, **kwds
) -> pt.CrossedSiteAaModel:
    random.seed(random_seed)
    index = pd.MultiIndex.from_tuples(
        itertools.combinations(strains, 2), names=["antigen", "serum"]
    )

    sequences = pd.DataFrame(
        [random.choices("WYFMLIVAPGCQNTSEDHKR", k=seq_len) for _ in strains],
        columns=range(1, seq_len + 1),
        index=strains,
    )

    titers_unique = ["<10", "10", "20", "40", "80", "160", "320", "640", "1280"]
    titers = pd.Series(random.choices(titers_unique, k=len(index)), index=index)

    covariates = pd.DataFrame(
        np.random.randn(len(index), n_covariates),
        index=index,
        columns="cov1 cov2 cov3 cov4".split(),
    )

    return pt.CrossedSiteAaModel(
        sequences=sequences, titers=titers, covariates=covariates, **kwds
    )


@pytest.fixture
def seqdf():
    """
                    Site
                    1 2 3 4
                -----------
    Sequence    a   N C A A
                b   N S A N
                c   N S A N
                d   A C A A
                e   N S A N
    """
    return pt.SeqDf(
        pd.DataFrame(
            {
                1: ["N", "N", "N", "A", "N"],
                2: ["C", "S", "S", "C", "S"],
                3: ["A", "A", "A", "A", "A"],
                4: ["A", "N", "N", "A", "N"],
            },
            index="a b c d e".split(),
        )
    )


@pytest.fixture
def titers():
    index = pd.MultiIndex.from_tuples(
        [("a", "b"), ("a", "c"), ("a", "d"), ("a", "e"), ("b", "c")],
        names=["antigen", "serum"],
    )
    return pd.Series(["10", "20", "<10", "20/40", "1280"], index=index)


@pytest.fixture
def covariates():
    return pd.DataFrame(
        np.random.randn(5, 3),
        columns=["cov1", "cov2", "cov3"],
        index=pd.MultiIndex.from_tuples(
            [("a", "b"), ("a", "c"), ("a", "d"), ("a", "e"), ("b", "c")]
        ),
    )


@pytest.fixture
def titer_reg_obj():
    """
    TiterRegression object with 15 strains, 50-length sequences and 4 covariates.
    """
    return make_titer_reg_obj(
        random_seed=42,
        strains=list("abcdefghijklmno"),
        seq_len=10,
        n_covariates=4,
        constrain_aa_effects=False,
        symmetric_aas=True,
    )


@pytest.fixture
def titer_reg_obj_con():
    """
    TiterRegression object with 15 strains, 50-length sequences and 4 covariates.
    aa effects for substitutions and congruences are constrained to be negative /
    positive respectively.
    """
    return make_titer_reg_obj(
        random_seed=42,
        strains=list("abcdefghijklmno"),
        seq_len=10,
        n_covariates=4,
        constrain_aa_effects=True,
        symmetric_aas=True,
    )
