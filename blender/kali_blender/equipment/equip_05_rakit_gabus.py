"""Rakit Gabus starter raft (player boat tier 1, 1.8 x 1.4 m): three chipped white styrofoam blocks side by
side, four bamboo poles lashed across them with black inner-tube rubber wraps at every crossing.

Origin = WATERLINE (centred, on the water surface): styrofoam floats high, a third of the blocks under water.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 5,
    "name": "SM_Prop_RakitGabus",
    "prefab": "PF_Prop_RakitGabus",
    "label": "Styrofoam starter raft: 3 foam blocks, bamboo poles, rubber lashings",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (500, 900),
    "max_size": 2.5,
    "palette": [
        ("#e8e6dc", 0.0, 0.25),  # 0 styrofoam (used, off-white)
        ("#c9a464", 0.0, 0.35),  # 1 bamboo
        ("#1c1c1c", 0.0, 0.3),   # 2 black rubber strip
    ],
}

BLOCK_Y = (-0.42, 0.0, 0.42)       # block centres across the raft
BLOCK = (0.90, 0.17, -0.10, 0.20)  # half length, half width, bottom z, top z (a third submerged)
POLE_X = (-0.75, -0.25, 0.25, 0.75)
POLE_Z = BLOCK[3] + 0.03


def build():
    geo = ts.Geo()
    hx, hy, z0, z1 = BLOCK
    for y in BLOCK_Y:
        ts.box(geo, 0, (-hx, y - hy, z0), (hx, y + hy, z1), n=(6, 2, 2))
    ts.crumple(geo, 0.012, 5.0, seed=5)                         # chipped, uneven foam
    for x in POLE_X:                                            # bamboo poles across, one node each
        geo.xform = Matrix.Translation((x, -0.70, POLE_Z)) @ Matrix.Rotation(math.radians(-90), 4, "X")
        ts.lathe(geo, [(0.0, 0.028, 0.028), (0.68, 0.03, 0.03), (0.70, 0.034, 0.034), (0.72, 0.03, 0.03),
                       (1.40, 0.028, 0.028)], 6, lambda r: 1, cap0=1, cap1=1)
    geo.xform = None
    for x in POLE_X:                                            # inner-tube rubber wrap at every crossing
        for y in BLOCK_Y:
            ts.box(geo, 2, (x - 0.05, y - 0.035, z1 - 0.012), (x + 0.05, y + 0.035, POLE_Z + 0.04))
    geo.recentre(keep_z=True)                                  # waterline stays at z = 0
    return geo.objects(SPEC["name"])
