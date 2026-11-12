# coding: utf-8

import unittest
from dataclasses import dataclass

import yaml

from hydra_genetics.utils.verification.common import (
    DIFFERENT, IDENTICAL, WITHIN_TOLERANCE, SpecLoader, VerificationError, compare_values, json_safe, normalise_tolerance,
    parse_columns,
)


class TestTolerances(unittest.TestCase):
    def test_compare_values(self):
        @dataclass
        class TestCase:
            name: str
            reference: object
            candidate: object
            tolerance: object
            expected: str

        testcases = [
            TestCase("equal strings", "chr1", "chr1", "=", IDENTICAL),
            TestCase("different strings", "chr1", "chr2", "=", DIFFERENT),
            TestCase("exact numbers differ", "0.10", "0.11", None, DIFFERENT),
            TestCase("absolute within", "0.10", "0.11", 0.01, WITHIN_TOLERANCE),
            TestCase("absolute outside", "0.10", "0.12", 0.01, DIFFERENT),
            TestCase("same number written differently", "1.0", "1.00", 0.01, IDENTICAL),
            TestCase("relative within", "100", "104", "5%", WITHIN_TOLERANCE),
            TestCase("relative outside", "100", "106", "5%", DIFFERENT),
            TestCase("text with tolerance", "NA", "0.5", 1, DIFFERENT),
            TestCase("nan equals nan", "NaN", "nan", 0.1, IDENTICAL),
            TestCase("unordered list", "a&b&c", "c&a&b", "unordered", WITHIN_TOLERANCE),
            TestCase("tuples within", ("0.1", "0.2"), ("0.1", "0.205"), 0.01, WITHIN_TOLERANCE),
            TestCase("tuples of different length", ("0.1",), ("0.1", "0.2"), 0.01, DIFFERENT),
            TestCase("no underscores in numbers", "1_000", "1000", 1, DIFFERENT),
        ]
        for case in testcases:
            actual = compare_values(case.reference, case.candidate, normalise_tolerance(case.tolerance))
            self.assertEqual(case.expected, actual, "failed test '{}': expected {}, got {}".format(
                case.name, case.expected, actual))

    def test_invalid_tolerance(self):
        self.assertRaises(VerificationError, normalise_tolerance, "about")
        self.assertRaises(VerificationError, normalise_tolerance, True)

    def test_parse_columns(self):
        columns = parse_columns([{"a": "="}, {1: 0.5}, "b"])
        self.assertEqual(list(columns), ["a", "1", "b"])
        self.assertEqual(columns["1"], {"type": "absolute", "value": 0.5})

    def test_spec_loader_accepts_bare_equals(self):
        text = "columns:\n  - chrom: = #Exact match\n  - FORMAT:\n    - AF: 0.01\n  - INFO:\n    - XX: \n"
        self.assertRaises(yaml.constructor.ConstructorError, yaml.safe_load, text)
        self.assertEqual(yaml.load(text, Loader=SpecLoader),
                         {"columns": [{"chrom": "="}, {"FORMAT": [{"AF": 0.01}]}, {"INFO": [{"XX": None}]}]})

    def test_json_safe(self):
        self.assertEqual(json_safe({1: (float("nan"), None)}), {"1": ["nan", None]})
