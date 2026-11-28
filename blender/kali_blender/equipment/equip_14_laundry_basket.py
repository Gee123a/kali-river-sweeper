"""Villager laundry basket (4B): round woven bamboo bakul (55 cm wide, 26 cm tall) with a thick rolled rim, the
weave painted procedurally (labels.py "anyaman"), and a heap of wet washing (batik red, blue, white) inside.

Origin = centre of the bbox bottom (base pivot): it sits on the washing steps or on a hip via a socket.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 14,
    "name": "SM_Prop_LaundryBasket",
    "prefab": "PF_Prop_LaundryBasket",
    "label": "Woven bamboo laundry basket with wet washing",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (200, 400),
    "label_art": {"name": "anyaman", "rows": 3},
    "palette": [
        ("#8a5f2a", 0.0, 0.35),  # 0 rim / inside weave (dark)
        ("#b83227", 0.0, 0.4),   # 1 red batik cloth
        ("#2f5fb3", 0.0, 0.4),   # 2 blue cloth
        ("#efece4", 0.0, 0.4),   # 3 white cloth
    ],
}


def _outer_uv(am, a, z):
    return ts.panel_uv("pack", "front", a / (2 * math.pi), z / 0.24)     # a runs 0..2pi, no wrap at the seam


def build():
    geo = ts.Geo()
    outer = [(0.0, 0.17, 0.17), (0.03, 0.22, 0.22), (0.24, 0.27, 0.27)]
    ts.lathe(geo, outer, 12, lambda r: "label", uv=_outer_uv, cap0=0)
    ts.lathe(geo, [(0.24, 0.255, 0.255), (0.03, 0.205, 0.205), (0.015, 0.16, 0.16)], 12, lambda r: 0, cap1=0)  # inside
    geo.xform = Matrix.Translation((0, 0, 0.245))
    ts.torus(geo, 0, 0.265, 0.015, 12, 4)                                                       # rolled rim
    geo.xform = None
    for (x, y, z), r, key in (((-0.06, 0.03, 0.17), 0.12, 1), ((0.08, -0.04, 0.18), 0.10, 2), ((0.02, 0.09, 0.2), 0.08, 3)):
        geo.xform = Matrix.Translation((x, y, z)) @ Matrix.Scale(1.0, 4)
        ts.lathe(geo, [(-0.03, r * 0.6, r * 0.5), (0.02, r, r * 0.8), (0.05, r * 0.4, r * 0.35)], 6,
                 lambda rr, k=key: k, cap1=key)                                                  # washing heaps
    geo.xform = None
    ts.crumple(geo, 0.006, 14.0, seed=14, sel=geo.select(lambda co: co.z > 0.1 and abs(co.x) < 0.2 and abs(co.y) < 0.2))
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
