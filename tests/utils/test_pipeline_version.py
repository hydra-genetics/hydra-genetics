import os
import git
import tempfile
import unittest
from unittest.mock import Mock

from hydra_genetics.utils import software_versions


class TestPipelineVersion(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_plain_directory_version(self):
        # create a mock pipeline, in this case an empty directory
        pipeline_dir = tempfile.mkdtemp()

        # create a mock workflow
        workflow = Mock(basedir=pipeline_dir)

        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": None, "commit_id": None}})

    def test_git_directory_version(self):
        # create a mock repo with an empty README
        repo_dir = tempfile.mkdtemp()
        repo = git.Repo.init(repo_dir, initial_branch="develop")
        repo_file = os.path.join(repo_dir, "README.md")
        open(repo_file, "wb").close()
        repo.index.add([repo_file])
        commit = repo.index.commit("initial commit")

        # create a mock workflow
        workflow = Mock(basedir=repo_dir)

        # no tag, so version will be the branch name
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": "develop", "commit_id": commit.hexsha}})

        # create a tag
        repo.create_tag("v1.2.3")
        version = software_versions.get_pipeline_version(workflow, "test_pipeline")
        self.assertEqual(version, {"test_pipeline": {"version": "v1.2.3", "commit_id": commit.hexsha}})
