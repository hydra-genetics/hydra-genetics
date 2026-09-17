# coding: utf-8

import unittest

from snakemake.exceptions import WorkflowError

from hydra_genetics.utils.config import config_accessor, get_config_value


class TestConfigUtils(unittest.TestCase):
    def setUp(self):
        self.config = {
            "reference": {
                "fasta": "reference/ref.fasta",
                "skip_contigs": ["chrM"],
                "blank": "",
                "whitespace": "   ",
            },
            "purecn": {
                "interval_padding": 100,
                "enabled": True,
            },
            "deeptrio_call_variants": {
                "model": {"child": "child.ckpt", "parent": "parent.ckpt"},
            },
            "empty_section": {},
            "not_a_section": "scalar",
        }

    def tearDown(self):
        pass

    # --- required entries -------------------------------------------------

    def test_returns_configured_value(self):
        self.assertEqual(get_config_value(self.config, "reference", "fasta"), "reference/ref.fasta")

    def test_walks_nested_dicts(self):
        self.assertEqual(get_config_value(self.config, "deeptrio_call_variants", "model", "parent"), "parent.ckpt")

    def test_missing_section_names_the_entry(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "absent", "fasta")
        self.assertIn("missing config entry 'absent'", str(ctx.exception))

    def test_missing_key_names_the_full_path(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "reference", "absent")
        self.assertIn("missing config entry 'reference:absent'", str(ctx.exception))

    def test_blank_string_is_rejected(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "reference", "blank")
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_whitespace_only_string_is_rejected(self):
        with self.assertRaises(WorkflowError):
            get_config_value(self.config, "reference", "whitespace")

    def test_walking_into_a_scalar_is_reported_as_missing(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "not_a_section", "fasta")
        self.assertIn("missing config entry 'not_a_section:fasta'", str(ctx.exception))

    def test_non_string_is_returned_with_its_own_type(self):
        # the config schema declares the type; the accessor must not override it
        self.assertEqual(get_config_value(self.config, "purecn", "interval_padding"), 100)
        self.assertIsInstance(get_config_value(self.config, "purecn", "interval_padding"), int)

    def test_bool_is_returned_with_its_own_type(self):
        self.assertIs(get_config_value(self.config, "purecn", "enabled"), True)

    def test_list_is_returned_without_an_expect(self):
        self.assertEqual(get_config_value(self.config, "reference", "skip_contigs"), ["chrM"])

    # --- optional entries -------------------------------------------------

    def test_default_returned_when_section_missing(self):
        self.assertEqual(get_config_value(self.config, "absent", "fasta", default=[]), [])

    def test_default_returned_when_key_missing(self):
        self.assertEqual(get_config_value(self.config, "reference", "absent", default=[]), [])

    def test_default_returned_when_value_blank(self):
        self.assertEqual(get_config_value(self.config, "reference", "blank", default=[]), [])

    def test_configured_value_wins_over_default(self):
        self.assertEqual(get_config_value(self.config, "reference", "fasta", default=[]), "reference/ref.fasta")

    def test_none_is_a_usable_default(self):
        # None must be distinguishable from "no default given"
        self.assertIsNone(get_config_value(self.config, "absent", "key", default=None))

    def test_empty_string_is_a_usable_default(self):
        self.assertEqual(get_config_value(self.config, "absent", "key", default=""), "")

    # --- expect ------------------------------------------------------------

    def test_expect_list_accepts_a_list(self):
        self.assertEqual(get_config_value(self.config, "reference", "skip_contigs", expect=list), ["chrM"])

    def test_expect_list_rejects_a_string(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "reference", "fasta", expect=list)
        self.assertIn("must be of type list", str(ctx.exception))

    def test_expect_dict_accepts_a_dict(self):
        self.assertEqual(
            get_config_value(self.config, "deeptrio_call_variants", "model", expect=dict),
            {"child": "child.ckpt", "parent": "parent.ckpt"},
        )

    def test_expect_none_skips_the_type_check(self):
        self.assertEqual(get_config_value(self.config, "reference", "skip_contigs", expect=None), ["chrM"])

    def test_expect_raises_even_when_a_default_is_given(self):
        # a configured value of the wrong type is a config error, not an absent entry
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "reference", "fasta", expect=list, default=[])
        self.assertIn("must be of type list", str(ctx.exception))

    def test_expect_is_skipped_for_an_absent_entry_with_a_default(self):
        self.assertEqual(get_config_value(self.config, "reference", "absent", expect=list, default=[]), [])

    def test_expect_str_still_rejects_a_number(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "purecn", "interval_padding", expect=str)
        self.assertIn("must be of type str", str(ctx.exception))

    def test_expect_int_rejects_a_bool(self):
        # bool is a subclass of int, but a YAML true is not a number
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "purecn", "enabled", expect=int)
        self.assertIn("must be of type int", str(ctx.exception))

    def test_expect_int_accepts_an_int(self):
        self.assertEqual(get_config_value(self.config, "purecn", "interval_padding", expect=int), 100)

    # --- module tag --------------------------------------------------------

    def test_module_tag_prefixes_missing_entry(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "absent", module="alignment")
        self.assertTrue(str(ctx.exception).startswith("alignment: "))

    def test_module_tag_prefixes_blank_value(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "reference", "blank", module="qc")
        self.assertTrue(str(ctx.exception).startswith("qc: "))

    def test_without_module_tag_there_is_no_prefix(self):
        with self.assertRaises(WorkflowError) as ctx:
            get_config_value(self.config, "absent")
        self.assertTrue(str(ctx.exception).startswith("missing config entry"))

    # --- config_accessor ---------------------------------------------------

    def test_accessor_binds_config_and_tag(self):
        get_value = config_accessor(self.config, module="snv_indels")
        self.assertEqual(get_value("reference", "fasta"), "reference/ref.fasta")
        with self.assertRaises(WorkflowError) as ctx:
            get_value("absent", "key")
        self.assertTrue(str(ctx.exception).startswith("snv_indels: "))

    def test_accessor_forwards_default(self):
        get_value = config_accessor(self.config, module="cnv_sv")
        self.assertEqual(get_value("absent", "key", default=[]), [])

    def test_accessor_forwards_expect(self):
        get_value = config_accessor(self.config, module="cnv_sv")
        self.assertEqual(get_value("reference", "skip_contigs", expect=list), ["chrM"])

    def test_accessors_are_independent(self):
        other = {"reference": {"fasta": "other.fasta"}}
        a = config_accessor(self.config, module="a")
        b = config_accessor(other, module="b")
        self.assertEqual(a("reference", "fasta"), "reference/ref.fasta")
        self.assertEqual(b("reference", "fasta"), "other.fasta")

    def test_accessor_without_module_still_works(self):
        get_value = config_accessor(self.config)
        self.assertEqual(get_value("reference", "fasta"), "reference/ref.fasta")
        with self.assertRaises(WorkflowError) as ctx:
            get_value("absent")
        self.assertTrue(str(ctx.exception).startswith("missing config entry"))


if __name__ == "__main__":
    unittest.main()
