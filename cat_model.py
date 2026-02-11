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

# 1. Body (Rounded Box)
body = (
    cq.Workplane("XY")
    .box(body_length, body_width, body_height)
    .edges("|Z")
    .fillet(2.0)
    .translate((0, 0, body_height / 2 + leg_height))
)

# 2. Head (Sphere)
head_center_x = body_length / 2 + head_radius * 0.5
head_center_z = body_height / 2 + leg_height + head_radius * 0.5

head = (
    cq.Workplane("XY")
    .sphere(head_radius)
    .translate((head_center_x, 0, head_center_z))
)

# 3. Ears (Cones)
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
    .circle(0.1) # nearly a point
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

# 4. Legs (Cylinders)
leg_x_offset = body_length / 2 - leg_radius * 2
leg_y_offset = body_width / 2 - leg_radius
leg_z = 0

def make_leg(x, y):
    return (
        cq.Workplane("XY")
        .workplane(offset=leg_z)
        .center(x, y)
        .circle(leg_radius)
        .extrude(leg_height)
    )

leg_fl = make_leg(leg_x_offset, leg_y_offset)
leg_fr = make_leg(leg_x_offset, -leg_y_offset)
leg_bl = make_leg(-leg_x_offset, leg_y_offset)
leg_br = make_leg(-leg_x_offset, -leg_y_offset)

# 5. Tail (Spline/Sweep)
tail_start_x = -body_length / 2
tail_start_z = body_height / 2 + leg_height

# Simple tail: a cylinder sticking out and curving up
# Constructing a path for the tail
tail_path = (
    cq.Workplane("YZ")
    .workplane(offset=tail_start_x)
    .moveTo(0, tail_start_z)
    .spline([(0, tail_start_z + tail_length * 0.5), (tail_length * 0.5, tail_start_z + tail_length)], includeCurrent=True)
)

tail = (
    cq.Workplane("YZ")
    .workplane(offset=tail_start_x)
    .circle(tail_radius)
    .sweep(tail_path)
)

# Combine all parts
cat_model = (
    body
    .union(head)
    .union(ear_left)
    .union(ear_right)
    .union(leg_fl)
    .union(leg_fr)
    .union(leg_bl)
    .union(leg_br)
    # .union(tail) # Tail sweeping can be tricky with orientation, let's try a simple cylinder for robustness first if sweep fails, 
                   # but keeping sweep as it is standard.
)
# Adding tail separately to ensure union works if disjoint (though it should touch)
cat_model = cat_model.union(tail)

# Export
cq.exporters.export(cat_model, 'cat.step')
print("Cat model exported to cat.step")

# Visualization support for CQ-Editor
if 'show_object' in globals():
    show_object(cat_model)
