"""Lifeman shampoo bottle (parody brand, 170 ml, 6.2 x 3.8 x 19 cm): flat-oval white HDPE body squeezed in with a
thumb dent, dark-blue flip-top cap with the lid snapped open (nozzle showing). The body print is the
procedural Lifeman label (red cross + red shield wordmark, blue band) on front and back; it lies on its
back, print up, the way it floats.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 6,
    "name": "SM_Trash_BotolLifeman",
    "prefab": "PF_Trash_BotolLifeman",
    "label": "Lifeman shampoo bottle (dented, cap open)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "lifeman", "rows": 3},
    "palette": [
        ("#dfe4ea", 0.0, 0.5),   # 0 white HDPE (shoulder, base)
        ("#1c3a8c", 0.0, 0.55),  # 1 dark-blue flip cap
        ("#f2f2ee", 0.0, 0.4),   # 2 nozzle
    ],
}

SEGS = 12
LABEL_Z = (0.005, 0.150)
RINGS = [
    (0.000, 0.0260, 0.0140),   # base, set in
    (0.005, 0.0305, 0.0185),
    (0.045, 0.0312, 0.0190),
    (0.085, 0.0312, 0.0190),
    (0.125, 0.0305, 0.0186),
    (0.150, 0.0295, 0.0180),
    (0.163, 0.0265, 0.0160),   # shoulder
    (0.170, 0.0245, 0.0148),
    (0.171, 0.0250, 0.0154),   # cap skirt
    (0.190, 0.0240, 0.0148),   # cap deck
]
LID_H = 0.008


def _key(r):
    if 1 <= r <= 4:
        return "label"
    return 1 if r >= 7 else 0


def build():
    geo = ts.Geo()
    ts.lathe(geo, RINGS, SEGS, _key, uv=ts.pair_uv(*LABEL_Z), cap0=0, cap1=1)
    zt, rx, ry = RINGS[-1]
    ts.lathe(geo, [(zt, 0.0045, 0.0045), (zt + 0.006, 0.0035, 0.0035)], 6, lambda r: 2, cap1=2)   # nozzle
    # flip lid: oval cap shell hinged on the back edge of the deck, snapped open past vertical
    hinge = Matrix.Translation((0, ry, zt))
    geo.xform = hinge @ Matrix.Rotation(math.radians(-112), 4, "X") @ hinge.inverted()
    ts.lathe(geo, [(zt, rx, ry), (zt + LID_H, rx * 0.97, ry * 0.97)], SEGS, lambda r: 1, cap0=1, cap1=1)
    geo.xform = None
    # squeezed: thumb dent in the front, pressed-in back, slight banana bend
    ts.dent(geo, (0.004, -0.019, 0.075), 0.045, (0, 0.010, 0))
    ts.dent(geo, (-0.012, 0.019, 0.115), 0.035, (0.002, -0.006, 0))
    ts.bend(geo, (1, 0, 0), (0, 0, 0.09), 6, 0.09, 0.17)
    ts.lay_flat(geo, (6, 3), on_side=False)
    geo.recentre()
    return geo.objects(SPEC["name"])
