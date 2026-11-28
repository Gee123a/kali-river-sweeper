"""Three knotted kresek bags (red, blue, white) in one clump (~0.55 m).

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 1,
    "name": "SM_Trash_InstBundle_NormalKresek",
    "prefab": "PF_Trash_InstBundle_NormalKresek",
    "label": "Instanced bundle: three tied kresek bags",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#e11d2a", 0.0, 0.55),  # 0
        ("#1d6fe1", 0.0, 0.55),  # 1
        ("#f2f2ee", 0.0, 0.5),  # 2
    ],
}

def build():
    geo = ts.Geo()
    for (x, y, rz, s, key) in ((0.0, 0.0, 0.0, 1.0, 0), (0.17, 0.08, 1.9, 0.85, 1), (-0.14, 0.12, 4.0, 0.8, 2)):
        geo.xform = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(1.2, 4, "X") \
            @ Matrix.Scale(s, 4)
        ts.lathe(geo, [(-0.11, 0.06, 0.05), (0.0, 0.13, 0.11), (0.13, 0.03, 0.03)], 6,
                 lambda r, k=key: k, cap0=key, cap1=key)
    geo.xform = None
    ts.crumple(geo, 0.012, 8.0, seed=101)
    geo.recentre(keep_z=True)
    zmin = min(v.z for v in geo.v)
    geo.deform(lambda co: (co.x, co.y, co.z - zmin - 0.07))
    return geo.objects(SPEC["name"])
