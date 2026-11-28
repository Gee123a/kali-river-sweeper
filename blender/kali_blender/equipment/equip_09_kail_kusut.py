"""Kail kusut (quest 6B, jetty 2): a snag of tangled green and orange nylon fishing line wrapped round a white
plastic bag, with a red/white bobber and a lead sinker hanging off it.

Origin = WATERLINE: the bag floats half submerged with the loops of line on top.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 9,
    "name": "SM_Prop_KailKusut",
    "prefab": "PF_Prop_KailKusut",
    "label": "Tangled fishing line snagged round a plastic bag, bobber, sinker",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (200, 500),
    "palette": [
        ("#e9eef2", 0.0, 0.5),   # 0 white plastic bag
        ("#22c55e", 0.0, 0.6),   # 1 green nylon line
        ("#f97316", 0.0, 0.6),   # 2 orange nylon line
        ("#dc2626", 0.0, 0.6),   # 3 red bobber
        ("#f5f5f0", 0.0, 0.6),   # 4 white bobber half
        ("#5b6168", 0.8, 0.5),   # 5 lead sinker
    ],
}

LOOPS = [  # (rx, ry, rz, R, swatch)
    (0.3, 0.0, 0.0, 0.16, 1), (1.2, 0.4, 0.7, 0.14, 2), (-0.9, 0.8, 1.9, 0.15, 1), (0.6, -1.1, 2.6, 0.12, 2),
]


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(-0.08, 0.06, 0.05), (-0.05, 0.13, 0.10), (0.02, 0.14, 0.11), (0.07, 0.09, 0.07), (0.10, 0.03, 0.03),
                   (0.13, 0.05, 0.04)], 8, lambda r: 0, cap0=0, cap1=0)
    for rx, ry, rz, R, key in LOOPS:                                        # tangle of line loops
        geo.xform = Matrix.Translation((0, 0, 0.02)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") \
            @ Matrix.Rotation(rx, 4, "X")
        ts.torus(geo, key, R, 0.004, 10, 3)
    geo.xform = Matrix.Translation((0.20, -0.08, 0.0))                       # bobber
    ts.lathe(geo, [(-0.03, 0.004, 0.004), (-0.015, 0.02, 0.02), (0.0, 0.022, 0.022)], 6, lambda r: 3, cap0=3)
    ts.lathe(geo, [(0.0, 0.022, 0.022), (0.02, 0.012, 0.012), (0.05, 0.003, 0.003)], 6, lambda r: 4, cap1=4)
    geo.xform = Matrix.Translation((-0.18, 0.10, -0.06))                     # lead sinker
    ts.lathe(geo, [(-0.015, 0.004, 0.004), (0.0, 0.01, 0.01), (0.015, 0.004, 0.004)], 5, lambda r: 5, cap0=5, cap1=5)
    geo.xform = None
    ts.crumple(geo, 0.008, 10.0, seed=9)
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
