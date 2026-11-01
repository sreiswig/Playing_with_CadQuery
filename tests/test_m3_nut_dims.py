"""In-memory tests for the M3 hex-nut envelope. No CadQuery."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.m3_nut_dims import (
    ACROSS_CORNERS_MIN_MM,
    ACROSS_FLATS_MM,
    BORE_DIAMETER_MM,
    HEIGHT_MM,
    PITCH_MM,
    M3Nut,
    across_corners_mm,
    make_m3_nut,
    volume_mm3,
)
from cq_artifacts.m3_shcs_dims import (
    SHANK_DIAMETER_MM,
    THREAD_PITCH_MM,
    socket_across_corners_mm,
)


class M3NutDimsTests(unittest.TestCase):
    def test_cited_envelope(self):
        self.assertEqual(ACROSS_FLATS_MM, 5.5)
        self.assertEqual(HEIGHT_MM, 2.4)
        self.assertEqual(BORE_DIAMETER_MM, 3.0)
        self.assertEqual(BORE_DIAMETER_MM, SHANK_DIAMETER_MM)
        self.assertEqual(PITCH_MM, 0.5)
        self.assertEqual(PITCH_MM, THREAD_PITCH_MM)
        self.assertEqual(ACROSS_CORNERS_MIN_MM, 6.01)
        spec = make_m3_nut()
        self.assertIsInstance(spec, M3Nut)
        self.assertEqual(
            (spec.across_flats_mm, spec.height_mm, spec.bore_diameter_mm),
            (5.5, 2.4, 3.0),
        )
        prism = (math.sqrt(3.0) / 2.0) * (5.5 ** 2) * 2.4
        bore = math.pi * (1.5 ** 2) * 2.4
        self.assertAlmostEqual(volume_mm3(spec), prism - bore)
        corners = across_corners_mm()
        self.assertAlmostEqual(corners, socket_across_corners_mm(ACROSS_FLATS_MM))
        self.assertAlmostEqual(corners, 5.5 / math.cos(math.pi / 6.0))
        # Regular hexagon of s max is wider than ISO 4032 e min.
        self.assertGreater(corners, ACROSS_CORNERS_MIN_MM)
        with self.assertRaises(AttributeError):
            setattr(spec, "height_mm", 3)

    def test_import_does_not_import_kernel(self):
        loaded_before = "cadquery" in sys.modules
        import m3_nut

        self.assertTrue(callable(m3_nut.create_m3_nut))
        if not loaded_before:
            self.assertNotIn("cadquery", sys.modules)
