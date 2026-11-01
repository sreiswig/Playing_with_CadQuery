"""Pure millimetre layout for a modular gravity-fed bottle rack. No CadQuery.

One module stores 2 L PET bottles on their sides, rolling downhill in three
lanes stacked five deep. Defaults are design inputs, not measured results:

- bottle 110 mm diameter by 310 mm long, 2.1 kg full
- 3 lanes × 5 deep (15 bottles)
- 7° slope (allowed 6° to 8°)
- 12 mm plywood
- carcass about 380 × 680 × 520 mm

The frame is plywood plus a 20×20 mm 2020 outer envelope (Misumi HFS5-2020 /
80-20). The T-slot profile is not modeled. Lane guides and lift gates are
printed. Clearance holes are the ISO 273 medium M3 diameter from
``through_hole_dims`` (3.4 mm). Screw lengths in the pick list are ISO 888
preferred lengths checked with ``make_m3_shcs``.

Each module has locating feet and hooked pockets for a 2-high stack. The
foot's forward toe sits under a lip, so the upper module has to slide back
before it lifts off. Pins and pockets on the sides let modules tile; the
tile pitch is the carcass width. Inlet and outlet sensor holes and an
ESP32 hole pattern share a cable groove on the right side panel. The 2.1 kg
figure is only the nominal payload input.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .m3_shcs_dims import make_m3_shcs
from .outcome import Err, Ok, Result
from .through_hole_dims import DEFAULT_HOLE_DIAMETER_MM

# Nominal 2 L PET bottle. Design inputs for the default module.
DEFAULT_BOTTLE_DIAMETER_MM = 110.0
DEFAULT_BOTTLE_LENGTH_MM = 310.0
DEFAULT_LANES = 3
DEFAULT_DEPTH = 5
DEFAULT_SLOPE_DEG = 7.0
DEFAULT_THICKNESS_MM = 12.0
NOMINAL_FULL_BOTTLE_KG = 2.1

# Targets the default carcass is designed toward. Not a measured envelope.
TARGET_WIDTH_MM = 380.0
TARGET_DEPTH_MM = 680.0
TARGET_HEIGHT_MM = 520.0

EXTRUSION_MM = 20.0
GUIDE_WIDTH_MM = 18.0
GUIDE_BASE_MM = 3.0
GUIDE_RAIL_HEIGHT_MM = 16.0
GUIDE_RAIL_THICKNESS_MM = 5.0
END_GAP_MM = 5.0
BOTTLE_GAP_MM = 6.0
DECK_FRONT_MARGIN_MM = 20.0
DECK_REAR_MARGIN_MM = 22.0
ABOVE_GAP_MM = 16.0
FRONT_ZONE_MM = 36.0
FRONT_LIFT_MM = 40.0
REAR_GAP_MM = 18.0
HEADROOM_MM = 22.0
STRIP_Y_MM = 78.0
GATE_THICKNESS_MM = 6.0
GATE_WIDTH_MAX_MM = 160.0
APRON_DROP_MM = 8.0
FOOT_MM = 16.0
TOE_MM = 8.0
POCKET_CLEAR_MM = 0.4
FOOT_INSET_X_MM = 42.0
FOOT_INSET_Y_MM = 46.0
PIN_DIAMETER_MM = 7.6
PIN_POCKET_DIAMETER_MM = 8.4
CABLE_WIDTH_MM = 10.0
CABLE_DEPTH_MM = 5.0
ESP_DX_MM = 26.0
ESP_DY_MM = 48.0
GUIDE_SCREW_LENGTH_MM = 12
SENSOR_SCREW_LENGTH_MM = 10
GUIDE_SCREWS_EACH = 3
# Cutter bleed past an open face. Not a part dimension.
CUTTER_PAST_MM = 0.6

DIAMETER_MIN_MM = 90.0
DIAMETER_MAX_MM = 140.0
LENGTH_MIN_MM = 240.0
LENGTH_MAX_MM = 360.0
LANES_MIN = 1
LANES_MAX = 4
DEPTH_MIN = 2
DEPTH_MAX = 8
SLOPE_MIN_DEG = 6.0
SLOPE_MAX_DEG = 8.0
THICKNESS_MIN_MM = 6.0
THICKNESS_MAX_MM = 18.0

Vec3 = tuple[float, float, float]
Field = Literal[
    "bottle_diameter",
    "bottle_length",
    "lanes",
    "depth",
    "slope_deg",
    "thickness",
    "assembly",
]
_FLOAT_FIELDS = ("bottle_diameter", "bottle_length", "slope_deg", "thickness")
_INT_FIELDS = ("lanes", "depth")


class BottleRackDenyCode(Enum):
    NOT_A_NUMBER = "not_a_number"
    NON_FINITE = "non_finite"
    OUT_OF_RANGE = "out_of_range"
    DOES_NOT_FIT = "does_not_fit"


@dataclass(frozen=True, slots=True)
class BottleRackDeny:
    code: BottleRackDenyCode
    field: Field
    value: object


@dataclass(frozen=True, slots=True)
class Box:
    """Axis-aligned box. Intervals are half-open in spirit but closed in CAD."""

    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def cz(self) -> float:
        return (self.z0 + self.z1) / 2.0


@dataclass(frozen=True, slots=True)
class Hole:
    part: str
    name: str
    origin: Vec3
    axis: Literal["x", "y", "z"]
    diameter: float
    length: float


@dataclass(frozen=True, slots=True)
class Sample:
    part: str
    name: str
    point: Vec3
    inside: bool


@dataclass(frozen=True, slots=True)
class BottlePose:
    """Cylinder standing in for one bottle. The bottle is not a rack part."""

    lane: int
    index: int
    center: Vec3
    radius_mm: float
    length_mm: float


@dataclass(frozen=True, slots=True)
class CutPiece:
    name: str
    material: str
    qty: int
    length_mm: float
    width_mm: float
    thickness_mm: float
    notes: str


@dataclass(frozen=True, slots=True)
class Hardware:
    name: str
    spec: str
    qty: int
    notes: str


@dataclass(frozen=True, slots=True)
class GuidePlace:
    side: Literal["left", "right"]
    lane: int
    origin: Vec3


@dataclass(frozen=True, slots=True)
class GatePlace:
    lane: int
    x0: float
    y1: float
    z0: float


@dataclass(frozen=True, slots=True)
class BottleRackLayout:
    bottle_diameter_mm: float
    bottle_length_mm: float
    lanes: int
    depth: int
    slope_deg: float
    thickness_mm: float
    hole_diameter_mm: float
    carcass_width_mm: float
    carcass_depth_mm: float
    carcass_height_mm: float
    bbox: Box
    slots: int
    nominal_full_bottle_kg: float
    nominal_payload_kg: float
    deck_along_mm: float
    deck_width_mm: float
    deck_ty_mm: float
    deck_tz_mm: float
    lane_pitch_mm: float
    y_front_mm: float
    z_front_mm: float
    deck_y_max_mm: float
    guide_width_mm: float
    guide_rail_height_mm: float
    guide_rail_thickness_mm: float
    guide_base_mm: float
    gate_width_mm: float
    gate_height_mm: float
    gate_thickness_mm: float
    gate_notch_width_mm: float
    gate_notch_height_mm: float
    extrusion_mm: float
    stack_engagement_mm: float
    stack_toe_mm: float
    tile_pitch_mm: float
    pin_protrusion_mm: float
    panels: dict[str, Box]
    cuts: dict[str, tuple[Box, ...]]
    holes: tuple[Hole, ...]
    feet: tuple[tuple[Box, Box], ...]
    pins: tuple[Hole, ...]
    guides: tuple[GuidePlace, ...]
    gates: tuple[GatePlace, ...]
    bottles: tuple[BottlePose, ...]
    samples: tuple[Sample, ...]
    guide_samples: tuple[Sample, ...]
    gate_samples: tuple[Sample, ...]
    pieces: tuple[CutPiece, ...]
    hardware: tuple[Hardware, ...]

    def deck_world(self, local_x: float, local_y: float, local_z: float, lane: int) -> Vec3:
        """Map a centred deck-box point into the module frame."""
        y, z = _rot_x(local_y, local_z, self.slope_deg)
        return (
            self.carcass_width_mm / 2.0 + local_x,
            self.deck_ty_mm + y,
            self.deck_tz_mm + lane * self.lane_pitch_mm + z,
        )


def bottle_rack_deny_message(deny: BottleRackDeny) -> str:
    return f"bottle rack {deny.field} {deny.value!r} is {deny.code.value}"


def _rot_x(y: float, z: float, deg: float) -> tuple[float, float]:
    """Right-hand rotation about +X, matching CadQuery's ``rotate`` about +X."""
    angle = math.radians(deg)
    c, s = math.cos(angle), math.sin(angle)
    return (y * c - z * s, y * s + z * c)


def _slope_basis(deg: float) -> tuple[Vec3, Vec3]:
    angle = math.radians(deg)
    # Up-slope along the deck, and the deck's top normal.
    along = (0.0, math.cos(angle), math.sin(angle))
    normal = (0.0, -math.sin(angle), math.cos(angle))
    return along, normal


def _r(value: float) -> float:
    rounded = round(float(value), 3)
    if rounded == 0.0:
        return 0.0
    return rounded


def _box_of(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Box:
    return Box(x0, x1, y0, y1, z0, z1)


def _center(box: Box) -> Vec3:
    return (box.cx, box.cy, box.cz)


def _require_float(value: object, field: Field, low: float, high: float) -> Result[float, BottleRackDeny]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return Err(BottleRackDeny(BottleRackDenyCode.NOT_A_NUMBER, field, value))
    number = float(value)
    if not math.isfinite(number):
        return Err(BottleRackDeny(BottleRackDenyCode.NON_FINITE, field, value))
    if number < low or number > high:
        return Err(BottleRackDeny(BottleRackDenyCode.OUT_OF_RANGE, field, value))
    return Ok(number)


def _require_int(value: object, field: Field, low: int, high: int) -> Result[int, BottleRackDeny]:
    if isinstance(value, bool) or not isinstance(value, int):
        return Err(BottleRackDeny(BottleRackDenyCode.NOT_A_NUMBER, field, value))
    if value < low or value > high:
        return Err(BottleRackDeny(BottleRackDenyCode.OUT_OF_RANGE, field, value))
    return Ok(value)


def _fit(reason: str) -> Err[BottleRackDeny]:
    return Err(BottleRackDeny(BottleRackDenyCode.DOES_NOT_FIT, "assembly", reason))


def make_bottle_rack(
    bottle_diameter: float = DEFAULT_BOTTLE_DIAMETER_MM,
    bottle_length: float = DEFAULT_BOTTLE_LENGTH_MM,
    lanes: int = DEFAULT_LANES,
    depth: int = DEFAULT_DEPTH,
    slope_deg: float = DEFAULT_SLOPE_DEG,
    thickness: float = DEFAULT_THICKNESS_MM,
) -> Result[BottleRackLayout, BottleRackDeny]:
    """Layout, cut list, and probe points for one module. Units: millimetres."""
    diameter = _require_float(bottle_diameter, "bottle_diameter", DIAMETER_MIN_MM, DIAMETER_MAX_MM)
    if isinstance(diameter, Err):
        return diameter
    length = _require_float(bottle_length, "bottle_length", LENGTH_MIN_MM, LENGTH_MAX_MM)
    if isinstance(length, Err):
        return length
    lane_count = _require_int(lanes, "lanes", LANES_MIN, LANES_MAX)
    if isinstance(lane_count, Err):
        return lane_count
    depth_count = _require_int(depth, "depth", DEPTH_MIN, DEPTH_MAX)
    if isinstance(depth_count, Err):
        return depth_count
    slope = _require_float(slope_deg, "slope_deg", SLOPE_MIN_DEG, SLOPE_MAX_DEG)
    if isinstance(slope, Err):
        return slope
    panel = _require_float(thickness, "thickness", THICKNESS_MIN_MM, THICKNESS_MAX_MM)
    if isinstance(panel, Err):
        return panel

    for screw_length in (GUIDE_SCREW_LENGTH_MM, SENSOR_SCREW_LENGTH_MM):
        sized = make_m3_shcs(screw_length)
        if isinstance(sized, Err):
            return _fit(f"M3x{screw_length} is not an allowed ISO 888 length")

    return _layout(
        diameter=diameter.value,
        length=length.value,
        lanes=lane_count.value,
        depth=depth_count.value,
        slope=slope.value,
        thickness=panel.value,
    )


def _layout(
    *,
    diameter: float,
    length: float,
    lanes: int,
    depth: int,
    slope: float,
    thickness: float,
) -> Result[BottleRackLayout, BottleRackDeny]:
    radius = diameter / 2.0
    angle = math.radians(slope)
    carcass_width = 2.0 * thickness + 2.0 * GUIDE_WIDTH_MM + 2.0 * END_GAP_MM + length
    inner_x0 = thickness
    inner_x1 = carcass_width - thickness
    inner_width = inner_x1 - inner_x0

    deck_along = (
        DECK_FRONT_MARGIN_MM
        + DECK_REAR_MARGIN_MM
        + depth * diameter
        + (depth - 1) * BOTTLE_GAP_MM
    )
    # Vertical gap from a bottle's top to the next deck underside is ABOVE_GAP.
    # The circle's top is R above its centre, and the centre is R·cos above the deck.
    lane_pitch = radius * (1.0 + math.cos(angle)) + ABOVE_GAP_MM + thickness
    y_front = FRONT_ZONE_MM
    z_front = thickness + FRONT_LIFT_MM
    front_local_y, front_local_z = _rot_x(-deck_along / 2.0, thickness / 2.0, slope)
    deck_ty = y_front - front_local_y
    deck_tz = z_front - front_local_z

    def deck_world(local_x: float, local_y: float, local_z: float, lane: int) -> Vec3:
        y, z = _rot_x(local_y, local_z, slope)
        return (carcass_width / 2.0 + local_x, deck_ty + y, deck_tz + lane * lane_pitch + z)

    corner_ys = [
        deck_world(0.0, local_y, local_z, 0)[1]
        for local_y in (-deck_along / 2.0, deck_along / 2.0)
        for local_z in (-thickness / 2.0, thickness / 2.0)
    ]
    deck_y_max = max(corner_ys)
    y_panel0 = deck_y_max + REAR_GAP_MM
    carcass_depth = y_panel0 + thickness
    post_y1 = carcass_depth
    post_y0 = post_y1 - EXTRUSION_MM
    if post_y0 < deck_y_max + 2.0:
        return _fit("rear post collides with the lane decks")

    _, normal = _slope_basis(slope)
    bottles: list[BottlePose] = []
    for lane in range(lanes):
        for index in range(depth):
            contact_along = DECK_FRONT_MARGIN_MM + radius + index * (diameter + BOTTLE_GAP_MM)
            local_y = -deck_along / 2.0 + contact_along
            contact = deck_world(0.0, local_y, thickness / 2.0, lane)
            center = (
                contact[0] + normal[0] * radius,
                contact[1] + normal[1] * radius,
                contact[2] + normal[2] * radius,
            )
            bottles.append(
                BottlePose(
                    lane=lane,
                    index=index,
                    center=center,
                    radius_mm=radius,
                    length_mm=length,
                )
            )

    rear = bottles[-1]
    bottle_top = max(b.center[2] + b.radius_mm for b in bottles)
    top_gate_height = 0.55 * diameter
    top_gate_top = z_front + (lanes - 1) * lane_pitch - 4.0 + top_gate_height
    headroom = max(HEADROOM_MM, thickness + 8.0)
    carcass_height = max(bottle_top, top_gate_top) + headroom

    if carcass_depth < 2.0 * STRIP_Y_MM + 10.0:
        return _fit("module is too shallow for front and rear stack strips")

    engagement = min(8.0, thickness - 2.0)
    if engagement < 4.0:
        return _fit("plywood is too thin for the stack pocket")
    tile_depth = min(10.0, thickness - 2.0)
    pin_protrusion = tile_depth - 1.0
    cable_depth = min(CABLE_DEPTH_MM, thickness - 3.0)
    if cable_depth < 2.0:
        return _fit("plywood is too thin for the cable groove")

    # --- axis-aligned carcass ---
    panels: dict[str, Box] = {
        "left-side": _box_of(0.0, thickness, 0.0, carcass_depth, 0.0, carcass_height),
        "right-side": _box_of(
            carcass_width - thickness, carcass_width, 0.0, carcass_depth, 0.0, carcass_height
        ),
        "base": _box_of(inner_x0, inner_x1, 0.0, carcass_depth, 0.0, thickness),
        "apron": _box_of(inner_x0, inner_x1, 0.0, thickness, thickness, z_front - APRON_DROP_MM),
        "top-front": _box_of(
            inner_x0,
            inner_x1,
            0.0,
            STRIP_Y_MM,
            carcass_height - thickness,
            carcass_height,
        ),
        "top-rear": _box_of(
            inner_x0,
            inner_x1,
            carcass_depth - STRIP_Y_MM,
            carcass_depth,
            carcass_height - thickness,
            carcass_height,
        ),
        "post-left": _box_of(
            inner_x0,
            inner_x0 + EXTRUSION_MM,
            post_y0,
            post_y1,
            thickness,
            carcass_height - thickness,
        ),
        "post-right": _box_of(
            inner_x1 - EXTRUSION_MM,
            inner_x1,
            post_y0,
            post_y1,
            thickness,
            carcass_height - thickness,
        ),
        "rail-front": _box_of(
            inner_x0,
            inner_x1,
            28.0,
            28.0 + EXTRUSION_MM,
            carcass_height - thickness - EXTRUSION_MM,
            carcass_height - thickness,
        ),
        "rail-rear": _box_of(
            inner_x0,
            inner_x1,
            carcass_depth - STRIP_Y_MM + 8.0,
            carcass_depth - STRIP_Y_MM + 8.0 + EXTRUSION_MM,
            carcass_height - thickness - EXTRUSION_MM,
            carcass_height - thickness,
        ),
    }
    back_x0 = inner_x0 + EXTRUSION_MM
    back_x1 = inner_x1 - EXTRUSION_MM
    panels["back"] = _box_of(
        back_x0,
        back_x1,
        y_panel0,
        carcass_depth,
        thickness,
        carcass_height - thickness,
    )

    rail_front = panels["rail-front"]
    if rail_front.z0 <= top_gate_top + 2.0:
        return _fit("front rail meets the outlet gate")
    if panels["apron"].z1 <= panels["apron"].z0 + 8.0:
        return _fit("front apron has no height")

    # --- stack feet and hooked pockets ---
    foot_centers = (
        (FOOT_INSET_X_MM, FOOT_INSET_Y_MM),
        (carcass_width - FOOT_INSET_X_MM, FOOT_INSET_Y_MM),
        (FOOT_INSET_X_MM, carcass_depth - FOOT_INSET_Y_MM),
        (carcass_width - FOOT_INSET_X_MM, carcass_depth - FOOT_INSET_Y_MM),
    )
    half = FOOT_MM / 2.0
    feet: list[tuple[Box, Box]] = []
    cuts: dict[str, list[Box]] = {name: [] for name in panels}
    for cx, cy in foot_centers:
        main = _box_of(cx - half, cx + half, cy - half, cy + half, -engagement, 0.0)
        toe = _box_of(
            cx - half,
            cx + half,
            cy - half - TOE_MM,
            cy - half + 0.2,
            -engagement,
            -engagement / 2.0,
        )
        feet.append((main, toe))
        part = "top-front" if cy < carcass_depth / 2.0 else "top-rear"
        lower = _box_of(
            cx - half - POCKET_CLEAR_MM,
            cx + half + POCKET_CLEAR_MM,
            cy - half - TOE_MM - POCKET_CLEAR_MM,
            cy + half + POCKET_CLEAR_MM,
            carcass_height - engagement,
            carcass_height - engagement / 2.0 + 0.2,
        )
        upper = _box_of(
            cx - half - POCKET_CLEAR_MM,
            cx + half + POCKET_CLEAR_MM,
            cy - half - POCKET_CLEAR_MM,
            cy + half + TOE_MM + POCKET_CLEAR_MM,
            carcass_height - engagement / 2.0 - 0.2,
            carcass_height + CUTTER_PAST_MM,
        )
        host = panels[part]
        if (
            lower.x0 < host.x0
            or lower.x1 > host.x1
            or lower.y0 < host.y0
            or upper.y1 > host.y1
        ):
            return _fit("stack pocket falls outside the top strip")
        cuts[part].extend((lower, upper))

    # --- cable groove and sensor holes on the right side panel ---
    trunk_z = thickness + 18.0
    side = panels["right-side"]
    cuts["right-side"].append(
        _box_of(
            side.x0 - CUTTER_PAST_MM,
            side.x0 + cable_depth,
            16.0,
            carcass_depth - 16.0,
            trunk_z - CABLE_WIDTH_MM / 2.0,
            trunk_z + CABLE_WIDTH_MM / 2.0,
        )
    )

    holes: list[Hole] = []
    hole_d = DEFAULT_HOLE_DIAMETER_MM
    windows: list[Box] = []
    for lane in range(lanes):
        rear_top = deck_world(0.0, deck_along / 2.0, thickness / 2.0, lane)
        window_z0 = rear_top[2] + 6.0
        window_z1 = window_z0 + diameter * 0.50
        window_w = min(length * 0.50, (back_x1 - back_x0) - 36.0)
        if window_w < 40.0:
            return _fit("back panel is too narrow for a loading window")
        back = panels["back"]
        if window_z1 > back.z1 - 8.0:
            window_z1 = back.z1 - 8.0
        if window_z1 - window_z0 < 24.0:
            return _fit("loading window does not fit on the back panel")
        window = _box_of(
            carcass_width / 2.0 - window_w / 2.0,
            carcass_width / 2.0 + window_w / 2.0,
            back.y0 - CUTTER_PAST_MM,
            back.y1 + CUTTER_PAST_MM,
            window_z0,
            window_z1,
        )
        if window.x0 < back.x0 + 8.0 or window.x1 > back.x1 - 8.0:
            return _fit("loading window meets a rear post")
        windows.append(window)
        cuts["back"].append(window)

        inlet_y = deck_y_max - 16.0
        inlet_z = rear_top[2] + 0.30 * diameter
        if not (24.0 < inlet_y < carcass_depth - 24.0 and thickness + 6.0 < inlet_z < carcass_height - 6.0):
            return _fit("inlet sensor hole falls outside the side panel")
        for offset, tag in ((-7.0, "a"), (7.0, "b")):
            holes.append(
                Hole(
                    part="right-side",
                    name=f"inlet-{lane}-{tag}",
                    origin=(side.cx, inlet_y + offset, inlet_z),
                    axis="x",
                    diameter=hole_d,
                    length=thickness + 2.0 * CUTTER_PAST_MM,
                )
            )
            z0 = min(trunk_z, inlet_z) - CABLE_WIDTH_MM / 2.0
            z1 = max(trunk_z, inlet_z) + CABLE_WIDTH_MM / 2.0
            cuts["right-side"].append(
                _box_of(
                    side.x0 - CUTTER_PAST_MM,
                    side.x0 + cable_depth,
                    inlet_y + offset - CABLE_WIDTH_MM / 2.0,
                    inlet_y + offset + CABLE_WIDTH_MM / 2.0,
                    z0,
                    z1,
                )
            )
        outlet_y = y_front - 14.0
        outlet_z = z_front + lane * lane_pitch + 0.32 * diameter
        if not (12.0 < outlet_y < carcass_depth - 12.0 and thickness + 6.0 < outlet_z < carcass_height - 6.0):
            return _fit("outlet sensor hole falls outside the side panel")
        for offset, tag in ((-7.0, "a"), (7.0, "b")):
            holes.append(
                Hole(
                    part="right-side",
                    name=f"outlet-{lane}-{tag}",
                    origin=(side.cx, outlet_y + offset, outlet_z),
                    axis="x",
                    diameter=hole_d,
                    length=thickness + 2.0 * CUTTER_PAST_MM,
                )
            )
            riser_y = outlet_y + offset
            z0 = min(trunk_z, outlet_z) - CABLE_WIDTH_MM / 2.0
            z1 = max(trunk_z, outlet_z) + CABLE_WIDTH_MM / 2.0
            cuts["right-side"].append(
                _box_of(
                    side.x0 - CUTTER_PAST_MM,
                    side.x0 + cable_depth,
                    riser_y - CABLE_WIDTH_MM / 2.0,
                    riser_y + CABLE_WIDTH_MM / 2.0,
                    z0,
                    z1,
                )
            )

    # ESP32 pattern on the right side, above the cable trunk and clear of the outlet.
    esp_y = 96.0
    esp_z = trunk_z + 36.0
    for sy in (-ESP_DY_MM / 2.0, ESP_DY_MM / 2.0):
        for sz in (-ESP_DX_MM / 2.0, ESP_DX_MM / 2.0):
            origin = (side.cx, esp_y + sy, esp_z + sz)
            if not (
                side.y0 + 8.0 < origin[1] < side.y1 - 8.0
                and side.z0 + 8.0 < origin[2] < side.z1 - 8.0
            ):
                return _fit("ESP32 holes fall outside the right side panel")
            holes.append(
                Hole(
                    part="right-side",
                    name=f"esp-{len([h for h in holes if h.name.startswith('esp')])}",
                    origin=origin,
                    axis="x",
                    diameter=hole_d,
                    length=thickness + 2.0 * CUTTER_PAST_MM,
                )
            )
    cuts["right-side"].append(
        _box_of(
            side.x0 - CUTTER_PAST_MM,
            side.x0 + cable_depth,
            esp_y - CABLE_WIDTH_MM / 2.0,
            esp_y + CABLE_WIDTH_MM / 2.0,
            trunk_z - CABLE_WIDTH_MM / 2.0,
            esp_z + CABLE_WIDTH_MM / 2.0,
        )
    )

    # Tile pockets (left) and pins (right). Pins are separate solids.
    pin_places = (
        (carcass_depth * 0.30, carcass_height * 0.46),
        (carcass_depth * 0.56, carcass_height * 0.72),
    )
    pins: list[Hole] = []
    for index, (py, pz) in enumerate(pin_places):
        holes.append(
            Hole(
                part="left-side",
                name=f"tile-pocket-{index}",
                origin=((tile_depth - CUTTER_PAST_MM) / 2.0, py, pz),
                axis="x",
                diameter=PIN_POCKET_DIAMETER_MM,
                length=tile_depth + CUTTER_PAST_MM,
            )
        )
        insertion = tile_depth - 1.0
        bore_inner = carcass_width - insertion
        bore_outer = carcass_width + CUTTER_PAST_MM
        holes.append(
            Hole(
                part="right-side",
                name=f"tile-bore-{index}",
                origin=((bore_inner + bore_outer) / 2.0, py, pz),
                axis="x",
                diameter=PIN_POCKET_DIAMETER_MM,
                length=bore_outer - bore_inner,
            )
        )
        pin_x0 = carcass_width - insertion + 0.4
        pin_x1 = carcass_width + pin_protrusion
        pins.append(
            Hole(
                part=f"pin-{index}",
                name=f"pin-{index}",
                origin=((pin_x0 + pin_x1) / 2.0, py, pz),
                axis="x",
                diameter=PIN_DIAMETER_MM,
                length=pin_x1 - pin_x0,
            )
        )

    guides = tuple(
        GuidePlace(
            side=side_name,
            lane=lane,
            origin=(
                inner_x0 if side_name == "left" else inner_x1 - GUIDE_WIDTH_MM,
                y_front,
                z_front + lane * lane_pitch,
            ),
        )
        for lane in range(lanes)
        for side_name in ("left", "right")
    )
    gate_width = min(GATE_WIDTH_MAX_MM, length - 40.0)
    gate_height = top_gate_height
    notch_w = 36.0
    notch_h = min(22.0, gate_height * 0.36)
    gates = tuple(
        GatePlace(
            lane=lane,
            x0=carcass_width / 2.0 - gate_width / 2.0,
            y1=y_front - 1.0,
            z0=z_front + lane * lane_pitch - 4.0,
        )
        for lane in range(lanes)
    )

    # Bottle stay clear of the gate, the back panel, and the next deck.
    gate_ymax = y_front - 1.0
    for bottle in bottles:
        if bottle.index == 0 and bottle.center[1] - bottle.radius_mm <= gate_ymax + 1.0:
            return _fit("front bottle intersects the outlet gate")
        if bottle.center[1] + bottle.radius_mm >= y_panel0 - 2.0:
            return _fit("rear bottle intersects the back panel")
        if bottle.center[0] - length / 2.0 <= inner_x0 + GUIDE_WIDTH_MM:
            return _fit("bottle end intersects a lane guide")
        if bottle.center[2] + bottle.radius_mm >= carcass_height - thickness - 2.0:
            return _fit("bottle meets the top strip")
    if bottles[0].center[2] - radius <= panels["base"].z1:
        return _fit("bottle meets the base")

    samples = _samples(
        panels=panels,
        cuts=cuts,
        holes=holes,
        feet=feet,
        pins=pins,
        bottles=bottles,
        gates=gates,
        guides=guides,
        windows=windows,
        trunk_z=trunk_z,
        cable_depth=cable_depth,
        side=side,
        carcass_height=carcass_height,
        engagement=engagement,
        deck_world=deck_world,
        thickness=thickness,
        lanes=lanes,
        slope=slope,
    )
    guide_samples = _guide_samples(deck_along, hole_d)
    gate_samples = _gate_samples(gate_width, gate_height, GATE_THICKNESS_MM, notch_w, notch_h)
    pieces, hardware = _cut_list(
        thickness=thickness,
        carcass_width=carcass_width,
        carcass_depth=carcass_depth,
        carcass_height=carcass_height,
        inner_width=inner_width,
        deck_along=deck_along,
        lanes=lanes,
        gate_width=gate_width,
        gate_height=gate_height,
        engagement=engagement,
        pin_protrusion=pin_protrusion,
        tile_depth=tile_depth,
        panels=panels,
        back_width=back_x1 - back_x0,
    )

    layout = BottleRackLayout(
        bottle_diameter_mm=diameter,
        bottle_length_mm=length,
        lanes=lanes,
        depth=depth,
        slope_deg=slope,
        thickness_mm=thickness,
        hole_diameter_mm=hole_d,
        carcass_width_mm=carcass_width,
        carcass_depth_mm=carcass_depth,
        carcass_height_mm=carcass_height,
        bbox=_box_of(
            0.0,
            carcass_width + pin_protrusion,
            0.0,
            carcass_depth,
            -engagement,
            carcass_height,
        ),
        slots=lanes * depth,
        nominal_full_bottle_kg=NOMINAL_FULL_BOTTLE_KG,
        nominal_payload_kg=lanes * depth * NOMINAL_FULL_BOTTLE_KG,
        deck_along_mm=deck_along,
        deck_width_mm=inner_width,
        deck_ty_mm=deck_ty,
        deck_tz_mm=deck_tz,
        lane_pitch_mm=lane_pitch,
        y_front_mm=y_front,
        z_front_mm=z_front,
        deck_y_max_mm=deck_y_max,
        guide_width_mm=GUIDE_WIDTH_MM,
        guide_rail_height_mm=GUIDE_RAIL_HEIGHT_MM,
        guide_rail_thickness_mm=GUIDE_RAIL_THICKNESS_MM,
        guide_base_mm=GUIDE_BASE_MM,
        gate_width_mm=gate_width,
        gate_height_mm=gate_height,
        gate_thickness_mm=GATE_THICKNESS_MM,
        gate_notch_width_mm=notch_w,
        gate_notch_height_mm=notch_h,
        extrusion_mm=EXTRUSION_MM,
        stack_engagement_mm=engagement,
        stack_toe_mm=TOE_MM,
        tile_pitch_mm=carcass_width,
        pin_protrusion_mm=pin_protrusion,
        panels=panels,
        cuts={name: tuple(boxes) for name, boxes in cuts.items()},
        holes=tuple(holes),
        feet=tuple(feet),
        pins=tuple(pins),
        guides=guides,
        gates=gates,
        bottles=tuple(bottles),
        samples=samples,
        guide_samples=guide_samples,
        gate_samples=gate_samples,
        pieces=pieces,
        hardware=hardware,
    )
    return Ok(layout)


def _samples(
    *,
    panels: dict[str, Box],
    cuts: dict[str, list[Box]],
    holes: list[Hole],
    feet: list[tuple[Box, Box]],
    pins: list[Hole],
    bottles: list[BottlePose],
    gates: tuple[GatePlace, ...],
    guides: tuple[GuidePlace, ...],
    windows: list[Box],
    trunk_z: float,
    cable_depth: float,
    side: Box,
    carcass_height: float,
    engagement: float,
    deck_world,
    thickness: float,
    lanes: int,
    slope: float,
) -> tuple[Sample, ...]:
    found: list[Sample] = []
    for name, box in panels.items():
        found.append(Sample(name, "material", _center(box), True))
    # Deck centres. local (0,0,0) is the middle of the plywood.
    for lane in range(lanes):
        found.append(Sample(f"deck-{lane}", "material", deck_world(0.0, 0.0, 0.0, lane), True))
        found.append(
            Sample(
                f"deck-{lane}",
                "above",
                deck_world(0.0, 0.0, thickness / 2.0 + 3.0, lane),
                False,
            )
        )
    gate = gates[0]
    found.append(
        Sample(
            "gate-0",
            "stop",
            (
                gate.x0 + 20.0,
                gate.y1 - GATE_THICKNESS_MM / 2.0,
                gate.z0 + 8.0,
            ),
            True,
        )
    )
    found.append(
        Sample(
            "gate-0",
            "notch",
            (
                panels["base"].cx,
                gate.y1 - GATE_THICKNESS_MM / 2.0,
                gate.z0 + 0.55 * (bottles[0].radius_mm * 2.0) - 6.0,
            ),
            False,
        )
    )
    # Stored bottle centres are empty. Ends stay off the guides.
    for bottle in bottles:
        if bottle.index not in (0, bottle_depth_last(bottles, bottle.lane)):
            continue
        found.append(
            Sample(
                "lane",
                f"bottle-{bottle.lane}-{bottle.index}",
                bottle.center,
                False,
            )
        )
    # A point in the front foot and in the hooked pocket.
    main, toe = feet[0]
    found.append(Sample("foot-0", "block", _center(main), True))
    found.append(Sample("foot-0", "toe", (toe.cx, toe.y0 + 2.0, (toe.z0 + toe.z1) / 2.0), True))
    pocket = cuts["top-front"][0]
    found.append(Sample("top-front", "pocket", _center(pocket), False))
    # Lip over the toe: material at the top of the strip, above the toe's Y.
    found.append(
        Sample(
            "top-front",
            "lip",
            (main.cx, toe.cy, carcass_height - 1.5),
            True,
        )
    )
    # Slide-in opening behind the foot is open.
    upper = cuts["top-front"][1]
    found.append(Sample("top-front", "entry", (main.cx, upper.y1 - 2.0, carcass_height - 1.5), False))
    cable = (
        side.x0 + cable_depth / 2.0,
        (16.0 + (side.y1 - 16.0)) / 2.0,
        trunk_z,
    )
    found.append(Sample("right-side", "cable", cable, False))
    found.append(Sample("back", "window", _center(windows[0]), False))
    inlet = next(hole for hole in holes if hole.name == "inlet-0-a")
    outlet = next(hole for hole in holes if hole.name == "outlet-0-a")
    esp = next(hole for hole in holes if hole.name == "esp-0")
    found.append(Sample(inlet.part, inlet.name, inlet.origin, False))
    found.append(Sample(outlet.part, outlet.name, outlet.origin, False))
    found.append(Sample(esp.part, esp.name, esp.origin, False))
    pin = pins[0]
    found.append(Sample(pin.part, "pin", pin.origin, True))
    pocket_hole = next(hole for hole in holes if hole.name == "tile-pocket-0")
    found.append(Sample(pocket_hole.part, pocket_hole.name, pocket_hole.origin, False))
    # Guide rail, just inboard of the left guide, near the deck.
    origin = guides[0].origin
    rail_y, rail_z = _rot_x(40.0, GUIDE_RAIL_HEIGHT_MM / 2.0, slope)
    found.append(
        Sample(
            "guide-left-0",
            "rail",
            (
                origin[0] + GUIDE_WIDTH_MM - GUIDE_RAIL_THICKNESS_MM / 2.0,
                origin[1] + rail_y,
                origin[2] + rail_z,
            ),
            True,
        )
    )
    del engagement
    return tuple(found)


def bottle_depth_last(bottles: list[BottlePose], lane: int) -> int:
    return max(bottle.index for bottle in bottles if bottle.lane == lane)


def _guide_samples(length: float, hole_d: float) -> tuple[Sample, ...]:
    flange_x = (GUIDE_WIDTH_MM - GUIDE_RAIL_THICKNESS_MM) / 2.0
    return (
        Sample("guide", "base", (flange_x, length * 0.125, GUIDE_BASE_MM / 2.0), True),
        Sample(
            "guide",
            "rail",
            (
                GUIDE_WIDTH_MM - GUIDE_RAIL_THICKNESS_MM / 2.0,
                length * 0.5,
                GUIDE_RAIL_HEIGHT_MM / 2.0,
            ),
            True,
        ),
        Sample("guide", "hole", (flange_x, length * 0.25, GUIDE_BASE_MM / 2.0), False),
        Sample(
            "guide",
            "beside-hole",
            (flange_x + hole_d, length * 0.25, GUIDE_BASE_MM / 2.0),
            True,
        ),
    )


def _gate_samples(
    width: float,
    height: float,
    thick: float,
    notch_w: float,
    notch_h: float,
) -> tuple[Sample, ...]:
    return (
        Sample("gate", "stop", (width * 0.2, 8.0, thick / 2.0), True),
        Sample("gate", "notch", (width / 2.0, height - notch_h / 2.0, thick / 2.0), False),
        Sample("gate", "beside-notch", (width / 2.0 - notch_w / 2.0 - 4.0, height - 4.0, thick / 2.0), True),
    )


def _cut_list(
    *,
    thickness: float,
    carcass_width: float,
    carcass_depth: float,
    carcass_height: float,
    inner_width: float,
    deck_along: float,
    lanes: int,
    gate_width: float,
    gate_height: float,
    engagement: float,
    pin_protrusion: float,
    tile_depth: float,
    panels: dict[str, Box],
    back_width: float,
) -> tuple[tuple[CutPiece, ...], tuple[Hardware, ...]]:
    post = panels["post-left"]
    rail = panels["rail-front"]
    back = panels["back"]
    apron = panels["apron"]
    pieces = (
        CutPiece(
            "side-panel",
            "plywood",
            2,
            _r(carcass_depth),
            _r(carcass_height),
            _r(thickness),
            "Full sides. Right panel: cable groove, inlet and outlet sensor holes, ESP32 pattern. Left panel: tile pockets.",
        ),
        CutPiece(
            "base",
            "plywood",
            1,
            _r(carcass_depth),
            _r(inner_width),
            _r(thickness),
            "Floor between the side panels.",
        ),
        CutPiece(
            "back-panel",
            "plywood",
            1,
            _r(back.z1 - back.z0),
            _r(back_width),
            _r(thickness),
            "Loading window for each lane.",
        ),
        CutPiece(
            "deck",
            "plywood",
            lanes,
            _r(deck_along),
            _r(inner_width),
            _r(thickness),
            "One sloped lane floor. Install at the module slope.",
        ),
        CutPiece(
            "front-apron",
            "plywood",
            1,
            _r(apron.z1 - apron.z0),
            _r(inner_width),
            _r(thickness),
            "Closes the front below the outlet.",
        ),
        CutPiece(
            "top-strip",
            "plywood",
            2,
            _r(STRIP_Y_MM),
            _r(inner_width),
            _r(thickness),
            "Front and rear strips with hooked stack pockets.",
        ),
        CutPiece(
            "stack-foot",
            "plywood",
            4,
            _r(FOOT_MM + TOE_MM),
            _r(FOOT_MM),
            _r(engagement),
            "Locating foot with a forward toe. Glue or screw under the base.",
        ),
        CutPiece(
            "post",
            "2020 extrusion envelope",
            2,
            _r(post.z1 - post.z0),
            _r(EXTRUSION_MM),
            _r(EXTRUSION_MM),
            "Rear corners. 20×20 mm outer envelope only; T-slot is not cut here.",
        ),
        CutPiece(
            "rail",
            "2020 extrusion envelope",
            2,
            _r(rail.x1 - rail.x0),
            _r(EXTRUSION_MM),
            _r(EXTRUSION_MM),
            "Top front and top rear rails. 20×20 mm outer envelope only.",
        ),
        CutPiece(
            "lane-guide",
            "PLA or PETG",
            lanes * 2,
            _r(deck_along),
            _r(GUIDE_WIDTH_MM),
            _r(GUIDE_RAIL_HEIGHT_MM),
            "Printed side guide. Three 3.4 mm holes in the flange.",
        ),
        CutPiece(
            "outlet-gate",
            "PLA or PETG",
            lanes,
            _r(gate_width),
            _r(gate_height),
            _r(GATE_THICKNESS_MM),
            "Printed lift gate with a finger notch. One per lane.",
        ),
        CutPiece(
            "tile-pin",
            "PLA or PETG",
            2,
            _r(pin_protrusion + tile_depth - 1.0),
            _r(PIN_DIAMETER_MM),
            _r(PIN_DIAMETER_MM),
            "Press into the right side. The left side of the next module has the pocket.",
        ),
    )
    hardware = (
        Hardware(
            f"M3x{GUIDE_SCREW_LENGTH_MM} SHCS",
            "ISO 4762 / ISO 888",
            GUIDE_SCREWS_EACH * lanes * 2,
            "Lane guides into the decks. Clearance drill 3.4 mm (ISO 273 medium).",
        ),
        Hardware(
            f"M3x{SENSOR_SCREW_LENGTH_MM} SHCS",
            "ISO 4762 / ISO 888",
            4 * lanes + 4,
            "Two screws at each lane inlet, two at each lane outlet, four on the ESP32 pattern.",
        ),
        Hardware(
            "M3 hex nut",
            "ISO 4032",
            4 * lanes + 4,
            "Nuts for the sensor and ESP32 screws.",
        ),
    )
    return pieces, hardware


def cut_list_document(layout: BottleRackLayout | None = None) -> dict[str, object]:
    """JSON-ready cut list. ``layout`` defaults to the committed module."""
    if layout is None:
        found = make_bottle_rack()
        if isinstance(found, Err):
            raise ValueError(bottle_rack_deny_message(found.error))
        layout = found.value
    return {
        "units": "mm",
        "generated_from": "cq_artifacts.bottle_rack_dims.make_bottle_rack",
        "note": (
            "Shop sizes from the parameters. nominal_full_bottle_kg is a design "
            "input for the payload line, not a measured load rating."
        ),
        "parameters": {
            "bottle_diameter_mm": layout.bottle_diameter_mm,
            "bottle_length_mm": layout.bottle_length_mm,
            "lanes": layout.lanes,
            "depth": layout.depth,
            "slope_deg": layout.slope_deg,
            "thickness_mm": layout.thickness_mm,
        },
        "envelope_mm": {
            "width": _r(layout.carcass_width_mm),
            "depth": _r(layout.carcass_depth_mm),
            "height": _r(layout.carcass_height_mm),
        },
        "bounding_box_mm": {
            "xlen": _r(layout.bbox.x1 - layout.bbox.x0),
            "ylen": _r(layout.bbox.y1 - layout.bbox.y0),
            "zlen": _r(layout.bbox.z1 - layout.bbox.z0),
        },
        "slots": layout.slots,
        "nominal_full_bottle_kg": layout.nominal_full_bottle_kg,
        "nominal_payload_kg": layout.nominal_payload_kg,
        "tile_pitch_mm": _r(layout.tile_pitch_mm),
        "stack_engagement_mm": _r(layout.stack_engagement_mm),
        "pieces": [
            {
                "name": piece.name,
                "material": piece.material,
                "qty": piece.qty,
                "length_mm": piece.length_mm,
                "width_mm": piece.width_mm,
                "thickness_mm": piece.thickness_mm,
                "notes": piece.notes,
            }
            for piece in layout.pieces
        ],
        "hardware": [
            {
                "name": item.name,
                "spec": item.spec,
                "qty": item.qty,
                "notes": item.notes,
            }
            for item in layout.hardware
        ],
    }


def cut_list_json(layout: BottleRackLayout | None = None) -> str:
    return json.dumps(cut_list_document(layout), indent=2) + "\n"


def cut_list_csv(layout: BottleRackLayout | None = None) -> str:
    document = cut_list_document(layout)
    lines = [
        "kind,name,material,qty,length_mm,width_mm,thickness_mm,notes",
    ]
    for piece in document["pieces"]:
        lines.append(
            ",".join(
                [
                    "cut",
                    piece["name"],
                    _csv(piece["material"]),
                    str(piece["qty"]),
                    _csv(piece["length_mm"]),
                    _csv(piece["width_mm"]),
                    _csv(piece["thickness_mm"]),
                    _csv(piece["notes"]),
                ]
            )
        )
    for item in document["hardware"]:
        lines.append(
            ",".join(
                [
                    "hardware",
                    _csv(item["name"]),
                    _csv(item["spec"]),
                    str(item["qty"]),
                    "",
                    "",
                    "",
                    _csv(item["notes"]),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def _csv(value: object) -> str:
    text = str(value)
    if any(ch in text for ch in ",\"\n"):
        return '"' + text.replace('"', '""') + '"'
    return text


def write_cut_list(directory, layout: BottleRackLayout | None = None) -> tuple[object, object]:
    """Write ``cut-list.json`` and ``cut-list.csv`` under ``directory``."""
    from pathlib import Path

    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "cut-list.json"
    csv_path = root / "cut-list.csv"
    json_path.write_text(cut_list_json(layout), encoding="utf-8")
    csv_path.write_text(cut_list_csv(layout), encoding="utf-8")
    return json_path, csv_path
