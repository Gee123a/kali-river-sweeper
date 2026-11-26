"""Ember cat 20 L - weighted 20 L paint bucket on a rope, lead rim sinkers, -Z body."""
import bpy  # must be first
from math import cos, pi, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 9,
    "name": "SM_Tool_EmberCat20L",
    "label": "Ember cat 20 L (weighted paint bucket on rope)",
    "head_dir": "-Z",
    "palette": [
        ("#2e6fb5", 0.0, 0.35),  # 0 blue plastic bucket and rim bead
        ("#4b4f56", 0.6, 0.25),  # 1 lead rim sinker blocks
        ("#9aa0a6", 0.9, 0.50),  # 2 wire bail
        ("#c9a46a", 0.0, 0.30),  # 3 rope
        ("#222222", 0.0, 0.30),  # 4 hand grip
    ],
}

BUCKET_TOP = -0.28    # rim height (z)
BUCKET_H = 0.36
BAIL_R = 0.15


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _seg(p, q, r, verts=8):
    p, q = Vector(p), Vector(q)
    d = q - p
    obj = _add("cylinder", vertices=verts, radius=r, depth=d.length, end_fill_type="NGON",
               location=tuple((p + q) / 2))
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return obj


def build():
    parts = []

    # hand grip at the origin (the rope coil is held here)
    parts.append(tc.tag(_add("cylinder", vertices=12, radius=0.016, depth=0.1,
                             end_fill_type="NGON", location=(0, 0, 0)), 4))

    # coiled rope: two stacked rings around the grip
    for z in (0.03, 0.05):
        ring = _add("torus", major_segments=12, minor_segments=5, major_radius=0.07,
                    minor_radius=0.012, location=(0, 0, z))
        parts.append(tc.tag(ring, 3))

    # rope segment running down from the grip to the bail apex
    parts.append(tc.tag(_seg((0, 0, -0.05), (0, 0, BUCKET_TOP + 0.15), 0.006), 3))

    # wire bail: arc over the rim in the XZ plane, ends on the rim at +X and -X
    pts = [(BAIL_R * cos(radians(a)), 0.0, BUCKET_TOP + BAIL_R * sin(radians(a)))
           for a in range(0, 181, 30)]
    for p, q in zip(pts[:-1], pts[1:]):
        parts.append(tc.tag(_seg(p, q, 0.0035, 6), 2))

    # 20 L bucket: tapered cone, narrow bottom, top diameter 0.30 m, body hangs to -Z
    bucket = _add("cone", vertices=16, radius1=0.13, radius2=0.15, depth=BUCKET_H,
                  end_fill_type="NGON", location=(0, 0, BUCKET_TOP - BUCKET_H / 2))
    parts.append(tc.tag(bucket, 0))

    # rolled rim bead
    rim = _add("torus", major_segments=16, minor_segments=4, major_radius=0.15,
               minor_radius=0.008, location=(0, 0, BUCKET_TOP))
    parts.append(tc.tag(rim, 0))

    # five lead sinker blocks clamped around the rim
    for ang in (60, 120, 210, 270, 330):
        box = _add("cube", size=1.0, location=(0.158 * cos(radians(ang)),
                                               0.158 * sin(radians(ang)), BUCKET_TOP - 0.005),
                   rotation=(0, 0, radians(ang)))
        box.scale = (0.035, 0.05, 0.045)
        parts.append(tc.tag(box, 1))

    return parts
