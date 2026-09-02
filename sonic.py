"""Stylized chibi Sonic-like hedgehog — original CadQuery geometry only.

No Sega meshes, textures, or copied assets. Same box/sphere/cylinder/loft
style as cat_model.py. Units: millimetres. Origin near feet, +Z up, +X forward.
"""

import math

import cadquery as cq

# Overall ~40–50 mm tall chibi figure
HEAD_R = 12.0
BODY_R = 9.5
MUZZLE_R = 4.8
EAR_W = 3.0
EAR_D = 2.2
EAR_H = 4.2
ARM_L = 9.0
ARM_T = 2.6
GLOVE_R = 3.8
LEG_R = 2.3
LEG_H = 5.5
SHOE_L = 12.0
SHOE_W = 7.2
SHOE_H = 5.2


def _prism_quill(length, half_w, half_h, origin, direction):
    """Back-pointing triangular quill loft (polyhedral, compact STEP)."""
    quill = (
        cq.Workplane("YZ")
        .moveTo(0, half_h)
        .lineTo(half_w, -half_h)
        .lineTo(-half_w, -half_h)
        .close()
        .workplane(offset=length)
        .moveTo(0, 0.35)
        .lineTo(0.4, -0.25)
        .lineTo(-0.4, -0.25)
        .close()
        .loft()
    )
    dx, dy, dz = direction
    yaw = math.degrees(math.atan2(dy, dx))
    hyp = math.hypot(dx, dy) or 1e-9
    pitch = -math.degrees(math.atan2(dz, hyp))
    quill = quill.rotate((0, 0, 0), (0, 0, 1), yaw)
    quill = quill.rotate((0, 0, 0), (0, 1, 0), pitch)
    return quill.translate(origin)


def create_sonic():
    """Return a stylized Sonic-like solid. Used by python -m cq_artifacts export."""
    leg_z0 = SHOE_H * 0.85
    body_cz = leg_z0 + LEG_H + BODY_R * 0.55
    head_cz = body_cz + BODY_R + HEAD_R * 0.45

    body = cq.Workplane("XY").sphere(BODY_R).translate((0, 0, body_cz))
    head = cq.Workplane("XY").sphere(HEAD_R).translate((0, 0, head_cz))
    muzzle = (
        cq.Workplane("XY")
        .sphere(MUZZLE_R)
        .translate((HEAD_R * 0.72, 0, head_cz - HEAD_R * 0.18))
    )

    ear_z = head_cz + HEAD_R * 0.55
    ear_y = HEAD_R * 0.42
    ear_left = cq.Workplane("XY").box(EAR_D, EAR_W, EAR_H).translate((0, ear_y, ear_z))
    ear_right = cq.Workplane("XY").box(EAR_D, EAR_W, EAR_H).translate((0, -ear_y, ear_z))

    quill_specs = [
        (16.0, 3.2, 3.0, (-HEAD_R * 0.5, 0.0, head_cz + 2.0), (-1.0, 0.0, 0.22)),
        (14.0, 2.6, 2.4, (-HEAD_R * 0.4, 5.0, head_cz + 1.0), (-0.9, 0.5, 0.18)),
        (14.0, 2.6, 2.4, (-HEAD_R * 0.4, -5.0, head_cz + 1.0), (-0.9, -0.5, 0.18)),
        (12.0, 2.2, 2.0, (-HEAD_R * 0.3, 8.0, head_cz - 1.0), (-0.7, 0.75, 0.12)),
        (12.0, 2.2, 2.0, (-HEAD_R * 0.3, -8.0, head_cz - 1.0), (-0.7, -0.75, 0.12)),
        (11.0, 2.0, 1.8, (-HEAD_R * 0.2, 0.0, head_cz + HEAD_R * 0.7), (-0.25, 0.0, 1.0)),
    ]
    quills = [_prism_quill(*spec) for spec in quill_specs]

    arm_z = body_cz + 1.2
    arm_y = BODY_R * 0.55
    arm_left = cq.Workplane("XY").box(ARM_T, ARM_L, ARM_T).translate((0, arm_y + ARM_L / 2, arm_z))
    arm_right = cq.Workplane("XY").box(ARM_T, ARM_L, ARM_T).translate((0, -(arm_y + ARM_L / 2), arm_z))
    glove_left = cq.Workplane("XY").sphere(GLOVE_R).translate((0.3, arm_y + ARM_L * 0.95, arm_z))
    glove_right = cq.Workplane("XY").sphere(GLOVE_R).translate((0.3, -(arm_y + ARM_L * 0.95), arm_z))

    leg_y = BODY_R * 0.38
    leg_left = cq.Workplane("XY").box(LEG_R * 2, LEG_R * 2, LEG_H).translate((0, leg_y, leg_z0 + LEG_H / 2))
    leg_right = cq.Workplane("XY").box(LEG_R * 2, LEG_R * 2, LEG_H).translate((0, -leg_y, leg_z0 + LEG_H / 2))

    shoe_left = (
        cq.Workplane("XY")
        .box(SHOE_L, SHOE_W, SHOE_H)
        .translate((SHOE_L * 0.18, leg_y, SHOE_H / 2))
    )
    shoe_right = (
        cq.Workplane("XY")
        .box(SHOE_L, SHOE_W, SHOE_H)
        .translate((SHOE_L * 0.18, -leg_y, SHOE_H / 2))
    )

    solid = body.union(head).union(muzzle).union(ear_left).union(ear_right)
    for q in quills:
        solid = solid.union(q)
    solid = (
        solid.union(arm_left)
        .union(arm_right)
        .union(glove_left)
        .union(glove_right)
        .union(leg_left)
        .union(leg_right)
        .union(shoe_left)
        .union(shoe_right)
    )
    return solid


if __name__ == "__main__":
    model = create_sonic()
    cq.exporters.export(model, "sonic.step")
    print("Sonic model exported to sonic.step")

if "show_object" in globals():
    show_object(create_sonic())
