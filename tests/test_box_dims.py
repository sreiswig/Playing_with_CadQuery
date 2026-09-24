"""In-memory tests for box extents. No CadQuery."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.box_dims import (
    DEFAULT_BOX_MM,
    BoxDenyCode,
    BoxSize,
    box_deny_message,
    make_box_size,
    volume_mm3,
)
from cq_artifacts.outcome import Err, Ok


class BoxDimsTests(unittest.TestCase):
    def test_default_extent_matches_catalog_note(self):
        self.assertEqual(DEFAULT_BOX_MM, 10.0)
        found = make_box_size(DEFAULT_BOX_MM, DEFAULT_BOX_MM, DEFAULT_BOX_MM)
        self.assertIsInstance(found, Ok)
        self.assertEqual(volume_mm3(found.value), 1000.0)

    def test_accepts_ints_and_computes_volume(self):
        found = make_box_size(2, 3, 4)
        self.assertIsInstance(found, Ok)
        size = found.value
        self.assertIsInstance(size, BoxSize)
        self.assertEqual((size.length_mm, size.width_mm, size.height_mm), (2.0, 3.0, 4.0))
        self.assertEqual(volume_mm3(size), 24.0)
        with self.assertRaises(AttributeError):
            setattr(size, "length_mm", 9)

    def test_deny_codes_in_axis_order(self):
        cases = (
            (("nope", 1, 1), "length", BoxDenyCode.NOT_A_NUMBER),
            ((True, 1, 1), "length", BoxDenyCode.NOT_A_NUMBER),
            ((float("nan"), 1, 1), "length", BoxDenyCode.NON_FINITE),
            ((1, float("inf"), 1), "width", BoxDenyCode.NON_FINITE),
            ((1, 1, 0), "height", BoxDenyCode.NON_POSITIVE),
            ((1, -2, float("nan")), "width", BoxDenyCode.NON_POSITIVE),
            ((-1, -2, float("nan")), "length", BoxDenyCode.NON_POSITIVE),
        )
        for args, field, code in cases:
            with self.subTest(args=args):
                found = make_box_size(*args)
                self.assertIsInstance(found, Err)
                self.assertIs(found.error.code, code)
                self.assertEqual(found.error.field, field)
                self.assertEqual(found.error.value, args[{"length": 0, "width": 1, "height": 2}[field]])

    def test_deny_message(self):
        found = make_box_size(-1, 10, 10)
        self.assertIsInstance(found, Err)
        self.assertEqual(box_deny_message(found.error), "box length -1 is non_positive")

    def test_create_box_deny_does_not_import_kernel(self):
        loaded_before = "cadquery" in sys.modules
        from box import create_box

        with self.assertRaises(ValueError) as caught:
            create_box(length=0)
        self.assertEqual(str(caught.exception), "box length 0 is non_positive")
        if not loaded_before:
            self.assertNotIn("cadquery", sys.modules)
