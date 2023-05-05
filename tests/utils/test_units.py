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
        ).set_index(["sample", "type", "flowcell", "lane", "barcode"], drop=False).sort_index()

        self.units_2 = pandas.read_table(
            "tests/utils/files/units_2.tsv",
            dtype=str
        ).set_index(["sample", "type"], drop=False).sort_index()
        self.sample_NA12878 = {
            "L1": Wildcards(fromdict={
                'sample': 'NA12878', "flowcell": "HKTG2BGXG", "type": "N", "lane": "L001", "barcode": "ACGGAACA+ACGAGAAC"
            }),
            "L2": Wildcards(fromdict={
                'sample': 'NA12878', "flowcell": "HKTG2BGXG", "type": "N", "lane": "L002", "barcode": "CCGGAACA+ACGAGAAC"
            })
        }
        self.sample_NA13878 = Wildcards(fromdict={
            'sample': 'NA13878', "flowcell": "HKTG2BGXG", "type": "N", "lane": "L001", "barcode": "GCGGAACA+ACGAGAAC"
        })
        self.sample_NA22878 = Wildcards(fromdict={
            'sample': 'NA22878', "flowcell": "HKTG2BGXG", "type": "N", "lane": "L001", "barcode": "TGGGGGGG+ACGAGAAC"
        })
        self.sample_NA12978 = Wildcards(fromdict={
            'sample': 'NA12978', "flowcell": "HLCF3DRXY", "type": "N", "lane": "L001", "barcode": "AAGGAACA+ACGAGAAC"
        })
        self.sample_BE12878 = {
            "N_L1": Wildcards(fromdict={
                'sample': 'BE12878', "flowcell": "HLCF3DRXY", "type": "N", "lane": "L001", "barcode": "ACGGAACA+ACGAGAAC"
            }),
            "N_L2": Wildcards(fromdict={
                'sample': 'BE12878', "flowcell": "HLCF3DRXY", "type": "N", "lane": "L002", "barcode": "AGGGAACA+ACGAGAAC"
            }),
            "T_L3": Wildcards(fromdict={
                'sample': 'BE12878', "flowcell": "HLCF3DRXY", "type": "T", "lane": "L003", "barcode": "ATGGAACA+ACGAGAAC"
            }),
            "R_L4": Wildcards(fromdict={
                'sample': 'BE12878', "flowcell": "HLCF3DRXY", "type": "R", "lane": "L004", "barcode": "ACAGAACA+ACGAGAAC"
            })
        }

    def tearDown(self):
        pass

    def test_get_unit(self):
        from hydra_genetics.utils.units import get_unit
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001", "ACGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002", "CCGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001", "GCGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001", "TGGGGGGG+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001", "AAGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001", "ACGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002", "AGGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003", "ATGGAACA+ACGAGAAC")].dropna()
        )
        assert_series_equal(
            get_unit(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004", "ACAGAACA+ACGAGAAC")].dropna()
        )

    def test_get_fastq_file(self):
        from hydra_genetics.utils.units import get_fastq_file
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001", "ACGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"]),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002", "CCGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001", "GCGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001", "TGGGGGGG+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001", "AAGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001", "ACGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"]),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002", "AGGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"]),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003", "ATGGAACA+ACGAGAAC")].dropna()['fastq1']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"]),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004", "ACAGAACA+ACGAGAAC")].dropna()['fastq1']
        )

        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001", "ACGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12878["L2"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L002", "CCGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA13878, "fastq2"),
            self.units.loc[('NA13878', "N", "HKTG2BGXG", "L001", "GCGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA22878, "fastq2"),
            self.units.loc[('NA22878', "N", "HKTG2BGXG", "L001", "TGGGGGGG+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_NA12978, "fastq2"),
            self.units.loc[('NA12978', "N", "HLCF3DRXY", "L001", "AAGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L1"], "fastq2"),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L001", "ACGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["N_L2"], "fastq2"),
            self.units.loc[('BE12878', "N", "HLCF3DRXY", "L002", "AGGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["T_L3"], "fastq2"),
            self.units.loc[('BE12878', "T", "HLCF3DRXY", "L003", "ATGGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertEqual(
            get_fastq_file(self.units, self.sample_BE12878["R_L4"], "fastq2"),
            self.units.loc[('BE12878', "R", "HLCF3DRXY", "L004", "ACAGAACA+ACGAGAAC")].dropna()['fastq2']
        )
        self.assertNotEqual(
            get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq2"),
            self.units.loc[('NA12878', "N", "HKTG2BGXG", "L001", "ACGGAACA+ACGAGAAC")].dropna()['fastq1']
        )

        with self.assertRaisesRegex(ValueError, "Incorrect input value error fastq3: expected fastq1 or fastq2"):
            self.assertTrue(get_fastq_file(self.units, self.sample_NA12878["L1"], "fastq3"))

        with self.assertRaises(KeyError):
            self.assertTrue(
                get_fastq_file(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                               "flowcell": "HLCF3DRXY",
                                                               "type": "N",
                                                               "lane": "L005",
                                                               "barcode": "AAAAAA+CCCCCC"}))
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
                                                                  "flowcell": "HLCF3DRXY",
                                                                  "type": "N",
                                                                  "lane": "L005",
                                                                  "barcode": "AAAA+CCCC"}))
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
            2
        )

        # small dataframe that produces a pandas.Series in get_units
        units3 = pandas.DataFrame(
            dict(
                sample=["NA12878", "NA12878", "NA13878"],
                type=["N", "T", "N"],
            )
        ).set_index(["sample", "type"], drop=False)
        self.assertEqual(len(get_units(units3, Wildcards(fromdict={"sample": "NA12878", "type": "N"}))), 1)

    def test_get_unit_barcodes(self):
        from hydra_genetics.utils.units import get_unit_barcodes
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N"})),
            {'ACGGAACA+ACGAGAAC', 'CCGGAACA+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N"})),
            {'GCGGAACA+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N"})),
            {'TGGGGGGG+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "N"})),
            {'AAGGAACA+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "N"})),
            {'ACGGAACA+ACGAGAAC', 'AGGGAACA+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "T"})),
            {'ATGGAACA+ACGAGAAC'}
        )
        self.assertEqual(
            get_unit_barcodes(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "R"})),
            {'ACAGAACA+ACGAGAAC'}
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
                                                             'flowcell': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001",
                                                             'barcode': "ACGGAACA+ACGAGAAC"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                             'flowcell': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L002",
                                                             'barcode': "CCGGAACA+ACGAGAAC"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                             'flowcell': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001",
                                                             'barcode': "GCGGAACA+ACGAGAAC"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                             'flowcell': 'HKTG2BGXG',
                                                             'type': "N",
                                                             'lane': "L001",
                                                             'barcode': "TGGGGGGG+ACGAGAAC"})),
            'NDX550220'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                             'flowcell': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001',
                                                             'barcode': "AAGGAACA+ACGAGAAC"})),
            'M03273'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'flowcell': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L001',
                                                             'barcode': "ACGGAACA+ACGAGAAC"})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'flowcell': 'HLCF3DRXY',
                                                             'type': "N",
                                                             'lane': 'L002',
                                                             'barcode': "AGGGAACA+ACGAGAAC"})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'flowcell': 'HLCF3DRXY',
                                                             'type': "T",
                                                             'lane': 'L003',
                                                             'barcode': "ATGGAACA+ACGAGAAC"})),
            'A00687'
        )
        self.assertEqual(
            get_unit_machine(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                             'flowcell': 'HLCF3DRXY',
                                                             'type': "R",
                                                             'lane': 'L004',
                                                             'barcode': "ACAGAACA+ACGAGAAC"})),
            'A00687'
        )

    def test_get_unit_platform(self):
        from hydra_genetics.utils.units import get_unit_platform
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001",
                                                              'barcode': "ACGGAACA+ACGAGAAC"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L002",
                                                              'barcode': "CCGGAACA+ACGAGAAC"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA13878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001",
                                                              'barcode': "GCGGAACA+ACGAGAAC"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA22878',
                                                              'flowcell': 'HKTG2BGXG',
                                                              'type': "N",
                                                              'lane': "L001",
                                                              'barcode': "TGGGGGGG+ACGAGAAC"})),
            'nextseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'NA12978',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L001',
                                                              'barcode': "AAGGAACA+ACGAGAAC"})),
            'miniseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L001',
                                                              'barcode': "ACGGAACA+ACGAGAAC"})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "N",
                                                              'lane': 'L002',
                                                              'barcode': "AGGGAACA+ACGAGAAC"})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "T",
                                                              'lane': 'L003',
                                                              'barcode': "ATGGAACA+ACGAGAAC"})),
            'novaseq'
        )
        self.assertEqual(
            get_unit_platform(self.units, Wildcards(fromdict={'sample': 'BE12878',
                                                              'flowcell': 'HLCF3DRXY',
                                                              'type': "R",
                                                              'lane': 'L004',
                                                              'barcode': "ACAGAACA+ACGAGAAC"})),
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

    def test_get_units_per_flowcell(self):
        from hydra_genetics.utils.units import get_units_per_flowcell
        self.assertEqual(
            len(get_units_per_flowcell(self.units, Wildcards(fromdict={"flowcell": "HKTG2BGXG"}))),
            3
        )
        self.assertEqual(
            len(get_units_per_flowcell(self.units, Wildcards(fromdict={"flowcell": "HLCF3DRXY"}))),
            4
        )
