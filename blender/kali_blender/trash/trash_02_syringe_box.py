"""Sharps container (B3) - yellow box with red lid, dark slot opening, carry handle, red trefoil
badge on the front and two loose syringes (barrel, plunger, steel needle) sticking out of the slot.

Built around the origin; build() recentres the parts on the bounding-box centre.
"""
import bpy  # must be first
from math import cos, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 2,
    "name": "SM_Trash_SyringeBox",
    "prefab": "PF_Trash_SyringeBox",
    "label": "Sharps container (B3)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "palette": [
        ("#eab308", 0.0, 0.4),   # 0 hazard yellow box
        ("#dc2626", 0.0, 0.35),  # 1 red lid + biohazard badge
        ("#1f2937", 0.0, 0.3),   # 2 dark slot, handle, plungers
        ("#cbd5e1", 0.9, 0.7),   # 3 steel needles
        ("#f1f5f9", 0.0, 0.45),  # 4 translucent white syringe barrels
    ],
}


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _box(loc, half):
    o = _add("cube", size=2, location=loc)
    o.scale = half
    return o


def _seg(a, b, r, verts=6):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r, radius2=r, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def _disc_y(x, y, z, r, verts=6, depth=0.008):
    """Flat raised disc facing -Y (badge lobe)."""
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=(x, y, z), rotation=(radians(90), 0, 0))


def _recentre(parts):
    bpy.context.view_layer.update()
    pts = [p.matrix_world @ v.co for p in parts for v in p.data.vertices]
    lo = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
    hi = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
    c = (lo + hi) / 2
    for p in parts:
        p.location = p.location - c


def build():
    parts = []
    BODY_Y = 0.085  # front face of the body at y = -BODY_Y

    # yellow box body (z -0.11 .. 0.06) and red lid overhanging it (z 0.06 .. 0.11)
    parts.append(tc.tag(_box((0, 0, -0.025), (0.135, 0.085, 0.085)), 0))
    parts.append(tc.tag(_box((0, 0, 0.085), (0.14, 0.09, 0.025)), 1))

    # dark slot opening on the lid top
    parts.append(tc.tag(_box((0, 0, 0.114), (0.075, 0.012, 0.004)), 2))

    # carry handle over the back of the lid: two posts and a top bar
    parts.append(tc.tag(_box((-0.10, 0.07, 0.13), (0.006, 0.006, 0.02)), 2))
    parts.append(tc.tag(_box((0.10, 0.07, 0.13), (0.006, 0.006, 0.02)), 2))
    parts.append(tc.tag(_box((0, 0.07, 0.15), (0.10, 0.006, 0.006)), 2))

    # red trefoil biohazard badge on the front face (-Y)
    bx, bz = 0.0, -0.03
    lobe_d, lobe_r = 0.03, 0.015
    for ang in (90, 210, 330):
        lx = bx + lobe_d * cos(radians(ang))
        lz = bz + lobe_d * sin(radians(ang))
        parts.append(tc.tag(_disc_y(lx, -BODY_Y, lz, lobe_r), 1))
    parts.append(tc.tag(_disc_y(bx, -BODY_Y, bz, 0.01), 1))

    # two loose syringes sticking out of the slot: barrel, plunger rod, needle
    syringes = [
        ((-0.035, -0.01, 0.105), (-0.05, -0.04, 0.19), (-0.055, -0.05, 0.215), (-0.06, -0.06, 0.26)),
        ((0.03, 0.01, 0.105), (0.06, 0.035, 0.19), (0.065, 0.04, 0.215), (0.075, 0.05, 0.26)),
    ]
    for a, b, c, d in syringes:
        parts.append(tc.tag(_seg(a, b, 0.01, 8), 4))   # barrel
        parts.append(tc.tag(_seg(b, c, 0.004, 6), 2))  # plunger rod
        parts.append(tc.tag(_seg(c, d, 0.0015, 6), 3)) # needle

    _recentre(parts)
    return parts
