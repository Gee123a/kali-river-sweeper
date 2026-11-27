"""Kampung bin (200 L steel drum, 0.6 m x 0.92 m with lid): blue painted drum with rolling hoops, yellow
stencil SAMPAH ANORGANIK band (labels.py "tong_anorganik", lightly worn), loose lid with a bar handle.

Origin = centre of the bbox bottom (base pivot): it stands on the river bank.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 7,
    "name": "SM_Prop_TongSampahKampung",
    "prefab": "PF_Prop_TongSampahKampung",
    "label": "Kampung 200 L drum bin, blue with SAMPAH ANORGANIK stencil, lid",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (250, 400),
    "label_art": {"name": "tong_anorganik", "rows": 3},
    "palette": [
        ("#1e47b8", 0.2, 0.45),  # 0 blue painted steel
        ("#6b6f73", 0.7, 0.4),   # 1 worn steel rims
        ("#1c1c1c", 0.0, 0.3),   # 2 black handle
    ],
}

LABEL_Z = (0.31, 0.57)
RINGS = [
    (0.000, 0.270, 0.270),
    (0.015, 0.290, 0.290),    # bottom chime
    (0.030, 0.283, 0.283),
    (0.290, 0.283, 0.283),
    (0.300, 0.293, 0.293),    # rolling hoop
    (0.310, 0.283, 0.283),    # stencil band
    (0.570, 0.283, 0.283),
    (0.580, 0.293, 0.293),    # rolling hoop
    (0.590, 0.283, 0.283),
    (0.850, 0.283, 0.283),
    (0.870, 0.290, 0.290),    # top chime
]


def _key(r):
    if r == 5:
        return "label"
    return 1 if r in (0, 9) else 0


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, 12, _key, uv=ts.wrap_uv(*LABEL_Z), cap0=1)
    ts.lathe(geo, [(0.870, 0.300, 0.300), (0.895, 0.300, 0.300), (0.905, 0.270, 0.270)], 12, lambda r: 0, cap0=0, cap1=0)
    ts.box(geo, 2, (-0.10, -0.015, 0.905), (0.10, 0.015, 0.935))                  # lid handle bar
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
