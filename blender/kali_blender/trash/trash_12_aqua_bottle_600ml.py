"""600 ml PET mineral-water bottle (6.4 cm x 22 cm), ported from the old local prop: clear, faintly blue PET
with a grip groove, blue screw cap and a parody "AQUO" wrap label (labels.py, worn). Crushed flat in the
middle, dented and kinked; lies on its side, label up, the way it floats.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 12,
    "name": "SM_Trash_AquaBottle_600ml",
    "prefab": "PF_Trash_AquaBottle_600ml",
    "label": "600 ml PET water bottle, parody AQUO label (crushed)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "aquo", "rows": 3},
    "palette": [
        ("#c6dfe8", 0.0, 0.85),  # 0 clear PET (opaque stand-in, glossy, a little grubby)
        ("#1f5fd6", 0.0, 0.5),   # 1 blue screw cap
    ],
}

SEGS = 12
LABEL_Z = (0.090, 0.140)
RINGS = [
    (0.000, 0.0280, 0.0280),   # base
    (0.012, 0.0320, 0.0320),
    (0.070, 0.0295, 0.0295),   # grip groove
    (0.090, 0.0320, 0.0320),   # label band
    (0.140, 0.0320, 0.0320),
    (0.165, 0.0300, 0.0300),   # shoulder
    (0.190, 0.0180, 0.0180),
    (0.199, 0.0125, 0.0125),   # neck
    (0.201, 0.0145, 0.0145),   # cap
    (0.222, 0.0145, 0.0145),
]


def _key(r):
    if r == 3:
        return "label"
    return 1 if r >= 8 else 0


def _mid(z):
    """0 at the base and shoulder, 1 in the middle of the body (where it got stepped on)."""
    t = min(max((z - 0.01) / 0.16, 0.0), 1.0)
    return (4 * t * (1 - t)) ** 1.5


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, SEGS, _key, uv=ts.wrap_uv(*LABEL_Z), cap0=0, cap1=1)
    geo.deform(lambda co: (co.x * (1 + 0.15 * _mid(co.z)), co.y * (1 - 0.55 * _mid(co.z)), co.z))
    ts.dent(geo, (0.0, -0.02, 0.05), 0.035, (0.004, 0.009, 0.0))
    ts.dent(geo, (0.02, 0.015, 0.155), 0.03, (-0.007, -0.003, 0.0))
    ts.crumple(geo, 0.003, 30.0, seed=12, sel=geo.select(lambda co: co.z < 0.19))
    ts.bend(geo, (1, 0, 0), (0, 0, 0.07), -10, 0.07, 0.12)
    ts.lay_flat(geo, (10, 0), on_side=True)
    geo.recentre()
    return geo.objects(SPEC["name"])
