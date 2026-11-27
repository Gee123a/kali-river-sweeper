"""Risol Anti Noda + Molti detergent stand-up pouch (parody brand) (20 x 30 cm), emptied: cut open across the top,
gusset floor, bottom-left corner folded over, heavily crumpled. Green-to-purple print with the
yellow Risol wordmark and blue/green splash (labels.py); the cut top shows the metallised inside.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 8,
    "name": "SM_Trash_BungkusRisol",
    "prefab": "PF_Trash_BungkusRisol",
    "label": "Risol detergent pouch (cut open, crumpled)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "risol", "rows": 3},
    "palette": [
        ("#b8b9bd", 0.6, 0.5),   # 0 metallised film inside
    ],
}

W, H = 0.20, 0.30
XF = [i / 6 for i in range(7)]
ZF = [0.0, 0.111, 0.222, 0.38, 0.54, 0.7, 0.85, 0.93]   # square bottom cells (straight fold); cut below the top seal


def _depth(u, v):
    if u < 0.035 or u > 0.965:
        return 0.0008                                 # side seals
    edge = 1 - abs(2 * u - 1) ** 3
    if v > 0.92:
        return 0.003 + 0.006 * edge                   # open cut
    gus = max(0.0, 1 - v / 0.55) ** 2
    return max(0.0008, edge * (0.004 + 0.014 * gus))


def build():
    geo = ts.Geo()
    g = ts.pillow(geo, W, H, XF, ZF, _depth, open_edges=("top",), split=("bl", 2), gusset=True, inner=0)
    F, B, nx, nz = g["F"], g["B"], g["nx"], g["nz"]
    for i, dz in zip(range(nx + 1), (0.0, -0.006, 0.003, -0.004, 0.005, -0.003, 0.0)):   # scissor-ragged cut
        for idx in {F[i][nz], B[i][nz]}:
            geo.v[idx].z += dz
    ts.fold(geo, ts.corner_verts(g, "bl", 2), geo.v[F[2][0]], geo.v[F[0][2]], 150)
    ts.crumple(geo, 0.010, 13.0, seed=8)
    ts.bend(geo, (1, 0, 0), (0, 0, 0.02), 24, 0.02, 0.15)                # top half sags back
    ts.lay_flat(geo, (4, -7))
    geo.recentre()
    return geo.objects(SPEC["name"])
