# coding: utf-8

import unittest


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
