"""Gerobak (R2-J1, storage level 1): kampung wooden hand cart for trash, 1.9 m with handles - plank box bed with
raised side boards on an orange steel frame, two spoked-look rubber wheels on an axle, two long handles to the back
and a fold-down support leg.

Origin = ground centre (base pivot), forward +Z in Unity (Blender -Y): the bed faces forward, the handles trail
behind. Use it as a level-1 storage prop on the bank.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 18,
    "name": "SM_Prop_Gerobak",
    "prefab": "PF_Prop_Gerobak",
    "label": "Wooden kampung hand cart (gerobak) for trash",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (250, 700),
    "max_size": 2.5,
    "palette": [
        ("#8a6440", 0.0, 0.3),   # 0 weathered planks
        ("#e8651d", 0.2, 0.45),  # 1 orange steel frame / handles
        ("#1c1c1c", 0.0, 0.4),   # 2 rubber tyres
        ("#9aa0a6", 0.7, 0.45),  # 3 steel hubs / axle
        ("#6b4a2b", 0.0, 0.3),   # 4 dark wood boards
    ],
}

R = 0.30                       # wheel radius (wheels touch z = 0)


def build():
    geo = ts.Geo()
    z0 = R + 0.05
    ts.box(geo, 0, (-0.45, -0.55, z0), (0.45, 0.55, z0 + 0.04), n=(3, 2, 1))                 # bed floor planks
    for sx in (-1, 1):                                                                         # side boards
        ts.box(geo, 4, (sx * 0.45 - 0.02, -0.55, z0), (sx * 0.45 + 0.02, 0.55, z0 + 0.35), n=(1, 2, 1))
    for sy in (-1, 1):                                                                         # front / back boards
        ts.box(geo, 4, (-0.45, sy * 0.55 - 0.02, z0), (0.45, sy * 0.55 + 0.02, z0 + 0.35 if sy < 0 else z0 + 0.25))
    for sx in (-1, 1):                                                                         # frame rails -> handles
        ts.box(geo, 1, (sx * 0.38 - 0.025, -0.6, z0 - 0.05), (sx * 0.38 + 0.025, 0.6, z0))
        geo.xform = Matrix.Translation((sx * 0.38, 0.6, z0 - 0.025)) @ Matrix.Rotation(math.radians(-90 + 8), 4, "X")
        ts.lathe(geo, [(0.0, 0.02, 0.02), (0.65, 0.02, 0.02), (0.66, 0.026, 0.026), (0.78, 0.026, 0.026)], 6,
                 lambda r: 1 if r < 1 else 2, cap1=2)
        geo.xform = None
    geo.xform = Matrix.Translation((0, 0.0, R)) @ Matrix.Rotation(math.radians(90), 4, "Y")    # axle
    ts.lathe(geo, [(-0.58, 0.02, 0.02), (0.58, 0.02, 0.02)], 6, lambda r: 3)
    for sx in (-1, 1):                                                                         # wheels
        geo.xform = Matrix.Translation((sx * 0.52, 0.0, R)) @ Matrix.Rotation(math.radians(90), 4, "Y")
        ts.lathe(geo, [(-0.04, 0.22, 0.22), (-0.045, 0.28, 0.28), (-0.02, R, R), (0.02, R, R), (0.045, 0.28, 0.28),
                       (0.04, 0.22, 0.22)], 12, lambda r: 2 if r in (1, 2, 3) else 3, cap0=3, cap1=3)
    geo.xform = None
    ts.box(geo, 1, (-0.02, 0.48, 0.0), (0.02, 0.52, z0 - 0.05))                               # support leg
    ts.box(geo, 1, (-0.08, 0.45, 0.0), (0.08, 0.55, 0.02))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
