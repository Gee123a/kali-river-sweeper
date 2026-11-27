"""Bingo kecap manis refill stand-up pouch (parody brand) (16.5 x 25 cm), emptied: top-right corner cut off to pour,
gusset floor, top-left corner folded down, crumpled. Teal print with the stork disc and red BINGO
wordmark (labels.py); the cut corner shows the metallised inside.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 4,
    "name": "SM_Trash_SachetKecapBingo",
    "prefab": "PF_Trash_SachetKecapBingo",
    "label": "Bingo kecap manis refill pouch (emptied, folded)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "bingo", "rows": 3},
    "palette": [
        ("#b5b8bb", 0.6, 0.5),   # 0 metallised film inside
    ],
}

W, H = 0.165, 0.25
XF = [i / 6 for i in range(7)]
ZF = [0.0, 0.08, 0.22, 0.38, 0.54, 0.67, 0.78, 0.89, 1.0]   # top cells square (2.75 cm): straight fold / cut


def _depth(u, v):
    if u < 0.04 or u > 0.96 or v > 0.95:
        return 0.0008                                # side / top seals
    edge = 1 - abs(2 * u - 1) ** 3
    gus = max(0.0, 1 - v / 0.6) ** 2                 # gusset keeps the bottom open
    return max(0.0008, edge * (0.003 + 0.012 * gus))


def build():
    geo = ts.Geo()
    g = ts.pillow(geo, W, H, XF, ZF, _depth, tear=("tr", 2), split=("tl", 3), gusset=True, inner=0)
    F, nx, nz = g["F"], g["nx"], g["nz"]
    ts.fold(geo, ts.corner_verts(g, "tl", 3), geo.v[F[0][nz - 3]], geo.v[F[3][nz]], 145)
    ts.crumple(geo, 0.007, 16.0, seed=4)
    ts.bend(geo, (0, 0, 1), (0, 0, 0), 14, -0.12, 0.12, along=2)     # slight twist up the pouch
    geo.deform(lambda co: (co.x, co.y - 0.012 * (2 * co.z / H) ** 2, co.z))
    ts.lay_flat(geo, (6, 8))
    geo.recentre()
    return geo.objects(SPEC["name"])
