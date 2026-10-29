import unittest
import os
import shutil
import tempfile
import pandas as pd
import pysam
from hydra_genetics.commands.create import CreateLongReadInputFiles, extract_bam_information


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

    def _write_bam(self, read_group, name="test.bam"):
        """Write a one-read unmapped BAM whose header has the given read group (None for no RG line)."""
        path = os.path.join(self.test_dir, name)
        header = {"HD": {"VN": "1.6"}}
        if read_group is not None:
            header["RG"] = [read_group]
        with pysam.AlignmentFile(path, "wb", header=header) as bam:
            read = pysam.AlignedSegment()
            read.query_name = "read1"
            read.query_sequence = "ACGT"
            read.flag = 4
            bam.write(read)
        return path

    def test_extract_bam_information_missing_tags_give_clear_error(self):
        ont_ds = "runid=abc basecall_model=model1"
        cases = [
            ("no RG line", "ONT", None, "read group"),
            ("no PL", "ONT", {"ID": "x", "PU": "pu", "DS": ont_ds, "SM": "s"}, "PL"),
            ("no PU", "ONT", {"ID": "x", "PL": "ONT", "DS": ont_ds, "SM": "s"}, "PU"),
            ("ONT without DS", "ONT", {"ID": "x", "PL": "ONT", "PU": "pu", "SM": "s"}, "DS"),
            ("ONT DS without runid", "ONT", {"ID": "x", "PL": "ONT", "PU": "pu", "DS": "basecall_model=m", "SM": "s"}, "runid"),
            ("ONT without al, SM and LB", "ONT", {"ID": "x", "PL": "ONT", "PU": "pu", "DS": ont_ds}, "LB"),
            ("PACBIO without SM and LB", "PACBIO", {"ID": "x", "PL": "PACBIO", "PU": "pu"}, "LB"),
        ]
        for label, platform, read_group, expected in cases:
            with self.subTest(label):
                path = self._write_bam(read_group)
                with self.assertLogs("hydra_genetics.commands.create", level="ERROR") as logs:
                    with self.assertRaises(SystemExit):
                        extract_bam_information(path, platform=platform)
                self.assertIn(expected, logs.output[0])
                self.assertIn(path, logs.output[0])

    def test_extract_bam_information_pacbio_does_not_need_ds(self):
        path = self._write_bam({"ID": "x", "PL": "PACBIO", "PU": "pu1", "SM": "sample1"})
        rg_dict = extract_bam_information(path, platform="PACBIO")
        self.assertEqual(rg_dict["pu"], "pu1")
        self.assertEqual(rg_dict["sample"], "sample1")


if __name__ == "__main__":
    unittest.main()
