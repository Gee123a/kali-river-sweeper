"""GUDANG GULA International cigarette pack (5.5 x 2.2 x 8.8 cm), NEW: the trash pack's printed card box,
square and uncrushed, flip-top lid shut, standing upright. Clean print (labels.py "gudang_gula", dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts
from kali_blender.trash import trash_11_kotak_rokok as pack   # same printed shell

SPEC = {
    "index": 9,
    "name": "SM_Product_GudangGula",
    "prefab": "PF_Product_GudangGula",
    "label": "GUDANG GULA cigarette pack (new, closed)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "gudang_gula", "rows": 3, "dirty": False},
    "palette": [
        ("#c3c3bd", 0.7, 0.55),  # 0 foil (top of the body, under the lid)
        ("#e9e2d2", 0.0, 0.3),   # 1 white card (unused: lid shut)
        ("#8e1420", 0.0, 0.35),  # 2 red card (bottom, lid top)
    ],
}


def build():
    geo = ts.Geo()
    pack._shell(geo, 0.0, pack.HB, 4, 0)                                                   # body
    ts.grid(geo, 2, (-pack.W / 2, pack.D / 2, 0), (pack.W, 0, 0), (0, -pack.D, 0), 4, 2)   # bottom
    pack._shell(geo, pack.HB, pack.H, 1, 2)                                                # lid, shut
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
