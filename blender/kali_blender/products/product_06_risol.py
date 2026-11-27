"""Risol Anti Noda + Molti detergent stand-up pouch (20 x 30 cm), NEW and full: standing on its gusset floor,
bulging with powder, sealed top with a tear notch. Clean Risol print (labels.py, dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 6,
    "name": "SM_Product_Risol",
    "prefab": "PF_Product_Risol",
    "label": "Risol detergent pouch (full)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "risol", "rows": 3, "dirty": False},
    "palette": [("#b8b9bd", 0.6, 0.5)],   # 0 metallised film (unused: the pouch is sealed)
}

W, H = 0.20, 0.30
XF = [0.0, 0.035, 0.27, 0.5, 0.73, 0.965, 1.0]
ZF = [0.0, 0.1, 0.25, 0.42, 0.6, 0.78, 0.953, 1.0]


def _depth(u, v):
    if u < 0.035 or u > 0.965 or v > 0.95:
        return 0.0008                                   # side / top seals
    edge = (1 - abs(2 * u - 1) ** 3) ** 0.5
    return max(0.0008, edge * (0.008 + 0.034 * (1 - v) ** 1.1))


def build():
    geo = ts.Geo()
    ts.pillow(geo, W, H, XF, ZF, _depth, tear=("tr", 1), gusset=True, inner=None)   # tear notch, still sealed
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
