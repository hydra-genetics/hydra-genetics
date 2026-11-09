import hashlib
import os
import shutil
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import git
import yaml

from hydra_genetics.utils import software_versions

# output of "singularity inspect" for an image built from a docker image with software labels
INSPECT_OUTPUT = b"""maintainer: hydra-genetics
org.label-schema.build-date: Monday_1_January_2024
org.label-schema.usage.singularity.deffile.from: hydragenetics/common:1.0.1
license: GPL3
samtools: 1.9
picard: 2.20.1
version: 1.0.1
"""

INSPECT_OUTPUT_NO_LABELS = b"""maintainer: hydra-genetics
org.label-schema.usage.singularity.deffile.from: hydragenetics/common:1.0.1
"""


def inspect(output):
    return patch.object(software_versions.subprocess, "check_output", return_value=output)


class TempDirTestCase(unittest.TestCase):
    """Runs every test inside a fresh temporary working directory"""

    def setUp(self):
        self.cwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tempdir)


class TestContainerNameVersionString(unittest.TestCase):
    def test_docker_image_with_tag(self):
        name = software_versions._create_container_name_version_string("docker://hydragenetics/bcbio-vc:0.2.6")
        self.assertEqual(name, "bcbio-vc_0.2.6")

    def test_docker_image_without_tag(self):
        name = software_versions._create_container_name_version_string("docker://hydragenetics/common")
        self.assertEqual(name, "common_NoVersion")

    def test_sif_file_with_version(self):
        name = software_versions._create_container_name_version_string("/images/hydragenetics__common_1.0.1.sif")
        self.assertEqual(name, "common_1.0.1")

    def test_sif_file_without_version(self):
        name = software_versions._create_container_name_version_string("/images/common.sif")
        self.assertEqual(name, "common_NoVersion")

    def test_unparsable_image_raises(self):
        for image in ["/images/!.sif", "common"]:
            with self.subTest(image=image), self.assertRaises(Exception):
                software_versions._create_container_name_version_string(image)


class TestGetImagePath(unittest.TestCase):
    def test_local_file_is_returned_unchanged(self):
        self.assertEqual(software_versions.get_image_path("/images/common.sif", "/cache"), "/images/common.sif")

    def test_remote_image_is_snakemake_cache_path(self):
        container = "docker://hydragenetics/common:1.0.1"
        expected = os.path.join("/cache", hashlib.md5(container.encode()).hexdigest() + ".simg")
        self.assertEqual(software_versions.get_image_path(container, "/cache"), expected)


class TestWorkflowSettings(unittest.TestCase):
    # snakemake < 8 workflow objects, SimpleNamespace since hasattr() is always True on a Mock
    def test_container_prefix_from_workflow(self):
        workflow = SimpleNamespace(use_singularity=True, singularity_prefix="/cache")
        self.assertEqual(software_versions.get_container_prefix(workflow), "/cache")

    def test_container_prefix_default(self):
        workflow = SimpleNamespace(use_singularity=True)
        self.assertEqual(software_versions.get_container_prefix(workflow), ".snakemake/singularity")

    def test_container_prefix_unknown_workflow(self):
        self.assertIsNone(software_versions.get_container_prefix(SimpleNamespace()))

    def test_use_container(self):
        self.assertTrue(software_versions.use_container(SimpleNamespace(use_singularity=True)))
        self.assertFalse(software_versions.use_container(SimpleNamespace()))


class TestAddVersionFilesToMultiqc(unittest.TestCase):
    def test_files_are_added_to_every_report(self):
        config = {"multiqc": {"reports": {"DNA": {"qc_files": ["a.txt"]}, "RNA": {"qc_files": []}}}}
        software_versions.add_version_files_to_multiqc(config, ["v1.yaml", "v2.yaml"])
        self.assertEqual(config["multiqc"]["reports"]["DNA"]["qc_files"], ["a.txt", "v1.yaml", "v2.yaml"])
        self.assertEqual(config["multiqc"]["reports"]["RNA"]["qc_files"], ["v1.yaml", "v2.yaml"])

    def test_missing_multiqc_config_warns(self):
        config = {"samtools": {}}
        with self.assertLogs(software_versions.__name__, level="WARNING"):
            software_versions.add_version_files_to_multiqc(config, ["v1.yaml"])
        self.assertEqual(config, {"samtools": {}})


class TestSingularityInspect(unittest.TestCase):
    def test_software_versions_from_labels(self):
        with inspect(INSPECT_OUTPUT) as check_output:
            versions = software_versions.get_software_version_from_labels("/images/common.sif")
        check_output.assert_called_once_with(["singularity", "inspect", "/images/common.sif"])
        self.assertEqual(versions, [("samtools", "1.9"), ("picard", "2.20.1"), ("version", "1.0.1")])

    def test_deffile(self):
        with inspect(INSPECT_OUTPUT):
            self.assertEqual(software_versions.get_deffile("/images/common.sif"), "hydragenetics/common:1.0.1")

    def test_deffile_missing(self):
        with inspect(b"samtools: 1.9\n"):
            self.assertIsNone(software_versions.get_deffile("/images/common.sif"))


class TestAddSoftwareVersionToConfig(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.workflow = SimpleNamespace(use_singularity=True, singularity_prefix=self.tempdir)
        self.image = os.path.join(self.tempdir, "hydragenetics__common_1.0.1.sif")
        open(self.image, "w").close()

    def test_versions_are_added_from_labels(self):
        config = {"default_container": self.image, "samtools": {"container": self.image}}
        with inspect(INSPECT_OUTPUT):
            config, versions = software_versions.add_software_version_to_config(config, self.workflow)
        expected = {"samtools": "1.9", "picard": "2.20.1"}  # the image's own "version" label is dropped
        self.assertEqual(config["default_container_software_versions"], expected)
        self.assertEqual(config["samtools"]["software_versions"], expected)
        self.assertEqual(versions, {"common_1.0.1": expected})

    def test_missing_image_raises(self):
        config = {"samtools": {"container": "/images/missing.sif"}}
        with self.assertRaises(Exception):
            software_versions.add_software_version_to_config(config, self.workflow)

    def test_missing_image_warns_when_allowed(self):
        config = {"samtools": {"container": "/images/missing.sif"}}
        with self.assertLogs(software_versions.__name__, level="WARNING"):
            config, versions = software_versions.add_software_version_to_config(config, self.workflow, False)
        self.assertNotIn("software_versions", config["samtools"])
        self.assertEqual(versions, {})

    def test_image_without_labels_raises(self):
        config = {"samtools": {"container": self.image}}
        with inspect(INSPECT_OUTPUT_NO_LABELS), self.assertRaises(Exception):
            software_versions.add_software_version_to_config(config, self.workflow)

    def test_image_without_labels_falls_back_to_image_name(self):
        config = {"samtools": {"container": self.image}}
        with inspect(INSPECT_OUTPUT_NO_LABELS), self.assertLogs(software_versions.__name__, level="WARNING"):
            config, versions = software_versions.add_software_version_to_config(config, self.workflow, False)
        expected = {"common": "1.0.1", "NOTE": "version extract from image name and not labels"}
        self.assertEqual(config["samtools"]["software_versions"], expected)
        self.assertEqual(versions, {"common_1.0.1": expected})


class TestSoftwareVersionFiles(TempDirTestCase):
    def test_touch_creates_and_updates_file(self):
        software_versions._touch("file.txt")
        self.assertTrue(os.path.isfile("file.txt"))
        os.utime("file.txt", (0, 0))
        software_versions._touch("file.txt")
        self.assertGreater(os.path.getmtime("file.txt"), time.time() - 60)

    def test_export_writes_versions(self):
        versions = {"common_1.0.1": {"samtools": "1.9", "picard": "2.20.1"}}
        output = software_versions.export_software_version_as_file(versions, date_string="20240101")
        self.assertEqual(output, os.path.join("versions/software_20240101", "softwares_mqc_versions.yaml"))
        with open(output) as fh:
            self.assertEqual(yaml.safe_load(fh), versions)

    def test_export_writes_note_only_as_comment(self):
        note = "version extract from image name and not labels"
        versions = {"common_1.0.1": {"common": "1.0.1", "NOTE": note}}
        output = software_versions.export_software_version_as_file(versions, date_string="20240101")
        with open(output) as fh:
            content = fh.read()
        self.assertEqual(yaml.safe_load(content), {"common_1.0.1": {"common": "1.0.1"}})
        self.assertIn(f"# {note}", content)

    def test_export_writes_each_note_on_its_own_line(self):
        versions = {"common_1.0.1": {"common": "1.0.1", "NOTE": "first"}, "bwa_0.7": {"bwa": "0.7", "NOTE": "second"}}
        output = software_versions.export_software_version_as_file(versions, date_string="20240101")
        with open(output) as fh:
            comments = [line.rstrip("\n") for line in fh if line.startswith("#")]
        self.assertEqual(comments, ["# first", "# second"])

    def test_touch_and_export_use_the_same_file(self):
        # the touched file is passed to multiqc before the dag is built, export must later write to the same path
        for directory in ["versions/software", "versions", ""]:
            with self.subTest(directory=directory):
                kwargs = {"directory": directory, "file_name": "softwares_mqc_versions.yaml", "date_string": "20240101"}
                touched = software_versions.touch_software_version_file({}, **kwargs)
                exported = software_versions.export_software_version_as_file({"common_1.0.1": {}}, **kwargs)
                self.assertEqual(touched, exported)
                self.assertTrue(os.path.isfile(touched))

    def test_touch_warns_on_name_multiqc_ignores(self):
        with self.assertLogs(software_versions.__name__, level="WARNING"):
            software_versions.touch_software_version_file({}, file_name="versions.yaml", date_string="20240101")


class TestPipelineVersionFiles(TempDirTestCase):
    def test_touch_and_export_use_the_same_files(self):
        pipeline_versions = {"pipeline": {"version": "v1.2.3", "commit_id": "abc"}}
        touched = software_versions.touch_pipeline_version_file_name(pipeline_versions, date_string="20240101")
        exported = software_versions.export_pipeline_version_as_file(pipeline_versions, date_string="20240101")
        self.assertEqual(touched, [os.path.join("versions/software_20240101", "pipeline__v1.2.3_mqc_versions.yaml")])
        self.assertEqual(exported, touched)
        with open(exported[0]) as fh:
            self.assertEqual(yaml.safe_load(fh), {"pipeline": "v1.2.3"})


class TestPipelineVersion(TempDirTestCase):
    def test_plain_directory_version(self):
        # a pipeline that is not a git repo
        workflow = Mock(basedir=self.tempdir)
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": None, "commit_id": None}})

    def test_git_directory_version(self):
        # create a mock repo with an empty README
        repo = git.Repo.init(self.tempdir, initial_branch="develop")
        repo_file = os.path.join(self.tempdir, "README.md")
        open(repo_file, "wb").close()
        repo.index.add([repo_file])
        commit = repo.index.commit("initial commit")

        workflow = Mock(basedir=self.tempdir)

        # no tag, so version will be the branch name
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": "develop", "commit_id": commit.hexsha}})

        # create a tag
        repo.create_tag("v1.2.3")
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": "v1.2.3", "commit_id": commit.hexsha}})

        # the snakemake basedir is the workflow folder inside the repo
        os.makedirs(os.path.join(self.tempdir, "workflow"))
        workflow = Mock(basedir=os.path.join(self.tempdir, "workflow"))
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": "v1.2.3", "commit_id": commit.hexsha}})
