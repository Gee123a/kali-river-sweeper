"""Sari Boti sobek bread bag (parody brand, 28 x 15 cm), emptied: crimp-sealed left end twisted like a sweet wrapper,
right end torn open, film crumpled. Dark chocolate print with gold stripes and the blue SARI BOTI box
(labels.py); the open end shows the inside of the film.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 7,
    "name": "SM_Trash_BungkusSariBoti",
    "prefab": "PF_Trash_BungkusSariBoti",
    "label": "Sari Boti sobek bread bag (empty, crumpled)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "sari_boti", "rows": 3},
    "palette": [
        ("#4a3a30", 0.0, 0.6),   # 0 inside of the dark film
    ],
}

W, H = 0.28, 0.15
XF = [0.0, 0.046, 0.17, 0.3, 0.43, 0.57, 0.7, 0.83, 0.93, 1.0]
ZF = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def _depth(u, v):
    if u < 0.05:
        return 0.0008                                # crimp seal
    edge = 1 - abs(2 * v - 1) ** 2
    if u > 0.99:
        return 0.004 + 0.008 * edge                  # open mouth
    return max(0.0008, 0.010 * edge * min(1.0, (u - 0.046) / 0.12))


def build():
    geo = ts.Geo()
    g = ts.pillow(geo, W, H, XF, ZF, _depth, open_edges=("right",), inner=0)
    F, nx, nz = g["F"], g["nx"], g["nz"]
    for j, dz in zip(range(1, nz), (0.004, -0.003, 0.005, -0.004)):   # ragged tear at the open end
        for idx in (g["F"][nx][j], g["B"][nx][j]):
            geo.v[idx].x -= abs(dz) * 1.5
            geo.v[idx].z += dz
    ts.crumple(geo, 0.008, 14.0, seed=7)
    ts.bend(geo, (1, 0, 0), (0, 0, 0), -55, -0.08, -0.13, along=0)     # twisted crimp end
    ts.bend(geo, (0, 0, 1), (0.05, 0, 0), 16, 0.05, 0.14, along=0)     # bag sags open at the torn end
    ts.lay_flat(geo, (8, -5))
    geo.recentre()
    return geo.objects(SPEC["name"])
