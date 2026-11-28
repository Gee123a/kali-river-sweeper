"""Villager fishing rod (4B, PF_Prop_FishingRod): 2.5 m tapered bamboo pole with three nodes, black rubber grip
wrap and a short butt behind the hand, three wire line guides and a small wooden reel spool.

Origin = GRIP (hand): parent the prefab under SK_VillagerNPC's Socket_RightHand with zero local transform
(Rigging/README.md: sockets have an identity rest frame). The pole points along Blender -Y = Unity +Z (forward),
matching KaliNpcBuilder's procedural rod; a 2.25 m jetty rod is a uniform 0.9 scale.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 13,
    "name": "SM_Prop_FishingRod",
    "prefab": "PF_Prop_FishingRod",
    "label": "Bamboo fishing rod, grip at origin, points +Z in Unity",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "grip",
    "tris": (150, 400),
    "max_size": 3.0,
    "palette": [
        ("#c9a464", 0.0, 0.4),   # 0 bamboo
        ("#1c1c1c", 0.0, 0.3),   # 1 rubber grip wrap
        ("#9aa0a6", 0.8, 0.5),   # 2 wire guides
        ("#7a5230", 0.0, 0.4),   # 3 wooden reel
    ],
}

LENGTH = 2.5


def build():
    geo = ts.Geo()
    geo.xform = Matrix.Rotation(math.radians(90), 4, "X")                                         # +Z -> -Y
    ts.lathe(geo, [(-0.25, 0.017, 0.017), (0.0, 0.017, 0.017), (0.18, 0.017, 0.017)], 6, lambda r: 1, cap0=1)           # grip wrap
    rings = [(0.18, 0.016), (0.60, 0.014), (0.62, 0.0165), (0.64, 0.014), (1.20, 0.011), (1.22, 0.013),
             (1.24, 0.011), (1.85, 0.008), (1.87, 0.0095), (1.89, 0.008), (LENGTH, 0.004)]
    ts.lathe(geo, [(z, r, r) for z, r in rings], 6, lambda r: 0, cap1=0)
    for z in (0.9, 1.55, 2.2):                                                                     # line guides
        geo.xform = Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation((0, 0.02, z)) \
            @ Matrix.Rotation(math.radians(90), 4, "Y")
        ts.torus(geo, 2, 0.008, 0.0015, 6, 3)
    geo.xform = Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation((0, 0.035, 0.12)) \
        @ Matrix.Rotation(math.radians(90), 4, "Y")                                                 # reel spool
    ts.lathe(geo, [(-0.02, 0.03, 0.03), (0.02, 0.03, 0.03)], 8, lambda r: 3, cap0=3, cap1=3)
    geo.xform = None
    return geo.objects(SPEC["name"])
