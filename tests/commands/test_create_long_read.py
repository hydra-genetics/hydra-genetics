import unittest
import os
import shutil
import tempfile
import pandas as pd
from hydra_genetics.commands.create import CreateLongReadInputFiles


class TestCreateLongReadInputFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.out_dir = tempfile.mkdtemp()

        # Paths to the test BAM files relative to this test file
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(test_file_dir, "..", ".."))
        self.src_ont_bam_dir = os.path.join(repo_root, ".tests", "integration", "ont_bams")
        self.src_pacbio_bam_dir = os.path.join(repo_root, ".tests", "integration", "pacbio_bams")

        # Temporary directories for each test case
        self.ont_test_dir = os.path.join(self.test_dir, "ont")
        self.pacbio_test_dir = os.path.join(self.test_dir, "pacbio")
        os.makedirs(self.ont_test_dir)
        os.makedirs(self.pacbio_test_dir)

        # Copy ONT BAM files
        for file_name in ["test_ont_with_alias.bam", "test_ont_without_alias.bam"]:
            src_path = os.path.join(self.src_ont_bam_dir, file_name)
            if not os.path.exists(src_path):
                self.fail(f"Required ONT fixture missing: {src_path}")
            shutil.copy(src_path, self.ont_test_dir)

        # Copy PacBio BAM files
        for file_name in ["m84010_220919_232145_s1.hifi_reads.bam"]:
            src_path = os.path.join(self.src_pacbio_bam_dir, file_name)
            if not os.path.exists(src_path):
                self.fail(f"Required PacBio fixture missing: {src_path}")
            shutil.copy(src_path, self.pacbio_test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.out_dir)

    def test_init_ont_bams(self):
        # Change working directory to out_dir to avoid polluting the workspace
        original_cwd = os.getcwd()
        os.chdir(self.out_dir)

        try:
            creator = CreateLongReadInputFiles(
                directory=[self.ont_test_dir],
                outdir=self.out_dir,
                platform="ONT"
            )
            creator.init()

            # Check if output files exist
            self.assertTrue(os.path.exists("samples.tsv"))
            self.assertTrue(os.path.exists("units.tsv"))

            # Validate contents of samples.tsv
            samples_df = pd.read_csv("samples.tsv", sep="\t")
            # Based on the BAM headers:
            # test_ont_with_alias.bam: al='sample1', SM='barcode01' -> sample_id='sample1'
            # test_ont_without_alias.bam: SM='barcode01', no al -> sample_id='barcode01'
            self.assertIn("sample1", samples_df["sample"].values)
            self.assertIn("barcode01", samples_df["sample"].values)

            # Validate contents of units.tsv
            units_df = pd.read_csv("units.tsv", sep="\t")
            self.assertEqual(len(units_df), 2)
            self.assertIn("ONT", units_df["platform"].values)
            self.assertIn("basecalling_model", units_df.columns)
            self.assertIn("run_id", units_df.columns)

        finally:
            os.chdir(original_cwd)

    def test_init_pacbio_bams_with_min_file_size(self):
        # Three distinct real samples/sizes: HG004 (120107 bytes), HG003 (132982 bytes), HG002 (149507 bytes)
        multi_sample_dir = os.path.join(self.test_dir, "pacbio_multi")
        os.makedirs(multi_sample_dir)
        for file_name in ["m84010_220919_232145_s1.hifi_reads.bam",   # HG004, 120107 bytes
                          "m84010_220919_235306_s2.hifi_reads.bam",   # HG003, 132982 bytes
                          "m84011_220902_175841_s1.hifi_reads.bam"]:  # HG002, 149507 bytes
            shutil.copy(os.path.join(self.src_pacbio_bam_dir, file_name), multi_sample_dir)

        original_cwd = os.getcwd()
        os.chdir(self.out_dir)
        try:
            creator = CreateLongReadInputFiles(
                directory=[multi_sample_dir],
                outdir=self.out_dir,
                platform="PACBIO",
                min_file_size=140000,  # excludes HG004 and HG003, keeps HG002
            )
            creator.init()

            samples_df = pd.read_csv("samples.tsv", sep="\t")
            self.assertEqual(sorted(samples_df["sample"].values), ["HG002"])

            units_df = pd.read_csv("units.tsv", sep="\t")
            self.assertEqual(len(units_df), 1)
            self.assertIn("HG002", units_df["sample"].values)

            self.assertTrue(os.path.exists("excluded_samples_mqc.tsv"))
            with open("excluded_samples_mqc.tsv") as fh:
                content = fh.read()
            self.assertIn("HG004", content)
            self.assertIn("HG003", content)
            self.assertNotIn("HG002\t", content)
        finally:
            os.chdir(original_cwd)

    def test_init_pacbio_bams_min_file_size_excludes_all(self):
        multi_sample_dir = os.path.join(self.test_dir, "pacbio_all_excluded")
        os.makedirs(multi_sample_dir)
        shutil.copy(
            os.path.join(self.src_pacbio_bam_dir, "m84010_220919_232145_s1.hifi_reads.bam"), multi_sample_dir)

        original_cwd = os.getcwd()
        os.chdir(self.out_dir)
        try:
            creator = CreateLongReadInputFiles(
                directory=[multi_sample_dir],
                outdir=self.out_dir,
                platform="PACBIO",
                min_file_size=999999999,
            )
            with self.assertRaises(SystemExit):
                creator.init()
            self.assertFalse(os.path.exists("samples.tsv"))
        finally:
            os.chdir(original_cwd)

    def test_init_pacbio_bams(self):
        # Change working directory to out_dir to avoid polluting the workspace
        original_cwd = os.getcwd()
        os.chdir(self.out_dir)

        try:
            creator = CreateLongReadInputFiles(
                directory=[self.pacbio_test_dir],
                outdir=self.out_dir,
                platform="PACBIO"
            )
            creator.init()

            # Check if output files exist
            self.assertTrue(os.path.exists("samples.tsv"))
            self.assertTrue(os.path.exists("units.tsv"))

            # Validate contents of samples.tsv
            samples_df = pd.read_csv("samples.tsv", sep="\t")
            # Based on the BAM header: SM='HG004'
            self.assertIn("HG004", samples_df["sample"].values)

            # Validate contents of units.tsv
            units_df = pd.read_csv("units.tsv", sep="\t")
            self.assertEqual(len(units_df), 1)
            self.assertIn("PACBIO", units_df["platform"].values)
            # PacBio/non-ONT shouldn't have ONT specific columns
            self.assertNotIn("basecalling_model", units_df.columns)
            self.assertNotIn("run_id", units_df.columns)

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
