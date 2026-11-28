"""Quest marker (6B): chunky "!" (0.42 m) floating above quest givers: tapered bar + dot in emissive amber (its
swatch is white in the Emission map, so _EmissionColor makes it glow), with a dark back-plate disc for contrast
against bright sky. Billboard it in Unity (e.g. LookAt camera) or leave it upright facing +Z.

Origin = centre of the bbox bottom (bottom of the dot): place it above the NPC's head.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 12,
    "name": "SM_Prop_QuestMarker",
    "prefab": "PF_Prop_QuestMarker",
    "label": "Quest marker exclamation mark, emissive",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (60, 300),
    "palette": [
        ("#fbbf24", 0.0, 0.6, True),   # 0 glowing amber "!"
        ("#1f2937", 0.0, 0.4),         # 1 dark back plate / outline
    ],
}


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(0.0, 0.035, 0.035), (0.035, 0.05, 0.05), (0.07, 0.035, 0.035)], 8, lambda r: 0, cap0=0, cap1=0)
    ts.lathe(geo, [(0.11, 0.032, 0.032), (0.42, 0.06, 0.06)], 8, lambda r: 0, cap0=0, cap1=0)               # bar
    geo.xform = Matrix.Translation((0, 0.07, 0.22)) @ Matrix.Rotation(math.radians(90), 4, "X")            # back plate
    ts.lathe(geo, [(0.0, 0.17, 0.25), (0.01, 0.17, 0.25)], 12, lambda r: 1, cap0=1, cap1=1)
    geo.xform = None
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
