"""Serokan jumbo 4.5 m - jumbo waring net: two separate parallel Petung bamboo poles (dual grip,
0.10 m centre-to-centre along X) with node rings, joined by rope lashings and spacer blocks,
both meeting a small yoke under a 0.60 m wire hoop at the top (+Z). The hoop plane contains
the pole axis (XZ plane) and a deep black nylon mesh bag hangs back from it.

Grip at the origin, on the surface of the left pole's grip tape (within 0.05 m).
"""
import bpy  # must be first
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 12,
    "name": "SM_Tool_SerokanJumbo4_5m",
    "label": "Serokan jumbo 4.5 m (jumbo waring net)",
    "head_dir": "+Z",
    "palette": [
        ("#c9a95a", 0.0, 0.40),   # 0 Petung bamboo poles and node rings
        ("#101010", 0.0, 0.25),   # 1 black nylon mesh bag
        ("#9aa0a6", 1.0, 0.60),   # 2 steel wire hoop and yoke
        ("#b89a5c", 0.0, 0.30),   # 3 rope lashings, spacer blocks and grip tape
    ],
}

POLE_XS = (-0.05, 0.05)    # 0.10 m centre-to-centre
POLE_R = 0.02
BUTT, POLE_TOP = -0.80, 3.70
HOOP_C = 3.88              # hoop centre height; top at 4.18 keeps the tool under 5 m
HOOP_R = 0.30
YOKE_Z = 3.62


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0)):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=loc, rotation=rot)


def build():
    parts = []

    # two separate bamboo poles, each with a butt cap and node rings along its length
    pole_len = POLE_TOP - BUTT
    for x in POLE_XS:
        parts.append(tc.tag(_cyl((x, 0, (POLE_TOP + BUTT) / 2), POLE_R, pole_len, 8), 0))
        parts.append(tc.tag(_cyl((x, 0, BUTT + 0.006), POLE_R + 0.003, 0.012, 8), 0))
        for z in (-0.20, 0.90, 2.00, 3.00):
            parts.append(tc.tag(_cyl((x, 0, z), POLE_R + 0.003, 0.012, 8), 0))

    # black-free grip tape wrapped on the left pole at the origin (surface ~0.03 m from origin)
    parts.append(tc.tag(_cyl((POLE_XS[0], 0, 0.0), POLE_R + 0.004, 0.14, 8), 3))

    # four rope lashings encircling both poles, each with a spacer block between them
    for z in (0.50, 1.50, 2.50, 3.20):
        lash = _add("torus", major_segments=8, minor_segments=3, major_radius=0.08,
                    minor_radius=0.005, location=(0, 0, z))
        parts.append(tc.tag(lash, 3))
        blk = _add("cube", size=2, location=(0, 0, z + 0.025))
        blk.scale = (0.07, 0.012, 0.02)
        parts.append(tc.tag(blk, 0))

    # yoke bar joining the two pole tops under the hoop
    yoke = _cyl((0, 0, YOKE_Z), 0.011, 0.12, 6, rot=(0, radians(90), 0))
    parts.append(tc.tag(yoke, 2))

    # steel wire hoop in the XZ plane, centred above the pole tops
    hoop = _add("torus", major_segments=16, minor_segments=4, major_radius=HOOP_R,
                minor_radius=0.011, location=(0, 0, HOOP_C), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(hoop, 2))

    # deep black nylon mesh bag: cone from the hoop mouth (y=0) backwards to y=0.80
    bag_len = 0.80
    bag = _add("cone", vertices=12, radius1=HOOP_R - 0.01, radius2=0.05, depth=bag_len,
               end_fill_type="NGON", location=(0, bag_len / 2, HOOP_C),
               rotation=(radians(-90), 0, 0))
    parts.append(tc.tag(bag, 1))

    # cod-end ring at the bag tip
    cod = _add("torus", major_segments=8, minor_segments=4, major_radius=0.05, minor_radius=0.010,
               location=(0, bag_len, HOOP_C), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(cod, 2))
    return parts
