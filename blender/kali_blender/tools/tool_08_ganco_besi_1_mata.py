"""Ganco besi 1-mata - single-spike iron pike hook on a 1.6 m pole, +Z head."""
import bpy  # must be first
from math import cos, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 8,
    "name": "SM_Tool_GancoBesi1Mata",
    "label": "Ganco besi 1-mata (single spike iron hook)",
    "head_dir": "+Z",
    "palette": [
        ("#9c6b3c", 0.0, 0.30),  # 0 wooden pole
        ("#4a3b33", 0.6, 0.25),  # 1 rust-dark iron socket and hook tine
        ("#3a3530", 0.7, 0.35),  # 2 iron spike
        ("#6b6e72", 0.9, 0.50),  # 3 wire binding
        ("#222222", 0.0, 0.30),  # 4 grip wrap
    ],
}

POLE_BOT, POLE_TOP = -0.4, 1.2   # grip at origin ~0.4 m above the butt
SOCKET_Z = 1.22                  # socket collar centre


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def _seg(p, q, r, verts=8):
    """Cylinder segment from point p to point q."""
    p, q = Vector(p), Vector(q)
    d = q - p
    obj = _add("cylinder", vertices=verts, radius=r, depth=d.length, end_fill_type="NGON",
               location=tuple((p + q) / 2))
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return obj


def _pole_r(z):
    return 0.018 - (z - POLE_BOT) / (POLE_TOP - POLE_BOT) * 0.004


def build():
    parts = []

    # 1.6 m tapered wooden pole, grip at the origin
    pole = _add("cone", vertices=10, radius1=0.018, radius2=0.014, depth=POLE_TOP - POLE_BOT,
                end_fill_type="NGON", location=(0, 0, (POLE_BOT + POLE_TOP) / 2))
    parts.append(tc.tag(pole, 0))

    # grip wrap around the origin
    parts.append(tc.tag(_cyl((0, 0, 0), _pole_r(0) + 0.0025, 0.07, 10), 4))

    # wire binding wraps just under the socket
    for z in (1.03, 1.06, 1.09):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.0018, 0.008, 8), 3))

    # forged socket collar sleeved over the pole tip
    parts.append(tc.tag(_cyl((0, 0, SOCKET_Z), 0.02, 0.14, 12), 1))

    # ONE straight spike rising from the collar along +Z
    spike = _add("cone", vertices=10, radius1=0.011, radius2=0.0, depth=0.26,
                 end_fill_type="NGON", location=(0, 0, SOCKET_Z + 0.07 + 0.13))
    parts.append(tc.tag(spike, 2))

    # ONE curved hook tine: a pike-pole arc in the XZ plane, sweeping out to +X
    cx, cz, r = 0.045, 1.22, 0.05
    pts = [(cx + r * cos(radians(a)), 0.0, cz + r * sin(radians(a))) for a in range(180, -1, -30)]
    for p, q in zip(pts[:-1], pts[1:]):
        parts.append(tc.tag(_seg(p, q, 0.0055, 8), 1))

    return parts
