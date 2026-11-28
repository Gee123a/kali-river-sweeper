"""Four PET bottles roped side by side with a yellow band (~0.6 m).

Instanced bundle (bundles_common): under 100 tris, flat swatches, WATERLINE origin, M_Bundles_Atlas.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 2,
    "name": "SM_Trash_InstBundle_NormalBotol",
    "prefab": "PF_Trash_InstBundle_NormalBotol",
    "label": "Instanced bundle: roped PET bottles",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#9fd8b0", 0.0, 0.85),  # 0
        ("#a9cfe8", 0.0, 0.85),  # 1
        ("#e11d2a", 0.0, 0.5),  # 2
        ("#facc15", 0.0, 0.4),  # 3
    ],
}

def build():
    geo = ts.Geo()
    for i in range(4):
        y = (i - 1.5) * 0.09
        geo.xform = Matrix.Translation((-0.3 + (0.04 if i % 2 else 0.0), y, 0.0)) @ Matrix.Rotation(math.radians(90), 4, "Y")
        ts.lathe(geo, [(0.0, 0.04, 0.04), (0.42, 0.045, 0.045), (0.52, 0.015, 0.015)], 4, lambda r, k=i % 2: k,
                 cap0=i % 2, cap1=2)
    geo.xform = None
    ts.box(geo, 3, (-0.06, -0.2, -0.05), (-0.03, 0.2, 0.05))
    geo.recentre(keep_z=True)
    geo.deform(lambda co: (co.x, co.y, co.z + 0.015))
    return geo.objects(SPEC["name"])
