import os
import shutil
import tempfile
import unittest

from click.testing import CliRunner

import hydra_genetics
from hydra_genetics.__main__ import cli

INTEGRATION = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           ".tests", "integration")


class TestCliMessages(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.pipeline_dir = os.path.join(self.tempdir, "testmod")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def invoke(self, *args):
        return CliRunner().invoke(cli, list(args))

    def create_pipeline(self):
        return self.invoke("create-pipeline", "-n", "testmod", "-d", "d", "-a", "a", "-e", "e", "-g", "g",
                           "--no-git", "-o", self.pipeline_dir)

    def test_version_flags(self):
        for flag in ["--version", "-V"]:
            with self.subTest(flag=flag):
                result = self.invoke(flag)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(hydra_genetics.__version__, result.output)

    def test_create_pipeline_reports_success(self):
        result = self.create_pipeline()
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(f"Created pipeline 'testmod' in {self.pipeline_dir}", result.output)

    def test_create_pipeline_failure_reports_no_success(self):
        os.makedirs(self.pipeline_dir)
        result = self.create_pipeline()
        self.assertEqual(result.exit_code, 1)
        self.assertNotIn("Created pipeline", result.output)

    def test_create_rule_reports_success(self):
        self.create_pipeline()
        result = self.invoke("create-rule", "-c", "sort", "-t", "samtools", "-m", "testmod", "-a", "a", "-e", "e",
                             "-o", self.tempdir)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Created rule 'samtools_sort'", result.output)

    def test_create_input_files_reports_success(self):
        result = self.invoke("create-input-files", "-d", INTEGRATION, "-o", self.tempdir, "-p", "Illumina",
                             "-s", r"([A-Za-z0-9]+_testing[0-9])_", "-n", "_R([12])", "--nreads", "10", "--every", "1")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn(f"Created {os.path.join(self.tempdir, 'samples.tsv')}", result.output)
        self.assertIn(f"Created {os.path.join(self.tempdir, 'units.tsv')}", result.output)
