"""Pure millimetre spec for a plate with one through hole. No CadQuery.

The default hole is the ISO 273:1979 medium-series clearance hole for an
M3 screw, 3.4 mm. The default plate, 20×20×3 mm, is a demo size and is
not from a standard. Plate length, width, thickness, and hole position
are free parameters. The hole axis is parallel to the thickness and must
lie strictly inside the plate outline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .outcome import Err, Ok, Result

# ISO 273:1979 medium series, M3.
DEFAULT_HOLE_DIAMETER_MM = 3.4
# Demo plate for the committed solid. Not taken from a standard.
DEFAULT_PLATE_LENGTH_MM = 20.0
DEFAULT_PLATE_WIDTH_MM = 20.0
DEFAULT_PLATE_THICKNESS_MM = 3.0
DEFAULT_HOLE_X_MM = 0.0
DEFAULT_HOLE_Y_MM = 0.0

Field = Literal["diameter", "length", "width", "thickness", "hole_x", "hole_y"]
_SIZE_FIELDS = ("diameter", "length", "width", "thickness")


class ThroughHoleDenyCode(Enum):
    NOT_A_NUMBER = "not_a_number"
    NON_FINITE = "non_finite"
    NON_POSITIVE = "non_positive"
    DOES_NOT_FIT = "does_not_fit"


@dataclass(frozen=True, slots=True)
class ThroughHoleDeny:
    code: ThroughHoleDenyCode
    field: Field
    value: object


@dataclass(frozen=True, slots=True)
class ThroughHole:
    """Plate centred on the origin. Hole axis at (hole_x, hole_y)."""

    diameter_mm: float
    length_mm: float
    width_mm: float
    thickness_mm: float
    hole_x_mm: float
    hole_y_mm: float


def through_hole_deny_message(deny: ThroughHoleDeny) -> str:
    return f"through-hole {deny.field} {deny.value!r} is {deny.code.value}"


def volume_mm3(spec: ThroughHole) -> float:
    """Plate volume minus the cylindrical hole."""
    plate = spec.length_mm * spec.width_mm * spec.thickness_mm
    hole = math.pi * (spec.diameter_mm / 2.0) ** 2 * spec.thickness_mm
    return plate - hole


def make_through_hole(
    diameter: object,
    length: object,
    width: object,
    thickness: object,
    hole_x: object,
    hole_y: object,
) -> Result[ThroughHole, ThroughHoleDeny]:
    """Accept a finite hole that sits strictly inside a finite plate.

    Size fields are strictly positive. Hole coordinates are finite offsets
    from the plate centre and may be zero or negative. The hole is rejected
    when its circular outline touches or crosses the plate edge.
    """
    diameter_mm = _finite_positive("diameter", diameter)
    if isinstance(diameter_mm, Err):
        return diameter_mm
    length_mm = _finite_positive("length", length)
    if isinstance(length_mm, Err):
        return length_mm
    width_mm = _finite_positive("width", width)
    if isinstance(width_mm, Err):
        return width_mm
    thickness_mm = _finite_positive("thickness", thickness)
    if isinstance(thickness_mm, Err):
        return thickness_mm
    hole_x_mm = _finite_number("hole_x", hole_x)
    if isinstance(hole_x_mm, Err):
        return hole_x_mm
    hole_y_mm = _finite_number("hole_y", hole_y)
    if isinstance(hole_y_mm, Err):
        return hole_y_mm

    radius = diameter_mm.value / 2.0
    if diameter_mm.value >= length_mm.value or diameter_mm.value >= width_mm.value:
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.DOES_NOT_FIT, "diameter", diameter))
    if abs(hole_x_mm.value) + radius >= length_mm.value / 2.0:
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.DOES_NOT_FIT, "hole_x", hole_x))
    if abs(hole_y_mm.value) + radius >= width_mm.value / 2.0:
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.DOES_NOT_FIT, "hole_y", hole_y))

    return Ok(
        ThroughHole(
            diameter_mm.value,
            length_mm.value,
            width_mm.value,
            thickness_mm.value,
            hole_x_mm.value,
            hole_y_mm.value,
        )
    )


def _finite_number(field: Field, value: object) -> Result[float, ThroughHoleDeny]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.NOT_A_NUMBER, field, value))
    number = float(value)
    if not math.isfinite(number):
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.NON_FINITE, field, value))
    return Ok(number)


def _finite_positive(field: Field, value: object) -> Result[float, ThroughHoleDeny]:
    found = _finite_number(field, value)
    if isinstance(found, Err):
        return found
    if found.value <= 0.0:
        return Err(ThroughHoleDeny(ThroughHoleDenyCode.NON_POSITIVE, field, value))
    return found
