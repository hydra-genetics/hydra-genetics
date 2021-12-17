# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

import logging
import os
import shutil
import tempfile
import unittest

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())


class TestModels(unittest.TestCase):
    def setUp(self):
        # create fixtures
        self.tempdir = tempfile.mkdtemp()
        with open(os.path.join(self.tempdir, "mapping"), 'w') as hotspots:
            hotspots.write("NC_000001.10\tchr1\t115252349\n")
            hotspots.write("NC_000017.10\tchr17\t37881164\n")
            hotspots.write("NC_000012.11\tchr12\t25398279")

    def tearDown(self):
        # delete fixtures
        shutil.rmtree(self.tempdir)

    def test_hotspot_creation(self):
        from hydra_genetics.utils.models.hotspot import Hotspot
        from hydra_genetics.utils.models.hotspot import ReportClass
        hotspot = Hotspot("NC_000017.10",
                          37880990,
                          37880990,
                          "ERBB2",
                          "c.123",
                          "p.V773",
                          ReportClass["region_all"], "-", "exon20", "NM_004448")
        self.assertEqual(hotspot.CHROMOSOME, "NC_000017.10")
        self.assertEqual(hotspot.START, 37880990)
        self.assertEqual(hotspot.END, 37880990)
        self.assertEqual(hotspot.GENE, "ERBB2")
        self.assertEqual(hotspot.CDS_MUTATION_SYNTAX, "c.123")
        self.assertEqual(hotspot.AA_MUTATION_SYNTAX, "p.V773")
        self.assertEqual(hotspot.REPORT, ReportClass.region_all)
        self.assertEqual(hotspot.COMMENT, "-")
        self.assertEqual(hotspot.EXON, "exon20")
        self.assertEqual(hotspot.ACCESSION_NUMBER, "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    "37880990",
                    37880990,
                    "ERBB2",
                    "c.123",
                    "p.V773",
                    ReportClass["region_all"], "-", "exon20", "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    "37880990",
                    "ERBB2",
                    "c.123",
                    "p.V773",
                    ReportClass["region_all"], "-", "exon20", "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    37880989,
                    "ERBB2",
                    "c.123",
                    "p.V773",
                    ReportClass["region_all"], "-", "exon20", "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    37880990,
                    "ERBB2",
                    "p.123",
                    "p.V773",
                    ReportClass["region_all"], "-", "exon20", "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    37880990,
                    "ERBB2",
                    "c.123",
                    "c.773",
                    ReportClass["region_all"], "-", "exon20", "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    37880990,
                    "ERBB2",
                    "c.123",
                    "p.V773",
                    "region_all",
                    "-",
                    "exon20",
                    "NM_004448")

        with self.assertRaises(ValueError):
            Hotspot("NC_000017.10",
                    37880990,
                    37880990,
                    "ERBB2",
                    "c.123",
                    "p.V773",
                    ReportClass["region_all"], "-", "e20", "NM_004448")

    def test_mapping_creation(self):
        from hydra_genetics.utils.io.chr import ChrTranslater
        translater = ChrTranslater(os.path.join(self.tempdir, "mapping"))

        self.assertEqual("chr1", translater.get_chr_value("NC_000001.10"))
        self.assertEqual("chr12", translater.get_chr_value("NC_000012.11"))
        self.assertEqual("chr17", translater.get_chr_value("NC_000017.10"))

        self.assertEqual("NC_000001.10", translater.get_nc_value("chr1"))
        self.assertEqual("NC_000012.11", translater.get_nc_value("chr12"))
        self.assertEqual("NC_000017.10", translater.get_nc_value("chr17"))


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level=logging.CRITICAL, stream=sys.stdout, format='%(message)s')
    unittest.main()
