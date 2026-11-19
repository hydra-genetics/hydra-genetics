# coding: utf-8

import json
import os
import shutil
import tempfile
import unittest

from hydra_genetics.utils.verification import (
    check_known_variants, compare_text, render_report, summarise_results, write_json, write_summary_tsv,
)
from tests.utils.verification.helpers import write_text, write_vcf


class TestKnownVariants(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        vcf = write_vcf(self.dir, "c.vcf", [(100, "A", "T", 0.10, 10, "mutect2", "KRAS")])
        cnv = write_text(self.dir, "cnv.tsv", "gene(s)\tcopy_number\nERBB2, GRB7\t8.1\nCDKN2A\t0.9\n")
        tmb = write_text(self.dir, "tmb.txt", "TMB:\t12.5\nNumber of variants:\t20\nchr1\t1\n")
        self.files = {
            "vcf": {"path": vcf, "comparator": "vcf", "settings": {}},
            "cnv": {"path": cnv, "comparator": "table", "settings": {}},
            "tmb": {"path": tmb, "comparator": "table", "settings": {"header": False, "rows": 2}},
            "gone": {"path": os.path.join(self.dir, "gone.tsv"), "comparator": "table", "settings": {}},
        }

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_statuses(self):
        expectations = [
            {"sample": "S1", "type": "T", "variant_type": "SNV", "file": "vcf",
             "variant": {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "T"}, "expression": "FORMAT:AF:0 > 0.05"},
            {"sample": "S1", "type": "T", "variant_type": "SNV", "file": "vcf",
             "variant": {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "T"}, "expression": "FORMAT:AF:0 > 0.5"},
            {"sample": "S1", "type": "T", "variant_type": "INDEL", "file": "vcf", "variant": {"chrom": "chr1", "pos": 7}},
            {"sample": "S1", "type": "T", "variant_type": "CNV", "file": "cnv",
             "match": {"gene(s)": {"regex": "\\bERBB2\\b"}}, "expect": {"copy_number": {"min": 6}}},
            {"sample": "S1", "type": "T", "variant_type": "CNV", "file": "cnv",
             "match": {"gene(s)": "CDKN2A"}, "expect": {"copy_number": {"max": 0.5}}},
            {"sample": "S1", "type": "T", "variant_type": "TMB", "file": "tmb",
             "match": {0: "TMB:"}, "expect": {1: {"min": 10, "max": 20}}},
            {"sample": "S1", "type": "T", "variant_type": "MSI", "file": "gone", "expect": {"%": {"min": 10}}},
            {"sample": "S1", "type": "T", "variant_type": "Fusion", "file": "unknown"},
        ]
        statuses = [r["status"] for r in check_known_variants(expectations, self.files)]
        self.assertEqual(statuses, ["found", "failed_expectation", "not_found", "found", "failed_expectation", "found",
                                    "not_checked", "not_checked"])


class TestReport(unittest.TestCase):
    def test_summary_tsv_and_html(self):
        directory = tempfile.mkdtemp()
        try:
            ref = write_text(directory, "r.txt", "a\n")
            comparison = compare_text(ref, write_text(directory, "c.txt", "b\n"))
            comparison.update({"name": "text <file>", "sample": "S1", "type": "T"})
            json_file = os.path.join(directory, "result.json")
            write_json(comparison, json_file)
            known = [{"kind": "known_variant", "sample": "S1", "type": "T", "variant_type": "SNV", "status": "found"}]
            summary = summarise_results([json_file, known], {"pipeline": "test"})
            self.assertEqual(summary["verdict"], "review_required")
            self.assertEqual(summary["totals"]["comparisons"]["different"], 1)
            self.assertEqual(summary["totals"]["known_variants"]["found"], 1)
            tsv = os.path.join(directory, "summary.tsv")
            write_summary_tsv(summary, tsv)
            with open(tsv) as fh:
                self.assertEqual(len(fh.read().splitlines()), 3)
            template = write_text(directory, "t.html", "<h1>{{ verdict }}</h1>{% for f in files %}{{ f.name }}{% endfor %}"
                                                       "<style>{{ css }}</style>{{ samples|join(',') }}")
            css = write_text(directory, "s.css", "h1 {}")
            html = render_report(summary, template, [css], os.path.join(directory, "report.html"))
            self.assertIn("text &lt;file&gt;", html)
            self.assertIn("S1_T", html)
            self.assertEqual(json.loads(json.dumps(summary))["verdict"], "review_required")
        finally:
            shutil.rmtree(directory)
