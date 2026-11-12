import inspect
import unittest

import hydra_genetics.utils.samples as samples
import hydra_genetics.utils.units as units


class TestStarImportCompatibility(unittest.TestCase):
    """Pipelines generated from older templates call pandas.read_table in their common.smk without importing pandas.
    It only works because 'from hydra_genetics.utils.samples import *' and '... units import *' re-export it."""

    def star_imported(self, module):
        namespace = {}
        exec(f"from {module.__name__} import *", namespace)
        return namespace

    def test_samples_star_import_exposes_pandas(self):
        self.assertTrue(inspect.ismodule(self.star_imported(samples).get("pandas")))

    def test_units_star_import_exposes_pandas(self):
        self.assertTrue(inspect.ismodule(self.star_imported(units).get("pandas")))
