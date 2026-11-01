"""Geometry fit tests for the bottle rack. Skipped when CadQuery is absent."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import cadquery
except ImportError:
    cadquery = None  # type: ignore[assignment]

from cq_artifacts.bottle_rack_dims import make_bottle_rack  # noqa: E402
from cq_artifacts.outcome import Ok  # noqa: E402


def _solid(shape):
    import cadquery as cq

    return shape.val() if isinstance(shape, cq.Workplane) else shape


@unittest.skipUnless(cadquery is not None, "cadquery is not installed")
class BottleRackFitTests(unittest.TestCase):
    def test_default_parts_match_the_probe_points(self):
        self._assert_module()

    def test_shorter_shallower_module_still_fits(self):
        self._assert_module(lanes=2, depth=3, slope_deg=6.0, thickness=9.0)

    def test_printable_guide_and_gate_match_their_probes(self):
        from bottle_rack import create_bottle_rack_gate, create_bottle_rack_guide

        layout = make_bottle_rack().value
        guide = _solid(create_bottle_rack_guide())
        gate = _solid(create_bottle_rack_gate())
        self.assertTrue(guide.isValid())
        self.assertTrue(gate.isValid())
        self.assertEqual(len(guide.Solids()), 1)
        self.assertEqual(len(gate.Solids()), 1)
        for sample in layout.guide_samples:
            self.assertEqual(guide.isInside(sample.point), sample.inside, sample.name)
        for sample in layout.gate_samples:
            self.assertEqual(gate.isInside(sample.point), sample.inside, sample.name)
        bounds = guide.BoundingBox()
        self.assertAlmostEqual(bounds.xlen, layout.guide_width_mm, places=3)
        self.assertAlmostEqual(bounds.ylen, layout.deck_along_mm, places=3)
        self.assertAlmostEqual(bounds.zlen, layout.guide_rail_height_mm, places=3)

    def _assert_module(self, **kwargs) -> None:
        from bottle_rack import assemble_parts

        found = make_bottle_rack(**kwargs)
        self.assertIsInstance(found, Ok)
        layout = found.value
        parts = assemble_parts(layout)
        solids = {name: _solid(shape) for name, shape in parts.items()}
        for name, solid in solids.items():
            self.assertTrue(solid.isValid(), name)
            self.assertGreater(solid.Volume(), 0.0, name)

        for sample in layout.samples:
            if sample.part == "lane":
                for name, solid in solids.items():
                    self.assertFalse(
                        solid.isInside(sample.point),
                        (sample.name, name, sample.point),
                    )
                continue
            self.assertIn(sample.part, solids, sample.part)
            self.assertEqual(
                solids[sample.part].isInside(sample.point),
                sample.inside,
                (sample.part, sample.name, sample.point),
            )

        self._assert_bottles_clear(layout, solids)
        kit = _solid(_compound(solids.values()))
        self.assertTrue(kit.isValid())
        self.assertGreaterEqual(len(kit.Solids()), len(solids))
        bounds = kit.BoundingBox()
        self.assertAlmostEqual(bounds.xmin, layout.bbox.x0, delta=0.2)
        self.assertAlmostEqual(bounds.xmax, layout.bbox.x1, delta=0.2)
        self.assertAlmostEqual(bounds.ymin, layout.bbox.y0, delta=0.2)
        self.assertAlmostEqual(bounds.ymax, layout.bbox.y1, delta=0.2)
        self.assertAlmostEqual(bounds.zmin, layout.bbox.z0, delta=0.2)
        self.assertAlmostEqual(bounds.zmax, layout.bbox.z1, delta=0.2)

    def _assert_bottles_clear(self, layout, solids) -> None:
        """A slightly smaller bottle cylinder misses the lane it sits in."""
        import cadquery as cq

        for bottle in layout.bottles:
            if bottle.index not in (0, layout.depth - 1):
                continue
            radius = bottle.radius_mm - 0.8
            length = bottle.length_mm - 2.0
            center = bottle.center
            bottle_solid = (
                cq.Workplane("YZ")
                .circle(radius)
                .extrude(length)
                .translate((center[0] - length / 2.0, center[1], center[2]))
            )
            for name in (
                f"deck-{bottle.lane}",
                f"guide-left-{bottle.lane}",
                f"guide-right-{bottle.lane}",
                f"gate-{bottle.lane}",
                "base",
                "back",
            ):
                volume = float(bottle_solid.val().intersect(solids[name]).Volume())
                self.assertLess(volume, 1.0, (bottle.lane, bottle.index, name, volume))


def _compound(shapes):
    import cadquery as cq

    return cq.Compound.makeCompound(list(shapes))


if __name__ == "__main__":
    unittest.main()
