"""Ember cat 5L - used 5 litre paint pail: tapered galvanised body, rolled rim, ear lugs,
wire bail with a plastic grip tube and paint drip streaks.

Grip at the origin = middle of the bail's grip tube; the pail hangs below (-Z).
"""
import bpy  # must be first
from math import cos, radians, sin, pi
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 5,
    "name": "SM_Tool_EmberCat5L",
    "label": "Ember cat 5L (5 litre paint pail)",
    "head_dir": "-Z",
    "palette": [
        ("#8c949c", 0.6, 0.35),  # 0 galvanised pail and rim
        ("#c8402a", 0.0, 0.45),  # 1 paint drip streaks
        ("#1e1e1e", 0.0, 0.30),  # 2 bail grip tube
        ("#6f767d", 1.0, 0.45),  # 3 wire bail, ear lugs, pins
    ],
}

TOP_Z = -0.07        # rim height
BOT_Z = -0.28        # bottom of the pail (height 0.21 m)
R_TOP = 0.11         # top diameter 0.22 m
R_BOT = 0.095        # bottom diameter 0.19 m
EAR_Z = -0.06        # bail ends (ear lugs) height
BAIL_RX = 0.11       # bail half width (ends on the ears)
BAIL_RZ = 0.06       # bail arc height above EAR_Z (top of arc at z = 0)


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def _box(loc, half, rot=(0, 0, 0)):
    o = _add("cube", size=2, location=loc, rotation=rot)
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


def _wall_r(z):
    """Outer wall radius at height z (tapered from R_BOT at the bottom to R_TOP at the rim)."""
    return R_BOT + (z - BOT_Z) / (TOP_Z - BOT_Z) * (R_TOP - R_BOT)


def build():
    parts = []

    # tapered pail body, open top; bottom closed separately
    body = _add("cone", vertices=16, radius1=R_BOT, radius2=R_TOP, depth=TOP_Z - BOT_Z,
                end_fill_type="NOTHING", location=(0, 0, (TOP_Z + BOT_Z) / 2))
    parts.append(tc.tag(body, 0))
    parts.append(tc.tag(_cyl((0, 0, BOT_Z + 0.002), R_BOT, 0.004, 16), 0))

    # rolled rim around the opening
    rim = _add("torus", major_segments=16, minor_segments=5, major_radius=R_TOP,
               minor_radius=0.007, location=(0, 0, TOP_Z))
    parts.append(tc.tag(rim, 0))

    # paint drip streaks running down the outside wall from the rim
    drips = [(-60, 0.07), (-20, 0.10), (25, 0.05), (110, 0.09), (170, 0.06), (240, 0.08)]
    for theta_deg, length in drips:
        th = radians(theta_deg)
        zc = TOP_Z - 0.005 - length / 2
        r = _wall_r(zc) + 0.0015
        pos = (r * cos(th), r * sin(th), zc)
        parts.append(tc.tag(_box(pos, (0.003, 0.0015, length / 2), rot=(0, 0, th - pi / 2)), 1))

    # ear lugs where the bail ends meet the rim
    for sx in (-1, 1):
        ear = _box((sx * (R_TOP + 0.002), 0, EAR_Z), (0.006, 0.012, 0.008))
        parts.append(tc.tag(ear, 3))

    # wire bail: half ellipse from ear to ear over the top
    steps = 10
    pts = []
    for i in range(steps + 1):
        t = pi * i / steps
        pts.append((BAIL_RX * cos(t), 0.0, EAR_Z + BAIL_RZ * sin(t)))
    for a, b in zip(pts[:-1], pts[1:]):
        parts.append(tc.tag(_seg(a, b, 0.0035, verts=6), 3))

    # plastic grip tube centred on the origin, lying along X over the top of the bail
    grip = _cyl((0, 0, 0), 0.011, 0.09, 10, rot=(0, radians(90), 0))
    parts.append(tc.tag(grip, 2))

    return parts
