"""Bola plastik (quest 6B): a kid's 22 cm plastic ball with red / yellow / blue bands, floating high.

Origin = WATERLINE: the hollow ball sits a third under water.
"""
import bpy  # must be first
import math
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 8,
    "name": "SM_Prop_BolaPlastik",
    "prefab": "PF_Prop_BolaPlastik",
    "label": "Floating plastic ball, red / yellow / blue bands",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (120, 400),
    "palette": [
        ("#e11d2a", 0.0, 0.7),   # 0 red
        ("#facc15", 0.0, 0.7),   # 1 yellow
        ("#1d6fe1", 0.0, 0.7),   # 2 blue
        ("#f2f2ee", 0.0, 0.7),   # 3 white poles
    ],
}

R = 0.11
RINGS = 7


def build():
    geo = ts.Geo()
    rings = [(R * -math.cos(math.pi * i / RINGS) + R * 0.3, R * math.sin(math.pi * i / RINGS) or 0.012,
              R * math.sin(math.pi * i / RINGS) or 0.012) for i in range(RINGS + 1)]
    ts.lathe(geo, rings, 12, lambda r: 3 if r in (0, RINGS - 1) else (r - 1) % 3, cap0=3, cap1=3)
    return geo.objects(SPEC["name"])
