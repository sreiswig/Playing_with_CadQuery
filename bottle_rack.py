"""Parametric gravity-fed FIFO water-bottle rack.

One module holds bottles on their sides in sloped lanes. Local frame: +X
right, +Y toward the inlet, +Z up. Stack feet extend below z = 0. Defaults
live in ``cq_artifacts.bottle_rack_dims`` (110 × 310 mm bottle, 3 lanes by
5 deep, 7° slope, 12 mm plywood).

``create_bottle_rack_guide`` is one lane guide in print orientation.
``create_bottle_rack_gate`` is one outlet lift gate in print orientation.
``create_bottle_rack`` places the plywood, the 2020 outer envelopes, both
guides per lane, the gates, the stack feet, and the tile pins.
"""

from __future__ import annotations

from cq_artifacts.bottle_rack_dims import (
    DEFAULT_BOTTLE_DIAMETER_MM,
    DEFAULT_BOTTLE_LENGTH_MM,
    DEFAULT_DEPTH,
    DEFAULT_LANES,
    DEFAULT_SLOPE_DEG,
    DEFAULT_THICKNESS_MM,
    GUIDE_SCREWS_EACH,
    BottleRackLayout,
    bottle_rack_deny_message,
    make_bottle_rack,
)
from cq_artifacts.outcome import Err

# Bleed past a face so a cutter is not coincident with it. Not a part dimension.
_HOLE_PAST_MM = 0.6


def create_bottle_rack_guide(
    bottle_diameter: float = DEFAULT_BOTTLE_DIAMETER_MM,
    bottle_length: float = DEFAULT_BOTTLE_LENGTH_MM,
    lanes: int = DEFAULT_LANES,
    depth: int = DEFAULT_DEPTH,
    slope_deg: float = DEFAULT_SLOPE_DEG,
    thickness: float = DEFAULT_THICKNESS_MM,
):
    """Left lane guide, flat on the print bed. Units: millimetres.

    Length runs along +Y, the flange is +X, and the rail stands on +Z.
    Three 3.4 mm holes sit in the flange.
    """
    layout = _require(
        bottle_diameter=bottle_diameter,
        bottle_length=bottle_length,
        lanes=lanes,
        depth=depth,
        slope_deg=slope_deg,
        thickness=thickness,
    )
    return _guide_print(layout, side="left")


def create_bottle_rack_gate(
    bottle_diameter: float = DEFAULT_BOTTLE_DIAMETER_MM,
    bottle_length: float = DEFAULT_BOTTLE_LENGTH_MM,
    lanes: int = DEFAULT_LANES,
    depth: int = DEFAULT_DEPTH,
    slope_deg: float = DEFAULT_SLOPE_DEG,
    thickness: float = DEFAULT_THICKNESS_MM,
):
    """Outlet lift gate, flat on the print bed. Units: millimetres.

    Width runs along +X, height along +Y, and thickness along +Z. A finger
    notch is cut from the top edge.
    """
    layout = _require(
        bottle_diameter=bottle_diameter,
        bottle_length=bottle_length,
        lanes=lanes,
        depth=depth,
        slope_deg=slope_deg,
        thickness=thickness,
    )
    return _gate_print(layout)


def create_bottle_rack(
    bottle_diameter: float = DEFAULT_BOTTLE_DIAMETER_MM,
    bottle_length: float = DEFAULT_BOTTLE_LENGTH_MM,
    lanes: int = DEFAULT_LANES,
    depth: int = DEFAULT_DEPTH,
    slope_deg: float = DEFAULT_SLOPE_DEG,
    thickness: float = DEFAULT_THICKNESS_MM,
):
    """One bottle-rack module. Units: millimetres.

    Plywood carcass, 20×20 mm 2020 envelopes at the rear posts and the top
    rails, printed lane guides and lift gates, stack feet, and side-tile pins.
    """
    layout = _require(
        bottle_diameter=bottle_diameter,
        bottle_length=bottle_length,
        lanes=lanes,
        depth=depth,
        slope_deg=slope_deg,
        thickness=thickness,
    )
    return _compound(assemble_parts(layout).values())


def assemble_parts(layout: BottleRackLayout) -> dict:
    """Named solids for one module. Keys match ``layout.samples``."""
    parts: dict = {}
    for name, box in layout.panels.items():
        solid = _box(box.x0, box.x1, box.y0, box.y1, box.z0, box.z1)
        for cutter in layout.cuts.get(name, ()):
            solid = solid.cut(_box(cutter.x0, cutter.x1, cutter.y0, cutter.y1, cutter.z0, cutter.z1))
        for hole in layout.holes:
            if hole.part == name:
                solid = solid.cut(_hole(hole.origin, hole.axis, hole.diameter, hole.length))
        parts[name] = solid

    for index, (main, toe) in enumerate(layout.feet):
        block = _box(main.x0, main.x1, main.y0, main.y1, main.z0, main.z1)
        hook = _box(toe.x0, toe.x1, toe.y0, toe.y1, toe.z0, toe.z1)
        parts[f"foot-{index}"] = block.union(hook)

    for pin in layout.pins:
        parts[pin.part] = _hole(pin.origin, pin.axis, pin.diameter, pin.length)

    for lane in range(layout.lanes):
        parts[f"deck-{lane}"] = _deck(layout, lane)
        for side in ("left", "right"):
            origin = next(
                place.origin for place in layout.guides if place.side == side and place.lane == lane
            )
            guide = _guide_print(layout, side=side)
            guide = guide.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), layout.slope_deg)
            parts[f"guide-{side}-{lane}"] = guide.translate(origin)
        gate = layout.gates[lane]
        plate = _gate_print(layout)
        # Print +Y becomes +Z and print +Z becomes −Y, so the gate stands
        # in front of the lane with its notch at the top.
        plate = plate.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        parts[f"gate-{lane}"] = plate.translate((gate.x0, gate.y1, gate.z0))
    return parts


def _require(**kwargs) -> BottleRackLayout:
    found = make_bottle_rack(**kwargs)
    if isinstance(found, Err):
        raise ValueError(bottle_rack_deny_message(found.error))
    return found.value


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    import cadquery as cq

    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0)
        .translate(((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0))
    )


def _hole(origin, axis: str, diameter: float, length: float):
    import cadquery as cq

    solid = (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
    if axis == "x":
        solid = solid.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
    elif axis == "y":
        solid = solid.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
    elif axis != "z":
        raise ValueError(f"bottle rack hole axis {axis!r} is out_of_range")
    return solid.translate(origin)


def _deck(layout: BottleRackLayout, lane: int):
    import cadquery as cq

    solid = cq.Workplane("XY").box(layout.deck_width_mm, layout.deck_along_mm, layout.thickness_mm)
    solid = solid.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), layout.slope_deg)
    return solid.translate(layout.deck_world(0.0, 0.0, 0.0, lane))


def _guide_print(layout: BottleRackLayout, side: str):
    width = layout.guide_width_mm
    length = layout.deck_along_mm
    base = layout.guide_base_mm
    rail_h = layout.guide_rail_height_mm
    rail_t = layout.guide_rail_thickness_mm
    if side == "left":
        rail_x0 = width - rail_t
        hole_x = (width - rail_t) / 2.0
    elif side == "right":
        rail_x0 = 0.0
        hole_x = rail_t + (width - rail_t) / 2.0
    else:
        raise ValueError(f"bottle rack guide side {side!r} is out_of_range")
    solid = _box(0.0, width, 0.0, length, 0.0, base).union(
        _box(rail_x0, rail_x0 + rail_t, 0.0, length, base - 0.2, rail_h)
    )
    for index in range(GUIDE_SCREWS_EACH):
        y = length * (index + 1) / (GUIDE_SCREWS_EACH + 1)
        solid = solid.cut(
            _hole((hole_x, y, base / 2.0), "z", layout.hole_diameter_mm, base + 2.0 * _HOLE_PAST_MM)
        )
    return solid


def _gate_print(layout: BottleRackLayout):
    width = layout.gate_width_mm
    height = layout.gate_height_mm
    thick = layout.gate_thickness_mm
    notch_w = layout.gate_notch_width_mm
    notch_h = layout.gate_notch_height_mm
    solid = _box(0.0, width, 0.0, height, 0.0, thick)
    return solid.cut(
        _box(
            width / 2.0 - notch_w / 2.0,
            width / 2.0 + notch_w / 2.0,
            height - notch_h,
            height + _HOLE_PAST_MM,
            -_HOLE_PAST_MM,
            thick + _HOLE_PAST_MM,
        )
    )


def _compound(shapes):
    import cadquery as cq

    solids = []
    for shape in shapes:
        solids.append(shape.val() if isinstance(shape, cq.Workplane) else shape)
    return cq.Compound.makeCompound(solids)


if __name__ == "__main__":
    import cadquery as cq

    cq.exporters.export(create_bottle_rack_guide(), "bottle-rack-guide.step")
    cq.exporters.export(create_bottle_rack_gate(), "bottle-rack-gate.step")
    cq.exporters.export(create_bottle_rack(), "bottle-rack.step")
    print("Bottle rack exported")

if "show_object" in globals():
    show_object(create_bottle_rack())
