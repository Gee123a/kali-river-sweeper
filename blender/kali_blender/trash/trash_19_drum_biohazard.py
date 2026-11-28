"""Biohazard bundle (~0.9 m): a 60 L purple tighthead drum lashed with yellow rope to a leaking lime jerrycan,
floating in a lime chemical slick. Distinct from SM_Trash_BiohazardDrum (single dented 200 L drum); the name
contains "Drum" + "Biohazard", so RiverTrashItem infers WasteClass.Biohazard. Purple #A855F7 + lime #84CC16
(docs/DESIGN.md).

Origin = WATERLINE: the slick lies on the water, drum and can half submerged.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 19,
    "name": "SM_Trash_DrumBiohazard",
    "prefab": "PF_Trash_DrumBiohazard",
    "label": "Biohazard bundle: 60 L purple drum + leaking lime jerrycan + slick",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "pivot": "waterline",
    "tris": (200, 600),
    "palette": [
        ("#a855f7", 0.3, 0.45),  # 0 purple drum
        ("#84cc16", 0.0, 0.5),   # 1 lime jerrycan
        ("#a3e635", 0.0, 0.95),  # 2 lime slick, wet
        ("#3a3540", 0.6, 0.4),   # 3 dark steel chimes / caps
        ("#facc15", 0.0, 0.4),   # 4 yellow rope
    ],
}


def build():
    geo = ts.Geo()
    geo.xform = Matrix.Translation((-0.12, 0.0, 0.0)) @ Matrix.Rotation(math.radians(90), 4, "Y")   # drum on its side
    ts.lathe(geo, [(-0.28, 0.17, 0.17), (-0.27, 0.19, 0.19), (-0.25, 0.185, 0.185), (-0.06, 0.185, 0.185),
                   (-0.05, 0.193, 0.193), (0.05, 0.193, 0.193), (0.06, 0.185, 0.185), (0.25, 0.185, 0.185),
                   (0.27, 0.19, 0.19), (0.28, 0.17, 0.17)], 10, lambda r: 3 if r in (0, 8) else 0, cap0=3, cap1=3)
    geo.xform = Matrix.Translation((0.30, 0.05, 0.0)) @ Matrix.Rotation(0.35, 4, "Z")
    ts.box(geo, 1, (-0.12, -0.08, -0.13), (0.12, 0.08, 0.13), n=(2, 2, 2))                     # jerrycan
    ts.box(geo, 1, (-0.05, -0.015, 0.13), (0.05, 0.015, 0.17))                                  # handle
    ts.lathe(geo, [(0.13, 0.025, 0.025), (0.16, 0.025, 0.025)], 6, lambda r: 3, cap1=3)         # spout cap
    geo.xform = None
    for x in (-0.20, -0.04):                                                                    # rope lashing
        ts.box(geo, 4, (x - 0.012, -0.21, -0.20), (x + 0.012, 0.21, 0.20))
    ts.box(geo, 4, (-0.02, -0.012, 0.15), (0.32, 0.012, 0.175))
    geo.xform = Matrix.Translation((0.05, 0.0, -0.01))                                          # lime slick on the water
    ts.lathe(geo, [(0.0, 0.55, 0.42), (0.004, 0.50, 0.38)], 12, lambda r: 2, cap1=2)
    geo.xform = None
    ts.dent(geo, (-0.20, -0.18, 0.06), 0.10, (0.0, 0.035, -0.01))
    ts.crumple(geo, 0.004, 8.0, seed=19)
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
