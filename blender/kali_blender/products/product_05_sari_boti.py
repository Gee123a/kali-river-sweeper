"""SARI BOTI sobek bread (28 x 15 cm bag), NEW: sealed bag wrapped round a loaf of 4 x 2 pull-apart rolls
(creases between the rolls), crimped at both ends, lying print-up on a flat bottom. Clean print with the
golden rolls showing in the window (labels.py "sari_boti_full", dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 5,
    "name": "SM_Product_SariBoti",
    "prefab": "PF_Product_SariBoti",
    "label": "SARI BOTI sobek bread (sealed, with loaf)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "sari_boti_full", "rows": 3, "dirty": False},
    "palette": [("#4a3a30", 0.0, 0.6)],   # 0 inside of the film (unused: the bag is sealed)
}

W, H = 0.28, 0.15
ROLL_X, ROLL_Z = (0.31, 0.5, 0.69), 0.5            # seams between the rolls (on grid lines)
XF = [0.0, 0.046, 0.12, 0.2, 0.31, 0.4, 0.5, 0.6, 0.69, 0.8, 0.88, 0.954, 1.0]
ZF = [0.0, 0.15, 0.3, 0.5, 0.7, 0.85, 1.0]
LOAF = 0.03                                         # half height of the loaf


def _depth(u, v):
    if u < 0.05 or u > 0.95:
        return 0.0008                                   # crimp seals
    d = LOAF * ts.plateau((u - 0.08) / 0.84, 0.12) * ts.plateau(v, 0.2)
    if any(abs(u - x) < 1e-6 for x in ROLL_X) or abs(v - ROLL_Z) < 1e-6:
        d *= 0.86                                       # crease between two rolls
    return max(0.0008, d)


def build():
    geo = ts.Geo()
    ts.pillow(geo, W, H, XF, ZF, _depth, inner=None)
    ts.lay_flat(geo, (0, 0))
    geo.deform(lambda co: (co.x, co.y, max(co.z, -LOAF * 0.7)))   # loaf rests on a flat bottom
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
