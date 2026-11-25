"""Gayung bolong - plastic dipper cup with drain holes on a straight handle, +Z head."""
import bpy  # must be first
from math import cos, pi, radians, sin
from kali_blender import tools_common as tc

SPEC = {
    "index": 2,
    "name": "SM_Tool_GayungBolong",
    "label": "Gayung bolong (holed water dipper)",
    "head_dir": "+Z",
    "palette": [
        ("#2563a8", 0.0, 0.35),  # 0 blue plastic cup
        ("#d9d6cc", 0.0, 0.30),  # 1 off-white handle and collar
        ("#101214", 0.0, 0.20),  # 2 drain holes
    ],
}

CUP_Z = 0.245  # cup centre height; opening faces +Y


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def build():
    parts = []

    # straight handle, grip at origin (-0.08 .. 0.17)
    parts.append(tc.tag(_cyl((0, 0, 0.045), 0.011, 0.25, 10), 1))
    # end knob at the bottom of the handle
    parts.append(tc.tag(_cyl((0, 0, -0.084), 0.016, 0.012, 12), 1))
    # hand guard collar
    parts.append(tc.tag(_cyl((0, 0, 0.14), 0.0145, 0.02, 12), 1))

    # cup: open tube along Y (opening faces +Y)
    parts.append(tc.tag(_cyl((0, 0, CUP_Z), 0.075, 0.13, 16, rot=(-pi / 2, 0, 0), fill="NOTHING"), 0))
    # closed base on the -Y side
    parts.append(tc.tag(_cyl((0, -0.063, CUP_Z), 0.075, 0.004, 16, rot=(-pi / 2, 0, 0)), 0))
    # rolled plastic bead around the opening
    bead = _add("torus", major_segments=16, minor_segments=5, major_radius=0.075,
                minor_radius=0.006, location=(0, 0.065, CUP_Z), rotation=(pi / 2, 0, 0))
    parts.append(tc.tag(bead, 0))

    # drain holes punched in the base: one centre + ring of 8 dark discs
    hole_pts = [(0.0, 0.0)] + [(0.042 * cos(radians(a)), 0.042 * sin(radians(a)))
                               for a in range(0, 360, 45)]
    for hx, hz in hole_pts:
        disc = _cyl((hx, -0.067, CUP_Z + hz), 0.0085, 0.006, 8, rot=(-pi / 2, 0, 0))
        parts.append(tc.tag(disc, 2))

    return parts
