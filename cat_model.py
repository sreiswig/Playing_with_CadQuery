import cadquery as cq

# Parameters
body_length = 20.0
body_width = 10.0
body_height = 10.0
head_radius = 7.0
leg_radius = 2.0
leg_height = 12.0
ear_height = 5.0
tail_length = 15.0
tail_radius = 1.5


def create_cat():
    """Return the cat solid. Used by python -m cq_artifacts export."""
    body = (
        cq.Workplane("XY")
        .box(body_length, body_width, body_height)
        .edges("|Z")
        .fillet(2.0)
        .translate((0, 0, body_height / 2 + leg_height))
    )

    head_center_x = body_length / 2 + head_radius * 0.5
    head_center_z = body_height / 2 + leg_height + head_radius * 0.5

    head = (
        cq.Workplane("XY")
        .sphere(head_radius)
        .translate((head_center_x, 0, head_center_z))
    )

    ear_base_radius = 2.5
    ear_offset_y = head_radius * 0.4
    ear_offset_x = head_center_x
    ear_z = head_center_z + head_radius * 0.8

    ear_left = (
        cq.Workplane("XY")
        .workplane(offset=ear_z)
        .center(ear_offset_x, ear_offset_y)
        .circle(ear_base_radius)
        .workplane(offset=ear_height)
        .center(0, 0)
        .circle(0.1)
        .loft()
    )

    ear_right = (
        cq.Workplane("XY")
        .workplane(offset=ear_z)
        .center(ear_offset_x, -ear_offset_y)
        .circle(ear_base_radius)
        .workplane(offset=ear_height)
        .center(0, 0)
        .circle(0.1)
        .loft()
    )

    leg_x_offset = body_length / 2 - leg_radius * 2
    leg_y_offset = body_width / 2 - leg_radius

    def make_leg(x, y):
        return (
            cq.Workplane("XY")
            .workplane(offset=0)
            .center(x, y)
            .circle(leg_radius)
            .extrude(leg_height)
        )

    tail_start_x = -body_length / 2
    tail_start_z = body_height / 2 + leg_height
    tail_path = (
        cq.Workplane("YZ")
        .workplane(offset=tail_start_x)
        .moveTo(0, tail_start_z)
        .spline(
            [
                (0, tail_start_z + tail_length * 0.5),
                (tail_length * 0.5, tail_start_z + tail_length),
            ],
            includeCurrent=True,
        )
    )
    tail = (
        cq.Workplane("YZ")
        .workplane(offset=tail_start_x)
        .circle(tail_radius)
        .sweep(tail_path)
    )

    return (
        body.union(head)
        .union(ear_left)
        .union(ear_right)
        .union(make_leg(leg_x_offset, leg_y_offset))
        .union(make_leg(leg_x_offset, -leg_y_offset))
        .union(make_leg(-leg_x_offset, leg_y_offset))
        .union(make_leg(-leg_x_offset, -leg_y_offset))
        .union(tail)
    )


if __name__ == "__main__":
    cat_model = create_cat()
    cq.exporters.export(cat_model, "cat.step")
    print("Cat model exported to cat.step")

if "show_object" in globals():
    show_object(create_cat())
