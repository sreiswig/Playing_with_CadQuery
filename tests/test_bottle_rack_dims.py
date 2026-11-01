"""In-memory tests for the bottle rack. No CadQuery."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.bottle_rack_dims import (  # noqa: E402
    ABOVE_GAP_MM,
    DEFAULT_BOTTLE_DIAMETER_MM,
    DEFAULT_BOTTLE_LENGTH_MM,
    EXTRUSION_MM,
    NOMINAL_FULL_BOTTLE_KG,
    TARGET_DEPTH_MM,
    TARGET_HEIGHT_MM,
    TARGET_WIDTH_MM,
    bottle_rack_deny_message,
    cut_list_csv,
    cut_list_json,
    make_bottle_rack,
)
from cq_artifacts.outcome import Err, Ok  # noqa: E402
from cq_artifacts.through_hole_dims import DEFAULT_HOLE_DIAMETER_MM  # noqa: E402

CUT_LIST_JSON = ROOT / "artifacts" / "bottle-rack" / "cut-list.json"
CUT_LIST_CSV = ROOT / "artifacts" / "bottle-rack" / "cut-list.csv"


class BottleRackDimsTests(unittest.TestCase):
    def test_default_module_is_fifteen_bottles_near_the_target_envelope(self):
        layout = self._default()
        self.assertEqual(layout.lanes, 3)
        self.assertEqual(layout.depth, 5)
        self.assertEqual(layout.slots, 15)
        self.assertEqual(layout.slope_deg, 7.0)
        self.assertEqual(layout.bottle_diameter_mm, DEFAULT_BOTTLE_DIAMETER_MM)
        self.assertEqual(layout.bottle_length_mm, DEFAULT_BOTTLE_LENGTH_MM)
        self.assertEqual(layout.nominal_full_bottle_kg, NOMINAL_FULL_BOTTLE_KG)
        self.assertEqual(layout.nominal_payload_kg, 15 * 2.1)
        self.assertAlmostEqual(layout.carcass_width_mm, 380.0, places=6)
        self.assertAlmostEqual(layout.carcass_depth_mm, 678.871, places=2)
        self.assertAlmostEqual(layout.carcass_height_mm, 524.458, places=2)
        for got, target in (
            (layout.carcass_width_mm, TARGET_WIDTH_MM),
            (layout.carcass_depth_mm, TARGET_DEPTH_MM),
            (layout.carcass_height_mm, TARGET_HEIGHT_MM),
        ):
            self.assertLess(abs(got - target) / target, 0.02, (got, target))
        self.assertEqual(layout.tile_pitch_mm, layout.carcass_width_mm)
        self.assertGreater(layout.stack_engagement_mm, 0.0)
        self.assertEqual(layout.hole_diameter_mm, DEFAULT_HOLE_DIAMETER_MM)
        self.assertEqual(len(layout.bottles), 15)
        self.assertEqual(len(layout.guides), 6)
        self.assertEqual(len(layout.gates), 3)

    def test_deck_slope_matches_the_parameter(self):
        layout = self._default()
        half = layout.deck_along_mm / 2.0
        top = layout.thickness_mm / 2.0
        front = layout.deck_world(0.0, -half, top, 0)
        rear = layout.deck_world(0.0, half, top, 0)
        rise = rear[2] - front[2]
        run = rear[1] - front[1]
        self.assertGreater(run, 0.0)
        self.assertAlmostEqual(math.degrees(math.atan2(rise, run)), layout.slope_deg, places=6)
        self.assertGreater(rear[2], front[2])

    def test_lane_clearance_and_bottle_gap_are_positive(self):
        layout = self._default()
        front = next(bottle for bottle in layout.bottles if bottle.lane == 0 and bottle.index == 0)
        above = layout.deck_world(0.0, 0.0, layout.thickness_mm / 2.0 + 1.0, 1)
        # The next deck's front is one pitch above this deck. The stored bottle
        # stays below that deck by at least the designed gap.
        self.assertGreater(layout.lane_pitch_mm - layout.thickness_mm, front.radius_mm)
        self.assertGreater(above[2], front.center[2] + front.radius_mm + ABOVE_GAP_MM - 1.0)
        self.assertGreater(layout.stack_toe_mm, 0.0)
        self.assertGreater(layout.pin_protrusion_mm, 0.0)
        self.assertLess(layout.bbox.z0, 0.0)
        self.assertGreater(layout.bbox.x1, layout.carcass_width_mm)

    def test_cut_list_follows_lanes_depth_and_diameter(self):
        layout = self._default()
        pieces = {piece.name: piece for piece in layout.pieces}
        self.assertEqual(pieces["deck"].qty, 3)
        self.assertEqual(pieces["lane-guide"].qty, 6)
        self.assertEqual(pieces["outlet-gate"].qty, 3)
        self.assertEqual(pieces["side-panel"].qty, 2)
        self.assertEqual(pieces["stack-foot"].qty, 4)
        self.assertEqual(pieces["post"].qty, 2)
        self.assertEqual(pieces["rail"].qty, 2)
        self.assertEqual(pieces["post"].width_mm, EXTRUSION_MM)
        self.assertEqual(pieces["post"].thickness_mm, EXTRUSION_MM)
        self.assertEqual(pieces["rail"].width_mm, EXTRUSION_MM)
        self.assertAlmostEqual(pieces["deck"].length_mm, layout.deck_along_mm, places=3)
        self.assertEqual(pieces["deck"].material, "plywood")
        self.assertEqual(pieces["lane-guide"].material, "PLA or PETG")
        self.assertIn("2020", pieces["post"].material)

        wider = make_bottle_rack(bottle_diameter=120.0)
        self.assertIsInstance(wider, Ok)
        wider_deck = next(piece for piece in wider.value.pieces if piece.name == "deck")
        self.assertGreater(wider_deck.length_mm, pieces["deck"].length_mm)

        fewer = make_bottle_rack(lanes=2, depth=4)
        self.assertIsInstance(fewer, Ok)
        self.assertEqual(fewer.value.slots, 8)
        fewer_deck = next(piece for piece in fewer.value.pieces if piece.name == "deck")
        self.assertEqual(fewer_deck.qty, 2)
        guide_screws = next(item for item in fewer.value.hardware if item.name.startswith("M3x12"))
        self.assertEqual(guide_screws.qty, 3 * 2 * 2)

    def test_committed_cut_list_matches_the_default_parameters(self):
        self.assertEqual(CUT_LIST_JSON.read_text(encoding="utf-8"), cut_list_json())
        self.assertEqual(CUT_LIST_CSV.read_text(encoding="utf-8"), cut_list_csv())
        text = CUT_LIST_JSON.read_text(encoding="utf-8")
        self.assertIn("nominal_full_bottle_kg", text)
        self.assertIn("not a measured load rating", text)
        self.assertIn("deck", text)

    def test_slope_and_counts_reject_values_outside_the_design_range(self):
        for kwargs, field in (
            ({"slope_deg": 5.9}, "slope_deg"),
            ({"slope_deg": 8.1}, "slope_deg"),
            ({"bottle_diameter": 89.0}, "bottle_diameter"),
            ({"bottle_length": 361.0}, "bottle_length"),
            ({"lanes": 0}, "lanes"),
            ({"lanes": 5}, "lanes"),
            ({"depth": 1}, "depth"),
            ({"thickness": 5.0}, "thickness"),
        ):
            found = make_bottle_rack(**kwargs)
            self.assertIsInstance(found, Err, kwargs)
            self.assertEqual(
                bottle_rack_deny_message(found.error),
                f"bottle rack {field} {kwargs[field]!r} is out_of_range",
            )
        for kwargs, field in (
            ({"slope_deg": True}, "slope_deg"),
            ({"lanes": True}, "lanes"),
            ({"lanes": 3.0}, "lanes"),
            ({"depth": 5.0}, "depth"),
        ):
            found = make_bottle_rack(**kwargs)
            self.assertIsInstance(found, Err, kwargs)
            self.assertIn("not_a_number", bottle_rack_deny_message(found.error))
        found = make_bottle_rack(slope_deg=float("nan"))
        self.assertIsInstance(found, Err)
        self.assertIn("non_finite", bottle_rack_deny_message(found.error))

    def test_endpoints_of_the_slope_range_build(self):
        for slope in (6.0, 8.0):
            found = make_bottle_rack(slope_deg=slope)
            self.assertIsInstance(found, Ok, slope)
            self.assertEqual(found.value.slope_deg, slope)

    def test_create_deny_does_not_need_a_kernel(self):
        from bottle_rack import create_bottle_rack

        with self.assertRaises(ValueError) as caught:
            create_bottle_rack(slope_deg=5)
        self.assertEqual(str(caught.exception), "bottle rack slope_deg 5 is out_of_range")

    def _default(self):
        found = make_bottle_rack()
        self.assertIsInstance(found, Ok)
        return found.value


if __name__ == "__main__":
    unittest.main()
