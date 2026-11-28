"""Es teh plastik (quest 6B, warung): Indonesian iced sweet tea bagged in a clear plastic bag, knotted with a rubber
band, a red/white striped straw sticking out of the knot; ice-cube bumps under the amber tea.

Origin = centre of the bbox bottom (base pivot): it sits on the warung counter.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 11,
    "name": "SM_Prop_GelasEsTeh",
    "prefab": "PF_Prop_GelasEsTeh",
    "label": "Iced tea in a knotted plastic bag with a straw",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (120, 400),
    "palette": [
        ("#b5651d", 0.0, 0.9),   # 0 amber iced tea (glossy bag)
        ("#e8e4da", 0.0, 0.85),  # 1 clear bag above the tea
        ("#e11d2a", 0.0, 0.6),   # 2 red straw stripe / rubber band
        ("#f5f5f0", 0.0, 0.6),   # 3 white straw stripe
        ("#d8eef0", 0.0, 0.95),  # 4 ice
    ],
}


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(0.0, 0.035, 0.035), (0.02, 0.065, 0.06), (0.07, 0.07, 0.065), (0.11, 0.055, 0.05),
                   (0.14, 0.03, 0.028), (0.16, 0.014, 0.014), (0.175, 0.014, 0.014), (0.20, 0.03, 0.02)], 10,
             lambda r: 0 if r < 3 else (2 if r == 5 else 1), cap0=0, cap1=1)
    for x, y, z in ((0.03, -0.045, 0.06), (-0.035, -0.04, 0.08), (0.0, 0.05, 0.05)):        # ice cube bumps
        ts.box(geo, 4, (x - 0.014, y - 0.014, z - 0.014), (x + 0.014, y + 0.014, z + 0.014))
    for k in range(5):                                                                      # striped straw
        geo.xform = Matrix.Translation((0.0, 0.0, 0.12)) @ Matrix.Rotation(math.radians(14), 4, "X")
        ts.lathe(geo, [(0.03 * k, 0.004, 0.004), (0.03 * (k + 1), 0.004, 0.004)], 5, lambda r, s=2 + k % 2: s,
                 cap1=2 + k % 2 if k == 4 else None)
    geo.xform = None
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
