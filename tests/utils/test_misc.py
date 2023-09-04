# coding: utf-8

import unittest
import yaml


class TestResourcesUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_merge(self):
        from hydra_genetics.utils.misc import merge
        dict1a = {'bwa_mem': {'extra': "some settings"}}
        dict1b = {'bwa_mem': {'extra': "some settings"}}
        dict2 = {'bwa_mem': {'cpu': 20, 'time': '12:00:00'}}
        dict1a.update(dict2)
        self.assertEqual({'bwa_mem': {'cpu': 20, 'time': '12:00:00'}}, dict1a)
        dict1b = merge(dict1b, dict2)
        self.assertEqual({'bwa_mem': {'extra': "some settings", 'cpu': 20, 'time': '12:00:00'}}, dict1b)

    def test_extract_chr(self):
        from hydra_genetics.utils.misc import extract_chr
        self.assertEqual(extract_chr("tests/utils/files/ref.fasta.fai"), [
                                     'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11',
                                     'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chr20', 'chr21',
                                     'chr22', 'chrX', 'chrY'])
        self.assertEqual(extract_chr("tests/utils/files/ref.fasta.fai", ['chr6', 'chr17', 'chrX']), [
                                     'chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11', 'chr12',
                                     'chr13', 'chr14', 'chr15', 'chr16', 'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrY',
                                     'chrM'])
        self.assertEqual(extract_chr(""), [''])

    def test_variable_replacement(self):
        with open("tests/utils/files/config_variable_replacement.yaml") as f:
            config = yaml.load(f, Loader=yaml.loader.SafeLoader)
        print(config)
        self.assertEqual(config,
                         {'PROJECT': 'MY variable', 'bwa_mem': {'extra': 'some settings {{PROJECT}}'}})

        from hydra_genetics.utils.misc import replace_dict_variables
        self.assertEqual(replace_dict_variables(config),
                         {'PROJECT': 'MY variable', 'bwa_mem': {'extra': 'some settings MY variable'}})
