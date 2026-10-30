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
from cq_artifacts.fetch import (
    ALLOWED_RAW_PREFIX,
    DEFAULT_FETCH_TIMEOUT,
    MAX_FETCH_BYTES,
    FetchTooLargeError,
    assert_fetch_url_allowed,
    fetch_file,
)


COMMITTED_FETCH_FILES = (
    "cat.step",
    "drone.step",
    "sonic.step",
    "box.step",
    "through-hole.step",
    "m3-shcs.step",
    "headset-earcup.step",
    "headset-headband.step",
    "headset-yoke.step",
    "headset.step",
    "artifacts/cat/cat.stl",
    "artifacts/drone/drone.stl",
    "artifacts/sonic/sonic.stl",
    "artifacts/box/box.stl",
    "artifacts/through-hole/through-hole.stl",
    "artifacts/m3-shcs/m3-shcs.stl",
    "artifacts/headset-earcup/headset-earcup.stl",
    "artifacts/headset-headband/headset-headband.stl",
    "artifacts/headset-yoke/headset-yoke.stl",
    "artifacts/headset/headset.stl",
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
        self.assertGreaterEqual(
            ids,
            {
                "cat",
                "drone",
                "sonic",
                "box",
                "through-hole",
                "m3-shcs",
                "headset-earcup",
                "headset-headband",
                "headset-yoke",
                "headset",
            },
        )
        self.assertIn("sonic", ids)
        self.assertIn("box", ids)
        self.assertIn("through-hole", ids)
        self.assertIn("m3-shcs", ids)

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

    def test_cli_url_path_and_fetch_through_hole(self):
        self._assert_cli_step_and_stl("through-hole")

    def test_cli_url_path_and_fetch_m3_shcs(self):
        self._assert_cli_step_and_stl("m3-shcs")

    def test_cli_url_path_and_fetch_headset_parts(self):
        for model_id in ("headset-earcup", "headset-headband", "headset-yoke", "headset"):
            with self.subTest(model=model_id):
                self._assert_cli_step_and_stl(model_id)

    def _assert_cli_step_and_stl(self, model_id: str) -> None:
        url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", model_id, "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(url.endswith(f"/{model_id}.step"))
        self.assertTrue(
            url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", model_id, "step"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(path.endswith(f"{model_id}.step"))
        stl_url = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "url", model_id, "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_url.endswith(f"/artifacts/{model_id}/{model_id}.stl"))
        self.assertTrue(
            stl_url.startswith(
                "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"
            )
        )
        stl_path = subprocess.run(
            [sys.executable, "-m", "cq_artifacts", "path", model_id, "stl"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertTrue(stl_path.endswith(f"artifacts/{model_id}/{model_id}.stl"))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "copied.step"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cq_artifacts",
                    "fetch",
                    model_id,
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
            self.assertEqual(dest.read_bytes(), (ROOT / f"{model_id}.step").read_bytes())

    def test_fetch_unknown_model(self):
        from cq_artifacts.fetch import fetch_file

        with self.assertRaises(KeyError):
            fetch_file("nope", "step", Path("/tmp/x.step"))

    def test_fetch_remote_mocked_no_network(self):
        seen = []

        class FakeResp:
            def __init__(self, url: str):
                self._url = url

            def read(self, size: int = -1) -> bytes:
                return b"remote-bytes"

            def geturl(self) -> str:
                return self._url

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(url: str, timeout=None, **kw):
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
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/through-hole.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/m3-shcs.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/through-hole/through-hole.stl"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/m3-shcs/m3-shcs.stl"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/headset.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/headset/headset.stl"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/headset-earcup.step"
        )
        assert_fetch_url_allowed(
            "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/headset-yoke/headset-yoke.stl"
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
            def read(self, size: int = -1) -> bytes:
                return b"stolen"

            def geturl(self) -> str:
                return "https://evil.example/steal"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def evil_urlopen(url: str, timeout=None, **kw):
            return EvilResp()

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            dest = Path(tmp) / "out" / "cat.step"
            with self.assertRaises(ValueError):
                fetch_file("cat", "step", dest, root=empty, urlopen=evil_urlopen)
            self.assertFalse(dest.exists())

    def _remote_fetch(self, urlopen, dest: Path, **kwargs):
        empty = dest.parent.parent / "empty-root"
        empty.mkdir(exist_ok=True)
        return fetch_file("cat", "step", dest, root=empty, urlopen=urlopen, **kwargs)

    def test_fetch_passes_default_and_override_timeout(self):
        seen = []

        class FakeResp:
            def read(self, size: int = -1) -> bytes:
                return b"remote-bytes"

            def geturl(self) -> str:
                return (
                    "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step"
                )

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(url: str, timeout=None, **kw):
            seen.append(timeout)
            return FakeResp()

        self.assertEqual(DEFAULT_FETCH_TIMEOUT, 30)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out" / "cat.step"
            self._remote_fetch(fake_urlopen, dest)
            override = Path(tmp) / "out" / "override.step"
            self._remote_fetch(fake_urlopen, override, timeout=5)
        self.assertEqual(seen, [DEFAULT_FETCH_TIMEOUT, 5])

    def test_fetch_oversize_raises_and_leaves_no_files(self):
        self.assertEqual(MAX_FETCH_BYTES, 32 * 1024 * 1024)

        class BigResp:
            def read(self, size: int = -1) -> bytes:
                return b"x" * 64

            def geturl(self) -> str:
                return (
                    "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step"
                )

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def big_urlopen(url: str, timeout=None, **kw):
            return BigResp()

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out" / "cat.step"
            with self.assertRaises(FetchTooLargeError) as caught:
                self._remote_fetch(big_urlopen, dest, max_bytes=32)
            self.assertIn("32", str(caught.exception))
            self.assertFalse(dest.exists())
            self.assertEqual(list(dest.parent.iterdir()), [])

    def test_fetch_remote_replace_failure_leaves_no_temp_or_dest(self):
        from unittest.mock import patch

        class FakeResp:
            def read(self, size: int = -1) -> bytes:
                return b"remote-bytes"

            def geturl(self) -> str:
                return (
                    "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step"
                )

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(url: str, timeout=None, **kw):
            return FakeResp()

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out" / "cat.step"
            with patch("cq_artifacts.fetch.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    self._remote_fetch(fake_urlopen, dest)
            self.assertFalse(dest.exists())
            self.assertEqual(list(dest.parent.iterdir()), [])

    def _run_fetch_cli(self, urlopen):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        from unittest.mock import patch

        from cq_artifacts.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            dest = Path(tmp) / "out.step"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch("urllib.request.urlopen", urlopen),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                code = main(
                    ["fetch", "cat", "step", "-o", str(dest), "--root", str(empty)]
                )
            return code, stdout.getvalue(), stderr.getvalue(), dest.exists()

    def test_cli_fetch_urlerror_exits_1(self):
        import urllib.error

        def boom(url: str, timeout=None, **kw):
            raise urllib.error.URLError("network down")

        code, stdout, stderr, dest_exists = self._run_fetch_cli(boom)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.splitlines(), ["<urlopen error network down>"])
        self.assertFalse(dest_exists)

    def test_cli_fetch_timeout_exits_1(self):
        def boom(url: str, timeout=None, **kw):
            raise TimeoutError("timed out")

        code, stdout, stderr, dest_exists = self._run_fetch_cli(boom)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.splitlines(), ["timed out"])
        self.assertFalse(dest_exists)

    def test_cli_fetch_oversize_exits_1(self):
        class BigResp:
            def read(self, size: int = -1) -> bytes:
                n = MAX_FETCH_BYTES + 1 if size is None or size < 0 else size
                return b"x" * n

            def geturl(self) -> str:
                return (
                    "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step"
                )

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def big_urlopen(url: str, timeout=None, **kw):
            return BigResp()

        code, stdout, stderr, dest_exists = self._run_fetch_cli(big_urlopen)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr.splitlines(),
            [f"remote artifact exceeds {MAX_FETCH_BYTES} byte cap"],
        )
        self.assertFalse(dest_exists)


if __name__ == "__main__":
    unittest.main()
