"""In-memory tests for catalog id/format lookup. No filesystem."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS
from cq_artifacts.catalog_lookup import (
    ArtifactRef,
    LookupCode,
    ModelRow,
    lookup_artifact,
    lookup_deny_message,
    lookup_model,
)
from cq_artifacts.outcome import Err, Ok

FIXTURE = (
    {
        "id": "box",
        "source": "box.py",
        "builder": "box:create_box",
        "units": "mm",
        "description": "prism",
        "files": {"step": "box.step", "stl": "artifacts/box/box.stl"},
    },
    {
        "id": "plate",
        "source": "plate.py",
        "builder": "plate:create_plate",
        "units": "mm",
        "description": "flat",
        "files": {"step": ""},
    },
)


class CatalogLookupTests(unittest.TestCase):
    def test_lookup_model_returns_frozen_row(self):
        found = lookup_model(FIXTURE, "box")
        self.assertIsInstance(found, Ok)
        row = found.value
        self.assertIsInstance(row, ModelRow)
        self.assertEqual(row.builder, "box:create_box")
        self.assertEqual(row.files, (("step", "box.step"), ("stl", "artifacts/box/box.stl")))
        with self.assertRaises(AttributeError):
            setattr(row, "id", "other")

    def test_unknown_model_lists_known_ids_in_order(self):
        found = lookup_model(FIXTURE, "nope")
        self.assertIsInstance(found, Err)
        self.assertIs(found.error.code, LookupCode.UNKNOWN_MODEL)
        self.assertEqual(found.error.known_ids, ("box", "plate"))
        self.assertEqual(found.error.fmt, None)
        self.assertEqual(
            lookup_deny_message(found.error, include_known=True),
            "unknown model 'nope'; known: box, plate",
        )
        self.assertEqual(
            lookup_deny_message(found.error, include_known=False),
            "unknown model 'nope'",
        )

    def test_missing_format_denies_without_inventing_a_path(self):
        found = lookup_artifact(FIXTURE, "plate", "stl")
        self.assertIsInstance(found, Err)
        self.assertIs(found.error.code, LookupCode.MISSING_FORMAT)
        self.assertEqual(found.error.fmt, "stl")
        self.assertEqual(
            lookup_deny_message(found.error, include_known=True),
            "no stl for plate",
        )

    def test_lookup_artifact_relpath(self):
        found = lookup_artifact(FIXTURE, "box", "stl")
        self.assertIsInstance(found, Ok)
        self.assertIsInstance(found.value, ArtifactRef)
        self.assertEqual(found.value.relpath, "artifacts/box/box.stl")
        with self.assertRaises(AttributeError):
            setattr(found.value, "relpath", "elsewhere")

    def test_first_duplicate_id_wins(self):
        rows = (
            {"id": "box", "files": {"step": "first.step"}},
            {"id": "box", "files": {"step": "second.step"}},
        )
        found = lookup_artifact(rows, "box", "step")
        self.assertIsInstance(found, Ok)
        self.assertEqual(found.value.relpath, "first.step")

    def test_live_catalog_resolves_committed_names(self):
        expected = {
            "cat": {"step": "cat.step", "stl": "artifacts/cat/cat.stl"},
            "drone": {"step": "drone.step", "stl": "artifacts/drone/drone.stl"},
            "sonic": {"step": "sonic.step", "stl": "artifacts/sonic/sonic.stl"},
            "box": {"step": "box.step", "stl": "artifacts/box/box.stl"},
        }
        self.assertEqual([row["id"] for row in MODELS], list(expected))
        for model_id, files in expected.items():
            for fmt, relpath in files.items():
                found = lookup_artifact(MODELS, model_id, fmt)
                self.assertIsInstance(found, Ok)
                self.assertEqual(found.value.relpath, relpath)
