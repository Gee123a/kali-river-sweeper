"""Raft of PET bottles (~0.95 x 0.38 m): twelve 1.5 L bottles in four rows of three, tied with yellow nylon rope
bands; pale green / blue / clear tints with red, blue and orange caps. A floating multi-unit pickup that reads
on brown water.

Origin = WATERLINE: bottles float high, roughly a third submerged.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 16,
    "name": "SM_Trash_RaftBotol",
    "prefab": "PF_Trash_RaftBotol",
    "label": "Raft of PET bottles tied with nylon rope",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "pivot": "waterline",
    "tris": (250, 600),
    "palette": [
        ("#9fd8b0", 0.0, 0.85),  # 0 pale green PET
        ("#a9cfe8", 0.0, 0.85),  # 1 pale blue PET
        ("#e4ece8", 0.0, 0.85),  # 2 clear PET
        ("#e11d2a", 0.0, 0.5),   # 3 red cap
        ("#1d6fe1", 0.0, 0.5),   # 4 blue cap
        ("#f97316", 0.0, 0.5),   # 5 orange cap
        ("#facc15", 0.0, 0.4),   # 6 yellow nylon rope
    ],
}

R, L = 0.045, 0.31
BOTTLE = [(0.0, 0.035), (0.02, R), (0.22, R), (0.29, 0.016), (0.31, 0.015)]


def build():
    geo = ts.Geo()
    n = 0
    for row in range(4):
        y = (row - 1.5) * 2 * R
        for col in range(3):
            x0 = (col - 1.5) * L + (0.03 if row % 2 else 0.0)
            flip = (row + col) % 2
            body, cap = n % 3, 3 + (n % 3)
            rot = Matrix.Rotation(math.radians(-90 if flip else 90), 4, "Y")             # lathe Z -> +/-X
            x = x0 + (L if flip else 0.0)
            geo.xform = Matrix.Translation((x, y, 0.0)) @ rot
            ts.lathe(geo, [(z, r, r) for z, r in BOTTLE[:-1]], 5, lambda r, b=body: b, cap0=body)
            ts.lathe(geo, [BOTTLE[-2][:1] + (0.016, 0.016), (L, 0.016, 0.016)], 5, lambda r, c=cap: c, cap1=cap)
            n += 1
    geo.xform = None
    for x in (-0.33, 0.0, 0.33):                                                      # rope bands round the raft
        ts.box(geo, 6, (x - 0.012, -4 * R - 0.006, -R - 0.006), (x + 0.012, 4 * R + 0.006, R + 0.006))
    ts.crumple(geo, 0.004, 12.0, seed=16)
    geo.recentre(keep_z=True)
    geo.deform(lambda co: (co.x, co.y, co.z + R * 0.35))                              # a third under water
    return geo.objects(SPEC["name"])
