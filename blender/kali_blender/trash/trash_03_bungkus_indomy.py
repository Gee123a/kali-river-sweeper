"""Indomy Mi Goreng pillow pack (parody brand) (12 x 10 cm): top torn off along a jagged line, mouth gaping, crumpled,
bottom-right corner folded over the front. Both sheets carry the procedural Indomy print (labels.py);
the inside of the mouth shows the metallised film.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 3,
    "name": "SM_Trash_BungkusIndomy",
    "prefab": "PF_Trash_BungkusIndomy",
    "label": "Indomy Mi Goreng wrapper (torn open, crumpled)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "indomy", "rows": 3},
    "palette": [
        ("#b9bcc0", 0.6, 0.55),  # 0 metallised film inside the pack
    ],
}

W, H = 0.12, 0.10
XF = [i / 8 for i in range(9)]
ZF = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9]       # square 1.5 cm cells (straight fold); top crimp torn away


def _depth(u, v):
    edge = 1 - abs(2 * u - 1) ** 2.2
    if v > 0.89:
        return 0.003 + 0.004 * edge                 # open lips
    return max(0.0008, 0.007 * edge * min(1.0, v / 0.3))


def build():
    geo = ts.Geo()
    g = ts.pillow(geo, W, H, XF, ZF, _depth, open_edges=("top",), split=("br", 3), inner=0)
    F, B, nx, nz = g["F"], g["B"], g["nx"], g["nz"]
    # jagged tear along the top and a gaping mouth
    jag = [0.0, -0.004, 0.002, -0.003, 0.003, -0.002, 0.004, -0.003, 0.0]
    for i in range(nx + 1):
        for idx in {F[i][nz], B[i][nz]}:
            geo.v[idx].z += jag[i]
    for i in range(1, nx):
        u = 1 - abs(2 * XF[i] - 1) ** 2
        geo.v[F[i][nz]].y -= 0.007 * u
        geo.v[B[i][nz]].y += 0.002 * u
    # dog-ear: bottom-right corner folded over the print
    ts.fold(geo, ts.corner_verts(g, "br", 3), geo.v[F[nx - 3][0]], geo.v[F[nx][3]], 150)
    # crumple + a gentle curl across the width
    ts.crumple(geo, 0.0045, 28.0, seed=3)
    geo.deform(lambda co: (co.x, co.y + 0.006 * (2 * co.x / W) ** 2, co.z))
    ts.lay_flat(geo, (14, -6))
    geo.recentre()
    return geo.objects(SPEC["name"])
