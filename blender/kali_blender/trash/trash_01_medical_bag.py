"""Medical biohazard sack (B3) - lumpy yellow tied bag, twisted knotted neck, red trefoil badge,
red B3 stripe band and two syringe ends poking out of the knot.

Built around the origin; trash_common / build_trash expects the bbox centre at (0,0,0) (recentred here).
"""
import bpy  # must be first
from math import cos, radians, sin, sqrt
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 1,
    "name": "SM_Trash_MedicalBag",
    "prefab": "PF_Trash_MedicalBag",
    "label": "Medical biohazard sack (B3)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "palette": [
        ("#eab308", 0.0, 0.4),   # 0 hazard yellow bag
        ("#dc2626", 0.0, 0.35),  # 1 biohazard red badge + B3 stripe
        ("#f1f5f9", 0.0, 0.45),  # 2 translucent white syringe barrels
        ("#cbd5e1", 0.9, 0.7),   # 3 steel needles
    ],
}

RX, RY, RZ = 0.17, 0.13, 0.12   # body ellipsoid half-sizes


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _seg(a, b, r, verts=6):
    """Cylinder segment from a to b (tapered-free), radius r."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r, radius2=r, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def _surf_y(x, z):
    """Front (-Y) surface height of the body ellipsoid at (x, z)."""
    return -RY * sqrt(max(0.0, 1 - (x / RX) ** 2 - (z / RZ) ** 2))


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

    # lumpy sack body (ellipsoid) plus one bulge on the side
    body = _add("uv_sphere", segments=8, ring_count=5, radius=1.0, location=(0, 0, 0))
    body.scale = (RX, RY, RZ)
    parts.append(tc.tag(body, 0))
    lump = _add("uv_sphere", segments=6, ring_count=4, radius=0.07, location=(0.11, 0.05, -0.04))
    lump.scale = (1.0, 1.0, 0.9)
    parts.append(tc.tag(lump, 0))

    # tied neck: tapered 8-sided cone rising from the top of the sack
    neck = _add("cone", vertices=8, radius1=0.05, radius2=0.03, depth=0.06,
                end_fill_type="NGON", location=(0, 0, 0.13))
    parts.append(tc.tag(neck, 0))
    # knot and one twisted tail of the tie
    knot = _add("uv_sphere", segments=6, ring_count=4, radius=0.035, location=(0.005, 0, 0.165))
    parts.append(tc.tag(knot, 0))
    parts.append(tc.tag(_seg((0.005, 0, 0.17), (-0.03, 0.012, 0.215), 0.02, 6), 0))

    # red biohazard trefoil badge on the front (-Y) face: three lobes + centre disc
    bx, bz = 0.0, 0.01
    lobe_d, lobe_r = 0.045, 0.022
    for ang in (90, 210, 330):
        lx = bx + lobe_d * cos(radians(ang))
        lz = bz + lobe_d * sin(radians(ang))
        parts.append(tc.tag(_disc_y(lx, _surf_y(lx, lz), lz, lobe_r), 1))
    parts.append(tc.tag(_disc_y(bx, _surf_y(bx, bz), bz, 0.016), 1))

    # red B3 stripe band across the front
    sz = -0.045
    stripe = _add("cube", size=2, location=(0, _surf_y(0, sz), sz))
    stripe.scale = (0.07, 0.004, 0.014)
    parts.append(tc.tag(stripe, 1))

    # syringe ends poking out of the knot: barrel (white), plunger (white), needle (steel)
    syringes = [
        ((0.02, -0.02, 0.17), (0.10, -0.05, 0.22), (0.135, -0.065, 0.25)),
        ((-0.03, 0.03, 0.17), (-0.08, 0.05, 0.21), (-0.11, 0.07, 0.235)),
    ]
    for a, b, c in syringes:
        parts.append(tc.tag(_seg(a, b, 0.009, 8), 2))
        parts.append(tc.tag(_seg(b, c, 0.0025, 6), 3))

    _recentre(parts)
    return parts
