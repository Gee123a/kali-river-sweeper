"""Biohazard bundle: purple drum (#A855F7) lying in a lime slick (#84CC16), lime band (~0.7 m). Name -> Biohazard.

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 6,
    "name": "SM_Trash_InstBundle_Biohazard",
    "prefab": "PF_Trash_InstBundle_Biohazard",
    "label": "Instanced bundle: biohazard drum in a lime slick",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#a855f7", 0.3, 0.45),  # 0
        ("#84cc16", 0.0, 0.5),  # 1
        ("#a3e635", 0.0, 0.95),  # 2
    ],
}

def build():
    geo = ts.Geo()
    geo.xform = Matrix.Rotation(math.radians(90), 4, "Y")
    ts.lathe(geo, [(-0.26, 0.17, 0.17), (-0.05, 0.18, 0.18), (0.05, 0.18, 0.18), (0.26, 0.17, 0.17)], 7,
             lambda r: 1 if r == 1 else 0, cap0=0, cap1=0)
    geo.xform = Matrix.Translation((0.0, 0.0, -0.02))
    ts.lathe(geo, [(0.0, 0.42, 0.33)], 7, lambda r: 2, cap1=2)
    geo.xform = None
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
