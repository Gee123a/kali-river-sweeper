"""Capitan ular - snake grabber for medical waste B3: aluminium pole, cable-actuated jaws, +Z head."""
import bpy  # must be first
from math import cos, pi, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 10,
    "name": "SM_Tool_CapitanUlar",
    "label": "Capitan ular (snake grabber for medical waste B3)",
    "head_dir": "+Z",
    "palette": [
        ("#c9ced4", 0.9, 0.60),  # 0 aluminium pole
        ("#1f2226", 0.0, 0.35),  # 1 black trigger, guard and cable clips
        ("#ff6a13", 0.0, 0.40),  # 2 safety-orange pistol grip and jaw tips
        ("#8e969e", 0.9, 0.50),  # 3 steel actuation cable and hinge pin
        ("#9aa3ab", 0.9, 0.45),  # 4 serrated steel jaws
    ],
}

POLE_BOT, POLE_TOP = -0.1, 1.1   # 1.2 m pole; pistol grip at the origin below it
JAW_HINGE_Z = 1.15


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0)):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=loc, rotation=rot)


def _box(size, loc, rot=(0, 0, 0)):
    obj = _add("cube", size=1.0, location=loc, rotation=rot)
    obj.scale = size
    return obj


def _seg(p, q, r, verts=6):
    p, q = Vector(p), Vector(q)
    d = q - p
    obj = _add("cylinder", vertices=verts, radius=r, depth=d.length, end_fill_type="NGON",
               location=tuple((p + q) / 2))
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return obj


def build():
    parts = []

    # 1.2 m aluminium pole
    parts.append(tc.tag(_cyl((0, 0, (POLE_BOT + POLE_TOP) / 2), 0.011, POLE_TOP - POLE_BOT, 12), 0))

    # orange pistol grip centred on the origin, tilted like a pistol handle
    grip = _cyl((0, 0, 0), 0.022, 0.16, 12, rot=(0, radians(12), 0))
    parts.append(tc.tag(grip, 2))
    # black trigger lever and trigger guard loop at the front of the grip
    parts.append(tc.tag(_box((0.008, 0.012, 0.035), (0, -0.024, 0.005), (radians(-20), 0, 0)), 1))
    guard = _add("torus", major_segments=10, minor_segments=4, major_radius=0.02,
                 minor_radius=0.003, location=(0, -0.012, 0.03), rotation=(0, pi / 2, 0))
    parts.append(tc.tag(guard, 1))

    # black collar at the top of the grip where the pole enters
    parts.append(tc.tag(_cyl((0, 0, POLE_BOT + 0.02), 0.0215, 0.02, 12), 1))

    # steel actuation cable running along the pole, offset to +X, with 3 guide clips
    parts.append(tc.tag(_cyl((0.016, 0, 0.5), 0.0028, POLE_TOP - 0.15, 6), 3))
    for z in (0.2, 0.6, 0.95):
        parts.append(tc.tag(_box((0.012, 0.01, 0.02), (0.013, 0, z)), 1))

    # collar housing and hinge pin at the top of the pole
    parts.append(tc.tag(_cyl((0, 0, POLE_TOP + 0.02), 0.016, 0.04, 12), 0))
    pin = _cyl((0, 0, JAW_HINGE_Z), 0.004, 0.05, 8, rot=(pi / 2, 0, 0))
    parts.append(tc.tag(pin, 3))

    # two curved serrated jaws closing toward +Z, one on each side of the pole tip
    for side in (1, -1):
        p0 = (side * 0.014, 0.0, JAW_HINGE_Z)
        p1 = (side * 0.030, 0.0, JAW_HINGE_Z + 0.05)
        p2 = (side * 0.028, 0.0, JAW_HINGE_Z + 0.12)
        p3 = (side * 0.010, 0.0, JAW_HINGE_Z + 0.20)
        # quadratic bezier sampled into 4 segments
        pts = []
        for i in range(5):
            t = i / 4
            pts.append(tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * p1[k] + t * t * p3[k]
                             if k != 2 else
                             (1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * p2[k] + t * t * p3[k]
                             for k in range(3)))
        for a, b in zip(pts[:-1], pts[1:]):
            parts.append(tc.tag(_seg(a, b, 0.0045, 6), 4))
        # serrated teeth on the inner face of the jaw
        for a, b in zip(pts[1:-1], pts[2:-1] + pts[-1:]):
            mid = [(a[k] + b[k]) / 2 for k in range(3)]
            inner = -side * 0.006
            parts.append(tc.tag(_box((0.004, 0.006, 0.01), (mid[0] + inner, 0, mid[2])), 4))
        # orange jaw tip pad
        parts.append(tc.tag(_box((0.008, 0.012, 0.012), (pts[-1][0], 0, pts[-1][2])), 2))

    return parts
