"""Jala cincin lempar - float ring cast net, gathered for throwing: held by a rope hand loop and
brass ring at the origin, the gathered net hangs down (-Z) as a folded cone with radial drape
folds, a ring of lead sinkers at the bottom, and orange float rings tied along the bundle.
"""
import bpy  # must be first
from math import cos, pi, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 14,
    "name": "SM_Tool_JalaCincinLempar",
    "label": "Jala cincin lempar (float ring cast net)",
    "head_dir": "-Z",
    "palette": [
        ("#4d6b5c", 0.0, 0.30),   # 0 nylon net
        ("#6b6f75", 0.9, 0.35),   # 1 lead sinkers
        ("#ff6a13", 0.0, 0.50),   # 2 orange float rings
        ("#c9a227", 1.0, 0.70),   # 3 brass horn ring
        ("#d8c9a3", 0.0, 0.30),   # 4 hand line rope loop
    ],
}

TOP_Z = -0.05          # where the gathered bundle leaves the hand
BOT_Z = -1.15          # bottom of the bundle (1.1 m long)
R_TOP = 0.02
R_BOT = 0.10


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _seg(a, b, r, verts=4):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r, radius2=r, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def _r(z):
    """Bundle radius at height z (narrow at the hand, wide at the sinkers)."""
    return R_TOP + (TOP_Z - z) / (TOP_Z - BOT_Z) * (R_BOT - R_TOP)


def build():
    parts = []

    # hand line loop (rope) passing through the origin, and the brass horn ring on it
    loop = _add("torus", major_segments=10, minor_segments=4, major_radius=0.025,
                minor_radius=0.0045, location=(0, 0, 0.03), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(loop, 4))
    horn = _add("torus", major_segments=10, minor_segments=4, major_radius=0.022,
                minor_radius=0.005, location=(0, 0, -0.02))
    parts.append(tc.tag(horn, 3))

    # gathered net bundle: folded cone tapering to the hand
    cone = _add("cone", vertices=10, radius1=R_BOT, radius2=R_TOP, depth=TOP_Z - BOT_Z,
                end_fill_type="NGON", location=(0, 0, (TOP_Z + BOT_Z) / 2))
    parts.append(tc.tag(cone, 0))

    # radial drape folds running down the bundle
    for k in range(6):
        t = 2 * pi * k / 6 + 0.3
        top = (R_TOP * cos(t) * 0.8, R_TOP * sin(t) * 0.8, TOP_Z - 0.01)
        bot = (R_BOT * cos(t) * 1.05, R_BOT * sin(t) * 1.05, BOT_Z + 0.01)
        parts.append(tc.tag(_seg(top, bot, 0.0045, 4), 0))

    # mesh rows (rings) around the bundle
    for z in (-0.35, -0.65):
        ring = _add("torus", major_segments=10, minor_segments=3, major_radius=_r(z),
                    minor_radius=0.0045, location=(0, 0, z))
        parts.append(tc.tag(ring, 0))

    # float rings tied along the bundle
    for z in (-0.30, -0.80):
        fl = _add("torus", major_segments=8, minor_segments=3, major_radius=_r(z) + 0.012,
                  minor_radius=0.010, location=(0, 0, z))
        parts.append(tc.tag(fl, 2))

    # lead sinkers: ring of 12 small cylinders bunched at the bottom
    n = 12
    for k in range(n):
        t = 2 * pi * k / n
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.009, depth=0.018,
                                            location=(0.102 * cos(t), 0.102 * sin(t), BOT_Z + 0.01))
        parts.append(tc.tag(bpy.context.object, 1))
    return parts
