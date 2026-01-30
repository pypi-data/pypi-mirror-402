import numpy as np
import pandas as pd
import pytest

import pytrate as pt


class TestSeqDf:
    """
    General tests for SeqDf.
    """

    def test_df_codes_values(self, seqdf):
        """
        df_codes should contain values from 0-20 that correspond to the index in the
        aminoAcidsAndGap tuple.
        """
        assert seqdf.df_codes.loc["a", 1] == pt.seqdf.aminoAcidsAndGap.index("N")

    def test_df_codes_values_gap(self):
        """
        Test a df_codes value that corresponds to a gap character.
        """
        seqdf = pt.SeqDf(
            pd.DataFrame(
                {
                    1: ["N", "N", "-", "A", "N"],
                    2: ["C", "S", "S", "C", "S"],
                    3: ["A", "A", "A", "A", "A"],
                    4: ["A", "N", "N", "A", "N"],
                },
                index="a b c d e".split(),
            )
        )
        assert seqdf.df_codes.loc["c", 1] == pt.seqdf.aminoAcidsAndGap.index("-")

    def test_unrecognised_amino_acid(self):
        """
        An unrecognised amino acid should raise a ValueError.
        """
        with pytest.raises(ValueError, match=r"unrecognised amino acid\(s\): X"):
            pt.SeqDf(
                pd.DataFrame(
                    {
                        1: ["N", "N", "X", "A", "N"],
                        2: ["C", "S", "S", "C", "S"],
                        3: ["A", "A", "A", "A", "A"],
                        4: ["A", "N", "N", "A", "N"],
                    },
                    index="a b c d e".split(),
                )
            )

    def test_non_integer_columns(self):
        """
        Test that passing a dataframe with non-integer columns raises a ValueError.
        """
        with pytest.raises(ValueError, match="column names must be integers"):
            pt.SeqDf(
                pd.DataFrame(
                    {
                        "1": ["N", "N", "A", "A", "N"],
                        "2": ["C", "S", "S", "C", "S"],
                        "3": ["A", "A", "A", "A", "A"],
                        "4": ["A", "N", "N", "A", "N"],
                    },
                )
            )

    def test_from_series(self):
        """
        Test that SeqDf.from_series creates a proper SeqDf from a pandas Series where
        each item is a sequence indexed by strain name.
        """
        sequences = pd.Series({"strain1": "ANCT", "strain2": "ADCT", "strain3": "ASCT"})

        seqdf = pt.SeqDf.from_series(sequences)

        assert isinstance(seqdf, pt.SeqDf)
        assert seqdf.df.index.tolist() == ["strain1", "strain2", "strain3"]
        assert seqdf.df.columns.tolist() == [1, 2, 3, 4]
        assert seqdf.df.loc["strain1"].tolist() == ["A", "N", "C", "T"]
        assert seqdf.df.loc["strain2"].tolist() == ["A", "D", "C", "T"]
        assert seqdf.df.loc["strain3"].tolist() == ["A", "S", "C", "T"]

    def test_from_series_with_unknown_aa(self):
        """
        Test SeqDf.from_series with allow_unknown_aa=True
        """
        sequences = pd.Series({"strain1": "ANCT", "strain2": "ADXT", "strain3": "ASCT"})

        with pytest.raises(ValueError, match=r"unrecognised amino acid\(s\): X"):
            pt.SeqDf.from_series(sequences)

        seqdf = pt.SeqDf.from_series(sequences, allow_unknown_aa=True)

        assert seqdf.df.loc["strain2", 3] == "X"
        assert isinstance(seqdf, pt.SeqDf)

    def test_from_series_with_empty_series(self):
        """
        Test SeqDf.from_series with an empty Series
        """
        sequences = pd.Series({})

        seqdf = pt.SeqDf.from_series(sequences)

        assert seqdf.df.empty
        assert isinstance(seqdf, pt.SeqDf)

    def test_from_series_different_lengths_warns(self):
        """
        SeqDf.from_series should warn if sequences are different lengths.
        """
        sequences = pd.Series({"strain1": "ANCT", "strain2": "ADC", "strain3": "ASCTG"})

        with pytest.warns(match="sequences have different lengths"):
            pt.SeqDf.from_series(sequences)

    def test_from_series_different_lengths_padding(self):
        """
        Sequences of different lengths should be padded with '-' characters.
        """
        sequences = pd.Series({"strain1": "ANCT", "strain2": "ADC", "strain3": "ASCTG"})

        seqdf = pt.SeqDf.from_series(sequences)

        assert seqdf.df.shape == (3, 5)
        assert seqdf.df.loc["strain1"].tolist() == ["A", "N", "C", "T", "-"]
        assert seqdf.df.loc["strain2"].tolist() == ["A", "D", "C", "-", "-"]
        assert seqdf.df.loc["strain3"].tolist() == ["A", "S", "C", "T", "G"]

    def test_from_series_different_lengths_with_unknown_aa(self):
        """
        Test SeqDf.from_series with sequences of different lengths and unknown amino acids.
        """
        sequences = pd.Series({"strain1": "ANCT", "strain2": "AXCT", "strain3": "ASC"})

        seqdf = pt.SeqDf.from_series(sequences, allow_unknown_aa=True)

        assert seqdf.df.shape == (3, 4)
        assert seqdf.df.loc["strain1"].tolist() == ["A", "N", "C", "T"]
        assert seqdf.df.loc["strain2"].tolist() == ["A", "X", "C", "T"]
        assert seqdf.df.loc["strain3"].tolist() == ["A", "S", "C", "-"]


class TestSequenceGroups:
    def test_sequence_groups_returns_dict(self, seqdf):
        """
        Test that sequence_groups returns a dictionary.
        """
        assert isinstance(seqdf.sequence_groups, dict)

    def test_sequence_groups_values(self, seqdf):
        """
        Test that the values in sequence_groups are lists of strain names.
        """
        for group in seqdf.sequence_groups.values():
            assert isinstance(group, list)
            for strain in group:
                assert strain in seqdf.df.index

    def test_sequence_groups_all_strains_present(self, seqdf):
        """
        Test that all strains in the SeqDf index are present in a group.
        """
        all_strains = set()
        for group in seqdf.sequence_groups.values():
            all_strains.update(group)

        assert all_strains == set(seqdf.df.index)

    def test_sequence_groups_correct_grouping(self):
        """
        Test that strains with identical sequences are grouped together.
        """
        df = pd.DataFrame(
            {1: ["A", "A", "C", "C"], 2: ["N", "N", "D", "D"], 3: ["G", "G", "G", "H"]},
            index=["s1", "s2", "s3", "s4"],
        )

        seqdf = pt.SeqDf(df)
        groups = seqdf.sequence_groups

        # s1 and s2 should be in the same group, s3 and s4 should be separate
        assert len(groups) == 3

        # Find which group contains s1
        s1_group = None
        for seq, strains in groups.items():
            if "s1" in strains:
                s1_group = strains
                break

        assert s1_group is not None
        assert set(s1_group) == {"s1", "s2"}

        # Check that s3 and s4 are in separate groups
        assert any(
            "s3" in strains and "s4" not in strains for strains in groups.values()
        )
        assert any(
            "s4" in strains and "s3" not in strains for strains in groups.values()
        )

    def test_sequence_groups_single_strain(self):
        """
        Test sequence_groups with a single strain.
        """
        df = pd.DataFrame({1: ["A"], 2: ["N"], 3: ["C"]}, index=["s1"])
        seqdf = pt.SeqDf(df)

        groups = seqdf.sequence_groups
        assert len(groups) == 1
        assert list(groups.values())[0] == ["s1"]


class TestAminoAcidSequencePairs:
    def test_containing_x(self):
        seqdf = pt.SeqDf(
            pd.DataFrame({1: ["N", "X"], 2: ["N", "X"]}, index=["a", "b"]),
            allow_unknown_aa=True,
        )
        pairs = seqdf.amino_acid_changes_sequence_pairs([("a", "b")], symmetric=True)
        assert {pt.seqdf.SymmetricAminoAcidPair("N", "X")} == pairs


class TestAminoAcidMatrix:
    def test_returns_df(self, seqdf):
        assert isinstance(seqdf.amino_acid_matrix(sequence_pairs=[]), pd.DataFrame)

    def test_columns_as_expected(self, seqdf):
        matrix = seqdf.amino_acid_matrix(sequence_pairs=(("a", "b"), ("c", "d")))
        assert list(matrix.columns) == list(pt.seqdf.aminoAcidsAndGap)

    def test_index_as_expected(self, seqdf):
        matrix = seqdf.amino_acid_matrix(sequence_pairs=(("a", "b"), ("c", "d")))
        assert list(matrix.index) == list(pt.seqdf.aminoAcidsAndGap)

    def test_value_correct_single_pair(self, seqdf):
        """
        Single pair is passed.
        """
        matrix = seqdf.amino_acid_matrix(sequence_pairs=(("a", "b"),))
        expect = pd.DataFrame(
            np.full((21, 21), False),
            index=list(pt.seqdf.aminoAcidsAndGap),
            columns=list(pt.seqdf.aminoAcidsAndGap),
        )
        expect.loc["N", "N"] = True
        expect.loc["C", "S"] = True
        expect.loc["A", "A"] = True
        expect.loc["A", "N"] = True
        assert (expect == matrix).all().all()

    def test_value_correct_two_pairs(self, seqdf):
        """
        Pass two pairs.
        """
        matrix = seqdf.amino_acid_matrix(sequence_pairs=(("a", "b"), ("c", "d")))
        expect = pd.DataFrame(
            np.full((21, 21), False),
            index=list(pt.seqdf.aminoAcidsAndGap),
            columns=list(pt.seqdf.aminoAcidsAndGap),
        )
        # pair (a, b)
        expect.loc["N", "N"] = True
        expect.loc["C", "S"] = True
        expect.loc["A", "A"] = True
        expect.loc["A", "N"] = True

        # pair (c, d)
        expect.loc["N", "A"] = True
        expect.loc["S", "C"] = True
        expect.loc["A", "A"] = True
        expect.loc["N", "A"] = True

        assert (expect == matrix).all().all()

    def test_single_pair_single_site(self, seqdf):
        matrix = seqdf.amino_acid_matrix(sequence_pairs=[("a", "b")], sites=[1])
        expect = pd.DataFrame(
            np.full((21, 21), False),
            index=list(pt.seqdf.aminoAcidsAndGap),
            columns=list(pt.seqdf.aminoAcidsAndGap),
        )
        expect.loc["N", "N"] = True
        assert (expect == matrix).all().all()

    def test_single_pair_two_sites(self, seqdf):
        matrix = seqdf.amino_acid_matrix(sequence_pairs=[("a", "b")], sites=[1, 2])
        expect = pd.DataFrame(
            np.full((21, 21), False),
            index=list(pt.seqdf.aminoAcidsAndGap),
            columns=list(pt.seqdf.aminoAcidsAndGap),
        )
        expect.loc["N", "N"] = True
        expect.loc["C", "S"] = True
        assert (expect == matrix).all().all()

    def test_two_pairs_two_sites(self, seqdf):
        matrix = seqdf.amino_acid_matrix(
            sequence_pairs=[("a", "b"), ("c", "d")], sites=[1, 2]
        )
        expect = pd.DataFrame(
            np.full((21, 21), False),
            index=list(pt.seqdf.aminoAcidsAndGap),
            columns=list(pt.seqdf.aminoAcidsAndGap),
        )
        expect.loc["N", "N"] = True
        expect.loc["C", "S"] = True
        expect.loc["N", "A"] = True
        expect.loc["S", "C"] = True
        assert (expect == matrix).all().all()


class TestSiteAminoAcidCombinations:
    def test_tuples_returned(self, seqdf):
        combinations = seqdf.site_aa_combinations(
            symmetric_aa=False, sequence_pairs=[("a", "b")]
        )
        assert all(isinstance(comb, tuple) for comb in combinations)

    def test_value_single_pair_asymmetric(self, seqdf):
        combinations = seqdf.site_aa_combinations(
            symmetric_aa=False, sequence_pairs=[("a", "b")]
        )
        expect = {(1, "NN"), (2, "CS"), (3, "AA"), (4, "AN")}
        assert expect == set(combinations)

    def test_value_two_pairs_asymmetric(self, seqdf):
        combinations = seqdf.site_aa_combinations(
            symmetric_aa=False, sequence_pairs=[("a", "b"), ("c", "d")]
        )
        expect = {
            (1, "NN"),
            (2, "CS"),
            (3, "AA"),
            (4, "AN"),
            (1, "NA"),
            (2, "SC"),
            (4, "NA"),
        }
        assert expect == set(combinations)

    def test_value_two_pairs_symmetric(self, seqdf):
        combinations = seqdf.site_aa_combinations(
            symmetric_aa=True, sequence_pairs=[("a", "b"), ("c", "d")]
        )
        expect = {(1, "NN"), (1, "AN"), (2, "CS"), (3, "AA"), (4, "AN")}
        assert expect == set(combinations)

    def test_gap_present(self):
        seqdf = pt.SeqDf(
            pd.DataFrame(
                {
                    1: ["N", "N", "-", "A", "N"],
                    2: ["C", "S", "S", "C", "S"],
                    3: ["A", "A", "A", "A", "A"],
                    4: ["A", "N", "N", "A", "N"],
                },
                index="a b c d e".split(),
            )
        )
        combinations = seqdf.site_aa_combinations(
            symmetric_aa=True, sequence_pairs=[("c", "d")]
        )
        expect = {(4, "AN"), (3, "AA"), (2, "CS"), (1, "-A")}
        assert expect == set(combinations)


class TestSiteAminoAcidChangesSequencePairs:
    def test_returns_set(self, seqdf):
        output = seqdf.site_amino_acid_changes_sequence_pairs([("a", "b")])
        assert isinstance(output, set)

    def test_single_pair(self, seqdf):
        expect = {
            pt.seqdf.Substitution.from_string(s) for s in ("N1N", "C2S", "A3A", "A4N")
        }
        output = seqdf.site_amino_acid_changes_sequence_pairs([("a", "b")])
        assert expect == output

    def test_two_pairs(self, seqdf):
        expect = {
            pt.seqdf.Substitution.from_string(s)
            for s in ("N1N", "C2S", "S2C", "A3A", "A4N", "N4A")
        }
        output = seqdf.site_amino_acid_changes_sequence_pairs([("a", "b"), ("b", "a")])
        assert expect == output


class TestSubstitution:
    def test_unknown_site(self):
        with pytest.raises(ValueError, match="invalid literal"):
            pt.seqdf.Substitution("N", "xyz", "K")

    def test_unknown_aa(self):
        with pytest.raises(ValueError, match="unrecognized amino acid"):
            pt.seqdf.Substitution("J", 10, "K")

    def test_equivalent(self):
        assert pt.seqdf.Substitution("N", 145, "K") == pt.seqdf.Substitution(
            "N", 145, "K"
        )

    def test_from_string(self):
        assert pt.Substitution.from_string("F159S") == pt.Substitution("F", 159, "S")

    def test_from_tuple(self):
        assert pt.Substitution.from_tuple(("F", 159, "S")) == pt.Substitution(
            "F", 159, "S"
        )


class TestAsymmetricAminoAcidPair:
    def test_NN_eq_NN(self):
        """NN should equal NN."""
        assert pt.seqdf.AsymmetricAminoAcidPair(
            "N", "N"
        ) == pt.seqdf.AsymmetricAminoAcidPair("N", "N")

    def test_NK_not_equal_KN(self):
        """NK should not be equal to KN."""
        assert pt.seqdf.AsymmetricAminoAcidPair(
            "N", "K"
        ) != pt.seqdf.AsymmetricAminoAcidPair("K", "N")

    def test_str(self):
        """String should contain amino acids in the order they are passed."""
        aap = pt.seqdf.AsymmetricAminoAcidPair("N", "K")
        assert str(aap) == "NK"

        aap = pt.seqdf.AsymmetricAminoAcidPair("K", "N")
        assert str(aap) == "KN"


class TestSymmetricAminoAcidPair:
    def test_pair_sorted(self):
        """The pair attribute should contain the amino acids alphabetically sorted."""
        aap = pt.seqdf.SymmetricAminoAcidPair("N", "K")
        assert aap.pair == ("K", "N")

        aap = pt.seqdf.SymmetricAminoAcidPair("K", "N")
        assert aap.pair == ("K", "N")

    def test_str(self):
        """String should contain sorted amino acids in the pair."""
        aap = pt.seqdf.SymmetricAminoAcidPair("N", "K")
        assert str(aap) == "KN"

        aap = pt.seqdf.SymmetricAminoAcidPair("K", "N")
        assert str(aap) == "KN"

    def test_NN_eq_NN(self):
        """NN should equal NN."""
        assert pt.seqdf.SymmetricAminoAcidPair(
            "N", "N"
        ) == pt.seqdf.SymmetricAminoAcidPair("N", "N")

    def test_NK_equal_KN(self):
        """NK should be equal to KN."""
        assert pt.seqdf.SymmetricAminoAcidPair(
            "N", "K"
        ) == pt.seqdf.SymmetricAminoAcidPair("K", "N")


class TestVariableSites:
    def test_variable_sites_all_variable(self):
        """Test when all sites are variable."""
        df = pd.DataFrame(
            {1: ["A", "C", "D"], 2: ["N", "S", "T"], 3: ["G", "H", "I"]},
            index=["s1", "s2", "s3"],
        )

        seqdf = pt.SeqDf(df)
        variable_sites = seqdf.variable_sites()

        assert variable_sites == [1, 2, 3]

    def test_variable_sites_none_variable(self):
        """Test when no sites are variable."""
        df = pd.DataFrame(
            {1: ["A", "A", "A"], 2: ["N", "N", "N"], 3: ["G", "G", "G"]},
            index=["s1", "s2", "s3"],
        )

        seqdf = pt.SeqDf(df)
        variable_sites = seqdf.variable_sites()

        assert variable_sites == []

    def test_variable_sites_mixed(self):
        """Test with a mix of variable and invariable sites."""
        df = pd.DataFrame(
            {
                1: ["A", "A", "A"],  # invariable
                2: ["N", "S", "T"],  # variable
                3: ["G", "G", "G"],  # invariable
                4: ["D", "E", "F"],  # variable
            },
            index=["s1", "s2", "s3"],
        )

        seqdf = pt.SeqDf(df)
        variable_sites = seqdf.variable_sites()

        assert variable_sites == [2, 4]

    def test_variable_sites_threshold(self):
        """Test with different threshold values."""
        df = pd.DataFrame(
            {
                1: ["A", "A", "A", "A", "C"],  # 80% A
                2: ["N", "N", "N", "S", "T"],  # 60% N
                3: ["G", "G", "G", "G", "G"],  # 100% G
            },
            index=["s1", "s2", "s3", "s4", "s5"],
        )

        seqdf = pt.SeqDf(df)

        # threshold 0.95, only site 1 and 2 should be variable
        assert seqdf.variable_sites(threshold=0.95) == [1, 2]

        # threshold 0.7, only site 2 should be variable
        assert seqdf.variable_sites(threshold=0.7) == [2]

        # threshold 0.5, no sites should be variable
        assert seqdf.variable_sites(threshold=0.5) == []

    def test_variable_sites_with_gaps(self):
        """Test behavior with gap characters."""
        df = pd.DataFrame(
            {
                1: ["A", "A", "A", "A", "-"],  # 80% A, 20% gap
                2: ["N", "N", "-", "-", "-"],  # 40% N, 60% gap
                3: ["-", "-", "-", "-", "-"],  # 100% gap
            },
            index=["s1", "s2", "s3", "s4", "s5"],
        )

        seqdf = pt.SeqDf(df)

        # By default gaps are counted, so site 3 is invariable
        assert 3 not in seqdf.variable_sites(threshold=0.95)

        # With ignore="-", site 3 should have no amino acids and be considered invariable
        assert 3 not in seqdf.variable_sites(threshold=0.95, ignore="-")

    def test_variable_sites_with_unknown(self):
        """Test behavior with unknown amino acid characters."""
        df = pd.DataFrame(
            {
                1: ["A", "A", "A", "A", "X"],  # 80% A, 20% X
                2: ["N", "N", "X", "X", "X"],  # 40% N, 60% X
                3: ["X", "X", "X", "X", "X"],  # 100% X
            },
            index=["s1", "s2", "s3", "s4", "s5"],
        )

        seqdf = pt.SeqDf(df, allow_unknown_aa=True)

        # By default X is counted, so site 3 is invariable
        assert 3 not in seqdf.variable_sites(threshold=0.95)

        # Site 2 is variable when counting X but invariable when ignoring X
        assert 2 in seqdf.variable_sites(threshold=0.95, ignore="")
        assert 2 not in seqdf.variable_sites(threshold=0.95, ignore="X")
