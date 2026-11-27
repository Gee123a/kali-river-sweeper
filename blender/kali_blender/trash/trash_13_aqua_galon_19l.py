"""19 L water-dispenser jug (27 cm x 48 cm), ported from the old local prop: blue polycarbonate body with two
rib rings, round shoulder, white screw cap and a parody "AQUO" sticker band (labels.py, worn). Empty, so it
floats high on its side; scuffed with two dents and a slightly squashed body.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 13,
    "name": "SM_Trash_AquaGalon_19L",
    "prefab": "PF_Trash_AquaGalon_19L",
    "label": "19 L polycarbonate water jug, parody AQUO sticker (dented)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "aquo_galon", "rows": 3},
    "palette": [
        ("#3f86d2", 0.0, 0.85),  # 0 blue polycarbonate (opaque stand-in for the translucent jug)
        ("#e6e6df", 0.0, 0.45),  # 1 white screw cap
    ],
}

SEGS = 12
LABEL_Z = (0.130, 0.230)
RINGS = [
    (0.000, 0.122, 0.122),    # base
    (0.012, 0.135, 0.135),
    (0.110, 0.135, 0.135),
    (0.120, 0.143, 0.143),    # rib
    (0.130, 0.135, 0.135),    # sticker band
    (0.230, 0.135, 0.135),
    (0.240, 0.143, 0.143),    # rib
    (0.250, 0.135, 0.135),
    (0.355, 0.135, 0.135),
    (0.390, 0.105, 0.105),    # shoulder
    (0.425, 0.042, 0.042),
    (0.432, 0.036, 0.036),    # neck
    (0.436, 0.041, 0.041),    # cap
    (0.480, 0.041, 0.041),
]


def _key(r):
    if r == 4:
        return "label"
    return 1 if r >= 12 else 0


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, SEGS, _key, uv=ts.wrap_uv(*LABEL_Z), cap0=0, cap1=1)
    geo.deform(lambda co: (co.x * 1.04, co.y * 0.93, co.z))                       # body sagged a little
    ts.dent(geo, (0.05, -0.12, 0.31), 0.09, (-0.01, 0.025, 0.0))
    ts.dent(geo, (-0.09, 0.09, 0.07), 0.07, (0.012, -0.012, 0.0))
    ts.crumple(geo, 0.0025, 9.0, seed=13, sel=geo.select(lambda co: co.z < 0.42))
    ts.lay_flat(geo, (14, 0), on_side=True)
    geo.recentre()
    return geo.objects(SPEC["name"])
