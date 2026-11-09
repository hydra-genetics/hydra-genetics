import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import snakemake
from click.testing import CliRunner
from packaging.specifiers import SpecifierSet

from hydra_genetics.__main__ import cli
from hydra_genetics.commands.create import DEFAULT_MIN_SNAKEMAKE_VERSION, PipelineCreate, next_major_version


def satisfies(specifier, version):
    # prereleases=True lets an installed prerelease, ex 7.9.0rc1, satisfy >=7.8.0,<8. Prereleases outside
    # the range, ex 7.8.0rc1 (before 7.8.0) or 8.0.0rc1 (excluded by <8, PEP 440), still fail.
    return SpecifierSet(specifier).contains(version, prereleases=True)


class TestCreatePipeline(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def create_pipeline(self, **kwargs):
        outdir = os.path.join(self.tempdir, "pipeline")
        PipelineCreate("test", "description", "author", "email", no_git=True, outdir=outdir, **kwargs).init_pipeline()
        return outdir

    def snakemake_requirement(self, outdir):
        """Return the version specifier of the snakemake line in requirements.txt, ex '>=7.8.0,<8'"""
        with open(os.path.join(outdir, "requirements.txt")) as requirements:
            for line in requirements:
                match = re.fullmatch(r"snakemake(>=[\d.]+,<[\d.]+)", line.strip())
                if match:
                    return match.group(1)
        self.fail("No 'snakemake>=X,<Y' line in requirements.txt")

    def test_next_major_version(self):
        self.assertEqual(next_major_version("7.8.0"), "8")
        self.assertEqual(next_major_version("9.18.1"), "10")
        self.assertEqual(next_major_version("7.8"), "8")
        self.assertEqual(next_major_version("7"), "8")

    def test_next_major_version_rejects_invalid_versions(self):
        for version in ["7.invalid", "v7.8.0", "7.", "7..0", ".7", "7.8.0.1", " 7.8.0", "7.8.0rc1", ""]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                next_major_version(version)

    def test_invalid_min_snakemake_version_fails_before_rendering(self):
        outdir = os.path.join(self.tempdir, "pipeline")
        with self.assertRaises(ValueError):
            PipelineCreate("test", "description", "author", "email", min_snakemake_version="7.invalid",
                           no_git=True, outdir=outdir)
        self.assertFalse(os.path.exists(outdir))

    def test_cli_rejects_invalid_min_snakemake_version(self):
        outdir = os.path.join(self.tempdir, "pipeline")
        result = CliRunner().invoke(cli, ["create-pipeline", "-n", "test", "-d", "d", "-a", "a", "-e", "e", "-g", "g",
                                          "--no-git", "-o", outdir, "--min-snakemake-version", "7.invalid"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Invalid version '7.invalid'", result.output)
        self.assertFalse(os.path.exists(outdir))

    def test_min_snakemake_version_is_applied(self):
        outdir = self.create_pipeline(min_snakemake_version="7.8.3")
        self.assertEqual(self.snakemake_requirement(outdir), ">=7.8.3,<8")
        with open(os.path.join(outdir, "workflow", "rules", "common.smk")) as common:
            self.assertIn('min_version("7.8.3")', common.read())

    def test_requirement_version_check(self):
        requirement = self.snakemake_requirement(self.create_pipeline(min_snakemake_version="7.8.0"))
        for version in ["7.8.0", "7.32.4", "7.9.0rc1"]:
            with self.subTest(version=version):
                self.assertTrue(satisfies(requirement, version))
        for version in ["7.7.9", "7.8.0rc1", "8.0.0rc1", "8.0.0", "9.18.1"]:
            with self.subTest(version=version):
                self.assertFalse(satisfies(requirement, version))

    def test_default_requirement_matches_installed_snakemake(self):
        # Fails when hydra-genetics moves to a new snakemake major version without
        # updating DEFAULT_MIN_SNAKEMAKE_VERSION, which would make new pipelines uninstallable.
        requirement = self.snakemake_requirement(self.create_pipeline())
        self.assertTrue(requirement.startswith(f">={DEFAULT_MIN_SNAKEMAKE_VERSION},"))
        self.assertTrue(
            satisfies(requirement, snakemake.__version__),
            f"Installed snakemake {snakemake.__version__} does not satisfy the default pipeline requirement "
            f"snakemake{requirement}, update DEFAULT_MIN_SNAKEMAKE_VERSION in hydra_genetics/commands/create.py",
        )

    def test_github_workflows_have_yaml_extension(self):
        # GitHub only runs workflow files with a .yml or .yaml extension
        workflows = os.path.join(self.create_pipeline(), ".github", "workflows")
        for name in os.listdir(workflows):
            with self.subTest(name=name):
                self.assertTrue(name.endswith((".yml", ".yaml")), f"{name} will never run on GitHub")

    def test_github_workflows_target_main_branch(self):
        # create-pipeline initialises the repository with the branches main and develop, there is no master
        workflows = os.path.join(self.create_pipeline(), ".github", "workflows")
        for name in os.listdir(workflows):
            with self.subTest(name=name):
                with open(os.path.join(workflows, name)) as fh:
                    self.assertNotIn("master", fh.read())

    def test_readme_instructions_match_generated_pipeline(self):
        with open(os.path.join(self.create_pipeline(), "README.md")) as fh:
            readme = fh.read()
        # the Snakefile lives in workflow/, relative to .tests/integration
        self.assertIn("snakemake -s ../../workflow/Snakefile", readme)
        # the module example must use the pipeline's own name and a github owner/repo
        self.assertNotIn("prealignment", readme)
        self.assertIn("module test:", readme)
        self.assertIn('"hydra-genetics/test",', readme)

    @unittest.skipIf(int(snakemake.__version__.split(".")[0]) >= 8, "pipelines are run with snakemake <8")
    def test_version_files_have_paths_independent_of_parse_time(self):
        # snakemake parses the Snakefile again for each dry run and in every cluster job, here run with "bash"
        integration = os.path.join(self.create_pipeline(), ".tests", "integration")
        hydra_genetics_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env = {**os.environ, "PYTHONPATH": hydra_genetics_root}
        command = [sys.executable, "-m", "snakemake", "-s", "../../workflow/Snakefile", "-j", "1",
                   "--configfiles", "../../config/config.yaml", "config/config.yaml"]
        subprocess.run(command + ["-n"], cwd=integration, env=env, check=True, capture_output=True)
        # with a timestamp in the path, the next parse would create a new directory
        time.sleep(1.1)
        # the job itself may fail, the template's copy rule uses GNU cp options, but the job process must have run
        subprocess.run(command + ["--cluster", "bash"], cwd=integration, env=env, capture_output=True)
        self.assertTrue(os.path.isfile(os.path.join(integration, "logs", "_copy__copy_samples_tsv_samples.tsv.log")))
        versions = os.path.join(integration, "results", "versions")
        archives = [name for name in os.listdir(versions) if name.startswith("software_")]
        # only the run, not the dry run or the cluster job, creates an archive
        self.assertEqual(len(archives), 1, os.listdir(versions))
        version_file = "test__None_mqc_versions.yaml"
        with open(os.path.join(versions, "software", version_file)) as fh:
            content = fh.read()
        # not a git repository, so the version is unknown
        self.assertEqual(content, "test: null\n")
        with open(os.path.join(versions, archives[0], version_file)) as fh:
            self.assertEqual(fh.read(), content)
