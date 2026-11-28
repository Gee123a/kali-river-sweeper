"""Medical bundle: yellow B3 bag with a red band and three syringes sticking out (~0.5 m). Name -> Medical.

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 5,
    "name": "SM_Trash_InstBundle_Medis",
    "prefab": "PF_Trash_InstBundle_Medis",
    "label": "Instanced bundle: medical (yellow B3 bag + syringes)",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#eab308", 0.0, 0.5),  # 0
        ("#dc2626", 0.0, 0.45),  # 1
        ("#f1f5f9", 0.0, 0.6),  # 2
    ],
}

def build():
    geo = ts.Geo()
    ts.lathe(geo, [(-0.09, 0.08, 0.07), (-0.02, 0.17, 0.14), (0.05, 0.13, 0.11), (0.1, 0.05, 0.05)], 5,
             lambda r: 1 if r == 1 else 0, cap0=0, cap1=0)
    for a in (0.3, 2.4, 4.3):
        geo.xform = Matrix.Translation((0.06 * math.cos(a), 0.06 * math.sin(a), 0.06)) @ Matrix.Rotation(a, 4, "Z") \
            @ Matrix.Rotation(math.radians(55), 4, "Y")
        ts.lathe(geo, [(0.0, 0.012, 0.012), (0.17, 0.012, 0.012)], 3, lambda r: 2, cap1=2)
    geo.xform = None
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
