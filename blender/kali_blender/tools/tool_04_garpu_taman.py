"""Garpu taman - garden hand fork: rubber/wood ergonomic handle, ferrule, steel neck and
three slightly curved pointed prongs at +Z.

Grip on the handle at the origin.
"""
import bpy  # must be first
from math import radians, sin, cos
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 4,
    "name": "SM_Tool_GarpuTaman",
    "label": "Garpu taman (garden hand fork)",
    "head_dir": "+Z",
    "palette": [
        ("#8a5a34", 0.0, 0.30),  # 0 wood handle
        ("#b5bcc4", 1.0, 0.60),  # 1 polished steel neck and prongs
        ("#4f555c", 0.8, 0.35),  # 2 dark steel ferrule and crossbar
    ],
}

PRONG_BASE_Z = 0.075
PRONG_BEND_Z = 0.125
PRONG_X = (-0.03, 0.0, 0.03)
PRONG_TILT = radians(8)


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _seg(a, b, r1, r2, verts=6):
    """Tapered cone from point a (radius r1) to point b (radius r2)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r1, radius2=r2, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def build():
    parts = []

    # ergonomic tapered handle, origin lies on its axis
    handle = _add("cone", vertices=16, radius1=0.0175, radius2=0.0145, depth=0.135,
                  end_fill_type="NGON", location=(0, 0, -0.0625))
    parts.append(tc.tag(handle, 0))

    # rounded butt cap
    cap = _add("uv_sphere", segments=12, ring_count=6, radius=0.0185, location=(0, 0, -0.13))
    parts.append(tc.tag(cap, 0))

    # steel ferrule where the handle meets the neck
    ferrule = _add("cylinder", vertices=12, radius=0.0155, depth=0.02, location=(0, 0, 0.015))
    parts.append(tc.tag(ferrule, 2))

    # steel neck
    neck = _seg((0, 0, 0.025), (0, 0, PRONG_BASE_Z), 0.0075, 0.007, verts=8)
    parts.append(tc.tag(neck, 1))

    # crossbar joining the prong bases
    bar = _add("cube", size=2, location=(0, 0, PRONG_BASE_Z))
    bar.scale = (0.042, 0.0045, 0.006)
    parts.append(tc.tag(bar, 2))

    # three slightly curved prongs: a straight lower leg and a tilted tip section
    for x in PRONG_X:
        lean = PRONG_TILT * (1 if x > 0 else -1 if x < 0 else 0)
        p0 = (x, 0.0, PRONG_BASE_Z)
        p1 = (x, 0.0, PRONG_BEND_Z)
        p2 = (x + 0.06 * sin(lean), 0.0, PRONG_BEND_Z + 0.06 * cos(lean))
        parts.append(tc.tag(_seg(p0, p1, 0.0045, 0.0035, verts=8), 1))
        parts.append(tc.tag(_seg(p1, p2, 0.0035, 0.0, verts=8), 1))

    return parts
