"""In-memory tests for the headset shell kit. No CadQuery."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.headset_dims import (
    BAND_THICKNESS_MM,
    COVER_SCREW_LENGTH_MM,
    DEFAULT_ARC_DEG,
    DEFAULT_DRIVER_DIAMETER_MM,
    DEFAULT_INNER_RADIUS_MM,
    DEFAULT_TRAVEL_MM,
    DRIVER_DIAMETER_MAX_MM,
    DRIVER_DIAMETER_MIN_MM,
    EXTENSION_SCREW_LENGTH_MM,
    HEAD_DIAMETER_MM,
    HINGE_SCREW_LENGTH_MM,
    LIPO_LENGTH_MM,
    LIPO_THICKNESS_MM,
    LIPO_WIDTH_MM,
    OUTER_DEPTH_MM,
    OUTER_HEIGHT_MM,
    OUTER_WIDTH_MM,
    PCB_LENGTH_MM,
    PCB_THICKNESS_MM,
    PCB_WIDTH_MM,
    SHANK_DIAMETER_MM,
    HeadsetDenyCode,
    HeadsetLayout,
    headset_deny_message,
    make_headset,
)
from cq_artifacts.m3_shcs_dims import PREFERRED_LENGTHS_MM, make_m3_shcs
from cq_artifacts.outcome import Err, Ok
from cq_artifacts.through_hole_dims import DEFAULT_HOLE_DIAMETER_MM


def _axis_distance(point, origin, direction) -> float:
    px = point[0] - origin[0]
    py = point[1] - origin[1]
    pz = point[2] - origin[2]
    dx, dy, dz = direction
    cx = dy * pz - dz * py
    cy = dz * px - dx * pz
    cz = dx * py - dy * px
    return math.sqrt(cx * cx + cy * cy + cz * cz) / math.sqrt(dx * dx + dy * dy + dz * dz)


class HeadsetDimsTests(unittest.TestCase):
    def test_defaults_are_the_documented_comfort_kit(self):
        self.assertEqual(DEFAULT_DRIVER_DIAMETER_MM, 50.0)
        self.assertEqual((DRIVER_DIAMETER_MIN_MM, DRIVER_DIAMETER_MAX_MM), (40.0, 50.0))
        self.assertEqual(DEFAULT_INNER_RADIUS_MM, 105.0)
        self.assertEqual(DEFAULT_ARC_DEG, 110.0)
        self.assertEqual(DEFAULT_TRAVEL_MM, 28.0)
        self.assertEqual((OUTER_WIDTH_MM, OUTER_HEIGHT_MM, OUTER_DEPTH_MM), (76.0, 88.0, 42.0))
        found = make_headset()
        self.assertIsInstance(found, Ok)
        layout = found.value
        self.assertIsInstance(layout, HeadsetLayout)
        self.assertEqual(layout.hole_diameter_mm, DEFAULT_HOLE_DIAMETER_MM)
        self.assertEqual(layout.hole_diameter_mm, 3.4)
        self.assertEqual(layout.shank_diameter_mm, SHANK_DIAMETER_MM)
        self.assertEqual(layout.head_diameter_mm, HEAD_DIAMETER_MM)
        self.assertLess(layout.shank_diameter_mm, layout.hole_diameter_mm)
        self.assertLess(layout.hole_diameter_mm, layout.head_diameter_mm)
        self.assertTrue(layout.mic_port)
        self.assertEqual(
            (EXTENSION_SCREW_LENGTH_MM, HINGE_SCREW_LENGTH_MM, COVER_SCREW_LENGTH_MM),
            (8, 25, 6),
        )
        for length in (8, 25, 6):
            self.assertIn(length, PREFERRED_LENGTHS_MM)
            self.assertIsInstance(make_m3_shcs(length), Ok)
        with self.assertRaises(AttributeError):
            setattr(layout, "hole_diameter_mm", 3.0)

    def test_driver_range_and_deny_codes(self):
        for diameter in (40, 40.0, 45, 50):
            found = make_headset(driver_diameter=diameter)
            self.assertIsInstance(found, Ok, diameter)
            cup = found.value.earcup
            self.assertGreater(cup.cavity_diameter_mm, cup.driver_diameter_mm)
            self.assertLess(cup.sound_hole_diameter_mm, cup.driver_diameter_mm)
            self.assertGreater(cup.sound_hole_diameter_mm, 0.0)
            self.assertLess(cup.cavity_diameter_mm, cup.inner_width_mm)
            self.assertLess(cup.cavity_diameter_mm, cup.inner_height_mm)
        cases = (
            (39, "driver_diameter", HeadsetDenyCode.OUT_OF_RANGE),
            (51, "driver_diameter", HeadsetDenyCode.OUT_OF_RANGE),
            (True, "driver_diameter", HeadsetDenyCode.NOT_A_NUMBER),
            ("50", "driver_diameter", HeadsetDenyCode.NOT_A_NUMBER),
            (float("nan"), "driver_diameter", HeadsetDenyCode.NON_FINITE),
            (89, "inner_radius", HeadsetDenyCode.OUT_OF_RANGE),
            (80, "arc_deg", HeadsetDenyCode.OUT_OF_RANGE),
            (50, "travel", HeadsetDenyCode.OUT_OF_RANGE),
            (15, "extension_offset", HeadsetDenyCode.DOES_NOT_FIT),
            (6, "hinge_deg", HeadsetDenyCode.OUT_OF_RANGE),
            (13, "swivel_deg", HeadsetDenyCode.OUT_OF_RANGE),
            ("yes", "mic_port", HeadsetDenyCode.NOT_A_BOOL),
        )
        for value, field, code in cases:
            kwargs = {field: value}
            found = make_headset(**kwargs)
            self.assertIsInstance(found, Err, kwargs)
            self.assertIs(found.error.code, code)
            self.assertEqual(found.error.field, field)

    def test_deny_message(self):
        found = make_headset(driver_diameter=39)
        self.assertIsInstance(found, Err)
        self.assertEqual(
            headset_deny_message(found.error),
            "headset driver_diameter 39 is out_of_range",
        )

    def test_pcb_and_lipo_sit_in_the_bay(self):
        cup = make_headset().value.earcup
        half_w = cup.inner_width_mm / 2.0
        half_h = cup.inner_height_mm / 2.0
        packs = (
            ("pcb", cup.pcb_center_mm, PCB_LENGTH_MM, PCB_WIDTH_MM, PCB_THICKNESS_MM),
            ("lipo", cup.lipo_center_mm, LIPO_LENGTH_MM, LIPO_WIDTH_MM, LIPO_THICKNESS_MM),
        )
        for name, center, length, width, thick in packs:
            self.assertGreater(center[0] - length / 2.0, -half_w, name)
            self.assertLess(center[0] + length / 2.0, half_w, name)
            self.assertGreater(center[1] - width / 2.0, -half_h, name)
            self.assertLess(center[1] + width / 2.0, half_h, name)
            self.assertGreater(center[2] - thick / 2.0, cup.bay_z0_mm, name)
            self.assertLess(center[2] + thick / 2.0, cup.bay_z1_mm, name)
        # The cell is behind the board, and both are behind the driver.
        self.assertGreater(cup.lipo_center_mm[2], cup.pcb_center_mm[2])
        self.assertGreater(cup.pcb_center_mm[2], cup.driver_z1_mm)

    def test_fastener_axes_line_up_on_the_default_pose(self):
        self._assert_axes(make_headset().value)

    def test_offset_hinge_and_swivel_keep_the_axes_aligned(self):
        found = make_headset(
            driver_diameter=40,
            extension_offset=6,
            hinge_deg=5,
            swivel_deg=-12,
        )
        self.assertIsInstance(found, Ok)
        self._assert_axes(found.value)

    def _assert_axes(self, layout: HeadsetLayout) -> None:
        by_name = {sample.name: sample for sample in layout.samples}
        # Several samples share a name on different parts. Index by (part, name).
        located = {(sample.part, sample.name): sample for sample in layout.samples}
        joints = {joint.name: joint for joint in layout.joints}
        pairs = (
            ("right-extension", ("headband", "right-extension-void"), ("right-yoke", "extension-void")),
            ("left-extension", ("headband", "left-extension-void"), ("left-yoke", "extension-void")),
            ("right-hinge", ("right-yoke", "hinge-void"), ("right-shell", "hinge-void")),
            ("left-hinge", ("left-yoke", "hinge-void"), ("left-shell", "hinge-void")),
            ("right-cover-0", ("right-shell", "shell-hole-0"), ("right-cover", "cover-hole-0")),
            ("left-cover-2", ("left-shell", "shell-hole-2"), ("left-cover", "cover-hole-2")),
        )
        del by_name
        for joint_name, *points in pairs:
            joint = joints[joint_name]
            self.assertAlmostEqual(math.sqrt(sum(c * c for c in joint.head_direction)), 1.0, places=6)
            for key in points:
                sample = located[key]
                distance = _axis_distance(sample.point, joint.bearing, joint.head_direction)
                self.assertLess(distance, 1e-6, (joint_name, key, distance))
        self.assertEqual(layout.hole_diameter_mm, DEFAULT_HOLE_DIAMETER_MM)
        self.assertEqual(BAND_THICKNESS_MM, 4.0)

    def test_left_extension_screw_mirrors_the_right(self):
        layout = make_headset().value
        joints = {joint.name: joint for joint in layout.joints}
        right = joints["right-extension"]
        left = joints["left-extension"]
        self.assertEqual(left.bearing, (-right.bearing[0], right.bearing[1], right.bearing[2]))
        self.assertEqual(left.head_direction, (-right.head_direction[0], 0.0, 0.0))
        self.assertEqual(right.length_mm, EXTENSION_SCREW_LENGTH_MM)
        self.assertEqual(joints["right-hinge"].length_mm, HINGE_SCREW_LENGTH_MM)
        self.assertEqual(joints["right-cover-0"].length_mm, COVER_SCREW_LENGTH_MM)

    def test_create_headset_deny_does_not_import_kernel(self):
        loaded_before = "cadquery" in sys.modules
        from headset import create_headset

        with self.assertRaises(ValueError) as caught:
            create_headset(driver_diameter=39)
        self.assertEqual(str(caught.exception), "headset driver_diameter 39 is out_of_range")
        if not loaded_before:
            self.assertNotIn("cadquery", sys.modules)


if __name__ == "__main__":
    unittest.main()
