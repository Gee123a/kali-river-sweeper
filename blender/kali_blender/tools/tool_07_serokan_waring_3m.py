"""Serokan waring 3 m - bamboo hand net: wire hoop + black nylon cone bag, +Z head."""
import bpy  # must be first
from math import pi
from kali_blender import tools_common as tc

SPEC = {
    "index": 7,
    "name": "SM_Tool_SerokanWaring3m",
    "label": "Serokan waring 3m (bamboo hand net with mesh bag)",
    "head_dir": "+Z",
    "palette": [
        ("#c2a85a", 0.0, 0.35),  # 0 bamboo pole
        ("#6f5f2a", 0.0, 0.30),  # 1 bamboo node rings
        ("#b8bcc0", 0.9, 0.50),  # 2 steel wire hoop
        ("#8a6a3a", 0.0, 0.30),  # 3 lashing twine and grip wrap
        ("#1c1f22", 0.0, 0.20),  # 4 black nylon net bag
    ],
}

POLE_BOT, POLE_LEN = -0.6, 3.0   # butt z=-0.6 (grip at origin ~0.6 m up), tip z=2.4
HOOP_R = 0.225
HOOP_Z = POLE_BOT + POLE_LEN + HOOP_R   # hoop bottom point sits on the pole tip
BAG_DEPTH = 0.35


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

    # 3.0 m tapered bamboo pole
    pole = _add("cone", vertices=10, radius1=0.020, radius2=0.0145, depth=POLE_LEN,
                end_fill_type="NGON", location=(0, 0, POLE_BOT + POLE_LEN / 2))
    parts.append(tc.tag(pole, 0))

    # node rings roughly every 0.4 m
    for z in (-0.45, -0.05, 0.35, 0.75, 1.15, 1.55, 1.95):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.0025, 0.012, 10), 1))

    # rattan/tape grip wrap centred on the origin
    parts.append(tc.tag(_cyl((0, 0, 0), _pole_r(0) + 0.002, 0.06, 10), 3))

    # thin steel wire hoop (plane containing the pole axis), bottom point on the pole tip
    hoop = _add("torus", major_segments=20, minor_segments=4, major_radius=HOOP_R,
                minor_radius=0.0035, location=(0, 0, HOOP_Z), rotation=(pi / 2, 0, 0))
    parts.append(tc.tag(hoop, 2))

    # twine lashings binding the hoop to the pole tip
    for z in (2.27, 2.30, 2.33, 2.36):
        parts.append(tc.tag(_cyl((0, 0, z), _pole_r(z) + 0.002, 0.012, 10), 3))

    # deep black nylon cone bag hanging from the hoop, open at both ends, narrow end at +Y
    bag = _add("cone", vertices=12, radius1=HOOP_R, radius2=0.06, depth=BAG_DEPTH,
               end_fill_type="NOTHING", location=(0, BAG_DEPTH / 2, HOOP_Z),
               rotation=(-pi / 2, 0, 0))
    parts.append(tc.tag(bag, 4))

    return parts
