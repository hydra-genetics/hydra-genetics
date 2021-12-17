# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

import logging
import os
import shutil
import tempfile
import unittest

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())


class TestHotspots(unittest.TestCase):
    def setUp(self):
        # create fixtures
        self.tempdir = tempfile.mkdtemp()
        with open(os.path.join(self.tempdir, "hotspot"), 'w') as hotspots:
            hotspots.write("#Chr\tStart\tEnd\tGene\tCDS_mutation_syntax\tAA_mutation_syntax\tReport\tcomment\tExon\tAccession_number\n")  # noqa
            hotspots.write("NC_000001.10\t115252190\t115252349\tNRAS\t-\t-\tindel\t-\texon4\tNM_002524\n")
            hotspots.write("NC_000001.10\t115252202\t115252202\tNRAS\tc.C438\tp.A146\thotspot\t-\texon4\tNM_002524\n")
            hotspots.write("NC_000017.10\t37880979\t37881164\tERBB2\t-\t-\tindel\t-\texon20\tNM_004448\n")
            hotspots.write("NC_000012.11\t25398279\t25398279\tKRAS\tc.G40\tp.V14\tregion\t-\texon2\tNM_004985\n")
            hotspots.write("NC_000017.10\t37880986\t37880987\tERBB2\t-\tp.Y772\tregion_all\t-\texon20\tNM_004448\n")

    def tearDown(self):
        # delete fixtures
        shutil.rmtree(self.tempdir)

    def test_header_parsing(self):
        from hydra_genetics.utils.io.hotspot import Reader
        reader = Reader(os.path.join(self.tempdir, "hotspot"))
        self.assertEqual(10, len(reader.header.keys()))
        self.assertEqual(0, reader.header["CHR"])
        self.assertEqual(1, reader.header["START"])
        self.assertEqual(2, reader.header["END"])
        self.assertEqual(3, reader.header["GENE"])
        self.assertEqual(4, reader.header["CDS_MUTATION_SYNTAX"])
        self.assertEqual(5, reader.header["AA_MUTATION_SYNTAX"])
        self.assertEqual(6, reader.header["REPORT"])
        self.assertEqual(7, reader.header["COMMENT"])
        self.assertEqual(8, reader.header["EXON"])
        self.assertEqual(9, reader.header["ACCESSION_NUMBER"])

    def test_record_parsing(self):
        from hydra_genetics.utils.io.hotspot import Reader
        from hydra_genetics.utils.models.hotspot import ReportClass
        reader = Reader(os.path.join(self.tempdir, "hotspot"))

        record = reader.next()
        self.assertEqual("NC_000001.10", record.CHROMOSOME)
        self.assertEqual(115252190, record.START)
        self.assertEqual(115252349, record.END)
        self.assertEqual("NRAS", record.GENE)
        self.assertEqual("-", record.CDS_MUTATION_SYNTAX)
        self.assertEqual("-", record.AA_MUTATION_SYNTAX)
        self.assertEqual(ReportClass.indel, record.REPORT)
        self.assertEqual("-", record.COMMENT)
        self.assertEqual("exon4", record.EXON)
        self.assertEqual("NM_002524", record.ACCESSION_NUMBER)
        self.assertEqual(160, len(record.VARIANTS))
        self.assertListEqual([{'extended': False, "variants": []} for i in range(160)], record.VARIANTS)

        record = reader.next()
        self.assertEqual("NC_000001.10", record.CHROMOSOME)
        self.assertEqual(115252202, record.START)
        self.assertEqual(115252202, record.END)
        self.assertEqual("NRAS", record.GENE)
        self.assertEqual("c.C438", record.CDS_MUTATION_SYNTAX)
        self.assertEqual("p.A146", record.AA_MUTATION_SYNTAX)
        self.assertEqual(ReportClass.hotspot, record.REPORT)
        self.assertEqual("-", record.COMMENT)
        self.assertEqual("exon4", record.EXON)
        self.assertEqual("NM_002524", record.ACCESSION_NUMBER)
        self.assertEqual(1, len(record.VARIANTS))
        self.assertEqual([{'extended': False, "variants": []}], record.VARIANTS)

        record = reader.next()
        self.assertEqual("NC_000017.10", record.CHROMOSOME)
        self.assertEqual(37880979, record.START)
        self.assertEqual(37881164, record.END)
        self.assertEqual("ERBB2", record.GENE)
        self.assertEqual("-", record.CDS_MUTATION_SYNTAX)
        self.assertEqual("-", record.AA_MUTATION_SYNTAX)
        self.assertEqual(ReportClass.indel, record.REPORT)
        self.assertEqual("-", record.COMMENT)
        self.assertEqual("exon20", record.EXON)
        self.assertEqual("NM_004448", record.ACCESSION_NUMBER)
        self.assertEqual(186, len(record.VARIANTS))
        self.assertEqual([{'extended': False, "variants": []} for i in range(186)], record.VARIANTS)

        record = reader.next()
        self.assertEqual("NC_000012.11", record.CHROMOSOME)
        self.assertEqual(25398279, record.START)
        self.assertEqual(25398279, record.END)
        self.assertEqual("KRAS", record.GENE)
        self.assertEqual("c.G40", record.CDS_MUTATION_SYNTAX)
        self.assertEqual("p.V14", record.AA_MUTATION_SYNTAX)
        self.assertEqual(ReportClass.region, record.REPORT)
        self.assertEqual("-", record.COMMENT)
        self.assertEqual("exon2", record.EXON)
        self.assertEqual("NM_004985", record.ACCESSION_NUMBER)
        self.assertEqual(1, len(record.VARIANTS))
        self.assertEqual([{'extended': False, "variants": []}], record.VARIANTS)

        record = reader.next()
        self.assertEqual("NC_000017.10", record.CHROMOSOME)
        self.assertEqual(37880986, record.START)
        self.assertEqual(37880987, record.END)
        self.assertEqual("ERBB2", record.GENE)
        self.assertEqual("-", record.CDS_MUTATION_SYNTAX)
        self.assertEqual("p.Y772", record.AA_MUTATION_SYNTAX)
        self.assertEqual(ReportClass.region_all, record.REPORT)
        self.assertEqual("-", record.COMMENT)
        self.assertEqual("exon20", record.EXON)
        self.assertEqual("NM_004448", record.ACCESSION_NUMBER)
        self.assertEqual(2, len(record.VARIANTS))
        self.assertEqual([{'extended': False, "variants": []}, {'extended': False, "variants": []}], record.VARIANTS)

        with self.assertRaises(StopIteration):
            reader.next()


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level=logging.CRITICAL, stream=sys.stdout, format='%(message)s')
    unittest.main()
