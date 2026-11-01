"""Geometry fit tests for the headset kit. Skipped when CadQuery is absent."""

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

from cq_artifacts.headset_dims import (  # noqa: E402
    BAND_THICKNESS_MM,
    DEFAULT_INNER_RADIUS_MM,
    LIPO_LENGTH_MM,
    LIPO_THICKNESS_MM,
    LIPO_WIDTH_MM,
    PCB_LENGTH_MM,
    PCB_THICKNESS_MM,
    PCB_WIDTH_MM,
    make_headset,
)
from cq_artifacts.outcome import Ok  # noqa: E402


def _solid(shape):
    import cadquery as cq

    return shape.val() if isinstance(shape, cq.Workplane) else shape


def _intersect_volume(a, b) -> float:
    return float(_solid(a).intersect(_solid(b)).Volume())


@unittest.skipUnless(cadquery is not None, "cadquery is not installed")
class HeadsetFitTests(unittest.TestCase):
    def test_local_shell_matches_driver_electronics_and_fastener_probes(self):
        from headset import _aabb, _build_cover, _build_shell, _cylinder

        for diameter in (40, 50):
            found = make_headset(driver_diameter=diameter)
            self.assertIsInstance(found, Ok)
            layout = found.value
            shell = _build_shell(layout, mic_port=True)
            cover = _build_cover(layout)
            solids = {"shell": _solid(shell), "cover": _solid(cover)}
            for sample in layout.earcup.samples:
                got = solids[sample.part].isInside(sample.point)
                self.assertEqual(got, sample.inside, (diameter, sample.part, sample.name))
            self.assertEqual(len(solids["shell"].Solids()), 1)
            self.assertTrue(solids["shell"].isValid())

            cup = layout.earcup
            z0 = cup.driver_z0_mm + 0.05
            z1 = cup.driver_z1_mm - 0.05
            driver = _cylinder((0.0, 0.0, (z0 + z1) / 2.0), diameter / 2.0, z1 - z0)
            self.assertLess(_intersect_volume(driver, shell), 1e-3)
            tight = _cylinder(
                (0.0, 0.0, (z0 + z1) / 2.0),
                cup.cavity_diameter_mm / 2.0 + 0.4,
                z1 - z0,
            )
            self.assertGreater(_intersect_volume(tight, shell), 100.0)

            pcb = cup.pcb_center_mm
            lipo = cup.lipo_center_mm
            pcb_box = _aabb(
                pcb[0] - PCB_LENGTH_MM / 2.0,
                pcb[0] + PCB_LENGTH_MM / 2.0,
                pcb[1] - PCB_WIDTH_MM / 2.0,
                pcb[1] + PCB_WIDTH_MM / 2.0,
                pcb[2] - PCB_THICKNESS_MM / 2.0,
                pcb[2] + PCB_THICKNESS_MM / 2.0,
            )
            lipo_box = _aabb(
                lipo[0] - LIPO_LENGTH_MM / 2.0,
                lipo[0] + LIPO_LENGTH_MM / 2.0,
                lipo[1] - LIPO_WIDTH_MM / 2.0,
                lipo[1] + LIPO_WIDTH_MM / 2.0,
                lipo[2] - LIPO_THICKNESS_MM / 2.0,
                lipo[2] + LIPO_THICKNESS_MM / 2.0,
            )
            self.assertLess(_intersect_volume(pcb_box, shell), 1e-3)
            self.assertLess(_intersect_volume(lipo_box, shell), 1e-3)

    def test_plain_cup_has_no_mic_port(self):
        from headset import _build_shell

        layout = make_headset().value
        plain = _solid(_build_shell(layout, mic_port=False))
        self.assertTrue(plain.isInside(layout.earcup.mic_wall_mm))

    def test_default_assembly_probes_and_clearance(self):
        self._assert_pose()

    def test_extended_hinged_swivelled_kit_still_fits(self):
        self._assert_pose(
            driver_diameter=40,
            extension_offset=6,
            hinge_deg=5,
            swivel_deg=-12,
        )

    def _assert_pose(self, **kwargs) -> None:
        from headset import assemble_parts

        found = make_headset(**kwargs)
        self.assertIsInstance(found, Ok)
        layout = found.value
        parts = assemble_parts(layout)
        for sample in layout.samples:
            solid = _solid(parts[sample.part])
            self.assertEqual(
                solid.isInside(sample.point),
                sample.inside,
                (sample.part, sample.name, sample.point),
            )
        clear = (
            ("right-extension", "headband"),
            ("right-extension", "right-yoke"),
            ("left-extension", "headband"),
            ("left-extension", "left-yoke"),
            ("right-hinge", "right-yoke"),
            ("right-hinge", "right-shell"),
            ("left-hinge", "left-shell"),
            ("right-cover-0", "right-cover"),
            ("right-cover-0", "right-shell"),
            ("left-cover-3", "left-cover"),
            ("left-cover-3", "left-shell"),
            ("right-yoke", "right-shell"),
            ("right-yoke", "headband"),
            ("right-shell", "headband"),
            ("right-cover", "right-shell"),
            ("left-shell", "headband"),
        )
        for left, right in clear:
            volume = _intersect_volume(parts[left], parts[right])
            self.assertLess(volume, 0.05, (left, right, volume))
        self.assertEqual(len(_solid(parts["headband"]).Solids()), 1)
        self.assertEqual(len(_solid(parts["right-yoke"]).Solids()), 1)
        self.assertEqual(len(_solid(parts["right-shell"]).Solids()), 1)

    def test_catalog_builders_export_valid_parts(self):
        from headset import (
            create_headset,
            create_headset_earcup,
            create_headset_headband,
            create_headset_yoke,
        )

        earcup = _solid(create_headset_earcup())
        self.assertTrue(earcup.isValid())
        self.assertEqual(len(earcup.Solids()), 2)
        self.assertGreater(earcup.Volume(), 0.0)

        band = _solid(create_headset_headband())
        self.assertTrue(band.isValid())
        self.assertEqual(len(band.Solids()), 1)
        crown = DEFAULT_INNER_RADIUS_MM + BAND_THICKNESS_MM / 2.0
        self.assertTrue(band.isInside((0.0, crown, 0.0)))
        self.assertFalse(band.isInside((0.0, DEFAULT_INNER_RADIUS_MM - 1.0, 0.0)))

        yoke = _solid(create_headset_yoke())
        self.assertTrue(yoke.isValid())
        self.assertEqual(len(yoke.Solids()), 1)
        # Recentred extension hole: axis through the origin, along X.
        self.assertFalse(yoke.isInside((0.0, 0.0, 0.0)))
        self.assertTrue(yoke.isInside((0.0, 0.0, 2.0)))
        self.assertFalse(yoke.isInside((0.0, 0.0, 1.5)))

        kit = _solid(create_headset())
        self.assertTrue(kit.isValid())
        self.assertGreaterEqual(len(kit.Solids()), 19)
        self.assertGreater(kit.Volume(), 0.0)


if __name__ == "__main__":
    unittest.main()
