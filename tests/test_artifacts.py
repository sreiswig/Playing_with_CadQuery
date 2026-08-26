"""Catalog/CLI tests. No CadQuery required."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS, build_manifest, load_manifest, model_url
from cq_artifacts.fetch import ALLOWED_RAW_PREFIX, assert_fetch_url_allowed, fetch_file


class ArtifactCatalogTests(unittest.TestCase):
    def test_manifest_on_disk_matches_catalog(self):
        disk = load_manifest(ROOT)
        built = build_manifest()
        self.assertEqual(disk["version"], 1)
        self.assertEqual(disk["units"], "mm")
        self.assertEqual({m["id"] for m in disk["models"]}, {m["id"] for m in MODELS})
        self.assertEqual(disk["models"], built["models"])

    def test_each_model_has_step_and_stl_urls(self):
        for m in build_manifest()["models"]:
            self.assertIn("step", m["files"])
            self.assertIn("stl", m["files"])
            step = m["files"]["step"]
            self.assertTrue(step["path"].endswith(".step"))
            self.assertEqual(step["url"], model_url(step["path"]))
            self.assertTrue(
                step["url"].startswith(
                    "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
                )
            )

    def test_cli_list_is_json_manifest(self):
        proc = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "list"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(proc.stdout)
        self.assertEqual(data["version"], 1)
        self.assertGreaterEqual({m["id"] for m in data["models"]}, {"cat", "drone"})

    def test_cli_url_and_path_cat_step(self):
        url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "cat", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(url.endswith("/cat.step"))
        path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", "cat", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(path.endswith("cat.step"))

    def test_unknown_model_url_fails(self):
        proc = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "nope", "step"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_fetch_prefers_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "cat.step"
            src.write_bytes(b"ISO-10303-fake")
            dest = tmp_path / "out" / "cat.step"
            result = fetch_file("cat", "step", dest, root=tmp_path)
            self.assertEqual(result["source"], "local")
            self.assertEqual(dest.read_bytes(), b"ISO-10303-fake")

    def test_fetch_unknown_model(self):
        with self.assertRaises(KeyError):
            fetch_file("nope", "step", Path("/tmp/x.step"))

    def test_committed_step_and_stl_exist(self):
        for rel in (
            "cat.step",
            "drone.step",
            "artifacts/cat/cat.stl",
            "artifacts/drone/drone.stl",
        ):
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"missing {rel}")
            self.assertGreater(path.stat().st_size, 0, f"empty {rel}")

    def test_cli_fetch_local_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cat.step"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cq_artifacts",
                    "fetch",
                    "cat",
                    "step",
                    "-o",
                    str(dest),
                    "--root",
                    str(ROOT),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["source"], "local")
            self.assertEqual(dest.read_bytes(), (ROOT / "cat.step").read_bytes())

    def test_fetch_remote_mocked(self):
        recorded: dict[str, str] = {}

        class FakeResp:
            def geturl(self):
                return recorded["url"]

            def read(self):
                return b"remote-bytes"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(url):
            recorded["url"] = url
            return FakeResp()

        with tempfile.TemporaryDirectory() as tmp:
            empty_root = Path(tmp) / "empty"
            empty_root.mkdir()
            dest = Path(tmp) / "out" / "cat.step"
            result = fetch_file("cat", "step", dest, root=empty_root, urlopen=fake_urlopen)
            self.assertEqual(result["source"], "remote")
            self.assertEqual(result["from"], recorded["url"])
            self.assertEqual(dest.read_bytes(), b"remote-bytes")
            self.assertTrue(recorded["url"].startswith(ALLOWED_RAW_PREFIX))
            self.assertTrue(recorded["url"].endswith("/cat.step"))

    def test_assert_fetch_url_allowed_accepts(self):
        assert_fetch_url_allowed(ALLOWED_RAW_PREFIX + "main/cat.step")
        assert_fetch_url_allowed(ALLOWED_RAW_PREFIX + "some-branch/artifacts/cat/cat.stl")

    def test_assert_fetch_url_allowed_rejects(self):
        bad = [
            "http://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step",
            "https://evil.example/",
            "https://github.com/sreiswig/Playing_with_CadQuery/blob/main/cat.step",
            "https://raw.githubusercontent.com/other/Playing_with_CadQuery/main/cat.step",
            "https://raw.githubusercontent.com/sreiswig/other-repo/main/cat.step",
            "",
        ]
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    assert_fetch_url_allowed(url)

    def test_fetch_refuses_off_prefix_redirect(self):
        class EvilResp:
            def geturl(self):
                return "https://evil.example/steal"

            def read(self):
                return b"stolen"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def evil_urlopen(url):
            return EvilResp()

        with tempfile.TemporaryDirectory() as tmp:
            empty_root = Path(tmp) / "empty"
            empty_root.mkdir()
            dest = Path(tmp) / "out" / "cat.step"
            with self.assertRaises(ValueError):
                fetch_file("cat", "step", dest, root=empty_root, urlopen=evil_urlopen)
            self.assertFalse(dest.exists() or (dest.is_file() and dest.stat().st_size > 0))


if __name__ == "__main__":
    unittest.main()
