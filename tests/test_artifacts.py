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


COMMITTED_FETCH_FILES = (
    "cat.step",
    "drone.step",
    "sonic.step",
    "box.step",
    "artifacts/cat/cat.stl",
    "artifacts/drone/drone.stl",
    "artifacts/sonic/sonic.stl",
    "artifacts/box/box.stl",
)


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
        ids = {m["id"] for m in data["models"]}
        self.assertGreaterEqual(ids, {"cat", "drone", "sonic", "box"})
        self.assertIn("sonic", ids)
        self.assertIn("box", ids)

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

    def test_cli_url_and_path_sonic_step_and_stl(self):
        url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "sonic", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(url.endswith("/sonic.step"))
        self.assertTrue(
            url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", "sonic", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(path.endswith("sonic.step"))
        stl_url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "sonic", "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_url.endswith("/artifacts/sonic/sonic.stl"))
        self.assertTrue(
            stl_url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        stl_path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", "sonic", "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_path.endswith("artifacts/sonic/sonic.stl"))

    def test_cli_url_and_path_box_step_and_stl(self):
        url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "box", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(url.endswith("/box.step"))
        self.assertTrue(
            url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", "box", "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(path.endswith("box.step"))
        stl_url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "box", "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_url.endswith("/artifacts/box/box.stl"))
        self.assertTrue(
            stl_url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        stl_path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", "box", "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_path.endswith("artifacts/box/box.stl"))

    def test_unknown_model_url_fails(self):
        proc = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", "nope", "step"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_committed_fetch_files_exist_and_nonempty(self):
        for rel in COMMITTED_FETCH_FILES:
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"missing {rel}")
            self.assertGreater(path.stat().st_size, 0, f"empty {rel}")

    def test_fetch_prefers_local(self):
        from cq_artifacts.fetch import fetch_file

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "cat.step"
            src.write_bytes(b"ISO-10303-fake")
            dest = tmp_path / "out" / "cat.step"
            result = fetch_file("cat", "step", dest, root=tmp_path)
            self.assertEqual(result["source"], "local")
            self.assertEqual(dest.read_bytes(), b"ISO-10303-fake")

    def test_cli_fetch_local_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "copied.step"
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

    def test_cli_fetch_local_sonic_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "copied.step"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cq_artifacts",
                    "fetch",
                    "sonic",
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
            self.assertEqual(dest.read_bytes(), (ROOT / "sonic.step").read_bytes())

    def test_cli_fetch_local_box_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "copied.step"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cq_artifacts",
                    "fetch",
                    "box",
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
            self.assertEqual(dest.read_bytes(), (ROOT / "box.step").read_bytes())

    def test_fetch_unknown_model(self):
        from cq_artifacts.fetch import fetch_file

        with self.assertRaises(KeyError):
            fetch_file("nope", "step", Path("/tmp/x.step"))

    def test_fetch_remote_mocked_no_network(self):
        seen = []

        class FakeResp:
            def __init__(self, url: str):
                self._url = url

            def read(self) -> bytes:
                return b"remote-bytes"

            def geturl(self) -> str:
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(url: str):
            seen.append(url)
            return FakeResp(url)

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            dest = Path(tmp) / "out" / "cat.step"
            result = fetch_file(
                "cat", "step", dest, root=empty, urlopen=fake_urlopen
            )
            self.assertEqual(result["source"], "remote")
            self.assertEqual(dest.read_bytes(), b"remote-bytes")
            self.assertEqual(len(seen), 1)
            self.assertTrue(seen[0].startswith(ALLOWED_RAW_PREFIX))
            self.assertTrue(seen[0].endswith("/cat.step"))
            assert_fetch_url_allowed(seen[0])

    def test_allowlist_accepts_raw_prefix(self):
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/some-branch/artifacts/cat/cat.stl"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/sonic.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/sonic/sonic.stl"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/box.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/box/box.stl"
        )

    def test_allowlist_rejects_other_hosts(self):
        bad = (
            "http://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step",
            "https://evil.example/cat.step",
            "https://github.com/sreiswig/Playing_with_CadQuery/blob/main/cat.step",
            "https://github.com/sreiswig/Playing_with_CadQuery/raw/main/cat.step",
            "https://raw.githubusercontent.com/other/Playing_with_CadQuery/main/cat.step",
            "https://raw.githubusercontent.com/sreiswig/other-repo/main/cat.step",
            "",
        )
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    assert_fetch_url_allowed(url)

    def test_allowlist_rejects_path_escape(self):
        bad = (
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/../other-repo/main/x",
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/%2e%2e/other-repo/main/x",
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/../../sreiswig/secrets/x",
        )
        for url in bad:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    assert_fetch_url_allowed(url)

    def test_fetch_rejects_redirect_off_prefix(self):
        class EvilResp:
            def read(self) -> bytes:
                return b"stolen"

            def geturl(self) -> str:
                return "https://evil.example/steal"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def evil_urlopen(url: str):
            return EvilResp()

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            dest = Path(tmp) / "out" / "cat.step"
            with self.assertRaises(ValueError):
                fetch_file("cat", "step", dest, root=empty, urlopen=evil_urlopen)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
