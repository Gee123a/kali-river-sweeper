"""Ember cat - tapered used paint pail with rolled rim, ear lugs, wire bail and drip streaks.

Grip at the origin = middle of the bail's grip tube; the pail hangs below (-Z).
"""
import bpy  # must be first
from math import cos, radians, sin, pi
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 5,
    "name": "SM_Tool_EmberCat",
    "label": "Ember cat (used paint pail)",
    "head_dir": "-Z",
    "palette": [
        ("#8c949c", 0.6, 0.35),  # 0 galvanised pail and rim
        ("#c8402a", 0.0, 0.45),  # 1 paint drip streaks
        ("#1e1e1e", 0.0, 0.30),  # 2 bail grip tube
        ("#6f767d", 1.0, 0.45),  # 3 wire bail, ear lugs, pins
    ],
}

TOP_Z = -0.12      # rim height
BOT_Z = -0.44      # bottom of the pail
R_TOP = 0.15
R_BOT = 0.13
EAR_X = 0.158      # bail ends (ear lugs) at x = +/-EAR_X, z = EAR_Z
EAR_Z = -0.135
BAIL_RX = 0.158    # bail is a half ellipse: x = RX cos t, z = EAR_Z + RZ sin t
BAIL_RZ = 0.135


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

    # tapered pail body, open top, bottom closed separately
    body = _add("cone", vertices=16, radius1=R_BOT, radius2=R_TOP, depth=TOP_Z - BOT_Z,
                end_fill_type="NOTHING", location=(0, 0, (TOP_Z + BOT_Z) / 2))
    parts.append(tc.tag(body, 0))
    parts.append(tc.tag(_cyl((0, 0, BOT_Z + 0.002), R_BOT, 0.004, 16), 0))

    # rolled rim around the opening
    rim = _add("torus", major_segments=16, minor_segments=5, major_radius=R_TOP,
               minor_radius=0.007, location=(0, 0, TOP_Z))
    parts.append(tc.tag(rim, 0))

    # paint drip streaks running down the outside wall (second colour)
    drips = [(-60, 0.09), (-20, 0.12), (25, 0.06), (110, 0.11), (170, 0.07), (240, 0.10)]
    for theta, length in drips:
        zc = TOP_Z - 0.008 - length / 2
        r = _wall_r(zc) + 0.0012
        x, y = r * cos(radians(theta)), r * sin(radians(theta))
        # local X = tangent, local Y = radial, local Z = vertical
        d = _box((x, y, zc), (0.0065, 0.0018, length / 2), rot=(0, 0, radians(theta - 90)))
        parts.append(tc.tag(d, 1))

    # ear lugs on the outside wall, one each side, with pivot pins
    for sx in (-1, 1):
        lug = _box((sx * 0.153, 0, EAR_Z), (0.010, 0.012, 0.012))
        parts.append(tc.tag(lug, 3))
        pin = _cyl((sx * EAR_X, 0, EAR_Z), 0.0045, 0.03, 8, rot=(radians(90), 0, 0))
        parts.append(tc.tag(pin, 3))

    # wire bail: half ellipse from one ear over the top (origin) to the other ear
    steps = 14
    pts = [(BAIL_RX * cos(pi * i / steps), 0.0, EAR_Z + BAIL_RZ * sin(pi * i / steps))
           for i in range(steps + 1)]
    for i in range(steps):
        parts.append(tc.tag(_seg(pts[i], pts[i + 1], 0.0035, verts=6), 3))

    # plastic grip tube at the top of the bail, centred on the origin, running along X
    grip = _cyl((0, 0, 0), 0.0125, 0.12, 12, rot=(0, radians(90), 0))
    parts.append(tc.tag(grip, 2))

    return parts
