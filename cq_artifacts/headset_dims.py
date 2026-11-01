"""Pure millimetre layout for the wireless headset shell kit. No CadQuery.

Comfort defaults (long sessions), all millimetres:

- Circumaural earcup 76 × 88 × 42. A 54 × 66 opening and 12 mm of pinna
  room sit in front of the driver so the ear does not rest on the baffle.
- Driver cavity accepts a 40–50 mm dynamic driver. Default 50 mm, with
  0.6 mm radial slip and a 1.5 mm retaining lip. The sound hole is smaller
  than the driver, so the driver cannot fall toward the ear.
- One cup holds a 34 × 24 × 1.6 mm PCB and a 42 × 30 × 6.5 mm LiPo behind
  the driver. The other cup is the same shell without the mic port.
- Pad lip 2.5 mm tall on the ear face. A 7 mm mic-boom port and a
  10 × 2.4 mm flex/cable slot are optional cuts on that shell.
- Headband inner radius 105 mm over a 110° arc, 18 mm wide where it meets
  the head. Each leg has an extension slot the screw center can travel
  28 mm along.
- The yoke slides on that slot, swivels about the clamp screw, and hinges
  about a pin through the cup trunnion.

Fasteners are not redefined here. Clearance holes use the ISO 273 medium
M3 diameter from ``through_hole_dims`` (3.4 mm). Screws are ISO 4762 /
ISO 888 M3 socket-head envelopes from ``m3_shcs_dims``: M3×8 extension
clamps, M3×25 hinge pins, M3×6 cover screws. A foam ear pad and a headband
cushion are not part of the shell kit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .m3_shcs_dims import (
    HEAD_DIAMETER_MM,
    HEAD_HEIGHT_MM,
    SHANK_DIAMETER_MM,
    make_m3_shcs,
)
from .outcome import Err, Ok, Result
from .through_hole_dims import DEFAULT_HOLE_DIAMETER_MM

# --- earcup ---
OUTER_WIDTH_MM = 76.0
OUTER_HEIGHT_MM = 88.0
OUTER_DEPTH_MM = 42.0
WALL_MM = 2.4
BACK_WALL_MM = 2.4
OUTER_CORNER_RADIUS_MM = 10.0
LIP_HEIGHT_MM = 2.5
LIP_LAND_MM = 1.2
EAR_OPENING_WIDTH_MM = 54.0
EAR_OPENING_HEIGHT_MM = 66.0
EAR_ROOM_MM = 12.0
RETAINING_THICKNESS_MM = 1.6
DRIVER_RADIAL_CLEARANCE_MM = 0.6
RETAINING_OVERHANG_MM = 1.5
DRIVER_DEPTH_MM = 14.0
DRIVER_DIAMETER_MIN_MM = 40.0
DRIVER_DIAMETER_MAX_MM = 50.0
DEFAULT_DRIVER_DIAMETER_MM = 50.0
BAY_CLEARANCE_MM = 1.2
PCB_LENGTH_MM = 34.0
PCB_WIDTH_MM = 24.0
PCB_THICKNESS_MM = 1.6
LIPO_LENGTH_MM = 42.0
LIPO_WIDTH_MM = 30.0
LIPO_THICKNESS_MM = 6.5
MIC_DIAMETER_MM = 7.0
MIC_BOSS_DIAMETER_MM = 12.0
MIC_BOSS_LENGTH_MM = 8.0
MIC_BOSS_EMBED_MM = 2.0
PASS_WIDTH_MM = 10.0
PASS_HEIGHT_MM = 2.4
PASS_X_MM = -16.0
TRUNNION_DIAMETER_MM = 14.0
TRUNNION_LENGTH_MM = 14.0
TRUNNION_RAISE_MM = 5.0
BOSS_Z_MM = 18.0
COVER_THICKNESS_MM = 2.0
COVER_HOLE_INSET_MM = 12.0

# --- headband / yoke ---
DEFAULT_INNER_RADIUS_MM = 105.0
DEFAULT_ARC_DEG = 110.0
DEFAULT_TRAVEL_MM = 28.0
BAND_THICKNESS_MM = 4.0
BAND_WIDTH_MM = 18.0
PLATE_THICKNESS_MM = 3.0
PLATE_HEIGHT_MM = 20.0
PLATE_WIDTH_MM = 16.0
YOKE_DROP_MM = 18.0
# Clears the pad lip, which hangs inboard of the pad face.
CUP_GAP_MM = 4.0
PART_GAP_MM = 0.25
CLEVIS_GAP_MM = 0.4
CLEVIS_EAR_THICKNESS_MM = 3.2
TOP_MARGIN_MM = 6.0
LEG_END_MARGIN_MM = 3.0
LEG_ARC_OVERLAP_MM = 8.0
BRIDGE_GAP_MM = 0.8
# Short enough that the bridge stays clear of the extension-screw head.
BRIDGE_HEIGHT_MM = 6.4

# ISO 888 preferred lengths. Checked with make_m3_shcs, not a new screw.
EXTENSION_SCREW_LENGTH_MM = 8
HINGE_SCREW_LENGTH_MM = 25
COVER_SCREW_LENGTH_MM = 6

INNER_RADIUS_MIN_MM = 90.0
INNER_RADIUS_MAX_MM = 125.0
ARC_MIN_DEG = 90.0
ARC_MAX_DEG = 140.0
TRAVEL_MIN_MM = 12.0
TRAVEL_MAX_MM = 40.0
# Positive hinge swings the cup top toward the leg. 5° stays clear of the
# leg at both ends of the extension travel. Swivel is about the clamp screw.
HINGE_LIMIT_DEG = 5.0
SWIVEL_LIMIT_DEG = 12.0

# How far a sample sits inside / outside a 3.4 mm hole to bracket its size.
_HOLE_VOID_INSET_MM = 0.15
_HOLE_MATERIAL_OUTSET_MM = 0.25

Vec3 = tuple[float, float, float]
Field = Literal[
    "driver_diameter",
    "inner_radius",
    "arc_deg",
    "travel",
    "extension_offset",
    "hinge_deg",
    "swivel_deg",
    "mic_port",
    "assembly",
]


class HeadsetDenyCode(Enum):
    NOT_A_NUMBER = "not_a_number"
    NON_FINITE = "non_finite"
    OUT_OF_RANGE = "out_of_range"
    NOT_A_BOOL = "not_a_bool"
    DOES_NOT_FIT = "does_not_fit"


@dataclass(frozen=True, slots=True)
class HeadsetDeny:
    code: HeadsetDenyCode
    field: Field
    value: object


@dataclass(frozen=True, slots=True)
class Sample:
    """A point that is inside or outside one named solid."""

    part: str
    name: str
    point: Vec3
    inside: bool


@dataclass(frozen=True, slots=True)
class Joint:
    """One M3 clamp. ``head_direction`` points from the bearing face into the head.

    ``bearing`` is the point on the screw axis at the under-head face
    (local z = 0 of ``create_m3_shcs``). The shank runs in the opposite
    direction for ``length_mm``.
    """

    name: str
    side: str
    length_mm: float
    bearing: Vec3
    head_direction: Vec3


@dataclass(frozen=True, slots=True)
class EarcupLayout:
    driver_diameter_mm: float
    mic_port: bool
    cavity_diameter_mm: float
    sound_hole_diameter_mm: float
    inner_width_mm: float
    inner_height_mm: float
    baffle_z0_mm: float
    baffle_z1_mm: float
    driver_z0_mm: float
    driver_z1_mm: float
    bay_z0_mm: float
    bay_z1_mm: float
    pcb_center_mm: Vec3
    lipo_center_mm: Vec3
    trunnion_center_mm: Vec3
    cover_hole_xy_mm: tuple[Vec3, ...]  # x, y, unused z = 0
    mic_axis_mm: Vec3
    mic_wall_mm: Vec3
    pass_center_mm: Vec3
    samples: tuple[Sample, ...]


@dataclass(frozen=True, slots=True)
class BoxMM:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float


@dataclass(frozen=True, slots=True)
class HeadsetLayout:
    driver_diameter_mm: float
    inner_radius_mm: float
    arc_deg: float
    travel_mm: float
    extension_offset_mm: float
    hinge_deg: float
    swivel_deg: float
    mic_port: bool
    hole_diameter_mm: float
    shank_diameter_mm: float
    head_diameter_mm: float
    head_height_mm: float
    earcup: EarcupLayout
    pad_x_mm: float
    ear_y_mm: float
    nominal_screw_y_mm: float
    screw_y_mm: float
    hinge_mm: Vec3
    leg_center_x_mm: float
    leg: BoxMM
    plate: BoxMM
    yoke_boxes: tuple[BoxMM, ...]
    swivel_origin_mm: Vec3
    joints: tuple[Joint, ...]
    samples: tuple[Sample, ...]


def headset_deny_message(deny: HeadsetDeny) -> str:
    return f"headset {deny.field} {deny.value!r} is {deny.code.value}"


def _rot(point: Vec3, origin: Vec3, axis: Vec3, deg: float) -> Vec3:
    """Right-hand rotation of ``point`` about ``axis`` through ``origin``."""
    if deg == 0.0:
        return point
    theta = math.radians(deg)
    c = math.cos(theta)
    s = math.sin(theta)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    z = point[2] - origin[2]
    ax, ay, az = axis
    dot = ax * x + ay * y + az * z
    cx = ay * z - az * y
    cy = az * x - ax * z
    cz = ax * y - ay * x
    return (
        origin[0] + x * c + cx * s + ax * dot * (1.0 - c),
        origin[1] + y * c + cy * s + ay * dot * (1.0 - c),
        origin[2] + z * c + cz * s + az * dot * (1.0 - c),
    )


def _cup_world(local: Vec3, layout: HeadsetLayout) -> Vec3:
    """Earcup local point → world, including hinge and swivel.

    Local +X points toward the face, +Y up, +Z out from the ear.
    On the right cup that becomes world +Z, +Y, +X before swivel.
    """
    spun = _rot(local, layout.earcup.trunnion_center_mm, (1.0, 0.0, 0.0), layout.hinge_deg)
    placed = (layout.pad_x_mm + spun[2], layout.ear_y_mm + spun[1], spun[0])
    return _rot(placed, layout.swivel_origin_mm, (1.0, 0.0, 0.0), layout.swivel_deg)


def _cup_direction(direction: Vec3, layout: HeadsetLayout) -> Vec3:
    spun = _rot(direction, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), layout.hinge_deg)
    placed = (spun[2], spun[1], spun[0])
    return _rot(placed, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), layout.swivel_deg)


def _mirror_x(point: Vec3) -> Vec3:
    return (-point[0], point[1], point[2])


def _mirror_dir(direction: Vec3) -> Vec3:
    return (-direction[0], direction[1], direction[2])


def make_headset(
    driver_diameter: object = DEFAULT_DRIVER_DIAMETER_MM,
    inner_radius: object = DEFAULT_INNER_RADIUS_MM,
    arc_deg: object = DEFAULT_ARC_DEG,
    travel: object = DEFAULT_TRAVEL_MM,
    extension_offset: object = 0.0,
    hinge_deg: object = 0.0,
    swivel_deg: object = 0.0,
    mic_port: object = True,
) -> Result[HeadsetLayout, HeadsetDeny]:
    """Validate one kit and return the layout used by the solids and the tests."""
    driver = _in_range(
        "driver_diameter",
        driver_diameter,
        DRIVER_DIAMETER_MIN_MM,
        DRIVER_DIAMETER_MAX_MM,
    )
    if isinstance(driver, Err):
        return driver
    radius = _in_range(
        "inner_radius", inner_radius, INNER_RADIUS_MIN_MM, INNER_RADIUS_MAX_MM
    )
    if isinstance(radius, Err):
        return radius
    arc = _in_range("arc_deg", arc_deg, ARC_MIN_DEG, ARC_MAX_DEG)
    if isinstance(arc, Err):
        return arc
    travel_mm = _in_range("travel", travel, TRAVEL_MIN_MM, TRAVEL_MAX_MM)
    if isinstance(travel_mm, Err):
        return travel_mm
    offset = _finite("extension_offset", extension_offset)
    if isinstance(offset, Err):
        return offset
    hinge = _in_range("hinge_deg", hinge_deg, -HINGE_LIMIT_DEG, HINGE_LIMIT_DEG)
    if isinstance(hinge, Err):
        return hinge
    swivel = _in_range("swivel_deg", swivel_deg, -SWIVEL_LIMIT_DEG, SWIVEL_LIMIT_DEG)
    if isinstance(swivel, Err):
        return swivel
    if not isinstance(mic_port, bool):
        return Err(HeadsetDeny(HeadsetDenyCode.NOT_A_BOOL, "mic_port", mic_port))
    if abs(offset.value) > travel_mm.value / 2.0:
        return Err(
            HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "extension_offset", extension_offset)
        )

    earcup = _earcup(driver.value, mic_port)
    fit = _electronics_fit(earcup)
    if fit is not None:
        return Err(HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "assembly", fit))

    theta = math.radians(arc.value / 2.0)
    r_mid = radius.value + BAND_THICKNESS_MM / 2.0
    leg_center_x = r_mid * math.sin(theta)
    end_y = r_mid * math.cos(theta)
    nominal_screw_y = end_y - (
        travel_mm.value / 2.0 + PLATE_HEIGHT_MM / 2.0 + TOP_MARGIN_MM
    )
    screw_y = nominal_screw_y + offset.value
    leg_outer = leg_center_x + BAND_THICKNESS_MM / 2.0
    pad_x = leg_outer + CUP_GAP_MM
    hinge_y = screw_y - YOKE_DROP_MM
    ear_y = hinge_y - (OUTER_HEIGHT_MM / 2.0 + TRUNNION_RAISE_MM)
    hinge_point = (pad_x + BOSS_Z_MM, hinge_y, 0.0)
    leg = BoxMM(
        leg_center_x - BAND_THICKNESS_MM / 2.0,
        leg_outer,
        nominal_screw_y - travel_mm.value / 2.0 - PLATE_HEIGHT_MM / 2.0 - LEG_END_MARGIN_MM,
        end_y + LEG_ARC_OVERLAP_MM,
        -BAND_WIDTH_MM / 2.0,
        BAND_WIDTH_MM / 2.0,
    )
    plate = BoxMM(
        leg_outer + PART_GAP_MM,
        leg_outer + PART_GAP_MM + PLATE_THICKNESS_MM,
        screw_y - PLATE_HEIGHT_MM / 2.0,
        screw_y + PLATE_HEIGHT_MM / 2.0,
        -PLATE_WIDTH_MM / 2.0,
        PLATE_WIDTH_MM / 2.0,
    )
    if plate.ymin < leg.ymin or plate.ymax > leg.ymax or leg.ymax <= leg.ymin:
        return Err(HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "assembly", "leg"))
    if pad_x <= leg.xmax:
        return Err(HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "assembly", "cup-clearance"))

    yoke_boxes = _yoke_boxes(plate, hinge_point)
    bridge = yoke_boxes[2]
    if bridge.ymax > screw_y - HEAD_DIAMETER_MM / 2.0 - 0.4:
        return Err(HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "assembly", "screw-head"))
    if yoke_boxes[3].ymin < hinge_y - TRUNNION_RAISE_MM + 0.8:
        return Err(HeadsetDeny(HeadsetDenyCode.DOES_NOT_FIT, "assembly", "clevis"))
    hole = DEFAULT_HOLE_DIAMETER_MM
    void_r = hole / 2.0 - _HOLE_VOID_INSET_MM
    mat_r = hole / 2.0 + _HOLE_MATERIAL_OUTSET_MM
    base = HeadsetLayout(
        driver_diameter_mm=driver.value,
        inner_radius_mm=radius.value,
        arc_deg=arc.value,
        travel_mm=travel_mm.value,
        extension_offset_mm=offset.value,
        hinge_deg=hinge.value,
        swivel_deg=swivel.value,
        mic_port=mic_port,
        hole_diameter_mm=hole,
        shank_diameter_mm=SHANK_DIAMETER_MM,
        head_diameter_mm=HEAD_DIAMETER_MM,
        head_height_mm=HEAD_HEIGHT_MM,
        earcup=earcup,
        pad_x_mm=pad_x,
        ear_y_mm=ear_y,
        nominal_screw_y_mm=nominal_screw_y,
        screw_y_mm=screw_y,
        hinge_mm=hinge_point,
        leg_center_x_mm=leg_center_x,
        leg=leg,
        plate=plate,
        yoke_boxes=yoke_boxes,
        swivel_origin_mm=(0.0, screw_y, 0.0),
        joints=(),
        samples=(),
    )
    joints, samples = _joints_and_samples(base, void_r, mat_r)
    return Ok(
        HeadsetLayout(
        driver_diameter_mm=base.driver_diameter_mm,
        inner_radius_mm=base.inner_radius_mm,
        arc_deg=base.arc_deg,
        travel_mm=base.travel_mm,
        extension_offset_mm=base.extension_offset_mm,
        hinge_deg=base.hinge_deg,
        swivel_deg=base.swivel_deg,
        mic_port=base.mic_port,
        hole_diameter_mm=base.hole_diameter_mm,
        shank_diameter_mm=base.shank_diameter_mm,
        head_diameter_mm=base.head_diameter_mm,
        head_height_mm=base.head_height_mm,
        earcup=base.earcup,
        pad_x_mm=base.pad_x_mm,
        ear_y_mm=base.ear_y_mm,
        nominal_screw_y_mm=base.nominal_screw_y_mm,
        screw_y_mm=base.screw_y_mm,
        hinge_mm=base.hinge_mm,
        leg_center_x_mm=base.leg_center_x_mm,
        leg=base.leg,
        plate=base.plate,
        yoke_boxes=base.yoke_boxes,
        swivel_origin_mm=base.swivel_origin_mm,
        joints=joints,
        samples=samples,
        )
    )


def _earcup(driver: float, mic_port: bool) -> EarcupLayout:
    cavity = driver + 2.0 * DRIVER_RADIAL_CLEARANCE_MM
    sound = driver - 2.0 * RETAINING_OVERHANG_MM
    inner_w = OUTER_WIDTH_MM - 2.0 * WALL_MM
    inner_h = OUTER_HEIGHT_MM - 2.0 * WALL_MM
    baffle_z0 = EAR_ROOM_MM
    baffle_z1 = EAR_ROOM_MM + RETAINING_THICKNESS_MM
    driver_z0 = baffle_z1
    driver_z1 = driver_z0 + DRIVER_DEPTH_MM
    bay_z0 = driver_z1
    bay_z1 = OUTER_DEPTH_MM - BACK_WALL_MM
    lipo_z1 = bay_z1 - BAY_CLEARANCE_MM
    lipo_z0 = lipo_z1 - LIPO_THICKNESS_MM
    pcb_z1 = lipo_z0 - BAY_CLEARANCE_MM
    pcb_z0 = pcb_z1 - PCB_THICKNESS_MM
    pcb_center = (0.0, 0.0, (pcb_z0 + pcb_z1) / 2.0)
    lipo_center = (0.0, 0.0, (lipo_z0 + lipo_z1) / 2.0)
    trunnion = (0.0, OUTER_HEIGHT_MM / 2.0 + TRUNNION_RAISE_MM, BOSS_Z_MM)
    inset = COVER_HOLE_INSET_MM
    hx = OUTER_WIDTH_MM / 2.0 - inset
    hy = OUTER_HEIGHT_MM / 2.0 - inset
    holes = (
        (hx, hy, 0.0),
        (hx, -hy, 0.0),
        (-hx, hy, 0.0),
        (-hx, -hy, 0.0),
    )
    mic_y = -(OUTER_HEIGHT_MM / 2.0 - 18.0)
    mic_z = 8.0
    mic_axis = (OUTER_WIDTH_MM / 2.0, mic_y, mic_z)
    mic_wall = (OUTER_WIDTH_MM / 2.0 - WALL_MM / 2.0, mic_y, mic_z)
    bay_mid_z = (bay_z0 + bay_z1) / 2.0
    pass_center = (PASS_X_MM, OUTER_HEIGHT_MM / 2.0, bay_mid_z)
    samples = _earcup_samples(
        driver,
        cavity,
        sound,
        baffle_z0,
        baffle_z1,
        driver_z0,
        driver_z1,
        pcb_center,
        lipo_center,
        trunnion,
        holes,
        mic_wall,
        mic_port,
        pass_center,
    )
    return EarcupLayout(
        driver_diameter_mm=driver,
        mic_port=mic_port,
        cavity_diameter_mm=cavity,
        sound_hole_diameter_mm=sound,
        inner_width_mm=inner_w,
        inner_height_mm=inner_h,
        baffle_z0_mm=baffle_z0,
        baffle_z1_mm=baffle_z1,
        driver_z0_mm=driver_z0,
        driver_z1_mm=driver_z1,
        bay_z0_mm=bay_z0,
        bay_z1_mm=bay_z1,
        pcb_center_mm=pcb_center,
        lipo_center_mm=lipo_center,
        trunnion_center_mm=trunnion,
        cover_hole_xy_mm=holes,
        mic_axis_mm=mic_axis,
        mic_wall_mm=mic_wall,
        pass_center_mm=pass_center,
        samples=samples,
    )


def _earcup_samples(
    driver: float,
    cavity: float,
    sound: float,
    baffle_z0: float,
    baffle_z1: float,
    driver_z0: float,
    driver_z1: float,
    pcb_center: Vec3,
    lipo_center: Vec3,
    trunnion: Vec3,
    holes: tuple[Vec3, ...],
    mic_wall: Vec3,
    mic_port: bool,
    pass_center: Vec3,
) -> tuple[Sample, ...]:
    mid_z = (driver_z0 + driver_z1) / 2.0
    driver_r = driver / 2.0
    cavity_r = cavity / 2.0
    sound_r = sound / 2.0
    lip_r = (sound_r + driver_r) / 2.0
    baffle_z = (baffle_z0 + baffle_z1) / 2.0
    hole_r = DEFAULT_HOLE_DIAMETER_MM / 2.0
    void_r = hole_r - _HOLE_VOID_INSET_MM
    mat_r = hole_r + _HOLE_MATERIAL_OUTSET_MM
    back_mid_z = (OUTER_DEPTH_MM - BACK_WALL_MM + OUTER_DEPTH_MM) / 2.0
    cover_mid_z = OUTER_DEPTH_MM + PART_GAP_MM + COVER_THICKNESS_MM / 2.0
    samples: list[Sample] = [
        Sample("shell", "driver-center", (0.0, 0.0, mid_z), False),
        Sample("shell", "driver-radius", (driver_r - 0.2, 0.0, mid_z), False),
        Sample("shell", "cavity-wall", (0.0, cavity_r + 0.35, mid_z), True),
        Sample("shell", "sound-hole", (0.0, 0.0, baffle_z), False),
        Sample("shell", "retaining-lip", (lip_r, 0.0, baffle_z), True),
        Sample("shell", "pcb", pcb_center, False),
        Sample("shell", "lipo", lipo_center, False),
        Sample("shell", "side-wall", (OUTER_WIDTH_MM / 2.0 - WALL_MM / 2.0, 0.0, 22.0), True),
        Sample("shell", "pass-through", pass_center, False),
        Sample("shell", "trunnion-axis", trunnion, False),
        Sample(
            "shell",
            "trunnion-material",
            (trunnion[0], trunnion[1] + mat_r, trunnion[2]),
            True,
        ),
        Sample(
            "shell",
            "trunnion-void-offset",
            (trunnion[0] + void_r, trunnion[1], trunnion[2]),
            False,
        ),
        Sample("shell", "mic-wall", mic_wall, not mic_port),
    ]
    for index, (hx, hy, _) in enumerate(holes):
        samples.append(Sample("shell", f"cover-hole-{index}", (hx, hy, back_mid_z), False))
        samples.append(
            Sample("shell", f"cover-land-{index}", (hx, hy + mat_r, back_mid_z), True)
        )
        samples.append(Sample("cover", f"cover-hole-{index}", (hx, hy, cover_mid_z), False))
        samples.append(
            Sample("cover", f"cover-land-{index}", (hx + mat_r, hy, cover_mid_z), True)
        )
    samples.append(
        Sample(
            "cover",
            "cover-plate",
            (0.0, 0.0, OUTER_DEPTH_MM + PART_GAP_MM + COVER_THICKNESS_MM / 2.0),
            True,
        )
    )
    return tuple(samples)


def _electronics_fit(earcup: EarcupLayout) -> str | None:
    if earcup.cavity_diameter_mm >= earcup.inner_width_mm:
        return "driver-width"
    if earcup.cavity_diameter_mm >= earcup.inner_height_mm:
        return "driver-height"
    if earcup.sound_hole_diameter_mm <= 0:
        return "sound-hole"
    if earcup.sound_hole_diameter_mm >= earcup.driver_diameter_mm:
        return "retaining-lip"
    if earcup.cavity_diameter_mm <= earcup.driver_diameter_mm:
        return "driver-clearance"
    bay_depth = earcup.bay_z1_mm - earcup.bay_z0_mm
    need = (
        BAY_CLEARANCE_MM
        + PCB_THICKNESS_MM
        + BAY_CLEARANCE_MM
        + LIPO_THICKNESS_MM
        + BAY_CLEARANCE_MM
    )
    if bay_depth < need:
        return "bay-depth"
    if PCB_LENGTH_MM + 2.0 * BAY_CLEARANCE_MM >= earcup.inner_width_mm:
        return "pcb-width"
    if LIPO_LENGTH_MM + 2.0 * BAY_CLEARANCE_MM >= earcup.inner_width_mm:
        return "lipo-width"
    if LIPO_WIDTH_MM + 2.0 * BAY_CLEARANCE_MM >= earcup.inner_height_mm:
        return "lipo-height"
    if earcup.pcb_center_mm[2] - PCB_THICKNESS_MM / 2.0 < earcup.bay_z0_mm + BAY_CLEARANCE_MM:
        return "pcb-driver-gap"
    stack = BAND_THICKNESS_MM + PART_GAP_MM + PLATE_THICKNESS_MM
    if not stack < EXTENSION_SCREW_LENGTH_MM <= stack + 2.0:
        return "extension-screw"
    span = TRUNNION_LENGTH_MM + 2.0 * CLEVIS_GAP_MM + 2.0 * CLEVIS_EAR_THICKNESS_MM
    if not span < HINGE_SCREW_LENGTH_MM <= span + 5.0:
        return "hinge-screw"
    cover_stack = COVER_THICKNESS_MM + PART_GAP_MM + BACK_WALL_MM
    if not cover_stack < COVER_SCREW_LENGTH_MM <= cover_stack + 2.5:
        return "cover-screw"
    for length in (
        EXTENSION_SCREW_LENGTH_MM,
        HINGE_SCREW_LENGTH_MM,
        COVER_SCREW_LENGTH_MM,
    ):
        if isinstance(make_m3_shcs(length), Err):
            return "screw-length"
    if HEAD_DIAMETER_MM <= DEFAULT_HOLE_DIAMETER_MM:
        return "head-clamps"
    if not SHANK_DIAMETER_MM < DEFAULT_HOLE_DIAMETER_MM < HEAD_DIAMETER_MM:
        return "shank-clearance"
    return None


def _yoke_boxes(plate: BoxMM, hinge: Vec3) -> tuple[BoxMM, ...]:
    hx, hy, _hz = hinge
    trunnion_r = TRUNNION_DIAMETER_MM / 2.0
    bridge_y0 = hy + trunnion_r + BRIDGE_GAP_MM
    bridge_y1 = bridge_y0 + BRIDGE_HEIGHT_MM
    ear_inner = TRUNNION_LENGTH_MM / 2.0 + CLEVIS_GAP_MM
    ear_outer = ear_inner + CLEVIS_EAR_THICKNESS_MM
    drop = BoxMM(
        plate.xmin,
        plate.xmax,
        bridge_y0,
        plate.ymax,
        -3.5,
        3.5,
    )
    reach = BoxMM(
        plate.xmin,
        hx + trunnion_r,
        bridge_y0,
        bridge_y1,
        -(ear_inner + 1.6),
        ear_inner + 1.6,
    )
    # Stay above the earcup shell. The shell top is TRUNNION_RAISE below the pin.
    ear_y0 = hy - TRUNNION_RAISE_MM + 1.6
    ear_y1 = bridge_y1
    ear_x0 = hx - trunnion_r
    ear_x1 = hx + trunnion_r
    front = BoxMM(ear_x0, ear_x1, ear_y0, ear_y1, ear_inner, ear_outer)
    back = BoxMM(ear_x0, ear_x1, ear_y0, ear_y1, -ear_outer, -ear_inner)
    return (plate, drop, reach, front, back)


def _joints_and_samples(
    layout: HeadsetLayout, void_r: float, mat_r: float
) -> tuple[tuple[Joint, ...], tuple[Sample, ...]]:
    joints: list[Joint] = []
    samples: list[Sample] = []

    def add_side(side: str, mirror: bool) -> None:
        def pt(point: Vec3) -> Vec3:
            spun = _rot(point, layout.swivel_origin_mm, (1.0, 0.0, 0.0), layout.swivel_deg)
            return _mirror_x(spun) if mirror else spun

        def direc(direction: Vec3) -> Vec3:
            spun = _rot(direction, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), layout.swivel_deg)
            return _mirror_dir(spun) if mirror else spun

        plate = layout.plate
        bearing = pt((plate.xmax, layout.screw_y_mm, 0.0))
        head = direc((1.0, 0.0, 0.0))
        joints.append(
            Joint(
                f"{side}-extension",
                side,
                EXTENSION_SCREW_LENGTH_MM,
                bearing,
                head,
            )
        )
        # Leg does not swivel. Plate does.
        leg_void = (layout.leg_center_x_mm, layout.screw_y_mm, 0.0)
        leg_mat = (layout.leg_center_x_mm, layout.screw_y_mm, mat_r)
        if mirror:
            leg_void = _mirror_x(leg_void)
            leg_mat = _mirror_x(leg_mat)
        samples.append(Sample("headband", f"{side}-extension-void", leg_void, False))
        samples.append(Sample("headband", f"{side}-extension-material", leg_mat, True))
        samples.append(
            Sample(
                f"{side}-yoke",
                "extension-void",
                pt((_plate_mid_x(plate), layout.screw_y_mm, 0.0)),
                False,
            )
        )
        samples.append(
            Sample(
                f"{side}-yoke",
                "extension-material",
                pt((_plate_mid_x(plate), layout.screw_y_mm, mat_r)),
                True,
            )
        )
        samples.append(
            Sample(
                f"{side}-yoke",
                "extension-shank",
                pt((_plate_mid_x(plate), layout.screw_y_mm, void_r)),
                False,
            )
        )

        hx, hy, _hz = layout.hinge_mm
        ear_outer = TRUNNION_LENGTH_MM / 2.0 + CLEVIS_GAP_MM + CLEVIS_EAR_THICKNESS_MM
        ear_mid = TRUNNION_LENGTH_MM / 2.0 + CLEVIS_GAP_MM + CLEVIS_EAR_THICKNESS_MM / 2.0
        hinge_bearing = pt((hx, hy, ear_outer))
        hinge_dir = direc((0.0, 0.0, 1.0))
        joints.append(Joint(f"{side}-hinge", side, HINGE_SCREW_LENGTH_MM, hinge_bearing, hinge_dir))
        samples.append(Sample(f"{side}-yoke", "hinge-void", pt((hx, hy, ear_mid)), False))
        samples.append(
            Sample(f"{side}-yoke", "hinge-material", pt((hx, hy + mat_r, ear_mid)), True)
        )
        shell_name = f"{side}-shell"
        samples.append(Sample(shell_name, "hinge-void", pt((hx, hy, 0.0)), False))
        samples.append(
            Sample(shell_name, "hinge-material", pt((hx + mat_r, hy, 0.0)), True)
        )
        samples.append(
            Sample(shell_name, "hinge-shank", pt((hx, hy, void_r)), False)
        )

        cover_name = f"{side}-cover"
        back_mid_z = (layout.earcup.bay_z1_mm + OUTER_DEPTH_MM) / 2.0
        cover_mid_z = OUTER_DEPTH_MM + PART_GAP_MM + COVER_THICKNESS_MM / 2.0
        cover_outer_z = OUTER_DEPTH_MM + PART_GAP_MM + COVER_THICKNESS_MM
        for index, (cx, cy, _) in enumerate(layout.earcup.cover_hole_xy_mm):
            local_bearing = (cx, cy, cover_outer_z)
            world_bearing = _cup_world(local_bearing, layout)
            world_dir = _cup_direction((0.0, 0.0, 1.0), layout)
            if mirror:
                world_bearing = _mirror_x(world_bearing)
                world_dir = _mirror_dir(world_dir)
            joints.append(
                Joint(
                    f"{side}-cover-{index}",
                    side,
                    COVER_SCREW_LENGTH_MM,
                    world_bearing,
                    world_dir,
                )
            )
            for part, local_z, label in (
                (shell_name, back_mid_z, "shell"),
                (cover_name, cover_mid_z, "cover"),
            ):
                center = (cx, cy, local_z)
                land = (cx + mat_r, cy, local_z)
                world_c = _cup_world(center, layout)
                world_l = _cup_world(land, layout)
                if mirror:
                    world_c = _mirror_x(world_c)
                    world_l = _mirror_x(world_l)
                samples.append(Sample(part, f"{label}-hole-{index}", world_c, False))
                samples.append(Sample(part, f"{label}-land-{index}", world_l, True))

        driver_mid = (
            0.0,
            0.0,
            (layout.earcup.driver_z0_mm + layout.earcup.driver_z1_mm) / 2.0,
        )
        world_driver = _cup_world(driver_mid, layout)
        if mirror:
            world_driver = _mirror_x(world_driver)
        samples.append(Sample(shell_name, "driver-center", world_driver, False))
        world_pass = _cup_world(layout.earcup.pass_center_mm, layout)
        if mirror:
            world_pass = _mirror_x(world_pass)
        samples.append(Sample(shell_name, "pass-through", world_pass, False))
        if layout.mic_port and not mirror:
            world_mic = _cup_world(layout.earcup.mic_wall_mm, layout)
            samples.append(Sample(shell_name, "mic-wall", world_mic, False))
        if mirror:
            world_mic = _mirror_x(_cup_world(layout.earcup.mic_wall_mm, layout))
            # Left shell is built without the port, so the wall point is material.
            # _cup_world uses the mic-on layout's coordinates; the plain shell
            # shares them. The point is the wall midline, solid when uncut.
            samples.append(Sample(shell_name, "mic-wall", world_mic, True))

    add_side("right", False)
    add_side("left", True)
    return tuple(joints), tuple(samples)


def _plate_mid_x(plate: BoxMM) -> float:
    return (plate.xmin + plate.xmax) / 2.0


def _finite(field: Field, value: object) -> Result[float, HeadsetDeny]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return Err(HeadsetDeny(HeadsetDenyCode.NOT_A_NUMBER, field, value))
    number = float(value)
    if not math.isfinite(number):
        return Err(HeadsetDeny(HeadsetDenyCode.NON_FINITE, field, value))
    return Ok(number)


def _in_range(
    field: Field, value: object, low: float, high: float
) -> Result[float, HeadsetDeny]:
    found = _finite(field, value)
    if isinstance(found, Err):
        return found
    if found.value < low or found.value > high:
        return Err(HeadsetDeny(HeadsetDenyCode.OUT_OF_RANGE, field, value))
    return found
