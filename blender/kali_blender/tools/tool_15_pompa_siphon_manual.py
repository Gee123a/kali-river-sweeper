"""Pompa siphon manual - manual bilge siphon: 1.2 m 2-inch white PVC barrel hanging down (-Z)
from a T-handle piston rod, with couplers, a pump clamp ring, a side outlet spout with a
corrugated hose stub, and a foot valve strainer cage at the bottom.

Grip at the origin = T-handle crossbar.
"""
import bpy  # must be first
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 15,
    "name": "SM_Tool_PompaSiphonManual",
    "label": "Pompa siphon manual (manual bilge siphon)",
    "head_dir": "-Z",
    "palette": [
        ("#f4f4f1", 0.0, 0.35),   # 0 white PVC pipe and couplers
        ("#1e1e1e", 0.0, 0.30),   # 1 black T-handle grips and piston rod
        ("#7b8088", 0.9, 0.45),   # 2 steel clamp ring and strainer
        ("#2e3236", 0.0, 0.30),   # 3 dark foot valve cage
        ("#222222", 0.0, 0.40),   # 4 corrugated black hose
    ],
}

BARREL_TOP, BARREL_BOT = -0.05, -1.20     # 1.15 m barrel
BARREL_R = 0.03                           # 2-inch PVC (60 mm OD)


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0)):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=loc, rotation=rot)


def build():
    parts = []
    along_x = (0, radians(90), 0)

    # PVC barrel, top cap, and the foot valve/strainer at the bottom
    parts.append(tc.tag(_cyl((0, 0, (BARREL_TOP + BARREL_BOT) / 2), BARREL_R,
                             BARREL_TOP - BARREL_BOT, 16), 0))
    parts.append(tc.tag(_cyl((0, 0, BARREL_TOP - 0.025), 0.034, 0.05, 16), 0))
    # PVC couplers at two joints and the steel pump clamp ring between them
    for z in (-0.45, -0.85):
        parts.append(tc.tag(_cyl((0, 0, z), 0.035, 0.04, 16), 0))
    clamp = _add("torus", major_segments=16, minor_segments=4, major_radius=0.037,
                 minor_radius=0.006, location=(0, 0, -0.65))
    parts.append(tc.tag(clamp, 2))
    parts.append(tc.tag(_cyl((0, 0, BARREL_BOT - 0.04), 0.040, 0.08, 8), 3))
    parts.append(tc.tag(_cyl((0, 0, BARREL_BOT - 0.085), 0.028, 0.01, 8), 2))

    # piston rod and T-handle crossbar at the origin, grips on each end
    parts.append(tc.tag(_cyl((0, 0, -0.03), 0.008, 0.08, 8), 1))
    parts.append(tc.tag(_cyl((0, 0, 0.0), 0.011, 0.18, 8, rot=along_x), 1))
    for sx in (-0.095, 0.095):
        parts.append(tc.tag(_cyl((sx, 0, 0.0), 0.015, 0.05, 10), 1))

    # side outlet spout near the top, pointing +X, with a corrugated hose stub
    parts.append(tc.tag(_cyl((0.055, 0, -0.20), 0.018, 0.09, 10, rot=(0, radians(90), 0)), 0))
    for k in range(3):
        x = 0.11 + k * 0.022
        ring = _add("torus", major_segments=10, minor_segments=3, major_radius=0.014,
                    minor_radius=0.005, location=(x, 0, -0.20), rotation=along_x)
        parts.append(tc.tag(ring, 4))
    return parts
