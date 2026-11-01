"""Pure millimetre envelope for an ISO 4032 style 1 M3 hex nut. No CadQuery.

Cited limits, not a product drawing beyond them. The M3 row is the one
published by the AmesWeb ISO 4032 chart and by Fuller Fasteners' ISO 4032
table (the table that notes it replaces DIN 934). Both give the same row,
and the CDE Fasteners ISO 4032 style 1 chart agrees on ``s``, ``e``, and
``m``:

- pitch ``P`` = 0.5 mm
- width across flats ``s`` max = nominal = 5.5 mm, ``s`` min = 5.32 mm
- width across corners ``e`` min = 6.01 mm
- nut height ``m`` max = 2.4 mm, ``m`` min = 2.15 mm
- face-hole diameter ``da`` min = 3 mm, ``da`` max = 3.45 mm

ISO 4032:2023 moved sizes below M5 into an informative annex. The 2023
revision notes do not change ``s`` or ``m`` for M3; the row above is the
one those tables still publish.

The solid uses the maximum outer envelope only:

- across flats is ``s`` max
- height is ``m`` max
- across corners is the regular hexagon of that ``s`` max (the same
  helper the M3 SHCS socket uses), which is wider than ``e`` min
- the bore is ``da`` min, the ISO 262 nominal major diameter already
  stored as the M3 SHCS shank diameter. The pitch is not swept into a
  helix

``s`` min, ``m`` min, ``e`` min, ``da`` max, the chamfer ``c``, the washer
face ``dw``, and the wrenching height ``mw`` are not modeled. No chamfer.
This is style 1 (ISO 4032), not an ISO 4033 style 2 nut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .m3_shcs_dims import SHANK_DIAMETER_MM, THREAD_PITCH_MM, socket_across_corners_mm

# ISO 4032 M3 style 1 maximum envelope.
ACROSS_FLATS_MM = 5.5
HEIGHT_MM = 2.4
# da min, equal to the ISO 262 nominal major diameter (M3 SHCS shank).
BORE_DIAMETER_MM = SHANK_DIAMETER_MM
# ISO 4032 / ISO 262 coarse pitch. Not a modeled helix.
PITCH_MM = THREAD_PITCH_MM

# ISO 4032 M3 minimum across corners. The solid is the regular hexagon of
# s max, so its corners are wider than this minimum.
ACROSS_CORNERS_MIN_MM = 6.01


@dataclass(frozen=True, slots=True)
class M3Nut:
    """Hex prism from z=0 to z=height. Bore is parallel to Z."""

    across_flats_mm: float
    height_mm: float
    bore_diameter_mm: float


def across_corners_mm(across_flats_mm: float = ACROSS_FLATS_MM) -> float:
    """Circumdiameter of the regular hexagon of width across flats ``s``."""
    return socket_across_corners_mm(across_flats_mm)


def volume_mm3(spec: M3Nut) -> float:
    """Hexagonal prism minus the cylindrical bore."""
    # Regular hexagon area = (√3 / 2) * s².
    prism = (math.sqrt(3.0) / 2.0) * spec.across_flats_mm ** 2 * spec.height_mm
    bore = math.pi * (spec.bore_diameter_mm / 2.0) ** 2 * spec.height_mm
    return prism - bore


def make_m3_nut() -> M3Nut:
    """The style 1 envelope. ISO 4032 fixes the M3 row, so there is no input."""
    return M3Nut(
        across_flats_mm=ACROSS_FLATS_MM,
        height_mm=HEIGHT_MM,
        bore_diameter_mm=BORE_DIAMETER_MM,
    )
