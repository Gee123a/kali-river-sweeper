"""Bundle of tied kresek plastic bags (~0.6 m): five knotted shopping bags (red, blue, white, yellow, black) jammed
together into one floating clump, crumpled. A readable multi-unit pickup (MECHANICS_SPEC §D bundles): loud
colours that pop on brown river water.

Origin = WATERLINE (RiverFlowBuoyancy puts the pivot on the water + floatOffsetY): about a third under water.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 15,
    "name": "SM_Trash_BundleKresek",
    "prefab": "PF_Trash_BundleKresek",
    "label": "Bundle of tied plastic bags (kresek), floating clump",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "pivot": "waterline",
    "tris": (250, 600),
    "palette": [
        ("#e11d2a", 0.0, 0.55),  # 0 red kresek
        ("#1d6fe1", 0.0, 0.55),  # 1 blue kresek
        ("#f2f2ee", 0.0, 0.5),   # 2 white kresek
        ("#facc15", 0.0, 0.55),  # 3 yellow kresek
        ("#1f1f1f", 0.0, 0.5),   # 4 black kresek
    ],
}

BAG = [(-0.10, 0.05), (-0.07, 0.11), (0.0, 0.13), (0.07, 0.10), (0.11, 0.045), (0.14, 0.02), (0.19, 0.035)]
BAGS = [  # (x, y, z, tilt about x, tilt about y, spin, scale, swatch)
    (0.00, 0.00, 0.02, 0.2, 0.1, 0.0, 1.15, 0),
    (0.20, 0.06, 0.00, 1.3, 0.3, 0.8, 1.0, 1),
    (-0.19, 0.08, 0.01, -1.2, 0.2, 2.0, 0.95, 2),
    (0.06, -0.19, -0.01, 1.4, 1.2, 3.5, 0.9, 3),
    (-0.06, 0.20, 0.0, -1.0, -1.1, 5.0, 0.85, 4),
]


def build():
    geo = ts.Geo()
    for x, y, z, rx, ry, rz, s, key in BAGS:
        geo.xform = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
                     @ Matrix.Rotation(rx, 4, "X") @ Matrix.Scale(s, 4))
        ts.lathe(geo, [(zz, r, r * 0.85) for zz, r in BAG], 7, lambda r, k=key: k, cap0=key, cap1=key)
    geo.xform = None
    ts.crumple(geo, 0.018, 9.0, seed=15)
    geo.recentre(keep_z=True)
    zmin = min(v.z for v in geo.v)
    geo.deform(lambda co: (co.x, co.y, co.z - zmin - 0.10))      # ~10 cm of the clump below the waterline
    return geo.objects(SPEC["name"])
