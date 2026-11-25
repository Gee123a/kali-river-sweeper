"""Serokan bambu - bamboo long-handle hand net with rattan hoop and cone bag, +Z head."""
import bpy  # must be first
from math import pi
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 3,
    "name": "SM_Tool_SerokanBambu",
    "label": "Serokan bambu (bamboo hand net)",
    "head_dir": "+Z",
    "palette": [
        ("#c2a85a", 0.0, 0.35),  # 0 bamboo pole
        ("#6f5f2a", 0.0, 0.30),  # 1 bamboo node rings
        ("#9a6b38", 0.0, 0.30),  # 2 rattan hoop and grip wrap
        ("#d8c79a", 0.0, 0.20),  # 3 twine
        ("#7d8270", 0.0, 0.15),  # 4 net bag
    ],
}

HOOP_Z = 1.525      # hoop centre; its bottom point sits on the pole tip at z=1.30
HOOP_R = 0.225


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0), fill="NGON"):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type=fill,
                location=loc, rotation=rot)


def _pole_r(z):
    """Taper of the bamboo pole: 0.020 at the butt (z=-0.5) to 0.0145 at the tip (z=1.3)."""
    return 0.020 - (z + 0.5) / 1.8 * 0.0055


def build():
    parts = []

    # 1.8 m tapered bamboo pole, butt at z=-0.5, tip at z=1.3, grip at the origin
    pole = _add("cone", vertices=10, radius1=0.020, radius2=0.0145, depth=1.8,
                end_fill_type="NGON", location=(0, 0, 0.4))
    parts.append(tc.tag(pole, 0))

    # node rings every ~0.35 m (skip the grip area at z=0)
    for z in (-0.40, -0.05, 0.30, 0.65, 0.95):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.0025, 0.012, 10), 1))

    # rattan wrap grip centred on the origin
    parts.append(tc.tag(_cyl((0, 0, 0), 0.0215, 0.06, 10), 2))

    # bent-rattan hoop, plane containing X and Z, bottom point at the pole tip
    hoop = _add("torus", major_segments=18, minor_segments=6, major_radius=HOOP_R,
                minor_radius=0.011, location=(0, 0, HOOP_Z), rotation=(pi / 2, 0, 0))
    parts.append(tc.tag(hoop, 2))

    # twine wraps lashing the hoop to the pole
    for z in (1.20, 1.23, 1.26, 1.29):
        parts.append(tc.tag(_cyl((0, 0, z), 0.0215, 0.012, 10), 3))

    # shallow cone net bag hanging from the hoop (open at the hoop, apex at +Y)
    bag = _add("cone", vertices=12, radius1=HOOP_R, radius2=0.0, depth=0.12,
               end_fill_type="NOTHING", location=(0, 0.06, HOOP_Z), rotation=(-pi / 2, 0, 0))
    parts.append(tc.tag(bag, 4))

    return parts
