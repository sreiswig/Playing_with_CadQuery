"""Compare rebuilt catalog models with ``tests/drift_baseline.json``.

Geometry checks need CadQuery and are skipped when it is not installed.
STEP and STL bytes are not compared.

Regenerate the baseline from the current builders (CadQuery required)::

    python -m tests.regen_drift_baseline
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS
from tests.drift_check import (
    BASELINE_PATH,
    BBOX_ABS_TOL_MM,
    BBOX_AXES,
    BBOX_REL_TOL,
    REGEN_COMMAND,
    REQUIRED_MODELS,
    STL_REL_TOL,
    VOLUME_REL_TOL,
    bbox_tolerance_mm,
    cadquery_available,
    catalog_by_id,
    claim_drift,
    geometry_claims,
    manifest_by_id,
    manifest_document,
    manifest_header,
    measure_model,
    triangle_window,
)


def _box_manifest_entry() -> dict:
    """Manifest-shaped box entry, including the real description text."""
    return {
        "id": "box",
        "source": "box.py",
        "builder": "box:create_box",
        "units": "mm",
        "description": "Parametric rectangular prism (CadQuery box). Defaults 10×10×10 mm.",
        "files": {
            "step": {"path": "box.step", "url": "https://example.invalid/box.step"},
            "stl": {
                "path": "artifacts/box/box.stl",
                "url": "https://example.invalid/artifacts/box/box.stl",
            },
        },
    }


class ManifestGeometryClaimTests(unittest.TestCase):
    """Manifest geometry extraction. No CadQuery."""

    def test_identity_fields_are_not_geometry(self):
        self.assertEqual(geometry_claims(_box_manifest_entry()), [])

    def test_committed_manifest_geometry_fields(self):
        """Geometry-derived manifest fields must be visible to the drift check.

        The committed manifest currently records identity only (name, files,
        description). A numeric volume, bounding box, solid count, or
        triangle count is reported here so it is compared to the rebuild
        instead of being dropped.
        """
        found = {
            model_id: geometry_claims(entry)
            for model_id, entry in manifest_by_id(ROOT).items()
        }
        self.assertEqual(
            found,
            {model_id: [] for model_id in found},
            "committed manifest has geometry-derived fields; "
            "the rebuild must match them (do not drop these claims):\n"
            f"{found}",
        )

    def test_extracts_volume_bbox_solids_and_triangles(self):
        entry = _box_manifest_entry()
        entry["volume_mm3"] = 1000
        entry["solid_count"] = 1
        entry["stl_triangles"] = 12
        entry["bbox_mm"] = {"xlen": 10, "ylen": 10, "zlen": 10}
        entry["dims"] = {"length": 10, "width": 10, "height": 10}
        kinds = {(claim["kind"], claim["path"]) for claim in geometry_claims(entry)}
        self.assertIn(("volume", "volume_mm3"), kinds)
        self.assertIn(("solids", "solid_count"), kinds)
        self.assertIn(("triangles", "stl_triangles"), kinds)
        self.assertIn(("bbox", "bbox_mm.xlen"), kinds)
        self.assertIn(("bbox", "dims.length"), kinds)

    def test_two_percent_scale_is_reported(self):
        scale = 1.02
        measured = {
            "volume_mm3": 1000.0 * scale ** 3,
            "bbox_mm": {"xlen": 10.0 * scale, "ylen": 10.0 * scale, "zlen": 10.0 * scale},
            "solid_count": 1,
            "stl_triangles": 12,
        }
        entry = {
            "volume_mm3": 1000.0,
            "bbox_mm": {"xlen": 10.0, "ylen": 10.0, "zlen": 10.0},
            "solid_count": 1,
            "stl_triangles": 12,
        }
        drifts = claim_drift(measured, entry)
        self.assertTrue(any("volume_mm3" in line for line in drifts), drifts)
        self.assertTrue(any("xlen" in line for line in drifts), drifts)
        self.assertFalse(any("solid_count" in line for line in drifts), drifts)
        self.assertFalse(any("triangles" in line for line in drifts), drifts)

    def test_within_tolerance_is_not_drift(self):
        measured = {
            "volume_mm3": 1005.0,
            "bbox_mm": {"xlen": 10.04, "ylen": 10.0, "zlen": 9.99},
            "solid_count": 1,
            "stl_triangles": 13,
        }
        entry = {
            "volume_mm3": 1000.0,
            "bbox_mm": {"xlen": 10.0, "ylen": 10.0, "zlen": 10.0},
            "solid_count": 1,
            "stl_triangles": 12,
        }
        self.assertEqual(claim_drift(measured, entry), [])

    def test_solid_count_mismatch_is_exact(self):
        measured = {
            "volume_mm3": 1000.0,
            "bbox_mm": {"xlen": 10.0, "ylen": 10.0, "zlen": 10.0},
            "solid_count": 2,
            "stl_triangles": 12,
        }
        drifts = claim_drift(measured, {"solid_count": 1})
        self.assertEqual(
            drifts,
            ["solid_count: manifest solid_count 1 vs rebuild 2"],
        )


@unittest.skipUnless(cadquery_available(), "cadquery is not installed")
class DriftTests(unittest.TestCase):
    def test_each_catalog_model_matches_baseline(self):
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(baseline["version"], 1)
        self.assertEqual(baseline["units"], "mm")
        self.assertEqual(baseline["regen"], REGEN_COMMAND)
        self.assertEqual(
            baseline["tolerances"],
            {
                "volume_relative": VOLUME_REL_TOL,
                "bbox_abs_mm": BBOX_ABS_TOL_MM,
                "bbox_relative": BBOX_REL_TOL,
                "stl_triangles_relative": STL_REL_TOL,
            },
        )

        manifest = manifest_document(ROOT)
        self.assertEqual(baseline["manifest_header"], manifest_header(manifest))
        catalog = catalog_by_id()
        by_manifest = manifest_by_id(ROOT)
        by_baseline = {row["id"]: row for row in baseline["models"]}
        self.assertEqual(list(by_baseline), [row["id"] for row in MODELS])
        for model_id in REQUIRED_MODELS:
            self.assertIn(model_id, by_baseline, f"baseline is missing {model_id}")

        for model_id, expected in by_baseline.items():
            with self.subTest(model=model_id):
                self.assertEqual(expected["catalog"], catalog[model_id])
                self.assertEqual(expected["manifest"], by_manifest[model_id])
                low, high = triangle_window(expected["stl_triangles"])
                self.assertEqual(expected["stl_triangles_min"], low)
                self.assertEqual(expected["stl_triangles_max"], high)
                self.assertLessEqual(low, expected["stl_triangles"])
                self.assertGreaterEqual(high, expected["stl_triangles"])

                measured = measure_model(model_id)
                print(
                    f"{model_id}: volume_mm3={measured['volume_mm3']!r} "
                    f"bbox_mm={measured['bbox_mm']!r} "
                    f"solids={measured['solid_count']} "
                    f"triangles={measured['stl_triangles']}",
                    flush=True,
                )
                self.assertTrue(measured["shape_valid"], f"{model_id}: shape is not valid")
                self.assertEqual(
                    measured["files"].get("step"),
                    by_manifest[model_id]["files"]["step"]["path"],
                )
                self.assertEqual(
                    measured["files"].get("stl"),
                    by_manifest[model_id]["files"]["stl"]["path"],
                )
                self._assert_volume(model_id, measured["volume_mm3"], expected["volume_mm3"])
                self._assert_bbox(model_id, measured["bbox_mm"], expected["bbox_mm"])
                self.assertEqual(
                    measured["solid_count"],
                    expected["solid_count"],
                    f"{model_id}: solid count {measured['solid_count']} != "
                    f"{expected['solid_count']}",
                )
                triangles = measured["stl_triangles"]
                self.assertGreaterEqual(
                    triangles,
                    expected["stl_triangles_min"],
                    f"{model_id}: STL triangles {triangles} < {expected['stl_triangles_min']}",
                )
                self.assertLessEqual(
                    triangles,
                    expected["stl_triangles_max"],
                    f"{model_id}: STL triangles {triangles} > {expected['stl_triangles_max']}",
                )
                drifts = claim_drift(measured, by_manifest[model_id])
                self.assertEqual(
                    drifts,
                    [],
                    f"{model_id}: manifest geometry drift:\n" + "\n".join(drifts),
                )

    def _assert_volume(self, model_id: str, actual: float, expected: float) -> None:
        if expected == 0.0:
            self.assertEqual(actual, 0.0, f"{model_id}: volume")
            return
        relative = abs(actual - expected) / abs(expected)
        self.assertLessEqual(
            relative,
            VOLUME_REL_TOL,
            f"{model_id}: Volume() {actual} vs baseline {expected} "
            f"(relative {relative:.4f}, tol {VOLUME_REL_TOL})",
        )

    def _assert_bbox(self, model_id: str, actual: dict, expected: dict) -> None:
        for axis in BBOX_AXES:
            got = float(actual[axis])
            want = float(expected[axis])
            tol = bbox_tolerance_mm(want)
            self.assertLessEqual(
                abs(got - want),
                tol,
                f"{model_id}: BoundingBox.{axis} {got} vs baseline {want} "
                f"(abs {abs(got - want):.6f}, tol {tol})",
            )


if __name__ == "__main__":
    unittest.main()
