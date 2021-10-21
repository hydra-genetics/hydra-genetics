# coding: utf-8

import unittest
import pandas as pandas
from snakemake.io import Wildcards


class TestSampleUtils(unittest.TestCase):
    def setUp(self):
        self.samples = pandas.read_table("tests/utils/files/samples.tsv", dtype=str).set_index("sample", drop=False)

    def tearDown(self):
        pass

    def test_get_sample(self):
        from hydra_genetics.utils.samples import get_sample
        sample = get_sample(self.samples, Wildcards(fromdict={'sample': 'NA12878'}))
        self.assertEqual(get_sample(self.samples, Wildcards(fromdict={'sample': 'NA12878'}))['TC'], '0.1')
        self.assertEqual(get_sample(self.samples, Wildcards(fromdict={'sample': 'NA13878'}))['TC'], '0.2')
        self.assertEqual(get_sample(self.samples, Wildcards(fromdict={'sample': 'NA22878'}))['TC'], '0.3')
        self.assertEqual(get_sample(self.samples, Wildcards(fromdict={'sample': 'NA12978'}))['TC'], '0.4')
        self.assertEqual(get_sample(self.samples, Wildcards(fromdict={'sample': 'BE12878'}))['TC'], '0.5')

    def test_get_samples(self):
        from hydra_genetics.utils.samples import get_samples
        samples = get_samples(self.samples)
        self.assertEqual(len(samples), 5)
        self.assertTrue('NA12878' in samples)
        self.assertTrue('NA13878' in samples)
        self.assertTrue('NA22878' in samples)
        self.assertTrue('NA12978' in samples)
        self.assertTrue('BE12878' in samples)
