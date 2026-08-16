"""Catalog/CLI tests. No CadQuery required."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS, build_manifest, load_manifest, model_url


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


if __name__ == "__main__":
    unittest.main()
