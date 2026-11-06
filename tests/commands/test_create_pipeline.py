import os
import re
import shutil
import tempfile
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
