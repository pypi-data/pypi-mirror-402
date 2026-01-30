import pandas as pd
import pytest

import pytrate as pt


class TestFoldChange:
    def test_df_mut_index_name(self):
        df_root = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [1, 2, 3]},
            index=pd.Index(list("xyz"), name="antigen"),
        )

        df_mut = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [2, 3, 4], "root": list("xyz")},
            index=pd.Index(list("lmn"), name="foo"),
        )

        mutant_subs = {"l": ["X1Y"], "m": ["X2Y"], "n": ["X3Y"]}

        with pytest.raises(ValueError, match="df_mut index must be named 'antigen'"):
            pt.FoldChangeModel(df_root, df_mut, mutant_subs)

    def test_df_root_index_name(self):
        df_root = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [1, 2, 3]},
            index=pd.Index(list("xyz"), name="foo"),
        )

        df_mut = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [2, 3, 4], "root": list("xyz")},
            index=pd.Index(list("lmn"), name="antigen"),
        )

        mutant_subs = {"l": ["X1Y"], "m": ["X2Y"], "n": ["X3Y"]}

        with pytest.raises(ValueError, match="df_root index must be named 'antigen'"):
            pt.FoldChangeModel(df_root, df_mut, mutant_subs)

    def test_passing_mutants_in_dict_not_in_df_raises_error(self):

        df_root = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [1, 2, 3]},
            index=pd.Index(list("xyz"), name="antigen"),
        )

        df_mut = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [2, 3, 4]},
            index=pd.Index(list("lmn"), name="antigen"),
        )

        mutant_subs = {
            "l": ["X1Y"],
            "m": ["X2Y"],
            "n": ["X3Y"],
            "o": ["X4Y"],  # This mutant isn't present in df_mut
        }

        with pytest.raises(
            ValueError, match=r"mutant\(s\) {'o'} in mutant_subs missing from df_mut"
        ):
            pt.FoldChangeModel(df_root, df_mut, mutant_subs)

    def test_passing_mutants_in_df_mut_not_in_mutant_substitutions_raises_error(self):

        df_root = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [1, 2, 3]},
            index=pd.Index(list("xyz"), name="antigen"),
        )

        df_mut = pd.DataFrame(
            {"serum": list("abc"), "log_titer": [2, 3, 4], "root": list("abc")},
            index=pd.Index(list("rst"), name="antigen"),
        )

        mutant_subs = {"r": ["X1Y"], "s": ["X2Y"]}

        with pytest.raises(
            ValueError, match=r"mutant\(s\) {'t'} in df_mut missing from mutant_subs"
        ):
            pt.FoldChangeModel(df_root, df_mut, mutant_subs)
