"""White broken styrofoam slab with a loose chunk (~0.6 m); floats very high.

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 3,
    "name": "SM_Trash_InstBundle_NormalStyrofoam",
    "prefab": "PF_Trash_InstBundle_NormalStyrofoam",
    "label": "Instanced bundle: styrofoam slab + chunk",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#f1efe8", 0.0, 0.25),  # 0
        ("#d9d2c0", 0.0, 0.2),  # 1
    ],
}

def build():
    geo = ts.Geo()
    ts.box(geo, 0, (-0.30, -0.20, -0.02), (0.30, 0.20, 0.08), n=(2, 2, 1))
    corner = geo.select(lambda co: co.x > 0.2 and co.y > 0.1)
    geo.deform(lambda co: (co.x - 0.05, co.y - 0.04, co.z - 0.02), corner)
    ts.box(geo, 1, (0.30, 0.10, -0.015), (0.40, 0.20, 0.05))
    ts.crumple(geo, 0.006, 8.0, seed=103)
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
