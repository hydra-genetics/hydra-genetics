# coding: utf-8

# Tests moved from the hydra-genetics filtering module (workflow/scripts/filter_vcf_test.py). The tests of the
# filtering driver use a minimal driver defined below, built on the shared helpers in hydra_genetics.utils.vcf_filter.

import unittest
import os
import tempfile
import yaml

from hydra_genetics.utils.io import utils
from pysam import VariantFile

from hydra_genetics.utils.vcf_filter import create_variant_filter
from hydra_genetics.utils.vcf_filter import _parse_helper
from hydra_genetics.utils.vcf_filter import _convert_string
from hydra_genetics.utils.vcf_filter import _and_function
from hydra_genetics.utils.vcf_filter import _or_function
from hydra_genetics.utils.vcf_filter import create_annotation_extractors
from hydra_genetics.utils.vcf_filter import create_convert_expression_function
from hydra_genetics.utils.vcf_filter import create_filter_from_vcf
from hydra_genetics.utils.vcf_filter import select_sample_index

FILES = "tests/utils/files/vcf_filter"


def filter_variants(sample_name_regex, in_vcf, out_vcf, filter_yaml_file):
    """Same behaviour as filter_variants in the filtering module, using the shared helpers."""
    variants = VariantFile(in_vcf)
    with open(filter_yaml_file) as file:
        filters = yaml.load(file, Loader=yaml.FullLoader)
    for name, value in filters["filters"].items():
        if "expression" not in value:
            raise Exception("No expression entry for %s" % name)
        if value.get("soft_filter", "True") != "False":
            if "soft_filter_flag" not in value:
                raise Exception("No soft_filter_flag entry for %s" % name)
            text = value.get("description", "Failed %s filter" % name)
        else:
            text = "%s (hard filtered)" % value.get("description", "Failed %s filter" % name)
        if "soft_filter_flag" in value:
            variants.header.filters.add(value["soft_filter_flag"], None, None, text)
    sample_index = select_sample_index(list(variants.header.samples), sample_name_regex)
    converter = create_convert_expression_function(create_annotation_extractors(variants, sample_index))
    vcf_filters = [(create_variant_filter(v["expression"], converter), v) for v in filters["filters"].values()]
    vcf_out = VariantFile(out_vcf, "w", header=variants.header)
    for variant in variants:
        hard_filter = False
        for vcf_filter, value in vcf_filters:
            if vcf_filter(variant):
                if value.get("soft_filter", "True") != "False":
                    variant.filter.add(value["soft_filter_flag"])
                else:
                    hard_filter = True
        if not hard_filter:
            vcf_out.write(variant)
    vcf_out.close()


def creater_filter(yaml_file, expression_converter):
    filters = {"filters": []}
    with open(yaml_file) as file:
        filters = yaml.load(file, Loader=yaml.FullLoader)
    vcf_filters = []
    for filter, value in filters["filters"].items():
        vcf_filters.append(create_variant_filter(value['expression'], expression_converter))
    return vcf_filters


class TestUnitUtils(unittest.TestCase):
    def setUp(self):
        self.in_vcf = os.path.join(FILES, "HD832.HES45_T.ensembled.vep_annotated.vcf.gz")

    def tearDown(self):
        pass

    def _test_filters(self, test_table, variants, vcf_filters):
        for variant in variants:
            for vcf_filter in vcf_filters:
                try:
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     vcf_filter(variant))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise e

    def test_data_structur_generation(self):
        """
        function used to convert filter string into a function that can evaluate objects
        """
        def true_fun(variant): return True
        def false_fun(variant): return False

        def process_string(data):
            """
            dummy function used to parse filter strings
            """
            data = data.rstrip(' ').lstrip(' ')
            if 'true' == data:
                return true_fun
            elif 'false' == data:
                return false_fun
            else:
                raise Exception("Unhandled filter substring: {}!".format(data))

        test1 = "(true or false) and (true and true)"
        data, _ = _parse_helper(iter(test1))
        self.assertEqual(data, ([['true', _or_function, 'false'], _and_function, ['true', _and_function, 'true']]))

        data = _convert_string(data, process_string)
        self.assertEqual(data, [[true_fun, _or_function, false_fun], _and_function, [true_fun, _and_function, true_fun]])

        variant_filter = create_variant_filter(test1, process_string)
        self.assertEqual(variant_filter(""), True)

        test2 = "((true and false) and true)"
        data, _ = _parse_helper(iter(test2))
        self.assertEqual(data, ([[['true', _and_function, 'false'], _and_function, 'true']]))

        data = _convert_string(data, process_string)
        self.assertEqual(data, [[true_fun, _and_function, false_fun], _and_function, true_fun])

        variant_filter = create_variant_filter(test2, process_string)
        self.assertEqual(variant_filter(""), False)

    def test_create_convert_expression(self):
        variants = VariantFile(self.in_vcf)
        annotation_extractor = {}
        for record in variants.header.records:
            if record.type == "INFO":
                if record['ID'] == "CSQ":
                    vep_fields = {v: c for c, v in enumerate(record['Description'].split("Format: ")[1].split("|"))}
                    annotation_extractor["VEP"] = utils.get_annotation_data_vep(vep_fields)
        annotation_extractor['FORMAT'] = utils.get_annotation_data_format(1)
        annotation_extractor['INFO'] = utils.get_annotation_data_info
        expression_converter = create_convert_expression_function(annotation_extractor)

        test_table = {
                        "chr1:934486-934487": True,  # SAMD11
                        "chr1:935221-935222": True,  # SAMD11
                        "chr1:935338-935339": True,  # SAMD11
                        "chr1:2460943-2460947": False,  # PLCH2
                        "chr1:2460960-2460961": False,  # PLCH2
                        "chr1:2461206-2461207": False  # PLCH2
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_expression_unittest_1.yaml"),
                                          expression_converter))
        test_table = {
                        "chr1:934486-934487": False,  # SAMD11
                        "chr1:935221-935222": False,  # SAMD11
                        "chr1:935338-935339": False,  # SAMD11
                        "chr1:2460943-2460947": False,  # PLCH2 -
                        "chr1:2460960-2460961": True,  # PLCH2 T
                        "chr1:2461206-2461207": False  # PLCH2 A
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_expression_unittest_2.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": False,  # SAMD11
                        "chr1:935221-935222": False,  # SAMD11
                        "chr1:935338-935339": False,  # SAMD11
                        "chr1:2460943-2460947": False,  # PLCH2 -
                        "chr1:2460960-2460961": True,  # PLCH2 T
                        "chr1:2461206-2461207": True  # PLCH2 A
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_expression_unittest_3.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": True,  # 1108,595
                        "chr1:935221-935222": True,  # 936,910
                        "chr1:935338-935339": False,  # 1301,127
                        "chr1:2460943-2460947": False,  # 278,9
                        "chr1:2460960-2460961": False,  # 314,5
                        "chr1:2461206-2461207": False  # 657,59
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_format_expression_unittest_1.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": False,  # SAMD11 1108,595
                        "chr1:935221-935222": False,  # SAMD11 936,910
                        "chr1:935338-935339": False,  # SAMD11 1301,127
                        "chr1:2460943-2460947": False,  # PLCH2 278,9
                        "chr1:2460960-2460961": False,  # PLCH2 314,5
                        "chr1:2461206-2461207": True  # PLCH2 657,59
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_format_and_vep_expresion_unittest_1.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": False,  # -
                        "chr1:935221-935222": False,  # -
                        "chr1:935338-935339": False,  # -
                        "chr1:2460943-2460947": True,  # XM_017002872
                        "chr1:2460960-2460961": True,  # XM_017002872
                        "chr1:2461206-2461207": True  # XM_017002872
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_existexpression_unittest_1.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": True,  # -
                        "chr1:935221-935222": True,  # -
                        "chr1:935338-935339": True,  # -
                        "chr1:2460943-2460947": False,  # XM_017002872
                        "chr1:2460960-2460961": False,  # XM_017002872
                        "chr1:2461206-2461207": False  # XM_017002872
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_existexpression_unittest_2.yaml"),
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": False,  # -
                        "chr1:935221-935222": False,  # -
                        "chr1:935338-935339": False,  # -
                        "chr1:2460943-2460947": False,  # XM_017002872
                        "chr1:2460960-2460961": False,  # XM_017002872 mutect2
                        "chr1:2461206-2461207": True  # XM_017002872
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_existexpression_unittest_3.yaml"),  # noqa
                                          expression_converter))

        test_table = {
                        "chr1:934486-934487": False,  # -
                        "chr1:935221-935222": False,  # -
                        "chr1:935338-935339": True,  # COSV52662066&COSV52670856&COSV52707054&COSV53164203
                        "chr1:2460943-2460947": False,  # -
                        "chr1:2460960-2460961": False,  # -
                        "chr1:2461206-2461207": False  # -
                      }

        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_vep_existexpression_unittest_4.yaml"),  # noqa
                                          expression_converter))

    def test_soft_and_hard_filtering(self):
        tempdir = tempfile.mkdtemp()
        vcf = os.path.join(tempdir, "test.vcf")

        # Filter using sample regex
        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("^[A-Za-z0-9-]+_[RT]{1}$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_and_vep_hard_and_soft_unittest_1.yaml"))
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SAMD11,AD50",  # SAMD11 1108,595 0.34
                            "chr1:935221-935222": "SAMD11",  # SAMD11 936,910 0.487
                            "chr1:935338-935339": "SAMD11",  # SAMD11 1301,127 0.084
                            "chr1:2460943-2460947": "AD50",  # PLCH2 278,9 0.007
                            "chr1:2460960-2460961": "AD50",  # PLCH2 314,5 0.0156
                            "chr1:2461206-2461207": "PASS"  # PLCH2 657,59 0.076
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise e
            self.assertEqual(counter, 6)

        # Filter using sample function
        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("VAL-02_T",
                            self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_and_vep_hard_and_soft_unittest_1.yaml"),
                            )
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SAMD11,AD50",  # SAMD11 1108,595 0.34
                            "chr1:935221-935222": "SAMD11",  # SAMD11 936,910 0.487
                            "chr1:935338-935339": "SAMD11",  # SAMD11 1301,127 0.084
                            "chr1:2460943-2460947": "AD50",  # PLCH2 278,9 0.007
                            "chr1:2460960-2460961": "AD50",  # PLCH2 314,5 0.0156
                            "chr1:2461206-2461207": "PASS"  # PLCH2 657,59 0.076
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise e
            self.assertEqual(counter, 6)

        # Filter on normal sample column info
        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("^[A-Za-z0-9-]+_[RN]{1}$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_and_vep_hard_and_soft_unittest_1.yaml"))
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SAMD11",  # SAMD11 1108,595 0.34
                            "chr1:935221-935222": "SAMD11",  # SAMD11 936,910 0.487
                            "chr1:935338-935339": "SAMD11",  # SAMD11 1301,127 0.084
                            "chr1:2460943-2460947": "AD50",  # PLCH2 278,9 0.007
                            "chr1:2460960-2460961": "AD50",  # PLCH2 314,5 0.0156
                            "chr1:2461206-2461207": "PASS"  # PLCH2 657,59 0.076
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise e
            self.assertEqual(counter, 6)

        # Fail to find matchin sample
        with open(vcf, 'w', encoding="ascii") as out_vcf:
            self.assertRaises(Exception, filter_variants, "^[A-Za-z0-9-]+_[W]{1}$", self.in_vcf, out_vcf,
                              os.path.join(FILES, "config_filter_format_and_vep_hard_and_soft_unittest_1.yaml"))

        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("^[A-Za-z0-9-]+_[RN]{1}$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_and_vep_hard_and_soft_unittest_2.yaml"))
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SAMD11",  # SAMD11 1108,595
                            "chr1:935221-935222": "SAMD11",  # SAMD11 936,910
                            "chr1:935338-935339": "SAMD11",  # SAMD11 1301,127
                            "chr1:2461206-2461207": "PASS"  # PLCH2 657,59
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise
            self.assertEqual(counter, 4)

    def test_handle_missing_data(self):
        tempdir = tempfile.mkdtemp()
        vcf = os.path.join(tempdir, "test.vcf")
        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("^([A-Za-z0-9-]+_[RN]{1})$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_missing_value_unittest_1.yaml"))
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SB_mutect2",
                            "chr1:935221-935222": "SB_mutect2",
                            "chr1:935338-935339": "SB_mutect2",
                            "chr1:2460943-2460947": "SB_mutect2",
                            "chr1:2460960-2460961": "SB_mutect2",
                            "chr1:2461206-2461207": "PASS"
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise e
            self.assertEqual(counter, 6)

        with open(vcf, 'w', encoding="ascii") as out_vcf:
            filter_variants("^[A-Za-z0-9-]+_[T]{1}$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_missing_value_unittest_2.yaml"))
        with VariantFile(vcf) as variants:
            test_table = {
                            "chr1:934486-934487": "SB_mutect2",
                            "chr1:935221-935222": "SB_mutect2",
                            "chr1:935338-935339": "SB_mutect2",
                            "chr1:2460943-2460947": "PASS",
                            "chr1:2460960-2460961": "PASS",
                            "chr1:2461206-2461207": "PASS"
                          }
            counter = 0
            for variant in variants:
                try:
                    counter += 1
                    self.assertEqual(test_table["{}:{}-{}".format(variant.chrom, variant.start, variant.stop)],
                                     ",".join([f for f in variant.filter]))
                except AssertionError as e:
                    print("Failed validation gene: " + str(variant))
                    raise
            self.assertEqual(counter, 6)

        with self.assertRaises(ValueError):
            filter_variants("^[A-Za-z0-9-]+_[RN]{1}$", self.in_vcf, out_vcf,
                            os.path.join(FILES, "config_filter_format_missing_value_unittest_3.yaml"))

    def test_qual_filter(self):
        test_table = {
                "chr1:934486-934487": False,  # .
                "chr1:935221-935222": False,  # .
                "chr1:935338-935339": False,  # .
                "chr1:2460943-2460947": False,  # 110
                "chr1:2460960-2460961": True,  # 61
                "chr1:2461206-2461207": False  # .
                }
        annotation_extractor = {}
        annotation_extractor["QUAL"] = lambda variant: None if variant.qual == '.' else variant.qual
        expression_converter = create_convert_expression_function(annotation_extractor)
        self._test_filters(test_table,
                           VariantFile(self.in_vcf),
                           creater_filter(os.path.join(FILES, "config_filter_qual_expression.yaml"),
                                          expression_converter))


class TestSharedHelpers(unittest.TestCase):
    def test_select_sample_index(self):
        self.assertEqual(select_sample_index(["VAL-02_T", "VAL-01_N"], "^[A-Za-z0-9-]+_[T]{1}$"), 0)
        self.assertEqual(select_sample_index(["VAL-02_T", "VAL-01_N"], "_N$"), 1)
        self.assertEqual(select_sample_index(["only"], "nomatch"), 0)
        self.assertEqual(select_sample_index(["only"], None), 0)
        self.assertRaises(Exception, select_sample_index, ["a_T", "b_T"], "_T$")
        self.assertRaises(Exception, select_sample_index, ["a_T", "b_N"], "_R$")

    def test_create_filter_from_vcf(self):
        in_vcf = os.path.join(FILES, "HD832.HES45_T.ensembled.vep_annotated.vcf.gz")
        variants = VariantFile(in_vcf)
        vcf_filter = create_filter_from_vcf(variants, "VEP:SYMBOL = SAMD11", sample_name_regex="_T$")
        self.assertEqual([vcf_filter(v) for v in variants], [True, True, True, False, False, False])
