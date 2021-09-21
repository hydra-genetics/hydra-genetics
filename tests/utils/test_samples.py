# coding: utf-8

import unittest
import pandas as pandas


class TestSampleUtils(unittest.TestCase):
    def setUp(self):
        self.samples = pandas.read_table("tests/utils/files/samples.tsv", dtype=str).set_index("sample", drop=False)

    def tearDown(self):
        pass

    def test_get_samples(self):
        from hydra_genetics.utils.samples import get_samples
        samples = get_samples(self.samples)
        self.assertEqual(len(samples), 5)
        self.assertTrue('NA12878' in samples)
        self.assertTrue('NA13878' in samples)
        self.assertTrue('NA22878' in samples)
        self.assertTrue('NA12978' in samples)
        self.assertTrue('BE12878' in samples)
