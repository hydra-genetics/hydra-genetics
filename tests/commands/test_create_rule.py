import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from click.testing import CliRunner

from hydra_genetics.__main__ import cli
from hydra_genetics.commands.create import PipelineCreate, RuleCreate


class TestCreateRule(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.module_dir = os.path.join(self.tempdir, "testmod")
        PipelineCreate("testmod", "description", "author", "email", no_git=True, outdir=self.module_dir).init_pipeline()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def create_rule(self, command, tool=None, **kwargs):
        RuleCreate(command, "testmod", "author", "email", tool=tool, outdir=self.tempdir, **kwargs).init_rule()

    def path(self, *parts):
        return os.path.join(self.module_dir, *parts)

    def read(self, *parts):
        with open(self.path(*parts)) as fh:
            return fh.read()

    def test_tool_rule_is_named_tool_command(self):
        self.create_rule("sort", tool="samtools")
        smk = self.read("workflow", "rules", "samtools.smk")
        self.assertIn("rule samtools_sort:", smk)
        self.assertIn("wrapper:", smk)
        self.assertFalse(os.path.exists(self.path("workflow", "scripts", "sort.py")))

    def test_append_rule_whose_name_is_a_substring_of_existing_rule(self):
        self.create_rule("sort_index", tool="samtools")
        self.create_rule("sort", tool="samtools")
        smk = self.read("workflow", "rules", "samtools.smk")
        self.assertIn("rule samtools_sort_index:", smk)
        self.assertIn("rule samtools_sort:", smk)

    def test_append_duplicate_rule_is_rejected(self):
        self.create_rule("sort", tool="samtools")
        with self.assertRaises(SystemExit) as cm:
            self.create_rule("sort", tool="samtools")
        self.assertEqual(cm.exception.code, 6)
        self.assertEqual(self.read("workflow", "rules", "samtools.smk").count("rule samtools_sort:"), 1)

    def test_rule_name_clash_in_another_file_is_rejected(self):
        self.create_rule("sort", tool="samtools")
        schema_before = self.read("workflow", "schemas", "rules.schema.yaml")
        for kwargs in ({"script": True}, {}):
            with self.subTest(**kwargs):
                with self.assertRaises(SystemExit) as cm:
                    self.create_rule("samtools_sort", **kwargs)
                self.assertEqual(cm.exception.code, 6)
                self.assertFalse(os.path.exists(self.path("workflow", "rules", "samtools_sort.smk")))
                self.assertFalse(os.path.exists(self.path("workflow", "scripts", "samtools_sort.py")))
                self.assertEqual(self.read("workflow", "schemas", "rules.schema.yaml"), schema_before)

    def test_rule_name_clash_with_snakefile_rule_is_rejected(self):
        with self.assertRaises(SystemExit) as cm:
            self.create_rule("all", script=True)
        self.assertEqual(cm.exception.code, 6)
        self.assertFalse(os.path.exists(self.path("workflow", "rules", "all.smk")))

    def test_checkpoint_and_spaced_rule_definitions_count_as_duplicates(self):
        self.create_rule("index", tool="samtools")
        with open(self.path("workflow", "rules", "samtools.smk"), "a") as fh:
            fh.write('\ncheckpoint samtools_sort:\n    shell:\n        ""\n')
            fh.write('\nif True:\n\n    rule samtools_stats :\n        shell:\n            ""\n')
        for command in ("sort", "stats"):
            with self.subTest(command=command):
                with self.assertRaises(SystemExit) as cm:
                    self.create_rule(command, tool="samtools")
                self.assertEqual(cm.exception.code, 6)

    def test_wrapper_rule_layout_is_unchanged(self):
        # pins the whitespace around the script/wrapper switch in skeleton_rule.smk
        self.create_rule("sort", tool="samtools")
        self.create_rule("index", tool="samtools")
        smk = self.read("workflow", "rules", "samtools.smk")
        tail = '    message:\n        "{rule}: do stuff on {input.input1}"\n    wrapper:\n        "..."\n'
        self.assertIn(tail + "\n\nrule samtools_index:\n", smk)
        self.assertTrue(smk.endswith(tail))

    def test_script_rule_without_tool_rejects_existing_smk(self):
        self.create_rule("cnv_json")
        with self.assertRaises(SystemExit) as cm:
            self.create_rule("cnv_json", script=True)
        self.assertEqual(cm.exception.code, 4)
        self.assertFalse(os.path.exists(self.path("workflow", "scripts", "cnv_json.py")))
        self.assertFalse(os.path.exists(self.path("workflow", "scripts", "test_cnv_json.py")))

    def test_script_rules_in_tool_file(self):
        self.create_rule("cnv_report", script=True)
        self.create_rule("cnv_json", tool="cnv_report", script=True)
        self.create_rule("merge_cnv_json", tool="cnv_report", script=True)
        smk = self.read("workflow", "rules", "cnv_report.smk")
        self.assertIn("rule cnv_report:", smk)
        self.assertIn("rule cnv_json:", smk)
        self.assertIn("rule merge_cnv_json:", smk)
        self.assertNotIn("rule cnv_report_cnv_json:", smk)
        self.assertIn('"../scripts/cnv_json.py"', smk)
        self.assertNotIn("wrapper:", smk)
        self.assertEqual(self.read("workflow", "Snakefile").count('include: "rules/cnv_report.smk"'), 1)
        self.assertIn("  cnv_json:", self.read("workflow", "schemas", "rules.schema.yaml"))
        self.assertIn("#SNAKEMAKE_RULE_SOURCE__cnv_report__cnv_json#", self.read("docs", "softwares.md"))

    def test_script_and_wrapper_rules_share_a_file(self):
        self.create_rule("sort", tool="samtools")
        self.create_rule("stats_json", tool="samtools", script=True)
        smk = self.read("workflow", "rules", "samtools.smk")
        self.assertIn("rule samtools_sort:", smk)
        self.assertIn("wrapper:", smk)
        self.assertIn("rule stats_json:", smk)
        self.assertTrue(smk.endswith('"\n    script:\n        "../scripts/stats_json.py"\n'), repr(smk[-80:]))
        self.assertIn('\n    wrapper:\n        "..."\n', smk)

    def test_script_stubs_pass_pipeline_ci(self):
        self.create_rule("cnv_json", tool="cnv_report", script=True)
        scripts_dir = self.path("workflow", "scripts")
        for name in ("cnv_json.py", "test_cnv_json.py"):
            self.assertNotIn("{{", self.read("workflow", "scripts", name))
        tests = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", scripts_dir],
                               cwd=self.module_dir, capture_output=True, text=True)
        self.assertEqual(tests.returncode, 0, tests.stdout + tests.stderr)
        style = subprocess.run([sys.executable, "-m", "pycodestyle", "--max-line-length=130", scripts_dir],
                               capture_output=True, text=True)
        self.assertEqual(style.returncode, 0, style.stdout + style.stderr)

    def test_scripts_folder_is_created_when_missing(self):
        shutil.rmtree(self.path("workflow", "scripts"))
        self.create_rule("cnv_json", script=True)
        self.assertTrue(os.path.exists(self.path("workflow", "scripts", "cnv_json.py")))

    def test_existing_script_aborts_before_writing(self):
        with open(self.path("workflow", "scripts", "cnv_json.py"), "w") as fh:
            fh.write("mine")
        schema_before = self.read("workflow", "schemas", "rules.schema.yaml")
        with self.assertRaises(SystemExit) as cm:
            self.create_rule("cnv_json", tool="cnv_report", script=True)
        self.assertEqual(cm.exception.code, 7)
        self.assertEqual(self.read("workflow", "scripts", "cnv_json.py"), "mine")
        self.assertFalse(os.path.exists(self.path("workflow", "rules", "cnv_report.smk")))
        self.assertEqual(self.read("workflow", "schemas", "rules.schema.yaml"), schema_before)

    def test_invalid_python_name_aborts_in_script_mode(self):
        for name in ("1qc", "import"):
            with self.subTest(name=name):
                with self.assertRaises(SystemExit) as cm:
                    self.create_rule(name, script=True)
                self.assertEqual(cm.exception.code, 8)
                self.assertFalse(os.path.exists(self.path("workflow", "rules", f"{name}.smk")))

    def test_name_that_breaks_the_stubs_aborts_in_script_mode(self):
        # json/os/shutil/snakemake: existing modules the stub import would resolve to instead
        # test_foo: collected by pytest as a test file; input_file/output_file/tmp_path: names used inside the stubs
        for name in ("json", "os", "shutil", "snakemake", "test_foo", "input_file", "output_file", "tmp_path"):
            with self.subTest(name=name):
                with self.assertRaises(SystemExit) as cm:
                    self.create_rule(name, script=True)
                self.assertEqual(cm.exception.code, 8)
                self.assertFalse(os.path.exists(self.path("workflow", "rules", f"{name}.smk")))
                self.assertFalse(os.path.exists(self.path("workflow", "scripts", f"{name}.py")))

    def test_module_names_are_allowed_without_script(self):
        self.create_rule("json")
        self.assertIn("rule json:", self.read("workflow", "rules", "json.smk"))

    def test_cli_script_flag(self):
        result = CliRunner().invoke(cli, ["create-rule", "-c", "cnv_json", "-t", "cnv_report", "-m", "testmod",
                                          "-a", "a", "-e", "e", "-o", self.tempdir, "--script"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("rule cnv_json:", self.read("workflow", "rules", "cnv_report.smk"))
        self.assertTrue(os.path.exists(self.path("workflow", "scripts", "cnv_json.py")))
