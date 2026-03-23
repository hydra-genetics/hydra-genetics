# coding: utf-8

import unittest
from unittest.mock import MagicMock

from snakemake.settings.types import DeploymentMethod

from hydra_genetics.utils.software_versions import get_container_prefix, get_image_path, use_container


def _make_workflow(apptainer_prefix=None, deployment_method=None):
    """Helper to build a mock snakemake workflow with snakemake 9 deployment_settings."""
    workflow = MagicMock()
    workflow.deployment_settings.apptainer_prefix = apptainer_prefix
    workflow.deployment_settings.deployment_method = deployment_method if deployment_method is not None else set()
    return workflow


class TestGetContainerPrefix(unittest.TestCase):
    def test_returns_default_when_prefix_is_none(self):
        workflow = _make_workflow(apptainer_prefix=None)
        self.assertEqual(get_container_prefix(workflow), ".snakemake/singularity")

    def test_returns_configured_prefix(self):
        workflow = _make_workflow(apptainer_prefix="/custom/apptainer/cache")
        self.assertEqual(get_container_prefix(workflow), "/custom/apptainer/cache")


class TestUseContainer(unittest.TestCase):
    def test_returns_true_when_apptainer_in_deployment_method(self):
        workflow = _make_workflow(deployment_method={DeploymentMethod.APPTAINER})
        self.assertTrue(use_container(workflow))

    def test_returns_false_when_apptainer_not_in_deployment_method(self):
        workflow = _make_workflow(deployment_method=set())
        self.assertFalse(use_container(workflow))

    def test_returns_false_when_deployment_method_is_empty(self):
        workflow = _make_workflow(deployment_method=set())
        self.assertFalse(use_container(workflow))


class TestGetImagePath(unittest.TestCase):
    def test_local_file_returned_unchanged(self):
        path = "/data/images/mycontainer.sif"
        self.assertEqual(get_image_path(path, "/prefix"), path)

    def test_docker_url_returns_md5_simg_path(self):
        container = "docker://hydragenetics/bcbio-vc:0.2.6"
        prefix = ".snakemake/singularity"
        result = get_image_path(container, prefix)
        self.assertTrue(result.startswith(prefix + "/"))
        self.assertTrue(result.endswith(".simg"))

    def test_same_docker_url_produces_same_path(self):
        container = "docker://hydragenetics/bcbio-vc:0.2.6"
        prefix = ".snakemake/singularity"
        self.assertEqual(get_image_path(container, prefix), get_image_path(container, prefix))

    def test_different_docker_urls_produce_different_paths(self):
        prefix = ".snakemake/singularity"
        path1 = get_image_path("docker://hydragenetics/image1:1.0", prefix)
        path2 = get_image_path("docker://hydragenetics/image2:1.0", prefix)
        self.assertNotEqual(path1, path2)
