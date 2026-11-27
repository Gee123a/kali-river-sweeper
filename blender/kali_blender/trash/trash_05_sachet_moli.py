"""MOLI 22 g sachet (parody brand, 10 x 9.5 cm): top-right corner torn off at the notch, bottom strip bent back,
crumpled. Green print with the white swoosh and brown MOLI wordmark (labels.py); the torn corner shows
the metallised inside.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 5,
    "name": "SM_Trash_SachetMoli",
    "prefab": "PF_Trash_SachetMoli",
    "label": "MOLI 22 g sachet (torn corner, crumpled)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "moli", "rows": 3},
    "palette": [
        ("#bfc2c4", 0.6, 0.5),   # 0 metallised film inside
    ],
}

W, H = 0.10, 0.095
XF = [i / 6 for i in range(7)]
ZF = [0.0, 0.063, 0.25, 0.45, 0.65, 0.82, 0.937, 1.0]


def _depth(u, v):
    if v < 0.07 or v > 0.93:
        return 0.0008                                # crimp seals
    edge = 1 - abs(2 * u - 1) ** 2
    return max(0.0008, 0.0035 * edge)


def build():
    geo = ts.Geo()
    g = ts.pillow(geo, W, H, XF, ZF, _depth, tear=("tr", 2), inner=0)
    # bottom strip bent back under the logo (squeezed-out sachet), then crumpled
    F = g["F"]
    zc = geo.v[F[0][2]].z
    ts.fold(geo, geo.select(lambda co: co.z < zc - 1e-4), geo.v[F[0][2]], geo.v[F[g["nx"]][2]], 38, toward=(0, 1, 0))
    ts.crumple(geo, 0.0032, 30.0, seed=5)
    ts.lay_flat(geo, (10, 4))
    geo.recentre()
    return geo.objects(SPEC["name"])
