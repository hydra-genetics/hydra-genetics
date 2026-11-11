import hashlib
import io
import os
import shutil
import tarfile
import tempfile
import unittest
from unittest import mock
from requests import HTTPError

from hydra_genetics.utils.io import reference
from hydra_genetics.utils.io.reference import extract_tar, fetch_reference_data, fetch_url_content


class TestReference(unittest.TestCase):
    genome = b"ACGT\n"

    def setUp(self) -> None:
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.outdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.tmpdir)
        shutil.rmtree(self.outdir)

    def test_fetch_url_content_404(self):
        url = "https://github.com/Twist_Solid_pipeline_files/raw/v1.0.0/design/this-is-surely-not-a-file.txt"
        with self.assertRaises(HTTPError) as e:
            fetch_url_content(url, self.outdir, self.tmpdir)
        self.assertEqual(e.exception.status, 404)

    @mock.patch("hydra_genetics.utils.io.reference.requests.Session.get")
    def test_fetch_url_content_bot_challenge(self, mock_get):
        mock_get.return_value = mock.Mock(status_code=202, headers={"x-amzn-waf-action": "challenge"})
        target = os.path.join(self.tmpdir, "file")
        self.assertFalse(fetch_url_content("https://ndownloader.figshare.com/files/1", target, self.tmpdir))
        # Fails at once instead of retrying
        self.assertEqual(mock_get.call_count, 1)
        self.assertFalse(os.path.exists(target))

    @mock.patch("hydra_genetics.utils.io.reference.requests.Session.get", autospec=True)
    def test_fetch_url_content_default_user_agent(self, mock_get):
        response = mock.Mock(status_code=200, headers={})
        response.iter_content.return_value = [b"content"]
        user_agents = []

        def get(session, url, **kwargs):
            user_agents.append(session.headers["User-Agent"])
            return response
        mock_get.side_effect = get
        target = os.path.join(self.tmpdir, "file")
        self.assertTrue(fetch_url_content("https://example.org/file", target, self.tmpdir))
        # requests' own User-Agent, not a browser's
        self.assertTrue(user_agents[0].startswith("python-requests/"))
        with open(target, "rb") as f:
            self.assertEqual(f.read(), b"content")

    def test_fetch_reference_data_404(self):
        validation_data = {
            "not a file": {
                "path": "files/not-a-file.txt",
                "type": "file",
                "url": "https://github.com/Twist_Solid_pipeline_files/raw/v1.0.0/design/this-is-surely-not-a-file.txt",
            },
        }
        fetched, links, failed, skipped = fetch_reference_data(
            validation_data, self.outdir, fetched=[], links=[], failed=[], skipped=[])
        self.assertEqual(len(fetched), 0)
        self.assertEqual(len(failed), 1)
        self.assertEqual(len(links), 0)
        self.assertEqual(len(skipped), 0)

    def test_fetch_reference_data_local_file(self):
        content = b"local file content"
        checksum = hashlib.md5(content).hexdigest()

        # Create an actual local file to fetch via file:// URL
        local_file = os.path.join(self.tmpdir, "test-source-file.txt")
        with open(local_file, "wb") as f:
            f.write(content)

        validation_data = {
            "local file": {
                "path": "files/local-test-file.txt",
                "type": "file",
                "checksum": checksum,
                "url": f"file://{local_file}",
            },
        }

        fetched, links, failed, skipped = fetch_reference_data(
            validation_data, self.outdir, fetched=[], links=[], failed=[], skipped=[])

        self.assertEqual(len(fetched), 1)
        self.assertEqual(len(failed), 0)
        self.assertEqual(len(links), 0)
        self.assertEqual(len(skipped), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.outdir, "files/local-test-file.txt")))

    def make_archive(self, *members):
        """Write a tar.gz with ref/genome.fa plus the given extra TarInfo members, return its path"""
        archive = os.path.join(self.tmpdir, "folder.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            for name in ["ref/genome.fa"] + [member for member in members if isinstance(member, str)]:
                info = tarfile.TarInfo(name)
                info.size = len(self.genome)
                tar.addfile(info, io.BytesIO(self.genome))
            for member in members:
                if isinstance(member, tarfile.TarInfo):
                    tar.addfile(member)
        return archive

    def symlink(self, name, target):
        info = tarfile.TarInfo(name)
        info.type = tarfile.SYMTYPE
        info.linkname = target
        return info

    def fetch_folder(self, content_checksum, archive=None):
        """Fetch a local tar.gz with ref/genome.fa as a folder entry with the given content_checksum"""
        archive = archive or self.make_archive()
        with open(archive, "rb") as f:
            compressed_checksum = hashlib.md5(f.read()).hexdigest()
        validation_data = {
            "folder": {
                "path": "data",
                "type": "folder",
                "compressed_checksum": compressed_checksum,
                "content_checksum": content_checksum,
                "url": f"file://{archive}",
            },
        }
        return fetch_reference_data(validation_data, self.outdir, fetched=[], links=[], failed=[], skipped=[])

    def test_fetch_reference_data_folder(self):
        fetched, links, failed, skipped = self.fetch_folder({"ref/genome.fa": hashlib.md5(self.genome).hexdigest()})
        self.assertEqual(fetched, ["data"])
        self.assertEqual(failed, [])
        with open(os.path.join(self.outdir, "data", "ref", "genome.fa"), "rb") as f:
            self.assertEqual(f.read(), self.genome)

    def test_fetch_reference_data_folder_wrong_content_checksum(self):
        fetched, links, failed, skipped = self.fetch_folder({"ref/genome.fa": "0" * 32})
        self.assertEqual(fetched, [])
        self.assertEqual(failed, [os.path.join(self.outdir, "data")])
        # the folder is not installed
        self.assertFalse(os.path.exists(os.path.join(self.outdir, "data")))

    def test_fetch_reference_data_folder_missing_content_file(self):
        fetched, links, failed, skipped = self.fetch_folder({
            "ref/genome.fa": hashlib.md5(self.genome).hexdigest(),
            "ref/genome.fa.fai": "0" * 32,
        })
        self.assertEqual(fetched, [])
        self.assertEqual(failed, [os.path.join(self.outdir, "data")])
        self.assertFalse(os.path.exists(os.path.join(self.outdir, "data")))

    def test_fetch_reference_data_folder_missing_content_file_is_logged(self):
        with self.assertLogs(level="WARNING") as logs:
            self.fetch_folder({
                "ref/genome.fa": hashlib.md5(self.genome).hexdigest(),
                "ref/genome.fa.fai": "0" * 32,
            })
        self.assertTrue(any("ref/genome.fa.fai" in m and "not found" in m for m in logs.output), logs.output)

    def test_fetch_reference_data_folder_member_outside_is_rejected(self):
        archive = self.make_archive("../evil.txt")
        fetched, links, failed, skipped = self.fetch_folder({"ref/genome.fa": hashlib.md5(self.genome).hexdigest()}, archive)
        self.assertEqual(fetched, [])
        self.assertEqual(failed, [os.path.join(self.outdir, "data")])
        self.assertFalse(os.path.exists(os.path.join(self.outdir, "data")))

    def test_fetch_reference_data_folder_corrupt_archive_fails_entry(self):
        archive = os.path.join(self.tmpdir, "folder.tar.gz")
        with open(archive, "wb") as f:
            f.write(b"not a tar.gz")
        fetched, links, failed, skipped = self.fetch_folder({"ref/genome.fa": hashlib.md5(self.genome).hexdigest()}, archive)
        self.assertEqual(fetched, [])
        self.assertEqual(failed, [os.path.join(self.outdir, "data")])

    def assert_extract_rejected(self, member, outside):
        """extract_tar raises for the member and writes nothing at outside, with and without tarfile's data filter"""
        archive = self.make_archive(member)
        for has_data_filter in [True, False]:
            with self.subTest(has_data_filter=has_data_filter), \
                    mock.patch.object(reference, "HAS_DATA_FILTER", has_data_filter and reference.HAS_DATA_FILTER):
                destination = tempfile.mkdtemp(dir=self.tmpdir)
                with self.assertRaises(tarfile.TarError):
                    extract_tar(archive, destination)
                self.assertFalse(os.path.lexists(outside))

    def test_extract_tar_rejects_parent_path(self):
        self.assert_extract_rejected("../../evil.txt", os.path.join(self.tmpdir, "evil.txt"))

    def test_extract_tar_rejects_symlink_outside(self):
        self.assert_extract_rejected(self.symlink("ref/link", self.outdir), os.path.join(self.outdir, "x"))

    def test_extract_tar_never_writes_absolute_path(self):
        outside = os.path.join(self.outdir, "absolute.txt")
        archive = self.make_archive(outside)
        for has_data_filter in [True, False]:
            with self.subTest(has_data_filter=has_data_filter), \
                    mock.patch.object(reference, "HAS_DATA_FILTER", has_data_filter and reference.HAS_DATA_FILTER):
                destination = tempfile.mkdtemp(dir=self.tmpdir)
                try:
                    extract_tar(archive, destination)
                except tarfile.TarError:
                    pass  # the fallback rejects it, the data filter extracts it inside destination
                self.assertFalse(os.path.lexists(outside))

    def test_extract_tar_extracts_safe_archive(self):
        archive = self.make_archive()
        for has_data_filter in [True, False]:
            with self.subTest(has_data_filter=has_data_filter), \
                    mock.patch.object(reference, "HAS_DATA_FILTER", has_data_filter and reference.HAS_DATA_FILTER):
                destination = tempfile.mkdtemp(dir=self.tmpdir)
                extract_tar(archive, destination)
                with open(os.path.join(destination, "ref", "genome.fa"), "rb") as f:
                    self.assertEqual(f.read(), self.genome)
