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
        ).set_index(["sample", "type", "run", "lane"], drop=False).sort_index()

        self.units_2 = pandas.read_table(
            "tests/utils/files/units_2.tsv",
            dtype=str
        ).set_index(["sample", "type"], drop=False).sort_index()
        self.sample_NA12878 = {
            "L1": Wildcards(fromdict={'sample': 'NA12878', "run": "HKTG2BGXG", "type": "N", "lane": "L001"}),
            "L2": Wildcards(fromdict={'sample': 'NA12878', "run": "HKTG2BGXG", "type": "N", "lane": "L002"})
            }
        self.sample_NA13878 = Wildcards(fromdict={'sample': 'NA13878', "run": "HKTG2BGXG", "type": "N", "lane": "L001"})
        self.sample_NA22878 = Wildcards(fromdict={'sample': 'NA22878', "run": "HKTG2BGXG", "type": "N", "lane": "L001"})
        self.sample_NA12978 = Wildcards(fromdict={'sample': 'NA12978', "run": "HLCF3DRXY", "type": "N", "lane": "L001"})
        self.sample_BE12878 = {
            "N_L1": Wildcards(fromdict={'sample': 'BE12878', "run": "HLCF3DRXY", "type": "N", "lane": "L001"}),
            "N_L2": Wildcards(fromdict={'sample': 'BE12878', "run": "HLCF3DRXY", "type": "N", "lane": "L002"}),
            "T_L3": Wildcards(fromdict={'sample': 'BE12878', "run": "HLCF3DRXY", "type": "T", "lane": "L003"}),
            "R_L4": Wildcards(fromdict={'sample': 'BE12878', "run": "HLCF3DRXY", "type": "R", "lane": "L004"})
        }

    def tearDown(self):
        pass

    def test_get_unit(self):
        from hydra_genetics.utils.units import get_unit
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004")].dropna()
        )

    def test_get_fastq_file(self):
        from hydra_genetics.utils.units import get_fastq_file
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004")].dropna()['fastq1']
        )

        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878, "fastq2"),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878, "fastq2"),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978, "fastq2"),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"], "fastq2"),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"], "fastq2"),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"], "fastq2"),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"], "fastq2"),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004")].dropna()['fastq2']
        )
        self.assertNotEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001")].dropna()['fastq1']
        )

        with self.assertRaisesRegex(ValueError, "Incorrect input value error fastq3: expected fastq1 or fastq2"):
            self.assertTrue(get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq3"))

        with self.assertRaises(KeyError):
            self.assertTrue(
                get_fastq_file(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                               "run": "HLCF3DRXY",
                                                               "type": "N",
                                                               "lane": "L005"}))
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
                get_fastq_adapter(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                                  "run": "HLCF3DRXY",
                                                                  "type": "N",
                                                                  "lane": "L005"}))
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
        self.assertEqual(
            len(get_units(self.units_2, Wildcards(fromdict={'sample': 'NA12878', "type": "N"}))),
            1
        )

    def test_get_unit_barcode(self):
        from hydra_genetics.utils.units import get_unit_barcode
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'ACGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L002"})),
            'CCGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'GCGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'TGGGGGGG+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001'})),
            'AAGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001'})),
            'ACGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L002'})),
            'AGGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "T",
                                                             'lane': 'L003'})),
            'ATGGAACA+ACGAGAAC'
        )
        self.assertEqual(
            get_unit_barcode(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "R",
                                                             'lane': 'L004'})),
            'ACAGAACA+ACGAGAAC'
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

    def test_get_unit_machine(self):
        from hydra_genetics.utils.units import get_unit_machine
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L002"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                             'run': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001'})),
            'M03273'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001'})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L002'})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "T",
                                                             'lane': 'L003'})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'run': 'HLCF3DRXY',
                                                             'type': "R",
                                                             'lane': 'L004'})),
            'A00687'
        )

    def test_get_unit_platform(self):
        from hydra_genetics.utils.units import get_unit_platform
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                              'run': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                              'run': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L002"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                              'run': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                              'run': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                              'run': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L001'})),
            'miniseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'run': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L001'})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'run': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L002'})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'run': 'HLCF3DRXY',
                                                              'type': "T",
                                                              'lane': 'L003'})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'run': 'HLCF3DRXY',
                                                              'type': "R",
                                                              'lane': 'L004'})),
            'novaseq'
        )

    def test_get_platforms(self):
        from hydra_genetics.utils.units import get_platforms
        self.assertEqual(
            get_platforms(self.units, Wildcards(fromdict={'sample': 'NA12878', 'type': "N"})),
            {'nextseq'}
        )
        self.assertEqual(
            get_platforms(self.units, Wildcards(fromdict={'sample': 'NA22878', 'type': "N"})),
            {'nextseq'}
        )
        self.assertEqual(
            get_platforms(self.units, Wildcards(fromdict={'sample': 'NA12978', 'type': "N"})),
            {'miniseq'}
        )
        self.assertEqual(
            get_platforms(self.units, Wildcards(fromdict={'sample': 'BE12878', 'type': "N"})),
            {'novaseq'}
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

    def test_get_units_per_run(self):
        from hydra_genetics.utils.units import get_units_per_run
        self.assertEqual(
            len(get_units_per_run(self.units, Wildcards(fromdict={"run": "HKTG2BGXG"}))),
            3
        )
        self.assertEqual(
            len(get_units_per_run(self.units, Wildcards(fromdict={"run": "HLCF3DRXY"}))),
            4
        )
