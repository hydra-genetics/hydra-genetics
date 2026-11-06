import os
import re
import shutil
import tempfile
import unittest

import snakemake

from hydra_genetics.commands.create import DEFAULT_MIN_SNAKEMAKE_VERSION, PipelineCreate, next_major_version


def version_tuple(version):
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


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
        with open(os.path.join(outdir, "requirements.txt")) as requirements:
            for line in requirements:
                match = re.fullmatch(r"snakemake>=([\d.]+),<([\d.]+)", line.strip())
                if match:
                    return match.group(1), match.group(2)
        self.fail("No 'snakemake>=X,<Y' line in requirements.txt")

    def test_next_major_version(self):
        self.assertEqual(next_major_version("7.8.0"), "8")
        self.assertEqual(next_major_version("9.18.1"), "10")
        with self.assertRaises(ValueError):
            next_major_version("v7.8.0")

    def test_min_snakemake_version_is_applied(self):
        outdir = self.create_pipeline(min_snakemake_version="7.8.3")
        self.assertEqual(self.snakemake_requirement(outdir), ("7.8.3", "8"))
        with open(os.path.join(outdir, "workflow", "rules", "common.smk")) as common:
            self.assertIn('min_version("7.8.3")', common.read())

    def test_default_requirement_matches_installed_snakemake(self):
        # Fails when hydra-genetics moves to a new snakemake major version without
        # updating DEFAULT_MIN_SNAKEMAKE_VERSION, which would make new pipelines uninstallable.
        min_version, max_version = self.snakemake_requirement(self.create_pipeline())
        self.assertEqual(min_version, DEFAULT_MIN_SNAKEMAKE_VERSION)
        installed = version_tuple(snakemake.__version__)
        self.assertTrue(
            version_tuple(min_version) <= installed < version_tuple(max_version),
            f"Installed snakemake {snakemake.__version__} is outside the default pipeline requirement "
            f"snakemake>={min_version},<{max_version}, update DEFAULT_MIN_SNAKEMAKE_VERSION "
            f"in hydra_genetics/commands/create.py",
        )
