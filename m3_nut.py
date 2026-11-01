from cq_artifacts.m3_nut_dims import make_m3_nut

# 0.05 mm past each face so the cutter is not coincident with it.
# This overshoot is a CAD-only modeling detail, not an ISO dimension.
_BORE_CUTTER_OVERSHOOT_MM = 0.05


def create_m3_nut():
    """ISO 4032 style 1 M3 hex nut envelope. No thread helix.

    Units are millimetres. The solid uses cited envelope limits only:

    - ISO 4032 width across flats s max = nominal = 5.5. No chamfer and
      no washer face. Across-corners is the regular hexagon of that s,
      which is wider than the standard's e min of 6.01.
    - ISO 4032 nut height m max = 2.4.
    - The bore is ISO 4032 da min, 3.0 mm, the ISO 262 nominal major
      diameter (M3×0.5). The pitch is not swept into a helix.

    One face is z = 0 and the nut occupies +Z. Flats are perpendicular
    to X, the same circumscribed hexagon as the M3 SHCS socket. This is
    not an ISO 4033 style 2 nut.
    """
    spec = make_m3_nut()
    import cadquery as cq

    body = (
        cq.Workplane("XY")
        .polygon(6, spec.across_flats_mm, circumscribed=True)
        .extrude(spec.height_mm)
    )
    bore = (
        cq.Workplane("XY")
        .workplane(offset=spec.height_mm + _BORE_CUTTER_OVERSHOOT_MM)
        .circle(spec.bore_diameter_mm / 2.0)
        .extrude(-(spec.height_mm + 2.0 * _BORE_CUTTER_OVERSHOOT_MM))
    )
    return body.cut(bore)


if __name__ == "__main__":
    import cadquery as cq

    model = create_m3_nut()
    cq.exporters.export(model, "m3-nut.step")
    print("M3 hex nut envelope exported to m3-nut.step")

if "show_object" in globals():
    show_object(create_m3_nut())
