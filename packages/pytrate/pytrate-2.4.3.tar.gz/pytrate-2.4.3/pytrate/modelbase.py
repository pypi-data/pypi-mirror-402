from abc import ABC
from functools import cached_property
from typing import Generator, Optional
import logging

from sklearn.model_selection import GroupKFold
import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

from .helper import (
    normal_lcdf,
    Titer,
    delete_unused_variables,
    CrossValidationFoldResult,
    CrossValidationResults,
    TrainTestTuple,
    UncensoredCensoredTuple,
)
from .seqdf import SeqDf


class ModelBase(ABC):
    def fit(self, netcdf_path: Optional[str] = None, **kwds) -> az.InferenceData:
        """
        Fit the model using variational inference.

        Args:
            netcdf_path: Path to save inference data NetCDF object. Attempt to load a
                file with this name before sampling.
            **kwds: Passed to pymc.fit
        """
        try:
            return az.from_netcdf(netcdf_path)
        except (FileNotFoundError, TypeError):
            with self.model:
                mean_field = pm.fit(
                    n=kwds.pop("n", 100_000),
                    callbacks=[
                        pm.callbacks.CheckParametersConvergence(
                            diff="absolute", tolerance=0.01
                        )
                    ],
                    **kwds,
                )

            idata = mean_field.sample(1_000)
            idata.attrs["mean_field_hist"] = mean_field.hist
            if netcdf_path is not None:
                az.to_netcdf(idata, netcdf_path)
            return idata

    def sample(
        self, netcdf_path: Optional[str] = None, use_nutpie: bool = False, **kwds
    ) -> az.InferenceData:
        """
        Sample from the model posterior.

        Args:
            netcdf_path: Path to save inference data NetCDF object. Attempt to load a
                file with this name before sampling.
            use_nutpie: Use nutpie NUTS implementation.
            **kwds: Passed to pymc.sample (or nutpie.sample).
        """
        try:
            idata = az.from_netcdf(netcdf_path)
            logging.info(f"inference data loaded from {netcdf_path}")

        except (FileNotFoundError, TypeError):

            if use_nutpie:
                import nutpie

                logging.info("sampling using nutpie...")
                compiled = nutpie.compile_pymc_model(self.model)
                idata = nutpie.sample(compiled, **kwds)

            else:
                logging.info("sampling using pymc...")
                with self.model:
                    idata = pm.sample(**kwds)

            if isinstance(netcdf_path, str):
                try:
                    # wrap this in a try / except so that idata is _always_ returned
                    az.to_netcdf(idata, netcdf_path)
                    logging.info(f"inference data saved to {netcdf_path}")

                except (FileNotFoundError, TypeError):
                    logging.warning(f"couldn't save netcdf file to {netcdf_path}")

        # Drop redundant variables from non-centered parametrisations and that contain
        # log probabilities.
        return delete_unused_variables(idata)


class TiterModelBase(ModelBase):
    def __init__(
        self,
        sequences: pd.DataFrame | SeqDf,
        titers: pd.Series,
        covariates: Optional[pd.DataFrame] = None,
        allow_unknown_aa: bool = False,
    ) -> None:
        """
        Data and methods that are shared by CrossedSiteAaModel and
        CombinedSiteAaModel.

        Args:
            sequences: DataFrame containing sequences.
            titers: Series containing titers.
            covariates: Optional DataFrame containing additional covariates to
                include in the model.
            allow_unknown_aa: Only has an effect if sequences is a DataFrame such that a
                new SeqDf instance gets generated.
        """
        try:
            self.seqdf = sequences.remove_invariant()
        except AttributeError:
            self.seqdf = SeqDf(
                sequences, allow_unknown_aa=allow_unknown_aa
            ).remove_invariant()

        self.titers = pd.Series(titers, dtype=str)
        self.n_titers = self.titers.shape[0]
        self.n_sites = self.seqdf.df.shape[1]

        # Check have all sequences for antigens and sera in titers
        antigens = self.titers.index.get_level_values("antigen")
        sera = self.titers.index.get_level_values("serum")
        for virus in *antigens, *sera:
            if virus not in self.seqdf.df.index:
                raise ValueError(f"{virus} not in sequences")

        self.Y = np.array([Titer(t).log_value for t in self.titers])

        # Titer table contains <10 and <20 values
        self.c = self.titers.str.contains("<").values  # 'c'ensored
        self.u = ~self.c  # 'u'ncensored

        # Add 0.5 to the censored values
        # For censored titers it is known that the true log value must be below half way
        # to the next highest titer (this is what using normal_lcdf achieves).
        # E.g. a titer of '10' has a log value of 0. A titer of '<10' has a log_value of
        # -1. But we know that the true log value must be below half way between -1 and
        # 0, i.e. less than -0.5.
        self.Y[self.c] += 0.5

        # Keep track of the order of antigens and sera
        self.ags, self.srs = [
            pd.Categorical(self.titers.index.get_level_values(level))
            for level in ("antigen", "serum")
        ]

        # Covariates
        if covariates is not None:
            if len(self.titers) != len(covariates):
                raise ValueError("covariates and titers have different length")

            elif not (self.titers.index == covariates.index).all():
                raise ValueError("covariates and titers must have identical indexes")

            else:
                self.covs = covariates.values
                self.cov_names = list(covariates.columns)

        else:
            self.covs = None

    def __repr__(self):
        return (
            f"ModelBase(sequences={self.seqdf}, titers={self.titers}, "
            f"covariates={self.covs})"
        )

    @property
    def titer_summary(self) -> pd.DataFrame:
        """
        Summarise what titers are in the dataset, what their log values are, whether they
        are censored/uncensored and their count.
        """
        return (
            pd.DataFrame(
                set(zip(self.Y, self.titers, self.c, self.u)),
                columns=["log_titer", "titer", "censored", "uncensored"],
            )
            .sort_values("log_titer")
            .set_index("titer")
            .join(self.titers.value_counts())
            .reset_index()
        )

    @classmethod
    def from_chart(cls, chart: "maps.Chart", sites: list[int]) -> "ModelBase":
        """
        Make an instance from a maps.Chart object.

        Args:
            chart: A `maps.Chart` instance.
            sites: Only include these sites in the regression.
        """
        ag_seqs = {ag.name: list(ag.sequence) for ag in chart.antigens}
        sr_seqs = {sr.name: list(sr.sequence) for sr in chart.sera}

        df_seq = pd.DataFrame.from_dict({**ag_seqs, **sr_seqs}, orient="index")
        df_seq.columns += 1

        df_seq = df_seq[sites]

        return cls(sequences=df_seq, titers=chart.table_long)

    @cached_property
    def uncensored_model(self) -> pm.Model:
        """
        Treat all data as uncensored.

        This was implemented in order to generate a posterior predictive for the censored
        data. For censored data the posterior predictive is computed as if the data
        were uncensored. I.e., it's only the likelihood (that uses the censored response)
        that requires special handling.
        """
        with pm.Model(coords=self.coords) as model:
            variables = self.make_variables()
            sigma = pm.Exponential("sd", 1)
            mu = self.calculate_titer(suffix="u", mask=None, **variables)
            Y_u = pm.Data("Y_u", self.Y)
            pm.Normal("obs_u", mu=mu, sigma=sigma, observed=Y_u)

        return model

    @cached_property
    def model(self) -> pm.Model:
        with pm.Model(coords=self.coords) as model:
            variables = self.make_variables()
            sigma = pm.Exponential("sd", 1.0)

            # Censored data (less than titers)
            Y_c = pm.Data("Y_c", self.Y[self.c])
            mu_c = self.calculate_titer(suffix="c", mask=self.c, **variables)

            # using pm.Censored here causes loss to be nan when calling pm.fit
            pm.Potential("obs_c", normal_lcdf(mu=mu_c, sigma=sigma, x=Y_c))

            # Uncensored data (numeric titers)
            Y_u = pm.Data("Y_u", self.Y[self.u])
            mu_u = self.calculate_titer(suffix="u", mask=self.u, **variables)
            pm.Normal("obs_u", mu=mu_u, sigma=sigma, observed=Y_u)

        return model

    def data_shape(self, model: pm.Model) -> dict[str, tuple]:
        """shapes of data currently set on a model."""
        shapes = {}
        for suffix in "u", "c":
            for variable in "site_aa", "aa", "ags", "srs", "Y":
                key = f"{variable}_{suffix}"
                if key in model:
                    shapes[key] = self.model[key].eval().shape
        return shapes

    def log_data_shape(self, model: pm.Model) -> None:
        """Log shapes of data currently set on a model."""
        logging.info(f"current data shapes: {self.data_shape(model)}")

    def grouped_cross_validation(
        self,
        n_splits: int,
        variational_inference: bool = False,
        netcdf_prefix: Optional[str] = None,
        vi_kwds: Optional[dict] = None,
        sample_kwds: Optional[dict] = None,
    ) -> CrossValidationResults:
        """
        Run cross validation.

        Args:
            n_splits: Number of train/test folds to generate.
            variational_inference: Fit using variational inference rather than sampling
                from a posterior.
            netcdf_prefix: Save an InferenceData object for each fold to disk with this
                prefix. Prefixes have "-fold{i}.nc" appended where 'i' indexes the fold.
                If files already exist then load them instead of sampling.
            vi_kwds: Keyword arguments passed to pymc.fit if variational inference is
                being used.
            sample_kwds: Keyword arguments passed to pymc.sample if variational inference
                is not being used.
        """
        folds = self.grouped_train_test_sets(n_splits=n_splits)

        vi_kwds = {} if vi_kwds is None else vi_kwds
        sample_kwds = {} if sample_kwds is None else sample_kwds

        results = []

        for i, (train, test) in enumerate(folds):
            netcdf_path = f"{netcdf_prefix}-fold{i}.nc"
            with self.model:
                logging.info(
                    "setting training data "
                    f"#uncensored={sum(train.uncensored)} "
                    f"#censored={sum(train.censored)}"
                )
                self.set_data(train.censored, suffix="c")
                self.set_data(train.uncensored, suffix="u")
                self.log_data_shape(self.model)
                idata = (
                    self.fit(netcdf_path=netcdf_path, **vi_kwds)
                    if variational_inference
                    else self.sample(netcdf_path=netcdf_path, **sample_kwds)
                )

            # Generate posterior predictive samples on the test data
            with self.uncensored_model:
                logging.info(
                    "setting testing data (all test data treated as uncensored) "
                    f"#combined={sum(test.combined)} "
                )
                # self.set_data(np.zeros_like(test.combined, dtype=bool), suffix="c")
                self.set_data(test.combined, suffix="u")
                self.log_data_shape(self.uncensored_model)
                idata.extend(pm.sample_posterior_predictive(idata, progressbar=False))

            results.append(
                CrossValidationFoldResult(
                    idata, y_true=self.Y[test.combined], train=train, test=test
                )
            )

        return CrossValidationResults(results)

    def make_train_test_sets(
        self, random_seed: int, test_proportion: float = 0.1
    ) -> None:
        """
        Attach boolean arrays to this instance that define train and test sets for censored and
        uncensored data.

        Args:
            random_seed: Passed to np.random.seed for repeatable datasets.
            test_proportion: Proportion of titers used for the test set.

        The following attributes are attached:
            `mask_test`,`mask_train`: Boolean ndarrays. All titers are either in mask_test or
                mask_train.
            `mask_train_c`,`mask_train_u`: Boolean ndarrays. Censored (c) and uncensored (u)
                titers for the training set. All titers in the training set are in one of
                these arrays.
            `mask_test_c`,`mask_test_u`: Boolean ndarrays. Censored (c) and uncensored (u)
                titers for the test set. All titers in the test set are in one of these
                arrays.
        """
        if not 0 < test_proportion < 1:
            raise ValueError("test_proportion should be between 0-1.")

        np.random.seed(random_seed)

        n_test = int(np.round(test_proportion * self.n_titers))
        idx_test = np.random.choice(np.arange(self.n_titers), replace=False, size=n_test)
        self.mask_test = np.repeat(False, self.n_titers)
        self.mask_test[idx_test] = True
        self.mask_train = ~self.mask_test

        self.mask_train_u, self.mask_train_c, *_ = self.make_censored_uncensored_masks(
            self.mask_train
        )

        self.mask_test_u, self.mask_test_c, *_ = self.make_censored_uncensored_masks(
            self.mask_test
        )

    def grouped_train_test_sets(self, n_splits: int) -> Generator[
        TrainTestTuple[UncensoredCensoredTuple, UncensoredCensoredTuple],
        None,
        None,
    ]:
        """
        Generate train and test sets of uncensored and censored arrays. The titers are
        grouped by the serum/antigen pair used such that all titers from a single
        serum/antigen pair will appear in the same train or test split. I.e. testing will
        never involve testing a titer that has also appeared in the training set.

        Arrays are boolean masks the same length as the number of titers in the dataset.

        sklearn.model_selection.GroupKFold is used which is deterministic and therefore
        does not require setting a random seed to generate repeatable folds.

        Args:
            n_splits: Number of folds.

        Returns:
            4-tuple containing: (uncensored training, censored training,
                uncensored testing, censored testing).
        """
        gkf = GroupKFold(n_splits=n_splits)
        for train, test in gkf.split(range(self.n_titers), groups=self.titers.index):
            mask_train = self.indexes_to_mask(train)
            mask_test = self.indexes_to_mask(test)
            yield TrainTestTuple(
                train=self.make_censored_uncensored_masks(mask_train),
                test=self.make_censored_uncensored_masks(mask_test),
            )

    def make_censored_uncensored_masks(
        self, mask: np.ndarray
    ) -> UncensoredCensoredTuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Given a boolean mask return the same mask but decomposed into censored and
        uncensored titers.

        Args:
            mask: 1D array containing True and False.

        Returns:
            3-tuple of boolean masks:
                - uncensored
                - censored
                - combination (the logical 'or' of censored and uncensored, also equal to
                  the input mask)
        """
        if len(mask) != self.n_titers:
            raise ValueError(
                f"mask length different to n. titers ({len(mask)} vs {self.n_titers})"
            )
        if any(set(mask) - {True, False}):
            raise ValueError("mask must only contain True and False")
        if mask.ndim != 1:
            raise ValueError("mask must be 1D")

        uncensored = np.logical_and(self.u, mask)
        censored = np.logical_and(self.c, mask)
        combined = np.logical_or(uncensored, censored)

        assert all(combined == mask)

        return UncensoredCensoredTuple(
            uncensored=uncensored, censored=censored, combined=combined
        )

    def indexes_to_mask(self, indexes: np.ndarray) -> np.ndarray:
        """
        Convert an array containing integer indexes to boolean masks.

        If indexes contains [2, 4, 6] and there are 9 titers in the dataset, this would
        return: [False, False, True, False, True, False, True, False, False, False].

        Args:
            indexes: Array of integers.
        """
        mask = np.full(self.n_titers, False)
        mask[indexes] = True
        return mask
