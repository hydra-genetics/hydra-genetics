# coding: utf-8

import unittest
from unittest.mock import Mock
import pytest
import pandas
from pandas.testing import assert_series_equal, assert_frame_equal
from snakemake.io import Wildcards


class TestUnitUtils(unittest.TestCase):
    def setUp(self):
        self.units = pandas.read_table(
            "tests/utils/files/units.tsv",
            dtype=str
        ).set_index(["sample", "type", "run", "lane"], drop=False)
        self.sample_NA12878 = {
            "L1": Wildcards(fromdict={'sample': 'NA12878', "run": "1", "type": "N", "lane": "1"}),
            "L2": Wildcards(fromdict={'sample': 'NA12878', "run": "1", "type": "N", "lane": "2"})
            }
        self.sample_NA13878 = Wildcards(fromdict={'sample': 'NA13878', "run": "1", "type": "N", "lane": "1"})
        self.sample_NA22878 = Wildcards(fromdict={'sample': 'NA22878', "run": "1", "type": "N", "lane": "1"})
        self.sample_NA12978 = Wildcards(fromdict={'sample': 'NA12978', "run": "1", "type": "N", "lane": "1"})
        self.sample_BE12878 = {
            "N_L1": Wildcards(fromdict={'sample': 'BE12878', "run": "2", "type": "N", "lane": "1"}),
            "N_L2": Wildcards(fromdict={'sample': 'BE12878', "run": "2", "type": "N", "lane": "2"}),
            "T_L3": Wildcards(fromdict={'sample': 'BE12878', "run": "2", "type": "T", "lane": "3"}),
            "R_L4": Wildcards(fromdict={'sample': 'BE12878', "run": "2", "type": "R", "lane": "4"})
        }

    def tearDown(self):
        pass

    def test_get_unit(self):
        from hydra_genetics.utils.units import get_unit
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "1", "1")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "1", "2")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "1", "1")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "1", "1")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "1", "1")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "2", "1")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "2", "2")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "2", "3")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "2", "4")].dropna()
        )

    def test_get_fastq_file(self):
        from hydra_genetics.utils.units import get_fastq_file
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "1", "1")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "1", "2")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "1", "1")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "1", "1")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "1", "1")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "2", "1")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "2", "2")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "2", "3")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "2", "4")].dropna()['fastq1']
        )

        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "1", "1")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"], "fastq2"),
            self.units.loc[('NA12878', "N", "1", "2")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878, "fastq2"),
            self.units.loc[('NA13878', "N", "1", "1")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878, "fastq2"),
            self.units.loc[('NA22878', "N", "1", "1")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978, "fastq2"),
            self.units.loc[('NA12978', "N", "1", "1")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"], "fastq2"),
            self.units.loc[('BE12878', "N", "2", "1")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"], "fastq2"),
            self.units.loc[('BE12878', "N", "2", "2")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"], "fastq2"),
            self.units.loc[('BE12878', "T", "2", "3")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"], "fastq2"),
            self.units.loc[('BE12878', "R", "2", "4")].dropna()['fastq2']
        )
        self.assertNotEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "1", "1")].dropna()['fastq1']
        )

        with self.assertRaisesRegex(ValueError, "Incorrect input value error fastq3: expected fastq1 or fastq2"):
            self.assertTrue(get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq3"))

        with self.assertRaises(KeyError):
            self.assertTrue(
                get_fastq_file(self.units, Wildcards(fromdict={'sample': 'BE12878', "run": "2", "type": "N", "lane": "5"}))
            )

    def test_get_fastq_adapter(self):
        from hydra_genetics.utils.units import get_fastq_adapter
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_NA12878["L1"]),
            "ACGT,TGCA1"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_NA12878["L2"]),
            "ACGT,TGCA2"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_NA13878),
            "ACGT,TGCA3"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_NA22878),
            "ACGT,TGCA4"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_NA12978),
            "ACGT,TGCA5"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_BE12878["N_L1"]),
            "ACGT,TGCA6"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_BE12878["N_L2"]),
            "ACGT,TGCA7"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_BE12878["T_L3"]),
            "ACGT,TGCA8"
        )
        self.assertEqual(
            get_fastq_adapter(self.units, self.sample_BE12878["R_L4"]),
            "ACGT,TGCA9"
        )

        with self.assertRaises(KeyError):
            self.assertTrue(
                get_fastq_adapter(self.units, Wildcards(fromdict={'sample': 'BE12878', "run": "1", "type": "N", "lane": "5"}))
            )

    def test_get_units(self):
        from hydra_genetics.utils.units import get_units
        self.assertEqual(
            len(get_units(self.units, Wildcards(fromdict={'sample': 'NA12878', "type": "N"}))),
            2
        )
        self.assertEqual(
            len(get_units(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N"}))),
            1
        )
        self.assertEqual(
            get_units(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N"}))[0],
            list(self.units.loc[('NA13878', "N")].dropna().itertuples())[0]
        )
        self.assertEqual(
            len(get_units(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "N"}))),
            2
        )
        self.assertEqual(
            len(get_units(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "T"}))),
            1
        )
        self.assertEqual(
            len(get_units(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "R"}))),
            1
        )

    def test_get_fastq_files(self):
        from hydra_genetics.utils.units import get_fastq_files
        self.assertEqual(
            len(get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA12878', "type": "N", "read": "fastq1"}))),
            2
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA12878', "type": "N", "read": "fastq1"})),
            ['input/1_R1_L1.fq.gz', 'input/2_R1_L2.fq.gz']
        )
        self.assertEqual(
            len(get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA12878', "type": "N", "read": "fastq2"}))),
            2
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA12878', "type": "N", "read": "fastq2"})),
            ['input/1_R2_L1.fq.gz', 'input/2_R2_L2.fq.gz']
        )
        self.assertEqual(
            len(get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N", "read": "fastq1"}))),
            1
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N", "read": "fastq1"})),
            ['input/3_R1_L1.fq.gz']
        )
        self.assertEqual(
            len(get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N", "read": "fastq2"}))),
            1
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N", "read": "fastq1"})),
            ['input/3_R1_L1.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'NA13878', "type": "N", "read": "fastq2"})),
            ['input/3_R2_L1.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "N", "read": "fastq1"})),
            ['input/6_R1_L1.fq.gz', 'input/7_R1_L2.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "N", "read": "fastq2"})),
            ['input/6_R2_L1.fq.gz', 'input/7_R2_L2.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "T", "read": "fastq1"})),
            ['input/8_R1_L3.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "T", "read": "fastq2"})),
            ['input/8_R2_L3.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "R", "read": "fastq1"})),
            ['input/9_R1_L4.fq.gz']
        )
        self.assertEqual(
            get_fastq_files(self.units, Wildcards(fromdict={'sample': 'BE12878', "type": "R", "read": "fastq2"})),
            ['input/9_R2_L4.fq.gz']
        )

    def test_get_unit_types(self):
        from hydra_genetics.utils.units import get_unit_types
        self.assertEqual(
            get_unit_types(self.units, Wildcards(fromdict={'sample': 'NA12878'})),
            {'N'}
        )
        self.assertEqual(
            get_unit_types(self.units, Wildcards(fromdict={'sample': 'BE12878'})),
            {'N', 'T', 'R'}
        )
