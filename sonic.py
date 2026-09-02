"""Stylized chibi Sonic-like hedgehog — original CadQuery geometry only.

No Sega meshes, textures, or copied assets. Same box/sphere/cylinder/loft
style as cat_model.py. Units: millimetres. Origin near feet, +Z up, +X forward.
"""

import cadquery as cq

# Overall ~50 mm tall chibi figure
HEAD_R = 12.0
BODY_R = 9.5
MUZZLE_R = 4.8
EAR_BASE = 2.6
EAR_H = 4.5
ARM_R = 2.3
ARM_LEN = 9.0
GLOVE_R = 4.0
GLOVE_H = 3.0
LEG_R = 2.8
LEG_H = 8.0
SHOE_L = 12.0
SHOE_W = 7.2
SHOE_H = 5.2
TAIL_R = 1.6
TAIL_LEN = 5.5


def _quill(base_r: float, tip_r: float, length: float, pitch_deg: float, yaw_deg: float):
    """Back-pointing quill loft, pitched/yawed from an origin at the loft base."""
    quill = (
        cq.Workplane("YZ")
        .circle(base_r)
        .workplane(offset=length)
        .circle(tip_r)
        .loft()
    )
    # Default loft extrudes +X; rotate so quills point back (-X) with +Z lift.
    quill = quill.rotate((0, 0, 0), (0, 1, 0), 180 + pitch_deg)
    quill = quill.rotate((0, 0, 0), (0, 0, 1), yaw_deg)
    return quill


def create_sonic():
    """Return a stylized Sonic-like solid. Used by python -m cq_artifacts export."""
    leg_z0 = SHOE_H * 0.55
    body_cz = leg_z0 + LEG_H + BODY_R * 0.85
    head_cz = body_cz + BODY_R + HEAD_R * 0.55

    body = cq.Workplane("XY").sphere(BODY_R).translate((0, 0, body_cz))
    head = cq.Workplane("XY").sphere(HEAD_R).translate((0, 0, head_cz))

    # Small muzzle sphere in front of the head (+X)
    muzzle = (
        cq.Workplane("XY")
        .sphere(MUZZLE_R)
        .translate((HEAD_R * 0.72, 0, head_cz - HEAD_R * 0.18))
    )

    # Ear stubs
    ear_z = head_cz + HEAD_R * 0.55
    ear_y = HEAD_R * 0.45
    ear_left = (
        cq.Workplane("XY")
        .workplane(offset=ear_z)
        .center(0, ear_y)
        .circle(EAR_BASE)
        .workplane(offset=EAR_H)
        .circle(0.3)
        .loft()
    )
    ear_right = (
        cq.Workplane("XY")
        .workplane(offset=ear_z)
        .center(0, -ear_y)
        .circle(EAR_BASE)
        .workplane(offset=EAR_H)
        .circle(0.3)
        .loft()
    )

    # Back spines / quills: 6, largest center
    quill_specs = [
        # base_r, tip_r, length, pitch (deg, extra lift), yaw (deg)
        (5.8, 0.5, 18.0, 20, 0),
        (4.5, 0.4, 15.5, 28, 30),
        (4.5, 0.4, 15.5, 28, -30),
        (3.6, 0.35, 13.0, 38, 52),
        (3.6, 0.35, 13.0, 38, -52),
        (2.8, 0.3, 10.5, 50, 0),
    ]
    quills = []
    for base_r, tip_r, length, pitch, yaw in quill_specs:
        q = _quill(base_r, tip_r, length, pitch, yaw)
        q = q.translate((-HEAD_R * 0.35, 0, head_cz + HEAD_R * 0.15))
        quills.append(q)

    arm_z = body_cz + 1.0
    arm_y = BODY_R * 0.65

    def make_arm(side: float):
        # Cylinder along +Y or -Y from the body
        arm = (
            cq.Workplane("XZ")
            .workplane(offset=side * arm_y)
            .center(0, arm_z)
            .circle(ARM_R)
            .extrude(side * ARM_LEN)
        )
        # Flattened glove disc (short cylinder) at the hand
        glove = (
            cq.Workplane("XZ")
            .workplane(offset=side * (arm_y + ARM_LEN * 0.85))
            .center(0.4, arm_z - 0.4)
            .circle(GLOVE_R)
            .extrude(side * GLOVE_H)
        )
        glove_ball = (
            cq.Workplane("XY")
            .sphere(GLOVE_R * 0.85)
            .translate((0.4, side * (arm_y + ARM_LEN * 0.95), arm_z - 0.4))
        )
        return arm.union(glove).union(glove_ball)

    leg_y = BODY_R * 0.38

    def make_leg(side: float):
        return (
            cq.Workplane("XY")
            .workplane(offset=leg_z0)
            .center(0, side * leg_y)
            .circle(LEG_R)
            .extrude(LEG_H)
        )

    def make_shoe(side: float):
        # Oversized, slightly elongated shoe box — reads as the classic sneakers
        shoe = (
            cq.Workplane("XY")
            .box(SHOE_L, SHOE_W, SHOE_H)
            .edges("|Z")
            .fillet(1.2)
            .translate((SHOE_L * 0.18, side * leg_y, SHOE_H / 2))
        )
        toe = (
            cq.Workplane("XY")
            .sphere(SHOE_W * 0.42)
            .translate((SHOE_L * 0.58, side * leg_y, SHOE_H * 0.42))
        )
        return shoe.union(toe)

    tail = (
        cq.Workplane("YZ")
        .workplane(offset=-BODY_R * 0.65)
        .circle(TAIL_R)
        .workplane(offset=-TAIL_LEN)
        .circle(0.2)
        .loft()
        .translate((0, 0, body_cz - 1.0))
    )

    solid = body.union(head).union(muzzle).union(ear_left).union(ear_right)
    for q in quills:
        solid = solid.union(q)
    solid = (
        solid.union(make_arm(1))
        .union(make_arm(-1))
        .union(make_leg(1))
        .union(make_leg(-1))
        .union(make_shoe(1))
        .union(make_shoe(-1))
        .union(tail)
    )
    return solid


if __name__ == "__main__":
    model = create_sonic()
    cq.exporters.export(model, "sonic.step")
    print("Sonic model exported to sonic.step")

if "show_object" in globals():
    show_object(create_sonic())
