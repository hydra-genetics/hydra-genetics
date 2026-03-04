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

        # Paths to the test BAM files (assumed to be in the integration test folder)
        self.src_ont_bam_dir = "/Users/padco251/Documents/github/hydra-genetics/.tests/integration/ont_bams"
        self.src_pacbio_bam_dir = "/Users/padco251/Documents/github/hydra-genetics/.tests/integration/pacbio_bams"

        # Temporary directories for each test case
        self.ont_test_dir = os.path.join(self.test_dir, "ont")
        self.pacbio_test_dir = os.path.join(self.test_dir, "pacbio")
        os.makedirs(self.ont_test_dir)
        os.makedirs(self.pacbio_test_dir)

        # Copy ONT BAM files
        for file_name in ["test_ont_with_alias.bam", "test_ont_without_alias.bam"]:
            src_path = os.path.join(self.src_ont_bam_dir, file_name)
            if os.path.exists(src_path):
                shutil.copy(src_path, self.ont_test_dir)

        # Copy PacBio BAM files
        for file_name in ["m84010_220919_232145_s1.hifi_reads.bam"]:
            src_path = os.path.join(self.src_pacbio_bam_dir, file_name)
            if os.path.exists(src_path):
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
