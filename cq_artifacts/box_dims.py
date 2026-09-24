"""Pure millimetre extents for the parametric box. No CadQuery."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .outcome import Err, Ok, Result

DEFAULT_BOX_MM = 10.0

Axis = Literal["length", "width", "height"]


class BoxDenyCode(Enum):
    NOT_A_NUMBER = "not_a_number"
    NON_FINITE = "non_finite"
    NON_POSITIVE = "non_positive"


@dataclass(frozen=True, slots=True)
class BoxDeny:
    code: BoxDenyCode
    field: Axis
    value: object


@dataclass(frozen=True, slots=True)
class BoxSize:
    length_mm: float
    width_mm: float
    height_mm: float


def box_deny_message(deny: BoxDeny) -> str:
    return f"box {deny.field} {deny.value!r} is {deny.code.value}"


def volume_mm3(size: BoxSize) -> float:
    return size.length_mm * size.width_mm * size.height_mm


def make_box_size(
    length: object,
    width: object,
    height: object,
) -> Result[BoxSize, BoxDeny]:
    """Accept a finite, strictly positive length, width, and height in mm."""
    length_mm = _finite_positive("length", length)
    if isinstance(length_mm, Err):
        return length_mm
    width_mm = _finite_positive("width", width)
    if isinstance(width_mm, Err):
        return width_mm
    height_mm = _finite_positive("height", height)
    if isinstance(height_mm, Err):
        return height_mm
    return Ok(BoxSize(length_mm.value, width_mm.value, height_mm.value))


def _finite_positive(field: Axis, value: object) -> Result[float, BoxDeny]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return Err(BoxDeny(BoxDenyCode.NOT_A_NUMBER, field, value))
    number = float(value)
    if not math.isfinite(number):
        return Err(BoxDeny(BoxDenyCode.NON_FINITE, field, value))
    if number <= 0.0:
        return Err(BoxDeny(BoxDenyCode.NON_POSITIVE, field, value))
    return Ok(number)
