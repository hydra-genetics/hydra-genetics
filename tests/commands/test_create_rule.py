import os
import shutil
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
