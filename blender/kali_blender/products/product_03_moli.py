"""MOLI 22 g sachet (10 x 9.5 cm), NEW: flat, sealed, lightly filled with powder, lying print-up.
Clean MOLI print (labels.py, dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 3,
    "name": "SM_Product_Moli",
    "prefab": "PF_Product_Moli",
    "label": "MOLI 22 g sachet (sealed)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "moli", "rows": 3, "dirty": False},
    "palette": [("#bfc2c4", 0.6, 0.5)],   # 0 metallised film (unused: the sachet is sealed)
}

W, H = 0.10, 0.095
XF = [i / 6 for i in range(7)]
ZF = [0.0, 0.063, 0.25, 0.45, 0.65, 0.82, 0.937, 1.0]


def _depth(u, v):
    if v < 0.07 or v > 0.93:
        return 0.0008                                   # crimp seals
    return max(0.0008, 0.0045 * ts.plateau(u, 0.17) * ts.plateau((v - 0.063) / 0.874, 0.2))


def build():
    geo = ts.Geo()
    ts.pillow(geo, W, H, XF, ZF, _depth, inner=None)
    ts.lay_flat(geo, (0, 0))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
