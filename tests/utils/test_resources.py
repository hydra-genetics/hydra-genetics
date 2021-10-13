# coding: utf-8

import unittest
import yaml


class TestMiscUtils(unittest.TestCase):
    def setUp(self):
        with open("tests/utils/files/configs.yaml") as file:
            self.config = yaml.load(file, Loader=yaml.FullLoader)

    def tearDown(self):
        pass

    def test_merge(self):
        from hydra_genetics.utils.resources import load_resources
        self.assertEqual({'bwa_mem': {'extra': "some settings"}}, self.config)
        self.config = load_resources(self.config, "tests/utils/files/resources.yaml")
        self.assertEqual({'bwa_mem': {'extra': "some settings", 'cpu': 20, 'time': '12:00:00'}}, self.config)
