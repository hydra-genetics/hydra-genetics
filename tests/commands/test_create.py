import unittest
import os
import gzip
import shutil
import tempfile
import pandas as pd
from hydra_genetics.commands.create import CreateInputFiles


class TestCreateInputFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.out_dir = tempfile.mkdtemp()

        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(test_file_dir, "..", ".."))
        self.src_fastq_dir = os.path.join(repo_root, ".tests", "integration")

        self.fastq_dir = os.path.join(self.test_dir, "fastq")
        os.makedirs(self.fastq_dir)

        # Two normal-size, distinct real samples (same machine/flowcell/lane headers, different content)
        shutil.copy(
            os.path.join(self.src_fastq_dir, "HD827sonic_testing1_S1_R1.fastq.gz"),
            os.path.join(self.fastq_dir, "SAMPLEA_R1.fastq.gz"))
        shutil.copy(
            os.path.join(self.src_fastq_dir, "HD827sonic_testing1_S1_R2.fastq.gz"),
            os.path.join(self.fastq_dir, "SAMPLEA_R2.fastq.gz"))
        shutil.copy(
            os.path.join(self.src_fastq_dir, "HD827sonic_testing2_R1.fastq.gz"),
            os.path.join(self.fastq_dir, "SAMPLEB_R1.fastq.gz"))
        shutil.copy(
            os.path.join(self.src_fastq_dir, "HD827sonic_testing2_R2.fastq.gz"),
            os.path.join(self.fastq_dir, "SAMPLEB_R2.fastq.gz"))

        # A deliberately tiny sample: just the first read, truncated from the same real fixture, so
        # extract_run_information still has one real, parseable read header to work with.
        for read in ["R1", "R2"]:
            src = os.path.join(self.src_fastq_dir, "HD827sonic_testing3_{}.fastq.gz".format(read))
            dst = os.path.join(self.fastq_dir, "SAMPLETINY_{}.fastq.gz".format(read))
            with gzip.open(src, "rt") as fh_in:
                first_read = "".join(fh_in.readline() for _ in range(4))
            with gzip.open(dst, "wt") as fh_out:
                fh_out.write(first_read)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.out_dir)

    def _run(self, **kwargs):
        original_cwd = os.getcwd()
        os.chdir(self.out_dir)
        try:
            # read_number_regex matches the CLI's actual default (-R([12]{1})_); the class's own
            # internal default captures "R1"/"R2" including the letter, which downstream code can't
            # use as-is (a pre-existing inconsistency, unrelated to --min-file-size, not fixed here).
            creator = CreateInputFiles(
                directory=[self.fastq_dir], outdir=self.out_dir, read_number_regex=r"_R([12]{1})[_.]", **kwargs)
            creator.init()
        finally:
            os.chdir(original_cwd)

    def test_init_without_min_file_size_keeps_all_samples(self):
        self._run()
        samples_df = pd.read_csv(os.path.join(self.out_dir, "samples.tsv"), sep="\t")
        self.assertEqual(sorted(samples_df["sample"].values), ["SAMPLEA", "SAMPLEB", "SAMPLETINY"])
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "excluded_samples_mqc.tsv")))

    def test_init_with_min_file_size_excludes_tiny_sample(self):
        self._run(min_file_size=10000)

        samples_df = pd.read_csv(os.path.join(self.out_dir, "samples.tsv"), sep="\t")
        self.assertEqual(sorted(samples_df["sample"].values), ["SAMPLEA", "SAMPLEB"])

        units_df = pd.read_csv(os.path.join(self.out_dir, "units.tsv"), sep="\t")
        self.assertEqual(sorted(units_df["sample"].unique()), ["SAMPLEA", "SAMPLEB"])
        # Both mates of each surviving sample should be present
        self.assertEqual(len(units_df), 2)

        excluded_path = os.path.join(self.out_dir, "excluded_samples_mqc.tsv")
        self.assertTrue(os.path.exists(excluded_path))
        with open(excluded_path) as fh:
            content = fh.read()
        self.assertIn("SAMPLETINY", content)
        self.assertNotIn("SAMPLEA\t", content)
        self.assertNotIn("SAMPLEB\t", content)

    def test_init_min_file_size_header_only_when_nothing_excluded(self):
        self._run(min_file_size=100)  # below even the tiny sample's size

        samples_df = pd.read_csv(os.path.join(self.out_dir, "samples.tsv"), sep="\t")
        self.assertEqual(sorted(samples_df["sample"].values), ["SAMPLEA", "SAMPLEB", "SAMPLETINY"])

        excluded_path = os.path.join(self.out_dir, "excluded_samples_mqc.tsv")
        self.assertTrue(os.path.exists(excluded_path))
        with open(excluded_path) as fh:
            lines = [line for line in fh if not line.startswith("#")]
        # Header row only, no excluded-sample data rows
        self.assertEqual(len(lines), 1)

    def test_init_min_file_size_excludes_all_hard_fails_and_writes_mqc(self):
        original_cwd = os.getcwd()
        os.chdir(self.out_dir)
        try:
            creator = CreateInputFiles(
                directory=[self.fastq_dir], outdir=self.out_dir, read_number_regex=r"_R([12]{1})[_.]",
                min_file_size=999999999)
            with self.assertRaises(SystemExit):
                creator.init()
        finally:
            os.chdir(original_cwd)

        # The mqc file must exist even though every sample was excluded -- that's the whole point of it.
        excluded_path = os.path.join(self.out_dir, "excluded_samples_mqc.tsv")
        self.assertTrue(os.path.exists(excluded_path))
        with open(excluded_path) as fh:
            content = fh.read()
        for sample in ["SAMPLEA", "SAMPLEB", "SAMPLETINY"]:
            self.assertIn(sample, content)
        # samples.tsv/units.tsv must NOT have been written -- fail fast before any output
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "samples.tsv")))
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, "units.tsv")))


if __name__ == "__main__":
    unittest.main()
