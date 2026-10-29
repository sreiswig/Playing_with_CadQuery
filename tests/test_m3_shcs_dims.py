"""In-memory tests for the M3 socket-head envelope. No CadQuery."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.m3_shcs_dims import (
    DEFAULT_LENGTH_MM,
    HEAD_DIAMETER_MM,
    HEAD_HEIGHT_MM,
    NON_PREFERRED_LENGTHS_MM,
    PREFERRED_LENGTHS_MM,
    SHANK_DIAMETER_MM,
    SOCKET_ACROSS_FLATS_MM,
    SOCKET_DEPTH_MM,
    THREAD_PITCH_MM,
    M3Shcs,
    M3ShcsDenyCode,
    m3_shcs_deny_message,
    make_m3_shcs,
    socket_across_corners_mm,
    volume_mm3,
)
from cq_artifacts.outcome import Err, Ok


class M3ShcsDimsTests(unittest.TestCase):
    def test_cited_envelope_and_default_length(self):
        self.assertEqual(HEAD_DIAMETER_MM, 5.5)
        self.assertEqual(HEAD_HEIGHT_MM, 3.0)
        self.assertEqual(SOCKET_ACROSS_FLATS_MM, 2.5)
        self.assertEqual(SOCKET_DEPTH_MM, 1.3)
        self.assertEqual(SHANK_DIAMETER_MM, 3.0)
        self.assertEqual(THREAD_PITCH_MM, 0.5)
        self.assertEqual(DEFAULT_LENGTH_MM, 10)
        self.assertIn(DEFAULT_LENGTH_MM, PREFERRED_LENGTHS_MM)
        found = make_m3_shcs(DEFAULT_LENGTH_MM)
        self.assertIsInstance(found, Ok)
        spec = found.value
        self.assertIsInstance(spec, M3Shcs)
        self.assertEqual(
            (
                spec.head_diameter_mm,
                spec.head_height_mm,
                spec.socket_across_flats_mm,
                spec.socket_depth_mm,
                spec.shank_diameter_mm,
                spec.length_mm,
            ),
            (5.5, 3.0, 2.5, 1.3, 3.0, 10.0),
        )
        head = math.pi * (2.75 ** 2) * 3.0
        shank = math.pi * (1.5 ** 2) * 10.0
        socket = (math.sqrt(3.0) / 2.0) * (2.5 ** 2) * 1.3
        self.assertAlmostEqual(volume_mm3(spec), head + shank - socket)
        corners = socket_across_corners_mm()
        self.assertAlmostEqual(corners, 2.5 / math.cos(math.pi / 6.0))
        self.assertGreater(corners, 2.873)
        with self.assertRaises(AttributeError):
            setattr(spec, "length_mm", 12)

    def test_allowed_lengths_are_iso_888_preferred_from_5_to_30(self):
        self.assertEqual(
            PREFERRED_LENGTHS_MM,
            (5, 6, 8, 10, 12, 16, 20, 25, 30),
        )
        self.assertEqual(DEFAULT_LENGTH_MM, 10)
        self.assertEqual(
            NON_PREFERRED_LENGTHS_MM,
            (
                2.5, 7, 9, 11, 14, 18, 22, 28, 32, 38,
                75, 85, 95, 105, 115, 125, 170, 190,
            ),
        )
        for length in PREFERRED_LENGTHS_MM:
            with self.subTest(length=length):
                found = make_m3_shcs(length)
                self.assertIsInstance(found, Ok)
                self.assertEqual(found.value.length_mm, float(length))
        for length in NON_PREFERRED_LENGTHS_MM:
            with self.subTest(length=length):
                found = make_m3_shcs(length)
                self.assertIsInstance(found, Err)
                self.assertIs(found.error.code, M3ShcsDenyCode.NOT_PREFERRED_LENGTH)

    def test_float_preferred_length_matches_the_int(self):
        found = make_m3_shcs(16.0)
        self.assertIsInstance(found, Ok)
        self.assertEqual(found.value.length_mm, 16.0)

    def test_deny_codes(self):
        cases = (
            ("nope", M3ShcsDenyCode.NOT_A_NUMBER),
            (True, M3ShcsDenyCode.NOT_A_NUMBER),
            (float("nan"), M3ShcsDenyCode.NON_FINITE),
            (float("-inf"), M3ShcsDenyCode.NON_FINITE),
            (0, M3ShcsDenyCode.NON_POSITIVE),
            (-10, M3ShcsDenyCode.NON_POSITIVE),
            (2, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (4, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (14, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (10.5, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (35, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (40, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (500, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
            (1000, M3ShcsDenyCode.NOT_PREFERRED_LENGTH),
        )
        for value, code in cases:
            with self.subTest(value=value):
                found = make_m3_shcs(value)
                self.assertIsInstance(found, Err)
                self.assertIs(found.error.code, code)
                self.assertEqual(found.error.field, "length")
                if isinstance(value, float) and math.isnan(value):
                    self.assertIsInstance(found.error.value, float)
                    self.assertTrue(math.isnan(found.error.value))
                else:
                    self.assertEqual(found.error.value, value)

    def test_deny_message(self):
        found = make_m3_shcs(14)
        self.assertIsInstance(found, Err)
        self.assertEqual(
            m3_shcs_deny_message(found.error),
            "m3-shcs length 14 is not_preferred_length",
        )

    def test_create_m3_shcs_deny_does_not_import_kernel(self):
        loaded_before = "cadquery" in sys.modules
        from m3_shcs import create_m3_shcs

        with self.assertRaises(ValueError) as caught:
            create_m3_shcs(length=14)
        self.assertEqual(str(caught.exception), "m3-shcs length 14 is not_preferred_length")
        if not loaded_before:
            self.assertNotIn("cadquery", sys.modules)
