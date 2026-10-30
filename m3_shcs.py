from cq_artifacts.m3_shcs_dims import (
    DEFAULT_LENGTH_MM,
    m3_shcs_deny_message,
    make_m3_shcs,
)
from cq_artifacts.outcome import Err

# 0.05 mm past the head face so the cutter is not coincident with it.
# This overshoot is a CAD-only modeling detail, not an ISO dimension.
# The pocket depth inside the head stays t min.
_SOCKET_CUTTER_OVERSHOOT_MM = 0.05


def create_m3_shcs(length: float = DEFAULT_LENGTH_MM):
    """ISO 4762 M3 socket head cap screw envelope. No thread helix.

    Units are millimetres. The solid uses cited envelope limits only:

    - ISO 4762 plain head: dk max 5.5, k max 3.0. No knurl, fillet, or chamfer.
    - ISO 4762 hexagon socket: nominal width across flats s = 2.5, depth
      t min = 1.3, cut from the top of the head. Across-corners is the
      regular hexagon of that s.
    - ISO 262 M3×0.5. The shank is a smooth cylinder of nominal diameter
      3.0. The pitch is not swept into a helix.
    - ISO 888:2012 nominal length is the under-head length for a screw
      with a flat bearing face perpendicular to the axis. ``length`` must
      be an unbracketed preferred value from ISO 888:2012 Table 1 in the
      range 5 mm through 30 mm: 5, 6, 8, 10, 12, 16, 20, 25, 30.
      Default 10.

    The bearing face is z = 0. The head occupies +Z and the shank occupies
    −Z. This is not an ISO 4017 hexagon-head bolt.
    """
    sized = make_m3_shcs(length)
    if isinstance(sized, Err):
        raise ValueError(m3_shcs_deny_message(sized.error))
    spec = sized.value
    import cadquery as cq

    body = (
        cq.Workplane("XY")
        .circle(spec.shank_diameter_mm / 2.0)
        .extrude(-spec.length_mm)
        .faces(">Z")
        .workplane()
        .circle(spec.head_diameter_mm / 2.0)
        .extrude(spec.head_height_mm)
    )
    socket = (
        cq.Workplane("XY")
        .workplane(offset=spec.head_height_mm + _SOCKET_CUTTER_OVERSHOOT_MM)
        .polygon(6, spec.socket_across_flats_mm, circumscribed=True)
        .extrude(-(spec.socket_depth_mm + _SOCKET_CUTTER_OVERSHOOT_MM))
    )
    return body.cut(socket)


if __name__ == "__main__":
    import cadquery as cq

    model = create_m3_shcs()
    cq.exporters.export(model, "m3-shcs.step")
    print("M3 SHCS envelope exported to m3-shcs.step")

if "show_object" in globals():
    show_object(create_m3_shcs())
