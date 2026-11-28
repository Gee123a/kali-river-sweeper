"""Slab of broken styrofoam packaging (~0.8 x 0.5 x 0.12 m) with a moulded groove, a snapped-off corner and the
broken chunk floating beside it. Bright white, unmistakable on brown water.

Origin = WATERLINE: foam floats very high, only the bottom 3 cm under water.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 17,
    "name": "SM_Trash_SlabStyrofoam",
    "prefab": "PF_Trash_SlabStyrofoam",
    "label": "Broken styrofoam packaging slab + broken-off chunk",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "pivot": "waterline",
    "tris": (200, 600),
    "palette": [
        ("#f1efe8", 0.0, 0.25),  # 0 white foam
        ("#d9d2c0", 0.0, 0.2),   # 1 grubby foam (chunk)
    ],
}


def build():
    geo = ts.Geo()
    ts.box(geo, 0, (-0.40, -0.25, -0.03), (0.40, 0.25, 0.09), n=(8, 5, 2))
    geo.deform(lambda co: (co.x, co.y, co.z - 0.035 if abs(co.y) < 0.06 and co.z > 0.08 else co.z))  # groove
    corner = geo.select(lambda co: co.x > 0.24 and co.y > 0.12)
    geo.deform(lambda co: (co.x - 0.06, co.y - 0.05, co.z - 0.02), corner)             # snapped-off corner
    ts.box(geo, 1, (0.43, 0.18, -0.025), (0.55, 0.30, 0.05), n=(2, 2, 1))              # the broken chunk
    ts.crumple(geo, 0.008, 7.0, seed=17)
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
