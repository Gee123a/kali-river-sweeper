"""Mixed clump: a black kresek bag, an orange bottle and a white foam chunk (~0.55 m).

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 4,
    "name": "SM_Trash_InstBundle_NormalCampur",
    "prefab": "PF_Trash_InstBundle_NormalCampur",
    "label": "Instanced bundle: mixed bag, bottle and foam",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#1f1f1f", 0.0, 0.5),  # 0
        ("#f97316", 0.0, 0.7),  # 1
        ("#f1efe8", 0.0, 0.25),  # 2
        ("#facc15", 0.0, 0.5),  # 3
    ],
}

def build():
    geo = ts.Geo()
    geo.xform = Matrix.Rotation(1.2, 4, "X")
    ts.lathe(geo, [(-0.11, 0.06, 0.05), (0.0, 0.14, 0.12), (0.09, 0.07, 0.06), (0.15, 0.025, 0.025)], 5,
             lambda r: 0, cap0=0, cap1=0)
    geo.xform = Matrix.Translation((0.08, -0.16, 0.0)) @ Matrix.Rotation(math.radians(80), 4, "Y")
    ts.lathe(geo, [(0.0, 0.04, 0.04), (0.24, 0.045, 0.045), (0.3, 0.015, 0.015)], 4, lambda r: 1, cap0=1, cap1=3)
    geo.xform = None
    ts.box(geo, 2, (-0.26, 0.04, -0.02), (-0.12, 0.2, 0.06))
    ts.crumple(geo, 0.01, 8.0, seed=104)
    geo.recentre(keep_z=True)
    zmin = min(v.z for v in geo.v)
    geo.deform(lambda co: (co.x, co.y, co.z - zmin - 0.06))
    return geo.objects(SPEC["name"])
