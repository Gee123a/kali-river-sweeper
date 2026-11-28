"""Villager water bucket (4B): 10 L orange plastic ember with a rolled rim, wire bail handle with a grip, and murky
river water inside.

Origin = centre of the bbox bottom (base pivot); carry it by the handle from Socket_RightHand if needed.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 15,
    "name": "SM_Prop_WaterBucket",
    "prefab": "PF_Prop_WaterBucket",
    "label": "Orange plastic water bucket with bail handle, water inside",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (150, 400),
    "palette": [
        ("#f97316", 0.0, 0.55),  # 0 orange plastic
        ("#6b8a8f", 0.0, 0.95),  # 1 murky water
        ("#9aa0a6", 0.8, 0.5),   # 2 wire handle
        ("#1c1c1c", 0.0, 0.4),   # 3 black grip
    ],
}


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(0.0, 0.10, 0.10), (0.02, 0.105, 0.105), (0.26, 0.135, 0.135), (0.27, 0.142, 0.142)], 12,
             lambda r: 0, cap0=0)
    ts.lathe(geo, [(0.27, 0.142, 0.142), (0.275, 0.128, 0.128), (0.20, 0.125, 0.125)], 12, lambda r: 0, cap1=1)
    geo.xform = Matrix.Translation((0, 0, 0.255)) @ Matrix.Rotation(math.radians(90), 4, "X")       # bail handle
    ts.torus(geo, 2, 0.14, 0.004, 8, 3, arc=0.5)
    geo.xform = Matrix.Translation((-0.04, 0, 0.395)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    ts.lathe(geo, [(0.0, 0.012, 0.012), (0.08, 0.012, 0.012)], 6, lambda r: 3, cap0=3, cap1=3)      # grip
    geo.xform = None
    for s in (-1, 1):                                                                               # handle lugs
        ts.box(geo, 0, (s * 0.14 - 0.012, -0.015, 0.235), (s * 0.14 + 0.012, 0.015, 0.27))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
