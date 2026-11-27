"""Lifeman shampoo bottle (170 ml, 6.2 x 3.8 x 20 cm), NEW: the trash bottle's flat-oval lathe, undented,
standing upright with the dark-blue flip-top lid snapped shut. Clean Lifeman print front and back.

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts
from kali_blender.trash import trash_06_botol_lifeman as bottle   # same body rings and label band

SPEC = {
    "index": 4,
    "name": "SM_Product_Lifeman",
    "prefab": "PF_Product_Lifeman",
    "label": "Lifeman shampoo bottle (new, cap closed)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "lifeman", "rows": 3, "dirty": False},
    "palette": [
        ("#e7ebf0", 0.0, 0.55),  # 0 white HDPE (shoulder, base)
        ("#1c3a8c", 0.0, 0.6),   # 1 dark-blue flip cap
    ],
}

RINGS = bottle.RINGS + [(0.190 + bottle.LID_H, 0.0236, 0.0146)]   # lid shut on top of the cap deck


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, bottle.SEGS, bottle._key, uv=ts.pair_uv(*bottle.LABEL_Z), cap0=0, cap1=1)
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
