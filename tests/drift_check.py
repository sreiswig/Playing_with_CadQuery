"""Stable values for the catalog geometry drift check.

STEP and STL bytes are not compared. Those files carry timestamps and
mesher float noise. The compared values are the catalog and manifest
records, ``Volume()``, bounding-box lengths, solid count, and the STL
triangle count from the smoke-test parser.

Regenerate the committed baseline (CadQuery required)::

    python -m tests.regen_drift_baseline
"""

from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS, load_manifest
from cq_artifacts.export import export_model
from tests.test_build_smoke import stl_triangle_count

BASELINE_PATH = Path(__file__).resolve().parent / "drift_baseline.json"
REGEN_COMMAND = "python -m tests.regen_drift_baseline"

# Relative tolerance on Volume(). 1% absorbs kernel float noise.
VOLUME_REL_TOL = 0.01
# Bounding-box lengths pass when the absolute error is within the
# larger of 0.01 mm and 0.5% of the expected length.
BBOX_ABS_TOL_MM = 0.01
BBOX_REL_TOL = 0.005
# STL triangle count window around the baseline count.
STL_REL_TOL = 0.10

REQUIRED_MODELS = ("cat", "drone", "sonic", "box", "through-hole", "m3-shcs")
BBOX_AXES = ("xlen", "ylen", "zlen")

_VOLUME_KEYS = {"volume", "volume_mm3"}
_SOLID_KEYS = {"solid_count", "solids"}
_TRIANGLE_KEYS = {"stl_triangles", "triangle_count", "triangles"}
_BBOX_CONTAINERS = {"bbox", "bbox_mm", "bounding_box", "boundingbox", "dims", "size"}
_DIRECT_BBOX_KEYS = {"xlen": "xlen", "ylen": "ylen", "zlen": "zlen"}
_NAMED_AXIS_KEYS = {
    "length": "xlen",
    "width": "ylen",
    "height": "zlen",
    "length_mm": "xlen",
    "width_mm": "ylen",
    "height_mm": "zlen",
}


def cadquery_available() -> bool:
    try:
        import cadquery  # noqa: F401
    except ImportError:
        return False
    return True


def catalog_by_id() -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in MODELS}


def manifest_document(root: Path | None = None) -> dict[str, Any]:
    return load_manifest(root)


def manifest_by_id(root: Path | None = None) -> dict[str, dict[str, Any]]:
    data = manifest_document(root)
    return {str(row["id"]): row for row in data["models"]}


def manifest_header(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if key != "models"}


def bbox_tolerance_mm(expected: float) -> float:
    return max(BBOX_ABS_TOL_MM, BBOX_REL_TOL * abs(expected))


def triangle_window(count: int) -> tuple[int, int]:
    """Inclusive ±10% window. Floor/ceil so the stored count stays inside."""
    low = math.floor(count * (1.0 - STL_REL_TOL))
    high = math.ceil(count * (1.0 + STL_REL_TOL))
    return low, high


def _length(box: Any, name: str) -> float:
    value = getattr(box, name)
    if callable(value):
        value = value()
    return float(value)


def _as_shape(shape: Any) -> Any:
    import cadquery as cq

    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    return shape


def measure_model(model_id: str) -> dict[str, Any]:
    """Rebuild one catalog model and return the stable comparable values.

    Uses ``export_model`` (the smoke-test export path) and
    ``stl_triangle_count`` (the smoke-test STL parser).
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        exported = export_model(model_id, root=root)
        shape = _as_shape(exported.shape)
        bounds = shape.BoundingBox()
        stl_path = root / exported.files["stl"]
        triangles = stl_triangle_count(stl_path.read_bytes())
        return {
            "files": {fmt: str(rel) for fmt, rel in exported.files.items()},
            "volume_mm3": float(shape.Volume()),
            "bbox_mm": {axis: _length(bounds, axis) for axis in BBOX_AXES},
            "solid_count": len(shape.Solids()),
            "stl_triangles": int(triangles),
            "shape_valid": bool(shape.isValid()),
        }


def round_measurement(value: float) -> float:
    """Round to 1e-6, far inside the volume and bounding-box tolerances."""
    return round(float(value), 6)


def baseline_record(
    model_id: str,
    measured: dict[str, Any],
    catalog: dict[str, Any],
    manifest_entry: dict[str, Any],
) -> dict[str, Any]:
    tri_min, tri_max = triangle_window(int(measured["stl_triangles"]))
    return {
        "id": model_id,
        "catalog": catalog,
        "manifest": manifest_entry,
        "volume_mm3": round_measurement(measured["volume_mm3"]),
        "bbox_mm": {
            axis: round_measurement(measured["bbox_mm"][axis]) for axis in BBOX_AXES
        },
        "solid_count": int(measured["solid_count"]),
        "stl_triangles": int(measured["stl_triangles"]),
        "stl_triangles_min": tri_min,
        "stl_triangles_max": tri_max,
    }


def baseline_document(records: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 1,
        "units": "mm",
        "regen": REGEN_COMMAND,
        "tolerances": {
            "volume_relative": VOLUME_REL_TOL,
            "bbox_abs_mm": BBOX_ABS_TOL_MM,
            "bbox_relative": BBOX_REL_TOL,
            "stl_triangles_relative": STL_REL_TOL,
        },
        "manifest_header": manifest_header(manifest),
        "models": records,
    }


def geometry_claims(manifest_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Numeric geometry fields recorded on one manifest model entry.

    Identity fields (id, source, builder, description, file paths) are
    skipped. ``xlen`` / ``ylen`` / ``zlen`` count anywhere. ``length`` /
    ``width`` / ``height`` count at the top of the entry or inside an
    object named like a bounding box, dims, or size. Volume, solid
    count, and triangle-count keys count anywhere they are numeric.
    """
    claims: list[dict[str, Any]] = []

    def walk(obj: Any, prefix: str, in_bbox: bool) -> None:
        if not isinstance(obj, dict):
            return
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                if key in _VOLUME_KEYS:
                    claims.append({"path": path, "kind": "volume", "value": float(value)})
                elif key in _SOLID_KEYS:
                    claims.append({"path": path, "kind": "solids", "value": int(value)})
                elif key in _TRIANGLE_KEYS:
                    claims.append({"path": path, "kind": "triangles", "value": int(value)})
                elif key in _DIRECT_BBOX_KEYS:
                    claims.append(
                        {
                            "path": path,
                            "kind": "bbox",
                            "axis": _DIRECT_BBOX_KEYS[key],
                            "value": float(value),
                        }
                    )
                elif key in _NAMED_AXIS_KEYS and (in_bbox or prefix == ""):
                    claims.append(
                        {
                            "path": path,
                            "kind": "bbox",
                            "axis": _NAMED_AXIS_KEYS[key],
                            "value": float(value),
                        }
                    )
                continue
            if isinstance(value, dict):
                walk(value, path, in_bbox or str(key).lower() in _BBOX_CONTAINERS)

    walk(manifest_entry, "", False)
    return claims


def claim_drift(measured: dict[str, Any], manifest_entry: dict[str, Any]) -> list[str]:
    """Mismatches between a rebuild and geometry fields on a manifest entry.

    Empty when the entry records no geometry, or the rebuild sits inside
    the same tolerances the baseline check uses.
    """
    lines: list[str] = []
    for claim in geometry_claims(manifest_entry):
        kind = claim["kind"]
        if kind == "volume":
            expected = float(claim["value"])
            actual = float(measured["volume_mm3"])
            if expected == 0.0:
                ok = actual == 0.0
                rel = None
            else:
                rel = abs(actual - expected) / abs(expected)
                ok = rel <= VOLUME_REL_TOL
            if not ok:
                lines.append(
                    f"{claim['path']}: manifest volume {expected} vs rebuild {actual}"
                    + (f" (relative {rel:.4f}, tol {VOLUME_REL_TOL})" if rel is not None else "")
                )
        elif kind == "bbox":
            axis = str(claim["axis"])
            expected = float(claim["value"])
            actual = float(measured["bbox_mm"][axis])
            tol = bbox_tolerance_mm(expected)
            if abs(actual - expected) > tol:
                lines.append(
                    f"{claim['path']}: manifest {axis} {expected} vs rebuild {actual} "
                    f"(abs {abs(actual - expected):.6f}, tol {tol})"
                )
        elif kind == "solids":
            actual = int(measured["solid_count"])
            expected = int(claim["value"])
            if actual != expected:
                lines.append(
                    f"{claim['path']}: manifest solid_count {expected} vs rebuild {actual}"
                )
        elif kind == "triangles":
            actual = int(measured["stl_triangles"])
            expected = int(claim["value"])
            low, high = triangle_window(expected)
            if not low <= actual <= high:
                lines.append(
                    f"{claim['path']}: manifest triangles {expected} "
                    f"(window {low}..{high}) vs rebuild {actual}"
                )
    return lines
