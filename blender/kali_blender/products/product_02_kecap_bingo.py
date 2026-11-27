"""BINGO kecap manis refill stand-up pouch (16.5 x 25 cm), NEW and full: standing on its gusset floor,
bulging at the bottom and tapering to the sealed top, tear notch on the top-right corner. Clean BINGO print.

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 2,
    "name": "SM_Product_KecapBingo",
    "prefab": "PF_Product_KecapBingo",
    "label": "BINGO kecap manis refill pouch (full)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "bingo", "rows": 3, "dirty": False},
    "palette": [("#b5b8bb", 0.6, 0.5)],   # 0 metallised film (unused: the pouch is sealed)
}

W, H = 0.165, 0.25
XF = [0.0, 0.04, 0.27, 0.5, 0.73, 0.96, 1.0]
ZF = [0.0, 0.1, 0.25, 0.42, 0.6, 0.78, 0.956, 1.0]


def _depth(u, v):
    if u < 0.04 or u > 0.96 or v > 0.95:
        return 0.0008                                   # side / top seals
    edge = (1 - abs(2 * u - 1) ** 3) ** 0.5
    return max(0.0008, edge * (0.005 + 0.030 * (1 - v) ** 1.2))


def build():
    geo = ts.Geo()
    ts.pillow(geo, W, H, XF, ZF, _depth, tear=("tr", 1), gusset=True, inner=None)   # tear notch, still sealed
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
