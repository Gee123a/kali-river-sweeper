"""Ganco bambu - bamboo pole with forged steel spike and curved hook, +Z head."""
import bpy  # must be first
from math import radians
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 4,
    "name": "SM_Tool_GancoBambu",
    "label": "Ganco bambu (bamboo hook)",
    "head_dir": "+Z",
    "palette": [
        ("#5b6068", 0.9, 0.50),  # 0 forged steel
        ("#b8a05a", 0.0, 0.30),  # 1 bamboo pole
        ("#6b5a2a", 0.0, 0.25),  # 2 bamboo node rings
        ("#8c8c8c", 1.0, 0.60),  # 3 binding wire
        ("#2a2a2a", 0.0, 0.25),  # 4 grip wrap
    ],
}

POLE_TOP = 1.20  # bamboo tip; the steel collar slides over it


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def _seg(a, b, r0, r1, verts=8):
    """Tapered tube segment from point a (radius r0) to point b (radius r1)."""
    from mathutils import Vector as V
    a, b = V(a), V(b)
    d = b - a
    o = _add("cone", vertices=verts, radius1=r0, radius2=r1, depth=d.length,
             end_fill_type="NGON", location=tuple((a + b) / 2))
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = V((0, 0, 1)).rotation_difference(d)
    return o


def _pole_r(z):
    """Taper: 0.020 at the butt (z=-0.4) down to 0.0145 at the tip (z=1.2)."""
    return 0.020 - (z + 0.4) / 1.6 * 0.0055


def build():
    parts = []

    # 1.6 m tapered bamboo pole, butt at z=-0.4, grip at the origin
    pole = _add("cone", vertices=10, radius1=0.020, radius2=0.0145, depth=1.6,
                end_fill_type="NGON", location=(0, 0, 0.4))
    parts.append(tc.tag(pole, 1))

    # bamboo node rings
    for z in (-0.30, 0.12, 0.50, 0.85, 1.05):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.003, 0.012, 10), 2))

    # grip wrap at the origin
    parts.append(tc.tag(_cyl((0, 0, 0), 0.0205, 0.07, 10), 4))

    # steel socket collar over the pole tip
    collar = POLE_TOP
    parts.append(tc.tag(_cyl((0, 0, collar), 0.0175, 0.12, 10), 0))

    # binding wire wraps just below the collar
    for z in (1.09, 1.11, 1.13):
        parts.append(tc.tag(_cyl((0, 0, z), 0.0165, 0.007, 10), 3))

    # straight spike from the top of the collar
    spike = _add("cone", vertices=8, radius1=0.0105, radius2=0.0, depth=0.16,
                 end_fill_type="NGON", location=(0, 0, 1.34))
    parts.append(tc.tag(spike, 0))

    # curved hook: bent tube segments sweeping out to +X and curling back down
    pts = [(0.0175, 0, 1.22), (0.045, 0, 1.255), (0.075, 0, 1.30),
           (0.090, 0, 1.355), (0.080, 0, 1.405), (0.055, 0, 1.420)]
    radii = [0.0058, 0.0056, 0.0053, 0.0049, 0.0044]
    for i in range(len(pts) - 1):
        r0 = radii[i]
        r1 = radii[i + 1] if i + 1 < len(radii) else 0.0035
        parts.append(tc.tag(_seg(pts[i], pts[i + 1], r0, r1, verts=8), 0))

    return parts
