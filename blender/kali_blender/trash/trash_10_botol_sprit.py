"""Sprit 1.5 L PET bottle (parody brand, 9.1 cm x 32 cm): clear-green body with petaloid feet and grip waist, green
wrap label (white Sprit wordmark, labels.py) on both halves, green cap. Crushed flat in the middle,
dented, kinked at the waist; lies on its side, label up, the way it floats.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 10,
    "name": "SM_Trash_BotolSprit",
    "prefab": "PF_Trash_BotolSprit",
    "label": "Sprit 1.5 L PET bottle (crushed)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "sprit", "rows": 3},
    "palette": [
        ("#7cc493", 0.0, 0.9),   # 0 clear-green PET (opaque stand-in, glossy)
        ("#0e7a3c", 0.0, 0.5),   # 1 green cap
    ],
}

SEGS = 12
LABEL_Z = (0.130, 0.218)
RINGS = [
    (0.005, 0.020, 0.020),   # base dome edge
    (0.000, 0.037, 0.037),   # feet (alternated below)
    (0.020, 0.0455, 0.0455),
    (0.090, 0.0455, 0.0455),
    (0.104, 0.0420, 0.0420),  # grip waist
    (0.118, 0.0455, 0.0455),
    (0.130, 0.0455, 0.0455),  # label band
    (0.218, 0.0455, 0.0455),
    (0.248, 0.0405, 0.0405),  # shoulder
    (0.274, 0.0270, 0.0270),
    (0.289, 0.0145, 0.0145),  # neck
    (0.292, 0.0190, 0.0190),  # support ring
    (0.295, 0.0155, 0.0155),  # cap
    (0.322, 0.0155, 0.0155),
]


def _key(r):
    if r == 6:
        return "label"
    return 1 if r >= 12 else 0


def build():
    geo = ts.Geo()
    R = ts.lathe(geo, RINGS, SEGS, _key, uv=ts.wrap_uv(*LABEL_Z), cap0=0, cap1=1)
    for k, idx in enumerate(R[1]):                       # petaloid feet
        if k % 2:
            geo.v[idx] = geo.v[idx] * 0.82
            geo.v[idx].z = 0.007
    # crushed: body squashed flat front-to-back, dents, kinked at the waist
    geo.deform(lambda co: (co.x * (1 + 0.12 * _mid(co.z)), co.y * (1 - 0.5 * _mid(co.z)), co.z))
    ts.dent(geo, (0.0, -0.03, 0.06), 0.05, (0.006, 0.012, 0.0))
    ts.dent(geo, (-0.025, -0.02, 0.17), 0.045, (0.008, 0.010, 0.0))
    ts.crumple(geo, 0.004, 22.0, seed=10, sel=geo.select(lambda co: co.z < 0.27))
    ts.dent(geo, (0.03, 0.02, 0.235), 0.04, (-0.010, -0.004, 0.0))
    ts.bend(geo, (1, 0, 0), (0, 0, 0.104), -9, 0.104, 0.16)
    ts.bend(geo, (0, 0, 1), (0, 0, 0), 12, 0.02, 0.25)
    ts.lay_flat(geo, (12, 0), on_side=True)
    geo.recentre()
    return geo.objects(SPEC["name"])


def _mid(z):
    """0 at the base and shoulder, 1 in the middle of the body (where the bottle got stepped on)."""
    t = min(max((z - 0.02) / 0.23, 0.0), 1.0)
    return (4 * t * (1 - t)) ** 1.5
