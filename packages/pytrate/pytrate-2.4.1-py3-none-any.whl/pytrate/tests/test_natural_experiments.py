from unittest import TestCase

import numpy as np
import pandas as pd
import pytest

import pytrate as pt


class TestMapCoordModel(TestCase):
    def setUp(self):
        coords = pd.DataFrame(
            np.random.randn(10, 2), index=list("abcdefghhh"), columns=["x", "y"]
        )
        mcm = pt.MapCoordModel(coords)
        self.post_ag_coords = mcm.sample(draws=500, tune=500)

    @pytest.mark.slow
    def test_posterior_contains_unique_items_in_coord_index(self):
        assert list(self.post_ag_coords.idata.posterior.name) == list("abcdefgh")

    @pytest.mark.slow
    def test_posterior_coords_dims(self):
        assert list(
            self.post_ag_coords.idata.posterior["ag_coords"].coords["ag_dim"]
        ) == ["x", "y"]
