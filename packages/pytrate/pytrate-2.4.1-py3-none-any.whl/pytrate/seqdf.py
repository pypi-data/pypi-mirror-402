from abc import ABC
from collections import defaultdict
from itertools import combinations
from typing import Optional, Iterable, Iterator, Generator
from functools import lru_cache, cached_property
import logging
import re

import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype


from .helper import (
    aminoAcidsAndGap,
    aminoAcidsAndGapAndUnknown,
    df_from_fasta,
    df_to_dict,
    expand_sequences,
    sequences_differ_by_n,
    test_known_aa,
)


@lru_cache
class Substitution:
    def __init__(self, aa_lost: str, site: int, aa_gained: str) -> None:
        """
        A pair of amino acids and a site.

        Args:
            aa_lost: Amino acid lost.
            site: Site.
            aa_gained: Amino acid gained.
        """
        for item in aa_lost, aa_gained:
            test_known_aa(item)

        self.aa_lost = aa_lost
        self.aa_gained = aa_gained
        self.site = int(site)

        self.items = self.aa_lost, self.site, self.aa_gained

        self.aa0 = aa_lost
        self.aa1 = aa_gained

    def __repr__(self) -> str:
        return f"{self.aa_lost}{self.site}{self.aa_gained}"

    @staticmethod
    def from_string(string: str) -> "Substitution":
        a, site, b = re.match(r"^(\w{1})(\d+)(\w{1})$", string.upper().strip()).groups()
        return Substitution(a, site, b)

    @staticmethod
    def from_tuple(items: tuple) -> "Substitution":
        a, site, b = items
        return Substitution(a, site, b)

    def __str__(self) -> str:
        return f"{self.aa_lost}{self.site}{self.aa_gained}"

    def __eq__(self, other: "Substitution") -> bool:
        return self.items == other.items

    def __hash__(self) -> int:
        return hash(self.items)


class AminoAcidPair(ABC):
    """
    A pair of amino acids.
    """

    def __init__(self, a: str, b: str) -> None:
        for item in a, b:
            test_known_aa(item)

    def __str__(self) -> str:
        return "".join(self.pair)

    def __eq__(self, other: "AminoAcidPair") -> bool:
        return self.pair == other.pair

    def __getitem__(self, item: int) -> str:
        return self.pair[item]

    def __hash__(self) -> int:
        return hash(self.pair)


@lru_cache
class SymmetricAminoAcidPair(AminoAcidPair):
    """
    A pair of amino acids. Symmetric means that it doesn't matter which order a and b are
    supplied in. I.e. NK == KN.
    """

    def __init__(self, a: str, b: str) -> None:
        super().__init__(a, b)
        self.pair = tuple(sorted((a, b)))

    def __repr__(self) -> str:
        return f"SymmetricAminoAcidPair({self.pair})"


@lru_cache
class AsymmetricAminoAcidPair(AminoAcidPair):
    """
    A pair of amino acids. Asymmetric means that the order of a and b matters, so NK !=
    KN.
    """

    def __init__(self, a: str, b: str) -> None:
        super().__init__(a, b)
        self.pair = a, b

    def __repr__(self) -> str:
        return f"AsymmetricAminoAcidPair({self.pair})"


class SeqDf:
    def __init__(self, df: pd.DataFrame, allow_unknown_aa: bool = False) -> None:
        """
        DataFrame containing amino acid sequences.

        Args:
            df: Columns are amino acid sites, rows are antigens or sera, cells
                contain amino acids.
            allow_unknown_aa: Allow unknown amino acids, represented by an `X` character.
        """
        self.characters = (
            aminoAcidsAndGapAndUnknown if allow_unknown_aa else aminoAcidsAndGap
        )
        self._unknown_aa_allowed = allow_unknown_aa

        if unknown_aa := set(np.unique(df.values)) - set(self.characters):
            if not allow_unknown_aa:
                raise ValueError(f"unrecognised amino acid(s): {', '.join(unknown_aa)}")

        if df.columns.inferred_type != "integer":
            raise ValueError("column names must be integers")

        self.df = df

        # Categorical DataFrame and codes
        self.df_cat = df.astype(CategoricalDtype(list(self.characters), ordered=False))
        self.df_codes = pd.DataFrame(
            {site: self.df_cat[site].cat.codes for site in self.df_cat}
        )

    def __repr__(self) -> None:
        return self.df.__repr__()

    def __str__(self) -> None:
        return str(self.df)

    @property
    def numbering_start(self) -> int:
        return min(self.df.columns)

    @classmethod
    def from_fasta(
        cls,
        path: str,
        sites: Optional[list[int]] = None,
        allow_unknown_aa: bool = False,
    ) -> "SeqDf":
        """Make a SeqDf from a fasta file.

        Args:
            path: Path to fasta file.
            sites: Optional 1-indexed sites to include.
            allow_unknown_aa: Allow unknown amino acids, represented by an 'X' character.

        Returns:
            SeqDf: New sequence sequence DataFrame.
        """
        return cls(
            df_from_fasta(path=path, sites=sites),
            allow_unknown_aa=allow_unknown_aa,
        )

    @classmethod
    def from_series(cls, series: pd.Series, allow_unknown_aa: bool = False) -> "SeqDf":
        """Make SeqDf from a series.

        Args:
            series (pd.Series): Each element in series is a string. See
                mapdeduce.helper.expand_sequences for more details.
            allow_unknown_aa: Allow unknown amino acids, represented by an 'X' character.

        Returns:
            SeqDf: New sequence sequence DataFrame.
        """
        return cls(expand_sequences(series), allow_unknown_aa=allow_unknown_aa)

    def remove_invariant(self) -> "SeqDf":
        """
        Remove sites (columns) that contain only one amino acid.
        """
        mask = self.df.apply(lambda x: pd.unique(x).shape[0] > 1)
        n = (~mask).sum()
        logging.info(f"removed {n} invariant sequence sites")
        new = self.df.loc[:, self.df.columns[mask]]
        return SeqDf(new, allow_unknown_aa=self._unknown_aa_allowed)

    def keep_sites(self, sites: list[int]) -> "SeqDf":
        """
        Keep only a subset of sites (columns).

        Args:
            sites: List of sites to keep.

        Returns:
            SeqDf: New SeqDf with only the specified sites.
        """
        return SeqDf(self.df.loc[:, sites], allow_unknown_aa=self._unknown_aa_allowed)

    def keep_strains(self, strains: list[str] = None, mask: pd.Series = None) -> "SeqDf":
        """
        Keep only a subset of strains (rows).

        Args:
            strains: List of strains to keep.
            mask: Boolean mask to apply to rows. Must be same length as number of rows.

        Returns:
            SeqDf: New SeqDf with only the specified strains.
        """
        if mask is not None and strains is not None:
            raise ValueError("Only one of strains or mask should be provided.")

        if mask is not None:
            if len(mask) != len(self.df):
                raise ValueError("Mask length must match number of rows in DataFrame.")
            strains = self.df.index[mask].tolist()

        return SeqDf(self.df.loc[strains, :], allow_unknown_aa=self._unknown_aa_allowed)

    def keep_variable_sites(self, threshold: float = 0.95, ignore="X-") -> "SeqDf":
        """
        Keep only variable sites, as defined by self.variable_sites.

        Args:
            threshold: Proportion of strains that must have the same amino acid at a site
                for it to be considered invariable.
            ignore: Characters to ignore when calculating proportions. Sites
                where the most common amino acid (excluding these characters) is
                above the threshold are considered invariable.
        Returns:
            SeqDf: New SeqDf with only variable sites.
        """
        return self.keep_sites(self.variable_sites(threshold=threshold, ignore=ignore))

    def amino_acid_changes_sequence_pairs(
        self, sequence_pairs: Iterable[tuple[str, str]], symmetric: bool
    ) -> set[AminoAcidPair]:
        """
        All amino acid changes that occur between pairs of sequences.

        Args:
            sequence_pairs: Pairs of sequence names.
            symmetric: If True, AB considered the same as BA. SymmetricAminoAcidPair
                instances are returned.
        """
        aa_idx = np.argwhere(self.amino_acid_matrix(sequence_pairs).values)
        Aa = SymmetricAminoAcidPair if symmetric else AsymmetricAminoAcidPair
        return set(Aa(self.characters[i], self.characters[j]) for i, j in aa_idx)

    def site_amino_acid_changes_sequence_pairs(
        self, sequence_pairs: Iterable[tuple[str, str]]
    ) -> set[Substitution]:
        """
        All site - amino acid pairs that occur between pairs of sequences.

        Args:
            sequence_pairs: Pairs of sequence names.

        Implementation note:
            Slow but clean...
        """
        return set(
            Substitution(self.df.loc[a, site], site, self.df.loc[b, site])
            for site in self.df.columns
            for a, b in set(sequence_pairs)
        )

    def amino_acid_matrix(
        self,
        sequence_pairs: Iterable[tuple[str, str]],
        sites: Optional[list[int]] = None,
        names: tuple[str, str] = ("antigen", "serum"),
    ) -> pd.DataFrame:
        """
        Generate an amino acid matrix based on the given sequence pairs.

        Args:
            sequence_pairs (Iterable[tuple[str, str]]): A collection of sequence pairs,
                where each pair consists of an antigen sequence and a serum sequence.
            sites (Optional[list[int]], optional): A list of sites to consider in
                the matrix. If None, all sites in the sequence pairs will be
                considered. Defaults to None.
            names (tuple[str, str], optional): A tuple of names for the antigen and serum
                sequences. Defaults to ("antigen", "serum").

        Returns:
            pd.DataFrame: A DataFrame representing the amino acid matrix, where each row
                and column corresponds to an amino acid and the values indicate
                whether the amino acids at the corresponding sites in the
                sequence pairs are found in the data.
        """

        aa = np.full((len(self.characters), len(self.characters)), False)

        sites = list(self.df_codes) if sites is None else sites
        df_codes = self.df_codes[sites]

        for pair in sequence_pairs:
            if len(pair) != 2:
                raise ValueError(f"sequence_pairs must contain pairs, found: {pair}")

            idx = df_codes.loc[list(pair)].values
            # (2x faster not to call np.unique(idx))
            aa[idx[0], idx[1]] = True

        return pd.DataFrame(
            aa,
            index=pd.Index(self.characters, name=f"{names[0]}_aa"),
            columns=pd.Index(self.characters, name=f"{names[1]}_aa"),
        )

    def site_aa_combinations(
        self, symmetric_aa: bool, sequence_pairs: Iterator[tuple[str, str]]
    ) -> Generator[tuple[int, tuple[str, str]], None, None]:
        """
        Generate combinations of amino acid pairs for each site in the dataset.

        Args:
            symmetric_aa (bool): Flag indicating whether to use symmetric amino acid pairs.
            sequence_pairs (Iterator[tuple[str, str]]): Iterator of sequence pairs.

        Yields:
            tuple[int, tuple[str, str]]: A tuple containing the site and amino acid
                pair.
        """
        Aa = SymmetricAminoAcidPair if symmetric_aa else AsymmetricAminoAcidPair
        for site in self.df:
            aa_mat = self.amino_acid_matrix(sequence_pairs=sequence_pairs, sites=[site])
            for a, b in self.amino_acid_matrix_to_pairs(aa_mat):
                yield site, str(Aa(a, b))

    @staticmethod
    def amino_acid_matrix_to_pairs(aa_mat: pd.DataFrame) -> Iterator[tuple[str, str]]:
        """
        Converts an amino acid matrix into pairs of amino acids.

        Args:
            aa_mat (pd.DataFrame): The amino acid matrix.

        Returns:
            Iterator[tuple[str, str]]: An iterator of pairs of amino acids.

        """
        row_aa_idx, col_aa_idx = np.where(aa_mat)
        return zip(aa_mat.index[row_aa_idx], aa_mat.index[col_aa_idx])

    @cached_property
    def sequence_groups(self) -> dict[str, list[str]]:
        """
        Groups of identical sequences.

        Returns:
            `dict`. Keys are sequences, values are a list of strain names with
                that sequence.
        """
        return {
            "".join(seq): list(sub_df.index)
            for seq, sub_df in self.df.groupby(list(self.df.columns))
        }

    @cached_property
    def single_substitution_pairs(
        self,
    ) -> dict[tuple[str, int, str], list[tuple[str, str]]]:
        """
        A dict that maps substitutions to lists of pairs of sequences that
        differ by a single substitution.

        Args:
            **kwds: Passed to `sequences_differ_by_n` and then `find_substitutions`.
        """
        groups = defaultdict(list)

        # keys of sequence_groups are unique sequences
        # so (a, b) are pairs of unique sequences
        for a, b in combinations(self.sequence_groups, 2):

            # check if the pair of sequences differ by a single sub
            if subs := sequences_differ_by_n(
                a, b, n=1, yield_tuples=True, numbering_start=self.numbering_start
            ):

                assert len(subs) == 1

                sub = subs[0]

                groups[sub].append((a, b))

        return groups

    @cached_property
    def single_substitutions(self) -> pd.DataFrame:
        """All pairs of unique sequences that differ by one amino acid substitution.

        Compares all pairs of sequences in sequence_groups, and identifies pairs that
        differ by exactly one amino acid. For each such pair, record the details
        of the substitution including the original and new amino acids, the position,
        and the sequences involved.

        Returns:
            pd.DataFrame: DataFrame containing substitution information with columns:
                - group_id: Unique identifier for each substitution group
                - sub: String representation of the substitution (e.g., 'A109G')
                - aa0: Original amino acid
                - pos: Position of substitution.
                - aa1: New amino acid
                - seq_a: First sequence in the pair
                - seq_b: Second sequence in the pair
        """
        df = []

        group_id = 0

        for seq_a, seq_b in combinations(self.sequence_groups, 2):

            if subs := sequences_differ_by_n(
                seq_a,
                seq_b,
                n=1,
                numbering_start=self.numbering_start,
                yield_tuples=True,
                sort_aas=True,
            ):

                aa0, pos, aa1 = subs[0]

                df.append(
                    {
                        "group_id": group_id,
                        "sub": f"{aa0}{pos}{aa1}",
                        "aa0": aa0,
                        "pos": pos,
                        "aa1": aa1,
                        "seq_a": seq_a,
                        "seq_b": seq_b,
                    }
                )

                group_id += 1

        return pd.DataFrame(df).set_index("group_id")

    def variable_sites(self, threshold: float = 0.95, ignore="X-") -> list[int]:
        """
        Lookup sites that aren't composed of a single amino acid that takes up more than
        `threshold` proportion of all strains.

        Args:
            threshold: Proportion of strains that must have the same amino acid at a site
                for it to be considered invariable.
            ignore: Characters to ignore when calculating proportions. Sites
                where the most common amino acid (excluding these characters) is
                above the threshold are considered invariable.

        Returns:
            List of variable sites.
        """
        df = self.amino_acid_proportions(ignore=ignore)

        invariable_sites_mask = (df > threshold).any()

        all_sites = invariable_sites_mask.index

        return all_sites[~invariable_sites_mask].tolist()

    def amino_acid_proportions(
        self, ignore: str = "X-", as_dict: Optional[bool] = False, round: int = 3
    ) -> pd.DataFrame:
        """
        Proportion of each amino acid at each site.

        Args:
            ignore: Characters to ignore.
            as_dict: If True, return a nested dict instead of a DataFrame.
            round: Number of decimal places to round to.

        Returns:
            pd.DataFrame: DataFrame containing proportions of each amino acid at each
                site. Rows are amino acids, columns are sites.
        """
        df = self.amino_acid_counts(ignore=ignore)
        proportions = df / df.sum()

        if round is not None:
            proportions = proportions.round(round)

        return df_to_dict(proportions) if as_dict else proportions

    def amino_acid_counts(
        self, ignore="X-", as_dict: Optional[bool] = False
    ) -> pd.DataFrame:
        """
        Count the occurrences of each amino acid at each site.

        Args:
            ignore: Characters to ignore.
            as_dict: If True, return a nested dict instead of a DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing counts of each amino acid at each
                site. Rows are amino acids, columns are sites.
        """
        df = (
            self.df.apply(pd.Series.value_counts, axis=0)
            .drop(index=list(ignore), errors="ignore")
            .dropna(axis=1, how="all")  # drop sites with _only_ ignored characters
        )

        return df_to_dict(df) if as_dict else df
