"""Karung (R2-J1, storage level 1): a full woven polypropylene rice sack (0.6 x 0.35 x 0.8 m) tied at the top with
twine, white weave with blue/red stripes and a plain BERAS 25 KG print (labels.py "karung"), slightly slumped.

Origin = centre of the bbox bottom (base pivot): the sack stands on the bank or the boat deck. To show it carried,
parent PF_Prop_Karung under SK_VillagerNPC / player Socket_Carry with local position (0, -0.45, 0.15) m and
rotation (0, 0, 90) deg - it then rides on the shoulder; or scale 0.6 for a hand-held half sack.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 17,
    "name": "SM_Prop_Karung",
    "prefab": "PF_Prop_Karung",
    "label": "Woven rice sack (karung), full, tied",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (150, 400),
    "label_art": {"name": "karung", "rows": 3},
    "palette": [
        ("#ecebe4", 0.0, 0.3),   # 0 sack weave (top, bottom)
        ("#a8763d", 0.0, 0.3),   # 1 twine
    ],
}


def _uv(am, a, z):
    if math.cos(am) > 0:                                 # front half: the print
        return ts.panel_uv("pack", "front", (math.sin(a) + 1) / 2, z / 0.72)
    return ts.panel_uv("pack", "front", (1 - math.sin(a)) / 2, z / 0.72)


def build():
    geo = ts.Geo()
    rings = [(0.0, 0.24, 0.13), (0.06, 0.30, 0.17), (0.30, 0.31, 0.18), (0.55, 0.29, 0.16), (0.72, 0.20, 0.12)]
    ts.lathe(geo, rings, 10, lambda r: "label", uv=_uv, cap0=0)
    ts.lathe(geo, [(0.72, 0.20, 0.12), (0.78, 0.05, 0.04), (0.80, 0.045, 0.035), (0.86, 0.12, 0.08)], 10,
             lambda r: 0 if r != 1 else 1, cap1=0)                                       # gathered neck, ears
    geo.xform = Matrix.Translation((0, 0, 0.785))
    ts.torus(geo, 1, 0.05, 0.008, 8, 3)                                                  # twine tie
    geo.xform = None
    ts.crumple(geo, 0.012, 6.0, seed=17)
    ts.bend(geo, (1, 0, 0), (0, 0, 0.3), 7, 0.3, 0.86)                                   # slumped
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
