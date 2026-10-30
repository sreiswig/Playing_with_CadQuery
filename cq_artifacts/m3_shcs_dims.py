"""Pure millimetre envelope for an M3 socket head cap screw. No CadQuery.

Cited limits, not a product drawing beyond them:

- ISO 4762 plain head: dk max 5.5 mm, k max 3.0 mm.
- ISO 4762 hexagon socket: nominal width across flats s = 2.5 mm, depth
  t min = 1.3 mm. Across-corners is the regular hexagon of that s.
- ISO 262: M3×0.5 coarse pitch. The shank diameter is the nominal major
  diameter, 3.0 mm. The pitch is not a modeled helix.
- ISO 888:2012 Table 1: nominal length is the under-head length for a
  screw whose bearing face is perpendicular to the axis. Accepted lengths
  are the unbracketed (preferred) values from 5 mm through 30 mm:
  5, 6, 8, 10, 12, 16, 20, 25, 30. Bracketed lengths, and preferred
  lengths outside that range, are rejected.

Not an ISO 4017 hexagon-head bolt.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .outcome import Err, Ok, Result

# ISO 4762 M3 plain-head envelope and ISO 262 nominal diameter.
HEAD_DIAMETER_MM = 5.5
HEAD_HEIGHT_MM = 3.0
SOCKET_ACROSS_FLATS_MM = 2.5
SOCKET_DEPTH_MM = 1.3
SHANK_DIAMETER_MM = 3.0
THREAD_PITCH_MM = 0.5

# ISO 888:2012 Table 1 unbracketed (preferred) lengths from 5 mm through 30 mm.
PREFERRED_LENGTHS_MM: tuple[int, ...] = (
    5,
    6,
    8,
    10,
    12,
    16,
    20,
    25,
    30,
)

# ISO 888:2012 Table 1 lengths in parentheses.
NON_PREFERRED_LENGTHS_MM: tuple[float, ...] = (
    2.5,
    7,
    9,
    11,
    14,
    18,
    22,
    28,
    32,
    38,
    75,
    85,
    95,
    105,
    115,
    125,
    170,
    190,
)

DEFAULT_LENGTH_MM = 10


class M3ShcsDenyCode(Enum):
    NOT_A_NUMBER = "not_a_number"
    NON_FINITE = "non_finite"
    NON_POSITIVE = "non_positive"
    NOT_PREFERRED_LENGTH = "not_preferred_length"


@dataclass(frozen=True, slots=True)
class M3ShcsDeny:
    code: M3ShcsDenyCode
    field: str
    value: object


@dataclass(frozen=True, slots=True)
class M3Shcs:
    """Head on +Z from the bearing face. Shank runs from z=0 to z=-length."""

    length_mm: float
    head_diameter_mm: float
    head_height_mm: float
    socket_across_flats_mm: float
    socket_depth_mm: float
    shank_diameter_mm: float


def m3_shcs_deny_message(deny: M3ShcsDeny) -> str:
    return f"m3-shcs {deny.field} {deny.value!r} is {deny.code.value}"


def socket_across_corners_mm(across_flats_mm: float = SOCKET_ACROSS_FLATS_MM) -> float:
    """Circumdiameter of a regular hexagon with width across flats ``s``."""
    return across_flats_mm / math.cos(math.pi / 6.0)


def volume_mm3(spec: M3Shcs) -> float:
    """Head cylinder plus shank cylinder, minus the hexagonal socket."""
    head = math.pi * (spec.head_diameter_mm / 2.0) ** 2 * spec.head_height_mm
    shank = math.pi * (spec.shank_diameter_mm / 2.0) ** 2 * spec.length_mm
    # Regular hexagon area = (√3 / 2) * s².
    socket = (
        (math.sqrt(3.0) / 2.0)
        * spec.socket_across_flats_mm ** 2
        * spec.socket_depth_mm
    )
    return head + shank - socket


def make_m3_shcs(length: object) -> Result[M3Shcs, M3ShcsDeny]:
    """Accept one ISO 888:2012 preferred length from 5 mm through 30 mm."""
    if isinstance(length, bool) or not isinstance(length, (int, float)):
        return Err(M3ShcsDeny(M3ShcsDenyCode.NOT_A_NUMBER, "length", length))
    number = float(length)
    if not math.isfinite(number):
        return Err(M3ShcsDeny(M3ShcsDenyCode.NON_FINITE, "length", length))
    if number <= 0.0:
        return Err(M3ShcsDeny(M3ShcsDenyCode.NON_POSITIVE, "length", length))
    if number not in PREFERRED_LENGTHS_MM:
        return Err(M3ShcsDeny(M3ShcsDenyCode.NOT_PREFERRED_LENGTH, "length", length))
    return Ok(
        M3Shcs(
            length_mm=number,
            head_diameter_mm=HEAD_DIAMETER_MM,
            head_height_mm=HEAD_HEIGHT_MM,
            socket_across_flats_mm=SOCKET_ACROSS_FLATS_MM,
            socket_depth_mm=SOCKET_DEPTH_MM,
            shank_diameter_mm=SHANK_DIAMETER_MM,
        )
    )
