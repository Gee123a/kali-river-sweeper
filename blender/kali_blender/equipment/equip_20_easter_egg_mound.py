"""Easter-egg mound (R4-J1): a low mud-and-trash mound (0.9 m wide, 0.3 m tall) with a hollow in its crown, a torn
bag and a bottle stuck in it - the bed the hidden tools (#5 Ember Cat 5L, #16 Blok Magnet, #19 Penebas Gergaji
Ganda) lie half-buried in. KaliPropPrefabBuilder assembles PF_EasterEgg_<Tool> = mound + tool prefab (posed in the
hollow) + PF_Prop_EasterEggGlint above it.

Origin = centre of the bbox bottom (base pivot). Equipment atlas cell 20, swatch rows 0-1 (the glint uses rows 2-3).
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 20,
    "name": "SM_Prop_EasterEggMound",
    "prefab": "PF_Prop_EasterEggMound",
    "label": "Mud and trash mound for half-buried easter-egg tools",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (150, 400),
    "palette": [
        ("#5b4630", 0.0, 0.2),   # 0 river mud
        ("#3d2f20", 0.0, 0.3),   # 1 wet mud in the hollow
        ("#e11d2a", 0.0, 0.5),   # 2 torn red bag
        ("#9fd8b0", 0.0, 0.8),   # 3 green bottle
    ],
}


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(0.0, 0.45, 0.38), (0.10, 0.40, 0.33), (0.22, 0.28, 0.23), (0.30, 0.20, 0.16)], 12, lambda r: 0,
             cap0=0)
    ts.lathe(geo, [(0.30, 0.20, 0.16), (0.24, 0.12, 0.10), (0.20, 0.05, 0.04)], 12, lambda r: 1, cap1=1)    # hollow
    geo.xform = Matrix.Translation((-0.26, 0.12, 0.14)) @ Matrix.Rotation(1.1, 4, "X") @ Matrix.Rotation(0.6, 4, "Z")
    ts.lathe(geo, [(-0.06, 0.04, 0.03), (0.0, 0.09, 0.07), (0.07, 0.03, 0.03)], 6, lambda r: 2, cap0=2, cap1=2)
    geo.xform = Matrix.Translation((0.25, -0.18, 0.12)) @ Matrix.Rotation(math.radians(70), 4, "Y")
    ts.lathe(geo, [(0.0, 0.04, 0.04), (0.16, 0.04, 0.04), (0.22, 0.014, 0.014)], 6, lambda r: 3, cap0=3, cap1=3)
    geo.xform = None
    ts.crumple(geo, 0.02, 6.0, seed=20)
    zmin = min(v.z for v in geo.v)
    geo.deform(lambda co: (co.x, co.y, max(co.z, zmin + 0.004) if co.z < 0.02 else co.z))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
