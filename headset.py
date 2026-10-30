"""Parametric wireless-headset shell kit.

Local earcup frame: +X toward the face, +Y up, +Z out from the ear. The pad
face is z = 0; the pad lip hangs toward -Z. Defaults live in
``cq_artifacts.headset_dims`` (50 mm driver, 105 mm headband radius, M3
clearance holes of 3.4 mm, ISO 4762 screws).

``create_headset_earcup`` is the electronics cup and its back cover in that
local frame. ``create_headset_headband`` is the arc as worn, centred on the
head. ``create_headset_yoke`` is the right-hand yoke with the extension-screw
hole on the origin. ``create_headset`` places both cups, both yokes, both
covers, and the screws.
"""

from __future__ import annotations

import math

from cq_artifacts.headset_dims import (
    BACK_WALL_MM,
    BAND_THICKNESS_MM,
    BAND_WIDTH_MM,
    COVER_THICKNESS_MM,
    CLEVIS_EAR_THICKNESS_MM,
    CLEVIS_GAP_MM,
    DEFAULT_ARC_DEG,
    DEFAULT_DRIVER_DIAMETER_MM,
    DEFAULT_INNER_RADIUS_MM,
    DEFAULT_TRAVEL_MM,
    EAR_OPENING_HEIGHT_MM,
    EAR_OPENING_WIDTH_MM,
    LIP_HEIGHT_MM,
    LIP_LAND_MM,
    WALL_MM,
    MIC_BOSS_DIAMETER_MM,
    MIC_BOSS_EMBED_MM,
    MIC_BOSS_LENGTH_MM,
    MIC_DIAMETER_MM,
    OUTER_CORNER_RADIUS_MM,
    OUTER_DEPTH_MM,
    OUTER_HEIGHT_MM,
    OUTER_WIDTH_MM,
    PART_GAP_MM,
    PASS_HEIGHT_MM,
    PASS_WIDTH_MM,
    TRUNNION_DIAMETER_MM,
    TRUNNION_LENGTH_MM,
    HeadsetLayout,
    headset_deny_message,
    make_headset,
)
from cq_artifacts.outcome import Err

# Through-cuts run this far past the wall so the cutter is not coincident
# with the face. Not a part dimension.
_CUTTER_OVERSHOOT_MM = 0.6
_LIP_EMBED_MM = 0.4


def create_headset_earcup(
    driver_diameter: float = DEFAULT_DRIVER_DIAMETER_MM,
    mic_port: bool = True,
):
    """Electronics earcup shell and back cover. Units: millimetres.

    The shell is open on the ear face, with a pad lip, a driver seat for
    ``driver_diameter`` (40–50 mm), a bay behind it for the PCB and LiPo,
    a top flex slot, and optional mic-boom port. Four 3.4 mm cover holes
    match the cover. The cover sits ``PART_GAP_MM`` behind the shell.
    """
    layout = _require(driver_diameter=driver_diameter, mic_port=mic_port)
    return _compound(
        (
            _build_shell(layout, mic_port=mic_port),
            _build_cover(layout),
        )
    )


def create_headset_headband(
    inner_radius: float = DEFAULT_INNER_RADIUS_MM,
    arc_deg: float = DEFAULT_ARC_DEG,
    travel: float = DEFAULT_TRAVEL_MM,
):
    """Headband arc and two legs with M3 extension slots. Units: millimetres."""
    layout = _require(inner_radius=inner_radius, arc_deg=arc_deg, travel=travel)
    return _build_headband(layout)


def create_headset_yoke(
    inner_radius: float = DEFAULT_INNER_RADIUS_MM,
    arc_deg: float = DEFAULT_ARC_DEG,
    travel: float = DEFAULT_TRAVEL_MM,
    extension_offset: float = 0.0,
    swivel_deg: float = 0.0,
):
    """Right-hand hinge yoke. The extension hole is centred on the origin.

    The plate normal is +X. The clevis runs toward +X and down (−Y) from
    the plate, matching the worn pose before the recentre.
    """
    layout = _require(
        inner_radius=inner_radius,
        arc_deg=arc_deg,
        travel=travel,
        extension_offset=extension_offset,
        swivel_deg=swivel_deg,
    )
    yoke = _swivel(_build_yoke(layout), layout)
    mid_x = (layout.plate.xmin + layout.plate.xmax) / 2.0
    return yoke.translate((-mid_x, -layout.screw_y_mm, 0.0))


def create_headset(
    driver_diameter: float = DEFAULT_DRIVER_DIAMETER_MM,
    inner_radius: float = DEFAULT_INNER_RADIUS_MM,
    arc_deg: float = DEFAULT_ARC_DEG,
    travel: float = DEFAULT_TRAVEL_MM,
    extension_offset: float = 0.0,
    hinge_deg: float = 0.0,
    swivel_deg: float = 0.0,
    mic_port: bool = True,
):
    """Both cups, the headband, both yokes, and the M3 screws. One compound."""
    layout = _require(
        driver_diameter=driver_diameter,
        inner_radius=inner_radius,
        arc_deg=arc_deg,
        travel=travel,
        extension_offset=extension_offset,
        hinge_deg=hinge_deg,
        swivel_deg=swivel_deg,
        mic_port=mic_port,
    )
    return _compound(assemble_parts(layout).values())


def assemble_parts(layout: HeadsetLayout) -> dict:
    """Named solids in the worn pose. Screws come from ``create_m3_shcs``."""
    right_shell = place_earcup(_build_shell(layout, mic_port=layout.mic_port), layout, side="right")
    left_shell = place_earcup(_build_shell(layout, mic_port=False), layout, side="left")
    right_cover = place_earcup(_build_cover(layout), layout, side="right")
    left_cover = place_earcup(_build_cover(layout), layout, side="left")
    right_yoke = _swivel(_build_yoke(layout), layout)
    left_yoke = right_yoke.mirror("YZ")
    parts = {
        "headband": _build_headband(layout),
        "right-shell": right_shell,
        "left-shell": left_shell,
        "right-cover": right_cover,
        "left-cover": left_cover,
        "right-yoke": right_yoke,
        "left-yoke": left_yoke,
    }
    right_screws = []
    for joint in layout.joints:
        if joint.side != "right":
            continue
        screw = _place_screw(joint.length_mm, joint.bearing, joint.head_direction)
        parts[joint.name] = screw
        right_screws.append((joint.name, screw))
    for name, screw in right_screws:
        left_name = "left" + name[len("right") :]
        parts[left_name] = screw.mirror("YZ")
    return parts


def place_earcup(shape, layout: HeadsetLayout, *, side: str = "right"):
    """Move an earcup-local solid onto the right cup, then mirror for the left."""
    placed = _rotate_about(
        shape,
        layout.earcup.trunnion_center_mm,
        (1.0, 0.0, 0.0),
        layout.hinge_deg,
    )
    # (x, y, z) → (z, y, x), then the pad origin, then swivel about +X.
    placed = placed.mirror("YZ")
    placed = placed.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90)
    placed = placed.translate((layout.pad_x_mm, layout.ear_y_mm, 0.0))
    placed = _rotate_about(placed, layout.swivel_origin_mm, (1.0, 0.0, 0.0), layout.swivel_deg)
    if side == "left":
        placed = placed.mirror("YZ")
    elif side != "right":
        raise ValueError(f"headset side {side!r} is out_of_range")
    return placed


def _require(**kwargs) -> HeadsetLayout:
    found = make_headset(**kwargs)
    if isinstance(found, Err):
        raise ValueError(headset_deny_message(found.error))
    return found.value


def _build_shell(layout: HeadsetLayout, *, mic_port: bool):
    cup = layout.earcup
    body = _rounded_slab(
        OUTER_WIDTH_MM,
        OUTER_HEIGHT_MM,
        0.0,
        OUTER_DEPTH_MM,
        OUTER_CORNER_RADIUS_MM,
    )
    # Thin shell: one interior void, then a baffle and a cylindrical driver seat.
    body = body.cut(
        _aabb(
            -cup.inner_width_mm / 2.0,
            cup.inner_width_mm / 2.0,
            -cup.inner_height_mm / 2.0,
            cup.inner_height_mm / 2.0,
            -_CUTTER_OVERSHOOT_MM,
            cup.bay_z1_mm,
        )
    )
    fuse = 0.6
    body = body.union(
        _aabb(
            -cup.inner_width_mm / 2.0 - fuse,
            cup.inner_width_mm / 2.0 + fuse,
            -cup.inner_height_mm / 2.0 - fuse,
            cup.inner_height_mm / 2.0 + fuse,
            cup.baffle_z0_mm,
            cup.baffle_z1_mm,
        )
    )
    seat_r = cup.cavity_diameter_mm / 2.0 + WALL_MM
    seat_z0 = cup.baffle_z0_mm
    seat_z1 = cup.driver_z1_mm
    body = body.union(
        _cylinder((0.0, 0.0, (seat_z0 + seat_z1) / 2.0), seat_r, seat_z1 - seat_z0)
    )
    baffle_mid = (cup.baffle_z0_mm + cup.baffle_z1_mm) / 2.0
    body = body.cut(
        _cylinder(
            (0.0, 0.0, baffle_mid),
            cup.sound_hole_diameter_mm / 2.0,
            cup.baffle_z1_mm - cup.baffle_z0_mm + 2.0 * _CUTTER_OVERSHOOT_MM,
        )
    )
    pocket_z0 = cup.driver_z0_mm - 0.15
    pocket_z1 = cup.driver_z1_mm + 0.15
    body = body.cut(
        _cylinder(
            (0.0, 0.0, (pocket_z0 + pocket_z1) / 2.0),
            cup.cavity_diameter_mm / 2.0,
            pocket_z1 - pocket_z0,
        )
    )
    lip = _rounded_slab(
        OUTER_WIDTH_MM - 2.0 * LIP_LAND_MM,
        OUTER_HEIGHT_MM - 2.0 * LIP_LAND_MM,
        -LIP_HEIGHT_MM,
        _LIP_EMBED_MM,
        max(OUTER_CORNER_RADIUS_MM - 2.0, 1.0),
    )
    lip = lip.cut(
        _aabb(
            -EAR_OPENING_WIDTH_MM / 2.0,
            EAR_OPENING_WIDTH_MM / 2.0,
            -EAR_OPENING_HEIGHT_MM / 2.0,
            EAR_OPENING_HEIGHT_MM / 2.0,
            -LIP_HEIGHT_MM - _CUTTER_OVERSHOOT_MM,
            _LIP_EMBED_MM + _CUTTER_OVERSHOOT_MM,
        )
    )
    body = body.union(lip)
    trunnion = cup.trunnion_center_mm
    body = body.union(
        _cylinder(trunnion, TRUNNION_DIAMETER_MM / 2.0, TRUNNION_LENGTH_MM, axis="x")
    )
    body = body.cut(
        _cylinder(
            trunnion,
            layout.hole_diameter_mm / 2.0,
            TRUNNION_LENGTH_MM + 2.0 * _CUTTER_OVERSHOOT_MM,
            axis="x",
        )
    )
    hole_r = layout.hole_diameter_mm / 2.0
    back_mid = (cup.bay_z1_mm + OUTER_DEPTH_MM) / 2.0
    for hx, hy, _hz in cup.cover_hole_xy_mm:
        body = body.cut(
            _cylinder(
                (hx, hy, back_mid),
                hole_r,
                BACK_WALL_MM + 2.0 * _CUTTER_OVERSHOOT_MM,
            )
        )
    px, _py, pz = cup.pass_center_mm
    body = body.cut(
        _aabb(
            px - PASS_WIDTH_MM / 2.0,
            px + PASS_WIDTH_MM / 2.0,
            cup.inner_height_mm / 2.0 - _CUTTER_OVERSHOOT_MM,
            OUTER_HEIGHT_MM / 2.0 + _CUTTER_OVERSHOOT_MM,
            pz - PASS_HEIGHT_MM / 2.0,
            pz + PASS_HEIGHT_MM / 2.0,
        )
    )
    if mic_port:
        boss_x = OUTER_WIDTH_MM / 2.0 + MIC_BOSS_LENGTH_MM / 2.0 - MIC_BOSS_EMBED_MM
        mic_y = cup.mic_axis_mm[1]
        mic_z = cup.mic_axis_mm[2]
        body = body.union(
            _cylinder(
                (boss_x, mic_y, mic_z),
                MIC_BOSS_DIAMETER_MM / 2.0,
                MIC_BOSS_LENGTH_MM,
                axis="x",
            )
        )
        body = body.cut(
            _cylinder(
                (boss_x, mic_y, mic_z),
                MIC_DIAMETER_MM / 2.0,
                MIC_BOSS_LENGTH_MM + 4.0 * _CUTTER_OVERSHOOT_MM,
                axis="x",
            )
        )
    return body


def _build_cover(layout: HeadsetLayout):
    cup = layout.earcup
    z0 = OUTER_DEPTH_MM + PART_GAP_MM
    z1 = z0 + COVER_THICKNESS_MM
    cover = _rounded_slab(
        OUTER_WIDTH_MM,
        OUTER_HEIGHT_MM,
        z0,
        z1,
        OUTER_CORNER_RADIUS_MM,
    )
    hole_r = layout.hole_diameter_mm / 2.0
    for hx, hy, _hz in cup.cover_hole_xy_mm:
        cover = cover.cut(
            _cylinder(
                (hx, hy, (z0 + z1) / 2.0),
                hole_r,
                COVER_THICKNESS_MM + 2.0 * _CUTTER_OVERSHOOT_MM,
            )
        )
    return cover


def _build_headband(layout: HeadsetLayout):
    arc = _revolve_arc(layout.inner_radius_mm, layout.arc_deg)
    leg = _aabb(
        layout.leg.xmin,
        layout.leg.xmax,
        layout.leg.ymin,
        layout.leg.ymax,
        layout.leg.zmin,
        layout.leg.zmax,
    )
    band = arc.union(leg).union(leg.mirror("YZ"))
    slot = _extension_slot(layout)
    return band.cut(slot).cut(slot.mirror("YZ"))


def _build_yoke(layout: HeadsetLayout):
    boxes = [
        _aabb(box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
        for box in layout.yoke_boxes
    ]
    yoke = boxes[0]
    for box in boxes[1:]:
        yoke = yoke.union(box)
    hole_r = layout.hole_diameter_mm / 2.0
    plate_mid_x = (layout.plate.xmin + layout.plate.xmax) / 2.0
    yoke = yoke.cut(
        _cylinder(
            (plate_mid_x, layout.screw_y_mm, 0.0),
            hole_r,
            (layout.plate.xmax - layout.plate.xmin) + 2.0 * _CUTTER_OVERSHOOT_MM,
            axis="x",
        )
    )
    span = TRUNNION_LENGTH_MM + 2.0 * (CLEVIS_GAP_MM + CLEVIS_EAR_THICKNESS_MM)
    yoke = yoke.cut(
        _cylinder(
            layout.hinge_mm,
            hole_r,
            span + 2.0 * _CUTTER_OVERSHOOT_MM,
            axis="z",
        )
    )
    return yoke


def _revolve_arc(inner_radius: float, arc_deg: float):
    import cadquery as cq

    width = BAND_WIDTH_MM
    thick = BAND_THICKNESS_MM
    arc = (
        cq.Workplane("XZ")
        .moveTo(inner_radius, -width / 2.0)
        .lineTo(inner_radius + thick, -width / 2.0)
        .lineTo(inner_radius + thick, width / 2.0)
        .lineTo(inner_radius, width / 2.0)
        .close()
        .revolve(arc_deg, (0.0, 0.0), (0.0, 1.0))
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 90.0 - arc_deg / 2.0)
    )
    return arc


def _extension_slot(layout: HeadsetLayout):
    length = layout.travel_mm + layout.hole_diameter_mm
    return _aabb(
        layout.leg.xmin - _CUTTER_OVERSHOOT_MM,
        layout.leg.xmax + _CUTTER_OVERSHOOT_MM,
        layout.nominal_screw_y_mm - length / 2.0,
        layout.nominal_screw_y_mm + length / 2.0,
        -layout.hole_diameter_mm / 2.0,
        layout.hole_diameter_mm / 2.0,
    )


def _swivel(shape, layout: HeadsetLayout):
    return _rotate_about(shape, layout.swivel_origin_mm, (1.0, 0.0, 0.0), layout.swivel_deg)


def _place_screw(length: float, bearing: tuple[float, float, float], head_direction: tuple[float, float, float]):
    from m3_shcs import create_m3_shcs

    screw = create_m3_shcs(length)
    screw = _aim_plus_z(screw, head_direction)
    return screw.translate(bearing)


def _aim_plus_z(shape, direction: tuple[float, float, float]):
    dx, dy, dz = direction
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / norm, dy / norm, dz / norm
    axis_x, axis_y = -dy, dx
    axis_len = math.hypot(axis_x, axis_y)
    if axis_len < 1e-9:
        if dz < 0.0:
            return shape.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 180)
        return shape
    angle = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
    return shape.rotate((0.0, 0.0, 0.0), (axis_x, axis_y, 0.0), angle)


def _rotate_about(shape, origin: tuple[float, float, float], direction: tuple[float, float, float], deg: float):
    if deg == 0.0:
        return shape
    end = (
        origin[0] + direction[0],
        origin[1] + direction[1],
        origin[2] + direction[2],
    )
    return shape.rotate(origin, end, deg)


def _rounded_slab(width: float, height: float, z0: float, z1: float, radius: float):
    import cadquery as cq

    slab = (
        cq.Workplane("XY")
        .box(width, height, z1 - z0, centered=(True, True, False))
        .translate((0.0, 0.0, z0))
    )
    if radius > 0.0:
        slab = slab.edges("|Z").fillet(radius)
    return slab


def _aabb(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    zmin: float,
    zmax: float,
):
    import cadquery as cq

    return (
        cq.Workplane("XY")
        .box(xmax - xmin, ymax - ymin, zmax - zmin, centered=(True, True, True))
        .translate(((xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0))
    )


def _cylinder(origin: tuple[float, float, float], radius: float, length: float, axis: str = "z"):
    import cadquery as cq

    solid = cq.Workplane("XY").circle(radius).extrude(length).translate((0.0, 0.0, -length / 2.0))
    if axis == "x":
        solid = solid.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90)
    elif axis == "y":
        solid = solid.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90)
    elif axis != "z":
        raise ValueError(f"headset cylinder axis {axis!r} is out_of_range")
    return solid.translate(origin)


def _compound(shapes):
    import cadquery as cq

    solids = []
    for shape in shapes:
        solids.append(shape.val() if isinstance(shape, cq.Workplane) else shape)
    return cq.Compound.makeCompound(solids)


if __name__ == "__main__":
    import cadquery as cq

    cq.exporters.export(create_headset_earcup(), "headset-earcup.step")
    cq.exporters.export(create_headset_headband(), "headset-headband.step")
    cq.exporters.export(create_headset_yoke(), "headset-yoke.step")
    cq.exporters.export(create_headset(), "headset.step")
    print("Headset kit exported")

if "show_object" in globals():
    show_object(create_headset())
