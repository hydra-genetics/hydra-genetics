import hashlib
import http.server
import os
import shutil
import socket
import tempfile
import threading
import unittest
from unittest import mock

from hydra_genetics.utils.io import reference
from hydra_genetics.utils.io.reference import fetch_reference_data


class ScriptedHandler(http.server.BaseHTTPRequestHandler):
    """Answers each GET with the next action scripted for its path, the last action repeats.

    Actions: ("status", code), ("body", bytes), ("truncated", bytes). A truncated response announces a longer
    Content-Length than it sends and then closes the connection, like a connection dropped mid-download."""

    def do_GET(self):
        actions = self.server.script[self.path]
        self.server.hits[self.path] = self.server.hits.get(self.path, 0) + 1
        kind, value = actions.pop(0) if len(actions) > 1 else actions[0]
        if kind == "status":
            self.send_response(value)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Length", str(len(value) + (1000 if kind == "truncated" else 0)))
            self.end_headers()
            self.wfile.write(value)
        self.close_connection = True

    def log_message(self, *args):
        pass


class TestFetchReferenceDataNetwork(unittest.TestCase):
    content = b"reference content\n"

    def setUp(self):
        self.outdir = tempfile.mkdtemp()
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ScriptedHandler)
        self.server.script, self.server.hits = {}, {}
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        # no waiting between retries
        patcher = mock.patch.object(reference, "RETRY_BACKOFF_FACTOR", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.outdir)

    def url(self, path, *actions):
        self.server.script[path] = list(actions)
        return f"http://127.0.0.1:{self.server.server_address[1]}{path}"

    def entry(self, name, url):
        return {"path": name, "type": "file", "checksum": hashlib.md5(self.content).hexdigest(), "url": url}

    def fetch(self, **entries):
        return fetch_reference_data({name: self.entry(name, url) for name, url in entries.items()},
                                    self.outdir, fetched=[], links=[], failed=[], skipped=[])

    def assert_fetched(self, name):
        with open(os.path.join(self.outdir, name), "rb") as f:
            self.assertEqual(f.read(), self.content)

    def test_server_errors_are_retried(self):
        fetched, links, failed, skipped = self.fetch(a=self.url("/a", ("status", 503), ("status", 502), ("body", self.content)))
        self.assertEqual((fetched, failed), (["a"], []))
        self.assertEqual(self.server.hits["/a"], 3)
        self.assert_fetched("a")

    def test_persistent_server_error_fails_entry_and_continues(self):
        fetched, links, failed, skipped = self.fetch(a=self.url("/a", ("status", 503)),
                                                     b=self.url("/b", ("body", self.content)))
        self.assertEqual((fetched, failed), (["b"], [os.path.join(self.outdir, "a")]))
        self.assertEqual(self.server.hits["/a"], 1 + reference.RETRY_TOTAL)
        self.assert_fetched("b")

    def test_client_error_is_not_retried(self):
        fetched, links, failed, skipped = self.fetch(a=self.url("/a", ("status", 404)))
        self.assertEqual(failed, [os.path.join(self.outdir, "a")])
        self.assertEqual(self.server.hits["/a"], 1)

    def test_connection_refused_fails_entry_and_continues(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            closed_port = s.getsockname()[1]
        fetched, links, failed, skipped = self.fetch(a=f"http://127.0.0.1:{closed_port}/a",
                                                     b=self.url("/b", ("body", self.content)))
        self.assertEqual((fetched, failed), (["b"], [os.path.join(self.outdir, "a")]))
        self.assert_fetched("b")

    def test_dropped_connection_mid_download_is_retried(self):
        fetched, links, failed, skipped = self.fetch(a=self.url("/a", ("truncated", self.content), ("body", self.content)))
        self.assertEqual((fetched, failed), (["a"], []))
        self.assertEqual(self.server.hits["/a"], 2)
        self.assert_fetched("a")

    def test_connection_always_dropped_fails_entry_and_continues(self):
        fetched, links, failed, skipped = self.fetch(a=self.url("/a", ("truncated", self.content)),
                                                     b=self.url("/b", ("body", self.content)))
        self.assertEqual((fetched, failed), (["b"], [os.path.join(self.outdir, "a")]))
        self.assertEqual(self.server.hits["/a"], reference.DOWNLOAD_ATTEMPTS)
        self.assertFalse(os.path.exists(os.path.join(self.outdir, "a")))
