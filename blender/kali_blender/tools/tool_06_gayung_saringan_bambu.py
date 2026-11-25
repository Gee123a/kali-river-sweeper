"""Gayung saringan bambu - perforated plastic dipper taped to a 3 m bamboo pole, +Z head."""
import bpy  # must be first
from math import cos, pi, radians, sin
from kali_blender import tools_common as tc

SPEC = {
    "index": 6,
    "name": "SM_Tool_GayungSaringanBambu",
    "label": "Gayung saringan bambu (perforated dipper on bamboo pole)",
    "head_dir": "+Z",
    "palette": [
        ("#c2a85a", 0.0, 0.35),  # 0 bamboo pole and cup rim bead
        ("#6f5f2a", 0.0, 0.30),  # 1 bamboo node rings
        ("#2563a8", 0.0, 0.35),  # 2 blue plastic gayung cup
        ("#101214", 0.0, 0.20),  # 3 drain holes
        ("#151515", 0.0, 0.25),  # 4 black electrical tape wraps and grip wrap
    ],
}

POLE_BOT, POLE_LEN = -0.6, 3.0   # butt at z=-0.6, tip at z=2.4 (grip at origin)
CUP_Z = 2.42                     # cup centre height; opening faces +Y (sideways)


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def _pole_r(z):
    """Bamboo taper: 0.020 at the butt to 0.0145 at the tip."""
    return 0.020 - (z - POLE_BOT) / POLE_LEN * 0.0055


def build():
    parts = []

    # 3.0 m tapered bamboo pole, grip at the origin
    pole = _add("cone", vertices=10, radius1=0.020, radius2=0.0145, depth=POLE_LEN,
                end_fill_type="NGON", location=(0, 0, POLE_BOT + POLE_LEN / 2))
    parts.append(tc.tag(pole, 0))

    # node rings roughly every 0.4 m
    for z in (-0.45, -0.05, 0.35, 0.75, 1.15, 1.55, 1.95):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.0025, 0.012, 10), 1))

    # tape wrap grip centred on the origin
    parts.append(tc.tag(_cyl((0, 0, 0), _pole_r(0) + 0.002, 0.06, 10), 4))

    # black electrical-tape wraps where the cup is lashed to the pole tip
    for z in (2.24, 2.27, 2.30, 2.33):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.002, 0.012, 10), 4))

    # cup: open tube along Y (opening faces +Y), centred on the pole tip
    parts.append(tc.tag(_cyl((0, 0, CUP_Z), 0.075, 0.13, 16, rot=(-pi / 2, 0, 0), fill="NOTHING"), 2))
    # closed base on the -Y side
    parts.append(tc.tag(_cyl((0, -0.063, CUP_Z), 0.075, 0.004, 16, rot=(-pi / 2, 0, 0)), 2))
    # rolled rim bead around the opening
    bead = _add("torus", major_segments=16, minor_segments=5, major_radius=0.075,
                minor_radius=0.006, location=(0, 0.065, CUP_Z), rotation=(pi / 2, 0, 0))
    parts.append(tc.tag(bead, 0))

    # drain holes punched in the base: one centre + ring of 8 dark discs
    hole_pts = [(0.0, 0.0)] + [(0.042 * cos(radians(a)), 0.042 * sin(radians(a)))
                               for a in range(0, 360, 45)]
    for hx, hz in hole_pts:
        disc = _cyl((hx, -0.0665, CUP_Z + hz), 0.0085, 0.006, 8, rot=(-pi / 2, 0, 0))
        parts.append(tc.tag(disc, 3))

    return parts
