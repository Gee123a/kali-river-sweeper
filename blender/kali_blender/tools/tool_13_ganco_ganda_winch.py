"""Ganco ganda winch - double winch hook: 1.8 m steel pipe pole, a hand-crank winch drum near
the bottom (side plates, crank arm with knob, 4:1 gear disc), a steel cable running up the
pole to a twin grappling claw at +Z.

Grip at the origin on a rubber sleeve just above the winch.
"""
import bpy  # must be first
from math import cos, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 13,
    "name": "SM_Tool_GancoGandaWinch",
    "label": "Ganco ganda winch (double winch hook)",
    "head_dir": "+Z",
    "palette": [
        ("#8e969e", 1.0, 0.55),   # 0 steel pipe pole
        ("#4a4f55", 0.9, 0.45),   # 1 gunmetal winch drum, plates, gear
        ("#1d1d1d", 0.0, 0.35),   # 2 rubber sleeve
        ("#b0b6bd", 1.0, 0.70),   # 3 claw and shackle
        ("#c9ccd0", 1.0, 0.50),   # 4 steel cable
        ("#e0701a", 0.0, 0.35),   # 5 orange crank knob
    ],
}

POLE_BOT, POLE_TOP = -0.35, 1.45          # 1.8 m pipe
POLE_R = 0.017
DRUM_Z = -0.20
PLATE_X = 0.075


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0)):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=loc, rotation=rot)


def _seg(a, b, r, verts=6):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r, radius2=r, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def build():
    parts = []

    # steel pipe pole, butt at -0.35 m, top at 1.45 m
    parts.append(tc.tag(_cyl((0, 0, (POLE_TOP + POLE_BOT) / 2), POLE_R,
                             POLE_TOP - POLE_BOT, 10), 0))
    # pole top collar
    parts.append(tc.tag(_cyl((0, 0, POLE_TOP - 0.03), 0.022, 0.05, 10), 0))

    # rubber grip sleeve at the origin, just above the winch
    parts.append(tc.tag(_cyl((0, 0, 0.01), 0.024, 0.20, 10), 2))

    # winch: drum between two side plates, axis along X
    parts.append(tc.tag(_cyl((0, 0, DRUM_Z), 0.045, 0.13, 12, rot=(0, radians(90), 0)), 1))
    for sx in (-PLATE_X, PLATE_X):
        parts.append(tc.tag(_cyl((sx, 0, DRUM_Z), 0.07, 0.012, 12, rot=(0, radians(90), 0)), 1))
    # 4:1 gear disc on the outside of the -X plate and the pinion beside it
    parts.append(tc.tag(_cyl((-PLATE_X - 0.012, 0, DRUM_Z), 0.035, 0.010, 12,
                             rot=(0, radians(90), 0)), 1))
    parts.append(tc.tag(_cyl((-PLATE_X - 0.02, 0.02, DRUM_Z), 0.012, 0.012, 8,
                             rot=(0, radians(90), 0)), 1))

    # crank arm: from the +X side plate out to a pin, with an orange knob
    crank_x = PLATE_X + 0.006
    parts.append(tc.tag(_seg((crank_x, 0, DRUM_Z), (crank_x, 0.085, DRUM_Z), 0.007, 6), 1))
    parts.append(tc.tag(_cyl((crank_x + 0.02, 0.085, DRUM_Z), 0.014, 0.03, 8,
                             rot=(0, radians(90), 0)), 5))

    # steel cable: from the drum tangent up the pole to the claw
    parts.append(tc.tag(_seg((0, 0.03, DRUM_Z + 0.045), (0, 0.03, 1.35), 0.0045, 6), 4))

    # twin grappling claw at the top: hub, shackle stem, two opposing hook tines
    parts.append(tc.tag(_seg((0, 0, POLE_TOP - 0.02), (0, 0, 1.56), 0.010, 8), 3))
    parts.append(tc.tag(_cyl((0, 0, 1.58), 0.022, 0.05, 10), 3))
    tine_pts = [(0.0, 1.61), (0.03, 1.69), (0.07, 1.72), (0.105, 1.69), (0.11, 1.63), (0.095, 1.60)]
    for sign in (1, -1):
        for a, b in zip(tine_pts, tine_pts[1:]):
            pa = (sign * a[0], 0.0, a[1])
            pb = (sign * b[0], 0.0, b[1])
            parts.append(tc.tag(_seg(pa, pb, 0.0085, 6), 3))
    return parts
