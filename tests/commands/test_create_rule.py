import os
import shutil
import subprocess
import sys
import tempfile
import unittest

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
        self.assertIn('\n    script:\n        "../scripts/stats_json.py"\n', smk)
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
