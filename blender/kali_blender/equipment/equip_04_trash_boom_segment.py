"""River trash boom segment (2.2 m): orange HDPE float in two sections with rounded ends, black skirt hanging
below it, galvanised eye brackets and heavy shackles at both ends to chain the next segment.

Origin = WATERLINE (float axis on the water surface, centred): the float rides half submerged and the importer
places "trash_boom" items at y = 0. Loaded as Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 4,
    "name": "SM_Prop_TrashBoomSegment",
    "prefab": "PF_Prop_TrashBoomSegment",
    "label": "Floating river trash boom segment: orange float, skirt, shackles",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (200, 400),
    "max_size": 2.5,
    "palette": [
        ("#e8651d", 0.0, 0.45),  # 0 orange float (sun-faded)
        ("#1c1d1f", 0.0, 0.3),   # 1 black skirt
        ("#8d949b", 0.8, 0.45),  # 2 galvanised steel
    ],
}

HALF = 1.0                         # float half length
R = 0.15                           # float radius


def build():
    geo = ts.Geo()
    geo.xform = Matrix.Rotation(math.radians(90), 4, "Y")          # lathe axis Z -> X
    rings = [(-HALF, 0.09), (-0.96, 0.14), (-0.90, R), (-0.04, R), (0.0, 0.13), (0.04, R),
             (0.90, R), (0.96, 0.14), (HALF, 0.09)]
    ts.lathe(geo, [(z, r, r) for z, r in rings], 8, lambda r: 0, cap0=0, cap1=0)
    geo.xform = None
    ts.grid(geo, 1, (-0.95, 0.0, -0.40), (1.9, 0, 0), (0, 0, 0.28), 2, 1)       # skirt, both faces
    ts.grid(geo, 1, (0.95, 0.0, -0.40), (-1.9, 0, 0), (0, 0, 0.28), 2, 1)
    for s in (-1, 1):
        xa, xb = sorted((s * (HALF - 0.03), s * (HALF + 0.05)))
        ts.box(geo, 2, (xa, -0.015, -0.03), (xb, 0.015, 0.03))                         # eye bracket
        geo.xform = Matrix.Translation((s * (HALF + 0.09), 0, 0)) @ Matrix.Rotation(math.radians(90), 4, "X")
        ts.torus(geo, 2, 0.045, 0.012, 6, 4)                                     # shackle ring
        geo.xform = None
    geo.recentre(keep_z=True)                                  # waterline stays at z = 0
    return geo.objects(SPEC["name"])
