import hashlib
import os
import shutil
import tempfile
import unittest
from requests import HTTPError

from hydra_genetics.utils.io.reference import fetch_reference_data, fetch_url_content


class TestReference(unittest.TestCase):
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

    def test_fetch_reference_data_404(self):
        validation_data = {
            "not a file": {
                "path": "files/not-a-file.txt",
                "type": "file",
                "url": "https://github.com/Twist_Solid_pipeline_files/raw/v1.0.0/design/this-is-surely-not-a-file.txt",
            },
        }
        fetched, links, failed, skipped = fetch_reference_data(validation_data, self.outdir,
                                                                fetched=[], links=[], failed=[], skipped=[])
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

        fetched, links, failed, skipped = fetch_reference_data(validation_data, self.outdir,
                                                                fetched=[], links=[], failed=[], skipped=[])

        self.assertEqual(len(fetched), 1)
        self.assertEqual(len(failed), 0)
        self.assertEqual(len(links), 0)
        self.assertEqual(len(skipped), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.outdir, "files/local-test-file.txt")))
