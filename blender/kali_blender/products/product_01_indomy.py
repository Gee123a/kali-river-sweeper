"""Indomy Mi Goreng pillow pack (12 x 10 cm), NEW: both crimps sealed, puffed over the flat noodle block,
lying print-up as it sits on a shelf. Clean Indomy print (labels.py, dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 1,
    "name": "SM_Product_Indomy",
    "prefab": "PF_Product_Indomy",
    "label": "Indomy Mi Goreng pack (sealed)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "indomy", "rows": 3, "dirty": False},
    "palette": [("#b9bcc0", 0.6, 0.55)],   # 0 metallised film (unused: the pack is sealed)
}

W, H = 0.12, 0.10
XF = [i / 8 for i in range(9)]
ZF = [0.0, 0.085, 0.14, 0.3, 0.5, 0.7, 0.86, 0.915, 1.0]   # crimp seals; short steep ends keep the print on top


def _depth(u, v):
    if v < 0.09 or v > 0.91:
        return 0.0008
    return max(0.0008, 0.011 * ts.plateau(u, 0.1) * ts.plateau((v - 0.085) / 0.83, 0.07))


def build():
    geo = ts.Geo()
    ts.pillow(geo, W, H, XF, ZF, _depth, inner=None)
    ts.lay_flat(geo, (0, 0))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
