"""In-memory tests for the through-hole plate. No CadQuery."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.outcome import Err, Ok
from cq_artifacts.through_hole_dims import (
    DEFAULT_HOLE_DIAMETER_MM,
    DEFAULT_HOLE_X_MM,
    DEFAULT_HOLE_Y_MM,
    DEFAULT_PLATE_LENGTH_MM,
    DEFAULT_PLATE_THICKNESS_MM,
    DEFAULT_PLATE_WIDTH_MM,
    ThroughHole,
    ThroughHoleDenyCode,
    make_through_hole,
    through_hole_deny_message,
    volume_mm3,
)


def _defaults(**overrides):
    args = {
        "diameter": DEFAULT_HOLE_DIAMETER_MM,
        "length": DEFAULT_PLATE_LENGTH_MM,
        "width": DEFAULT_PLATE_WIDTH_MM,
        "thickness": DEFAULT_PLATE_THICKNESS_MM,
        "hole_x": DEFAULT_HOLE_X_MM,
        "hole_y": DEFAULT_HOLE_Y_MM,
    }
    args.update(overrides)
    return (
        args["diameter"],
        args["length"],
        args["width"],
        args["thickness"],
        args["hole_x"],
        args["hole_y"],
    )


class ThroughHoleDimsTests(unittest.TestCase):
    def test_default_is_iso_273_medium_m3(self):
        self.assertEqual(DEFAULT_HOLE_DIAMETER_MM, 3.4)
        self.assertEqual(
            (
                DEFAULT_PLATE_LENGTH_MM,
                DEFAULT_PLATE_WIDTH_MM,
                DEFAULT_PLATE_THICKNESS_MM,
            ),
            (20.0, 20.0, 3.0),
        )
        self.assertEqual((DEFAULT_HOLE_X_MM, DEFAULT_HOLE_Y_MM), (0.0, 0.0))
        found = make_through_hole(*_defaults())
        self.assertIsInstance(found, Ok)
        spec = found.value
        self.assertIsInstance(spec, ThroughHole)
        self.assertEqual(spec.diameter_mm, 3.4)
        plate = 20.0 * 20.0 * 3.0
        hole = math.pi * (1.7 ** 2) * 3.0
        self.assertAlmostEqual(volume_mm3(spec), plate - hole)
        with self.assertRaises(AttributeError):
            setattr(spec, "diameter_mm", 4.0)

    def test_offset_hole_keeps_the_same_volume(self):
        centred = make_through_hole(*_defaults())
        offset = make_through_hole(*_defaults(hole_x=5, hole_y=-2))
        self.assertIsInstance(centred, Ok)
        self.assertIsInstance(offset, Ok)
        self.assertEqual(volume_mm3(centred.value), volume_mm3(offset.value))
        self.assertEqual((offset.value.hole_x_mm, offset.value.hole_y_mm), (5.0, -2.0))

    def test_deny_codes_in_field_order(self):
        cases = (
            ({"diameter": "nope"}, "diameter", ThroughHoleDenyCode.NOT_A_NUMBER),
            ({"diameter": True}, "diameter", ThroughHoleDenyCode.NOT_A_NUMBER),
            ({"diameter": float("nan")}, "diameter", ThroughHoleDenyCode.NON_FINITE),
            ({"length": float("inf")}, "length", ThroughHoleDenyCode.NON_FINITE),
            ({"width": 0}, "width", ThroughHoleDenyCode.NON_POSITIVE),
            ({"thickness": -1}, "thickness", ThroughHoleDenyCode.NON_POSITIVE),
            ({"hole_x": None}, "hole_x", ThroughHoleDenyCode.NOT_A_NUMBER),
            ({"hole_y": float("nan")}, "hole_y", ThroughHoleDenyCode.NON_FINITE),
            ({"diameter": 20, "length": 20}, "diameter", ThroughHoleDenyCode.DOES_NOT_FIT),
            ({"hole_x": 9}, "hole_x", ThroughHoleDenyCode.DOES_NOT_FIT),
            ({"hole_y": -9}, "hole_y", ThroughHoleDenyCode.DOES_NOT_FIT),
        )
        for overrides, field, code in cases:
            with self.subTest(overrides=overrides):
                args = _defaults(**overrides)
                found = make_through_hole(*args)
                self.assertIsInstance(found, Err)
                self.assertIs(found.error.code, code)
                self.assertEqual(found.error.field, field)

    def test_deny_message(self):
        found = make_through_hole(*_defaults(hole_x=9))
        self.assertIsInstance(found, Err)
        self.assertEqual(
            through_hole_deny_message(found.error),
            "through-hole hole_x 9 is does_not_fit",
        )

    def test_create_through_hole_deny_does_not_import_kernel(self):
        loaded_before = "cadquery" in sys.modules
        from through_hole import create_through_hole

        with self.assertRaises(ValueError) as caught:
            create_through_hole(diameter=0)
        self.assertEqual(str(caught.exception), "through-hole diameter 0 is non_positive")
        if not loaded_before:
            self.assertNotIn("cadquery", sys.modules)
