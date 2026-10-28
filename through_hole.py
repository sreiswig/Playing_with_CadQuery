from cq_artifacts.outcome import Err
from cq_artifacts.through_hole_dims import (
    DEFAULT_HOLE_DIAMETER_MM,
    DEFAULT_HOLE_X_MM,
    DEFAULT_HOLE_Y_MM,
    DEFAULT_PLATE_LENGTH_MM,
    DEFAULT_PLATE_THICKNESS_MM,
    DEFAULT_PLATE_WIDTH_MM,
    make_through_hole,
    through_hole_deny_message,
)


def create_through_hole(
    diameter: float = DEFAULT_HOLE_DIAMETER_MM,
    length: float = DEFAULT_PLATE_LENGTH_MM,
    width: float = DEFAULT_PLATE_WIDTH_MM,
    thickness: float = DEFAULT_PLATE_THICKNESS_MM,
    hole_x: float = DEFAULT_HOLE_X_MM,
    hole_y: float = DEFAULT_HOLE_Y_MM,
):
    """Plate with one cylindrical through hole. Units: millimetres.

    The default diameter is 3.4 mm, the ISO 273:1979 medium-series
    clearance hole for an M3 screw. ``length``, ``width``, and
    ``thickness`` are the plate extents (X, Y, Z). ``hole_x`` and
    ``hole_y`` place the hole axis relative to the plate centre. The
    hole is parallel to the thickness and must lie strictly inside the
    plate.
    """
    sized = make_through_hole(diameter, length, width, thickness, hole_x, hole_y)
    if isinstance(sized, Err):
        raise ValueError(through_hole_deny_message(sized.error))
    spec = sized.value
    import cadquery as cq

    plate = cq.Workplane("XY").box(spec.length_mm, spec.width_mm, spec.thickness_mm)
    # Extrude past both faces so the cutter is not coincident with the plate.
    cutter = (
        cq.Workplane("XY")
        .center(spec.hole_x_mm, spec.hole_y_mm)
        .circle(spec.diameter_mm / 2.0)
        .extrude(spec.thickness_mm, both=True)
    )
    return plate.cut(cutter)


if __name__ == "__main__":
    import cadquery as cq

    model = create_through_hole()
    cq.exporters.export(model, "through-hole.step")
    print("Through-hole model exported to through-hole.step")

if "show_object" in globals():
    show_object(create_through_hole())
