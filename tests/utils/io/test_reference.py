import hashlib
import io
import os
import shutil
import tarfile
import tempfile
import unittest
from unittest import mock
from requests import HTTPError

from hydra_genetics.utils.io.reference import fetch_reference_data, fetch_url_content


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

    def fetch_folder(self, content_checksum):
        """Fetch a local tar.gz with ref/genome.fa as a folder entry with the given content_checksum"""
        archive = os.path.join(self.tmpdir, "folder.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            info = tarfile.TarInfo("ref/genome.fa")
            info.size = len(self.genome)
            tar.addfile(info, io.BytesIO(self.genome))
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
