"""Build each catalog model through the export path.

The geometry checks need CadQuery, so they are skipped when it is not
installed. The STL parser tests are stdlib-only and always run.
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS
from cq_artifacts.export import export_model

try:
    import cadquery
except ImportError:
    cadquery = None  # type: ignore[assignment]

# Binary STL: 80-byte header, uint32 triangle count, then 50 bytes per
# triangle (normal + 3 vertices as float32, plus a uint16 attribute).
_STL_HEADER_BYTES = 80
_STL_COUNT_BYTES = 4
_STL_TRIANGLE_BYTES = 50
_STEP_MAGIC = b"ISO-10303-21"
_REQUIRED_MODELS = ("cat", "drone", "sonic", "box", "through-hole", "m3-shcs")


def _binary_stl_triangle_count(data: bytes) -> int | None:
    """Return the triangle count when ``data`` is a size-consistent binary STL."""
    header_and_count = _STL_HEADER_BYTES + _STL_COUNT_BYTES
    if len(data) < header_and_count:
        return None
    (count,) = struct.unpack_from("<I", data, _STL_HEADER_BYTES)
    expected = header_and_count + count * _STL_TRIANGLE_BYTES
    if len(data) != expected:
        return None
    return count


def stl_triangle_count(data: bytes) -> int:
    """Triangle count of a binary or ASCII STL.

    Binary is an 80-byte header, a little-endian uint32 count, and a body
    whose size is ``count * 50``. That layout is used only when the file
    size matches. Otherwise the file is ASCII and the count is the number
    of ``facet normal`` records.
    """
    binary = _binary_stl_triangle_count(data)
    if binary is not None:
        return binary
    return data.count(b"facet normal")


class StlParserTests(unittest.TestCase):
    def test_binary_count_requires_consistent_size(self):
        count = 3
        header = b"STL Exported by Open CASCADE Technology".ljust(_STL_HEADER_BYTES, b"\x00")
        body = b"\x00" * (count * _STL_TRIANGLE_BYTES)
        data = header + struct.pack("<I", count) + body
        self.assertEqual(stl_triangle_count(data), count)

        truncated = data[:-1]
        self.assertIsNone(_binary_stl_triangle_count(truncated))

    def test_binary_size_wins_over_header_text(self):
        count = 2
        header = b"solid facet normal decoy".ljust(_STL_HEADER_BYTES, b"\x00")
        body = b"\xab" * (count * _STL_TRIANGLE_BYTES)
        data = header + struct.pack("<I", count) + body
        self.assertEqual(stl_triangle_count(data), count)

    def test_ascii_counts_facet_normal(self):
        data = (
            b"solid demo\n"
            b"facet normal 0 0 1\n"
            b"  outer loop\n"
            b"    vertex 0 0 0\n"
            b"  endloop\n"
            b"endfacet\n"
            b"facet normal 0 1 0\n"
            b"endfacet\n"
            b"endsolid demo\n"
        )
        self.assertIsNone(_binary_stl_triangle_count(data))
        self.assertEqual(stl_triangle_count(data), 2)

    def test_size_mismatch_falls_back_to_ascii(self):
        data = b"solid demo\n" + (b"\x00" * 80) + b"facet normal 0 0 1\n"
        self.assertIsNone(_binary_stl_triangle_count(data))
        self.assertEqual(stl_triangle_count(data), 1)


@unittest.skipUnless(cadquery is not None, "cadquery is not installed")
class BuildSmokeTests(unittest.TestCase):
    def test_each_catalog_model_exports_a_solid(self):
        catalog_ids = [row["id"] for row in MODELS]
        for model_id in _REQUIRED_MODELS:
            self.assertIn(model_id, catalog_ids, f"catalog is missing {model_id}")
        for model_id in catalog_ids:
            with self.subTest(model=model_id):
                self._assert_model(model_id)

    def _assert_model(self, model_id: str) -> None:
        import cadquery as cq

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exported = export_model(model_id, root=root)
            shape = exported.shape
            if isinstance(shape, cq.Workplane):
                shape = shape.val()
            self.assertIsInstance(
                shape,
                cq.Shape,
                f"{model_id}: expected a CadQuery Shape, got {type(shape).__name__}",
            )
            self.assertTrue(
                shape.isValid(),
                f"{model_id}: shape.isValid() is false",
            )
            solids = shape.Solids()
            self.assertGreaterEqual(
                len(solids),
                1,
                f"{model_id}: expected at least one solid, found {len(solids)}",
            )
            volume = shape.Volume()
            self.assertGreater(
                volume,
                0,
                f"{model_id}: Volume() is {volume}, expected > 0",
            )

            self.assertIn("step", exported.files, f"{model_id}: export recorded no STEP path")
            self.assertIn("stl", exported.files, f"{model_id}: export recorded no STL path")

            step_path = root / exported.files["step"]
            self.assertTrue(
                step_path.is_file(),
                f"{model_id}: STEP file is missing ({exported.files['step']})",
            )
            step_bytes = step_path.read_bytes()
            self.assertGreater(len(step_bytes), 0, f"{model_id}: STEP file is empty")
            self.assertTrue(
                step_bytes.startswith(_STEP_MAGIC),
                f"{model_id}: STEP does not start with ISO-10303-21 "
                f"(got {step_bytes[:24]!r})",
            )

            stl_path = root / exported.files["stl"]
            self.assertTrue(
                stl_path.is_file(),
                f"{model_id}: STL file is missing ({exported.files['stl']})",
            )
            stl_bytes = stl_path.read_bytes()
            self.assertGreater(len(stl_bytes), 0, f"{model_id}: STL file is empty")
            triangles = stl_triangle_count(stl_bytes)
            self.assertGreater(
                triangles,
                0,
                f"{model_id}: STL triangle count is {triangles}",
            )
            print(
                f"{model_id}: volume_mm3={volume!r} triangles={triangles}",
                flush=True,
            )

    def test_through_hole_and_m3_shcs_match_cited_envelope(self):
        import math

        from cq_artifacts.m3_shcs_dims import make_m3_shcs
        from cq_artifacts.m3_shcs_dims import volume_mm3 as screw_volume
        from cq_artifacts.outcome import Ok
        from cq_artifacts.through_hole_dims import make_through_hole
        from cq_artifacts.through_hole_dims import volume_mm3 as plate_volume
        from m3_shcs import create_m3_shcs
        from through_hole import create_through_hole

        plate_spec = make_through_hole(3.4, 20, 20, 3, 0, 0)
        self.assertIsInstance(plate_spec, Ok)
        plate = self._shape(create_through_hole())
        self._assert_envelope(
            plate,
            plate_volume(plate_spec.value),
            (20.0, 20.0, 3.0),
        )
        self.assertAlmostEqual(plate.Center().x, 0.0, places=6)
        self.assertAlmostEqual(plate.Center().y, 0.0, places=6)
        self.assertFalse(plate.isInside((0, 0, 0)))
        self.assertTrue(plate.isInside((8, 0, 0)))

        offset_spec = make_through_hole(3.4, 20, 20, 3, 5, -2)
        self.assertIsInstance(offset_spec, Ok)
        offset = self._shape(create_through_hole(hole_x=5, hole_y=-2))
        self._assert_envelope(
            offset,
            plate_volume(offset_spec.value),
            (20.0, 20.0, 3.0),
        )
        hole_mass = math.pi * (1.7 ** 2) * 3.0
        total = 20.0 * 20.0 * 3.0 - hole_mass
        self.assertAlmostEqual(offset.Center().x, -5.0 * hole_mass / total, places=6)
        self.assertAlmostEqual(offset.Center().y, 2.0 * hole_mass / total, places=6)
        self.assertFalse(offset.isInside((5, -2, 0)))
        self.assertTrue(offset.isInside((0, 0, 0)))

        screw_spec = make_m3_shcs(10)
        self.assertIsInstance(screw_spec, Ok)
        screw = self._shape(create_m3_shcs())
        self._assert_envelope(
            screw,
            screw_volume(screw_spec.value),
            (5.5, 5.5, 13.0),
        )
        socket_z = 3.0 - 1.3 / 2.0
        self.assertFalse(screw.isInside((0, 0, socket_z)))
        # Circumscribed hex: flat midpoint on +X, vertex on +Y.
        self.assertTrue(screw.isInside((1.35, 0, socket_z)))
        self.assertFalse(screw.isInside((0, 1.40, socket_z)))
        self.assertTrue(screw.isInside((0, 0, 1.5)))
        self.assertTrue(screw.isInside((1.45, 0, -2)))
        self.assertFalse(screw.isInside((1.55, 0, -2)))
        for angle in range(0, 360, 45):
            radius = 1.45
            point = (
                radius * math.cos(math.radians(angle)),
                radius * math.sin(math.radians(angle)),
                -3.0,
            )
            self.assertTrue(screw.isInside(point), point)
        self.assertAlmostEqual(screw.Center().x, 0.0, places=6)
        self.assertAlmostEqual(screw.Center().y, 0.0, places=6)
        self.assertLess(screw.Center().z, 0.0)

        longer_spec = make_m3_shcs(16)
        self.assertIsInstance(longer_spec, Ok)
        longer = self._shape(create_m3_shcs(length=16))
        self._assert_envelope(
            longer,
            screw_volume(longer_spec.value),
            (5.5, 5.5, 19.0),
        )

    def _shape(self, workplane):
        import cadquery as cq

        shape = workplane.val() if isinstance(workplane, cq.Workplane) else workplane
        self.assertTrue(shape.isValid())
        self.assertEqual(len(shape.Solids()), 1)
        return shape

    def _assert_envelope(self, shape, expected_volume: float, bbox: tuple[float, float, float]) -> None:
        actual = float(shape.Volume())
        relative = abs(actual - expected_volume) / expected_volume
        self.assertLessEqual(
            relative,
            1e-6,
            f"Volume() {actual} vs cited envelope {expected_volume}",
        )
        bounds = shape.BoundingBox()
        for axis, expected in zip(("xlen", "ylen", "zlen"), bbox, strict=True):
            self.assertAlmostEqual(float(getattr(bounds, axis)), expected, places=6)


if __name__ == "__main__":
    unittest.main()
