import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from hydra_genetics.__main__ import cli
from hydra_genetics.commands.prep_pipeline_env import create_docker_file_path
from hydra_genetics.utils.software_versions import iter_container_entries

CONFIG = {
    "default_container": "docker://hydragenetics/common:1.0.1",
    "samples": "samples.tsv",
    "fastp_pe": {"container": "docker://hydragenetics/fastp:0.20.1"},
    "module": {
        "rule": {"container": "docker://hydragenetics/bwa:0.7.17"},
        "nested": {"deeper": {"container": "docker://hydragenetics/samtools:1.9"}},
    },
    "local_rule": {"container": "/data/images/local.sif"},
    "duplicate": {"container": "docker://hydragenetics/fastp:0.20.1"},
    "empty": {"container": None},
    "my_container_settings": "not an image",
}

REMOTE_IMAGES = [
    "docker://hydragenetics/bwa:0.7.17",
    "docker://hydragenetics/common:1.0.1",
    "docker://hydragenetics/fastp:0.20.1",
    "docker://hydragenetics/samtools:1.9",
]


class TestIterContainerEntries(unittest.TestCase):
    def test_finds_containers_at_any_depth(self):
        values = sorted({value for _, _, value in iter_container_entries(CONFIG)})
        self.assertEqual(values, sorted(REMOTE_IMAGES + ["/data/images/local.sif"]))

    def test_parent_allows_in_place_update(self):
        config = {"a": {"b": {"container": "docker://x/y:1"}}}
        for parent, key, _ in iter_container_entries(config):
            parent[key] = "updated"
        self.assertEqual(config["a"]["b"]["container"], "updated")


class TestPrepareEnvironment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.configfile = os.path.join(self.tmp, "config.yaml")
        with open(self.configfile, "w") as f:
            yaml.dump(CONFIG, f)
        self.output = os.path.join(self.tmp, "images")
        self.runner = CliRunner()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _build(self, *extra, returncodes=None):
        returncodes = returncodes or {}

        def fake_run(command):
            # singularity writes the image (possibly partial) to the output path,
            # also when the build fails
            open(command[-2], "w").close()
            return SimpleNamespace(returncode=returncodes.get(command[-1], 0))

        with patch("hydra_genetics.commands.prep_pipeline_env.shutil.which", return_value="/usr/bin/singularity"), \
                patch("hydra_genetics.commands.prep_pipeline_env.subprocess.run", side_effect=fake_run) as run:
            result = self.runner.invoke(
                cli, ["prepare-environment", "create-singularity-files", "-c", self.configfile, "-o", self.output, *extra]
            )
        return result, run

    def test_builds_every_remote_container_once(self):
        result, run = self._build()
        self.assertEqual(result.exit_code, 0, result.output)
        built = [call.args[0][-1] for call in run.call_args_list]
        self.assertEqual(built, REMOTE_IMAGES)
        self.assertEqual(
            run.call_args_list[0].args[0],
            ["singularity", "build", os.path.join(self.output, "hydragenetics__bwa_0.7.17.sif.tmp"), REMOTE_IMAGES[0]],
        )
        self.assertEqual(
            sorted(os.listdir(self.output)),
            sorted(os.path.basename(create_docker_file_path(self.output, image)) for image in REMOTE_IMAGES),
        )

    def test_failed_build_exits_non_zero_and_continues(self):
        result, run = self._build(returncodes={"docker://hydragenetics/bwa:0.7.17": 255})
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(run.call_count, len(REMOTE_IMAGES))

    def test_failed_build_leaves_no_image_and_is_retried(self):
        bwa = os.path.join(self.output, "hydragenetics__bwa_0.7.17.sif")
        result, _ = self._build(returncodes={"docker://hydragenetics/bwa:0.7.17": 255})
        self.assertEqual(result.exit_code, 1)
        self.assertFalse(os.path.exists(bwa))
        self.assertFalse(os.path.exists(bwa + ".tmp"))

        result, run = self._build()
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual([c.args[0][-1] for c in run.call_args_list], ["docker://hydragenetics/bwa:0.7.17"])
        self.assertTrue(os.path.exists(bwa))

    def test_stale_temp_file_is_removed_before_build(self):
        os.makedirs(self.output)
        stale = os.path.join(self.output, "hydragenetics__bwa_0.7.17.sif.tmp")
        with open(stale, "w") as f:
            f.write("partial")
        result, _ = self._build()
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(os.path.exists(stale))

    def test_existing_image_is_skipped_unless_forced(self):
        os.makedirs(self.output)
        open(os.path.join(self.output, "hydragenetics__bwa_0.7.17.sif"), "w").close()

        result, run = self._build()
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("docker://hydragenetics/bwa:0.7.17", [c.args[0][-1] for c in run.call_args_list])

        result, run = self._build("--force")
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(run.call_count, len(REMOTE_IMAGES))

    def test_missing_singularity_is_fine_when_nothing_to_build(self):
        os.makedirs(self.output)
        for image in REMOTE_IMAGES:
            open(create_docker_file_path(self.output, image), "w").close()
        with patch("hydra_genetics.commands.prep_pipeline_env.shutil.which", return_value=None), \
                patch("hydra_genetics.commands.prep_pipeline_env.subprocess.run") as run:
            result = self.runner.invoke(
                cli, ["prepare-environment", "create-singularity-files", "-c", self.configfile, "-o", self.output]
            )
        self.assertEqual(result.exit_code, 0, result.output)
        run.assert_not_called()

    def test_colliding_image_names_exit_non_zero(self):
        with open(self.configfile, "w") as f:
            yaml.dump({"a": {"container": "docker://example/tool:1_2"}, "b": {"container": "docker://example/tool_1:2"}}, f)
        result, run = self._build()
        self.assertEqual(result.exit_code, 1)
        run.assert_not_called()

        new_config = os.path.join(self.tmp, "new_config.yaml")
        result = self.runner.invoke(
            cli,
            ["prepare-environment", "container-path-update", "-c", self.configfile, "-n", new_config, "-p", "/cache"],
        )
        self.assertEqual(result.exit_code, 1)
        self.assertFalse(os.path.exists(new_config))

    def test_missing_singularity_exits_non_zero(self):
        with patch("hydra_genetics.commands.prep_pipeline_env.shutil.which", return_value=None), \
                patch("hydra_genetics.commands.prep_pipeline_env.subprocess.run") as run:
            result = self.runner.invoke(
                cli, ["prepare-environment", "create-singularity-files", "-c", self.configfile, "-o", self.output]
            )
        self.assertEqual(result.exit_code, 1)
        run.assert_not_called()

    def test_container_path_update_rewrites_nested_containers(self):
        new_config = os.path.join(self.tmp, "new_config.yaml")
        result = self.runner.invoke(
            cli,
            ["prepare-environment", "container-path-update", "-c", self.configfile, "-n", new_config, "-p", "/cache"],
        )
        self.assertEqual(result.exit_code, 0, result.output)
        with open(new_config) as f:
            updated = yaml.safe_load(f)
        self.assertEqual(updated["default_container"], "/cache/hydragenetics__common_1.0.1.sif")
        self.assertEqual(updated["module"]["nested"]["deeper"]["container"], "/cache/hydragenetics__samtools_1.9.sif")
        self.assertEqual(updated["local_rule"]["container"], "/data/images/local.sif")
        self.assertEqual(updated["my_container_settings"], "not an image")
