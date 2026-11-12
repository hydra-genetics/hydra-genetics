# coding: utf-8

import base64
import gzip
import json
import os
import shutil
import tempfile
import unittest

from hydra_genetics.utils.verification import compare_bam, compare_file, compare_table, compare_text, compare_vcf
from tests.utils.verification.helpers import write_bam, write_text, write_vcf

VCF_COLUMNS = [{"chrom": "="}, {"pos": "="}, {"FORMAT": [{"AF": 0.01}]}, {"INFO": [{"CALLERS": "unordered"}]}]


class TestCompareVcf(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.reference = write_vcf(self.dir, "reference.vcf", [
            (100, "A", "T", 0.10, 10, "mutect2,vardict", "KRAS"),
            (200, "C", "G", 0.50, 50, "mutect2", "TP53"),
            (300, "G", "A", 0.005, 1, "vardict", "EGFR"),
        ])

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_identical_apart_from_volatile_header(self):
        candidate = write_vcf(self.dir, "candidate.vcf", [
            (100, "A", "T", 0.10, 10, "mutect2,vardict", "KRAS"),
            (200, "C", "G", 0.50, 50, "mutect2", "TP53"),
            (300, "G", "A", 0.005, 1, "vardict", "EGFR"),
        ], date="20260202")
        result = compare_vcf(self.reference, candidate, {"header": True})
        self.assertEqual(result["status"], "identical", result)
        self.assertEqual(result["counts"]["matched"], 3)

    def test_tolerance_filter_and_missing_variant(self):
        candidate = write_vcf(self.dir, "candidate.vcf", [
            (100, "A", "T", 0.105, 10, "vardict,mutect2", "KRAS"),
            (250, "T", "C", 0.30, 30, "mutect2", "BRAF"),
        ], sample="S1_T_new")
        result = compare_vcf(self.reference, candidate, {"columns": VCF_COLUMNS})
        self.assertEqual(result["status"], "different")
        self.assertEqual(result["counts"]["within_tolerance"], 1)
        self.assertEqual(result["counts"]["only_in_reference"], 2)
        self.assertEqual(result["counts"]["only_in_candidate"], 1)
        # dropping the low AF variant and the variant missing in the candidate leaves one extra candidate variant
        filtered = compare_vcf(self.reference, candidate, {"columns": VCF_COLUMNS,
                                                           "filter": "FORMAT:AF:0 < 0.011 or VEP:SYMBOL = TP53"})
        self.assertEqual(filtered["counts"]["reference_filtered_out"], 2)
        self.assertEqual(filtered["counts"]["only_in_candidate"], 1)

    def test_filter_without_index_is_reported(self):
        result = compare_vcf(self.reference, self.reference, {"filter": "FORMAT:AF < 0.011"})
        self.assertEqual(result["status"], "error")
        self.assertIn("FORMAT:AF:0", result["messages"][0])

    def test_unknown_field_and_missing_file(self):
        result = compare_vcf(self.reference, self.reference, {"columns": [{"INFO": [{"XX": None}]}]})
        self.assertEqual(result["status"], "identical")
        self.assertIn("INFO field XX is not defined", " ".join(result["messages"]))
        missing = compare_vcf(self.reference, os.path.join(self.dir, "none.vcf"))
        self.assertEqual(missing["status"], "missing")


class TestCompareBam(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.reads = [("r1", 10, "ACGTACGTAC"), ("r2", 20, "TTTTACGTAC"), ("r3", 30, "GGGGACGTAC")]
        self.reference = write_bam(self.dir, "reference.bam", self.reads)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_identical_with_other_program_line(self):
        candidate = write_bam(self.dir, "candidate.bam", self.reads, program="bwa mem /other/a.fa")
        result = compare_bam(self.reference, candidate, {"header": True})
        self.assertEqual(result["status"], "identical", result)
        self.assertEqual(result["counts"]["reference_records"], 3)

    def test_order_and_content(self):
        reordered = write_bam(self.dir, "reordered.bam", [self.reads[1], self.reads[0], self.reads[2]])
        self.assertEqual(compare_bam(self.reference, reordered)["status"], "different")
        self.assertEqual(compare_bam(self.reference, reordered, {"sort": True})["status"], "identical")
        changed = write_bam(self.dir, "changed.bam", self.reads[:2] + [("r3", 31, "GGGGACGTAC")])
        result = compare_bam(self.reference, changed, {"sort": True})
        self.assertEqual(result["status"], "different")
        unsorted = compare_bam(self.reference, changed)
        self.assertEqual(unsorted["differences_total"], 1)


class TestCompareTable(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_keyed_table(self):
        reference = write_text(self.dir, "ref.tsv", "gene(s)\tcaller\tcopy_number\nERBB2\tcnvkit\t8.10\nMYC\tgatk\t3.00\n")
        candidate = write_text(self.dir, "cand.tsv", "gene(s)\tcaller\tcopy_number\nMYC\tgatk\t3.05\nERBB2\tcnvkit\t8.10")
        settings = {"key": ["gene(s)", "caller"], "columns": [{"copy_number": 0.1}]}
        result = compare_table(reference, candidate, settings)
        self.assertEqual(result["status"], "within_tolerance", result)
        self.assertEqual(compare_table(reference, candidate, {"key": ["gene(s)", "caller"]})["status"], "different")
        self.assertEqual(compare_table(reference, candidate, {"key": ["nope"]})["status"], "error")

    def test_ragged_key_value_file(self):
        reference = write_text(self.dir, "ref.TMB.txt", "TMB:\t7.6\nNumber of variants:\t10\nchr1\t1\t.\tA\tT\t...\n")
        candidate = write_text(self.dir, "cand.TMB.txt", "TMB:\t7.9\nNumber of variants:\t10\nchr1\t2\t.\tA\tT\t...\n")
        result = compare_table(reference, candidate, {"header": False, "rows": 2, "key": [0], "columns": [{1: 0.5}]})
        self.assertEqual(result["status"], "within_tolerance", result)

    def test_preamble_and_quoted_csv(self):
        text = "# command line /a/b\n## METRICS CLASS\tx\nA\tB\n1\t2\n\n## HISTOGRAM\nx\ty\n"
        reference = write_text(self.dir, "ref.txt", text)
        candidate = write_text(self.dir, "cand.txt", text.replace("/a/b", "/c/d"))
        result = compare_table(reference, candidate, {"skip_until": "^## METRICS", "stop_at": "^## HISTOGRAM"})
        self.assertEqual(result["status"], "identical", result)
        quoted = write_text(self.dir, "hrd.txt", '""\t"HRD"\t"LST"\n"S1_T"\t1\t3\n')
        self.assertEqual(compare_table(quoted, quoted, {"key": [""]})["status"], "identical")
        self.assertEqual(compare_table(quoted, write_text(self.dir, "empty.csv", ""), {"sep": ","})["status"], "different")

    def test_json_records_and_compressed_payload(self):
        data = [{"chromosome": "chr1", "callers": [{"name": "cnvkit", "segments": [{"start": 1, "end": 9, "log2": 0.5}]}]},
                {"chromosome": "chr2", "callers": [{"name": "cnvkit", "segments": [{"start": 1, "end": 9, "log2": -0.4}]}]}]
        reference = write_text(self.dir, "ref.json", json.dumps(data))
        data[1]["callers"][0]["segments"][0]["log2"] = -0.42
        payload = base64.b64encode(gzip.compress(json.dumps(data).encode())).decode()
        candidate = write_text(self.dir, "cand.json", payload)
        settings = {"records": "[*].callers[*].segments", "key": ["root.chromosome", "callers.name", "start", "end"],
                    "columns": [{"log2": 0.05}]}
        result = compare_table(reference, candidate, settings)
        self.assertEqual(result["status"], "within_tolerance", result)
        self.assertEqual(result["counts"]["matched"], 2)
        flat = compare_table(reference, candidate, {})
        self.assertEqual(flat["status"], "different")
        self.assertEqual(flat["differences"][0]["column"], "value")

    def test_html_table_and_embedded_json(self):
        payload = base64.b64encode(gzip.compress(json.dumps([{"chromosome": "chr1", "cn": 3}]).encode())).decode()
        html = ("<html><body><time>{date}</time><table id='other'><tr><td>x</td></tr></table>"
                "<table id='extra-table-1'><thead><tr><th>gene</th><th>fraction</th></tr></thead>"
                "<tbody><tr><td>ERBB2</td><td>{fraction}<br>%</td></tr></tbody></table>"
                "<script>const compressedData = '{payload}';</script></body></html>")
        reference = write_text(self.dir, "ref.html", html.format(date="2026-01-01", fraction="0.5", payload=payload))
        candidate = write_text(self.dir, "cand.html", html.format(date="2026-02-02", fraction="0.6", payload=payload))
        table = compare_table(reference, candidate, {"table": "extra-table-1", "key": ["gene"]})
        self.assertEqual(table["status"], "different")
        self.assertEqual(table["differences"][0]["reference"], "0.5 %")
        embedded = compare_file(reference, candidate, {"embedded_json": {"pattern": "const compressedData = '(.*?)';"},
                                                       "records": "[*]", "key": ["chromosome"]})
        self.assertEqual(embedded["status"], "identical", embedded)
        self.assertEqual(embedded["comparator"], "table")


class TestCompareText(unittest.TestCase):
    def test_text(self):
        directory = tempfile.mkdtemp()
        try:
            reference = write_text(directory, "ref.txt", "# version 1\nSN\treads\t10\nSN\tbases\t100\n")
            candidate = write_text(directory, "cand.txt", "# version 2\nSN\treads\t10\nSN\tbases\t101\n")
            self.assertEqual(compare_text(reference, candidate, {"ignore_lines": ["^#"]})["status"], "different")
            result = compare_text(reference, candidate, {"ignore_lines": ["^#"], "replace": [["\\t10[01]$", "\\tN"]]})
            self.assertEqual(result["status"], "identical", result)
        finally:
            shutil.rmtree(directory)
