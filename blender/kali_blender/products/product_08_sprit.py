"""Sprit 1.5 L PET bottle (9.1 x 32 cm), NEW and full: the trash bottle's lathe, uncrushed, standing on its
petaloid feet. The filled body is a deeper green than the empty neck above the fill line; green wrap label
(labels.py, dirty=False) and green cap.

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts
from kali_blender.trash import trash_10_botol_sprit as bottle   # same rings and label band

SPEC = {
    "index": 8,
    "name": "SM_Product_Sprit",
    "prefab": "PF_Product_Sprit",
    "label": "Sprit 1.5 L PET bottle (full)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "sprit", "rows": 3, "dirty": False},
    "palette": [
        ("#4fa872", 0.0, 0.9),   # 0 PET with lemon-lime soda inside
        ("#0e7a3c", 0.0, 0.5),   # 1 green cap
        ("#a9d8b6", 0.0, 0.9),   # 2 empty PET above the fill line
    ],
}


def _key(r):
    if r == 6:
        return "label"
    if r >= 12:
        return 1
    return 2 if r >= 8 else 0           # fill line at the shoulder (ring 8, z 0.248)


def build():
    geo = ts.Geo()
    R = ts.lathe(geo, bottle.RINGS, bottle.SEGS, _key, uv=ts.wrap_uv(*bottle.LABEL_Z), cap0=0, cap1=1)
    for k, idx in enumerate(R[1]):                       # petaloid feet
        if k % 2:
            geo.v[idx] = geo.v[idx] * 0.82
            geo.v[idx].z = 0.007
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
