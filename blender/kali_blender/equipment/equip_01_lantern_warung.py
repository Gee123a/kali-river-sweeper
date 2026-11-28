"""Warung roof lantern (0.56 m tall): wooden foot block, bamboo post with two nodes, wooden arm and diagonal
brace reaching forward (-Y, Unity +Z), short black cord, green enamel cone shade (white inside) over a
socket and an incandescent bulb. The bulb swatch is emissive (Emission map) so the shared material glows only
there; the point light in PF_Lantern_Warung sits on the bulb centre (BULB below).

Origin = post base (bottom of the foot block): the importer drops the prefab origin on the roof top.
"""
import bpy  # must be first
import math
from mathutils import Matrix, Vector
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 1,
    "name": "SM_Prop_LanternWarung",
    "prefab": "PF_Lantern_Warung",
    "label": "Warung roof lantern: bamboo post, arm, enamel shade, bulb",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#6b4a2b", 0.0, 0.3),          # 0 dark wood (foot, arm, brace)
        ("#c9a464", 0.0, 0.35),         # 1 bamboo
        ("#1b1b1b", 0.0, 0.4),          # 2 black cord / socket
        ("#2e6e52", 0.1, 0.65),         # 3 green enamel shade
        ("#f2f0e8", 0.0, 0.6),          # 4 white enamel inside
        ("#ffd27a", 0.0, 0.8, True),    # 5 bulb (emissive)
    ],
}

ARM_Y = -0.28                      # lamp hangs this far in front of the post (Blender -Y = Unity +Z)
BULB = (0.0, ARM_Y, 0.315)         # bulb centre, Blender coords -> Unity (0, 0.315, 0.28)


def build():
    geo = ts.Geo()
    ts.box(geo, 0, (-0.05, -0.05, 0.0), (0.05, 0.05, 0.03))                            # foot block
    ts.lathe(geo, [(0.03, 0.022, 0.022), (0.18, 0.022, 0.022), (0.19, 0.026, 0.026), (0.20, 0.022, 0.022),
                   (0.36, 0.022, 0.022), (0.37, 0.026, 0.026), (0.38, 0.022, 0.022), (0.56, 0.021, 0.021)],
             6, lambda r: 1, cap1=1)                                                    # bamboo post, 2 nodes
    ts.box(geo, 0, (-0.015, ARM_Y - 0.02, 0.50), (0.015, 0.02, 0.53))                  # arm
    a, b = Vector((0, -0.01, 0.40)), Vector((0, -0.15, 0.505))                          # brace post -> arm
    d = b - a
    geo.xform = Matrix.Translation(a) @ Matrix.Rotation(math.atan2(-d.y, d.z), 4, "X")
    ts.box(geo, 0, (-0.01, -0.01, 0.0), (0.01, 0.01, d.length))
    geo.xform = Matrix.Translation((0, ARM_Y, 0))
    ts.lathe(geo, [(0.38, 0.004, 0.004), (0.50, 0.004, 0.004)], 4, lambda r: 2)        # cord
    ts.lathe(geo, [(0.33, 0.085, 0.085), (0.36, 0.045, 0.045), (0.40, 0.016, 0.016)], 10, lambda r: 3, cap1=3)
    ts.lathe(geo, [(0.398, 0.014, 0.014), (0.358, 0.043, 0.043), (0.33, 0.085, 0.085)], 10, lambda r: 4)  # inside
    ts.lathe(geo, [(0.352, 0.013, 0.013), (0.378, 0.013, 0.013)], 6, lambda r: 2, cap0=2)               # socket
    ts.lathe(geo, [(0.292, 0.009, 0.009), (0.300, 0.019, 0.019), (0.315, 0.024, 0.024), (0.330, 0.020, 0.020),
                   (0.352, 0.011, 0.011)], 8, lambda r: 5, cap0=5)                       # bulb
    geo.xform = None
    return geo.objects(SPEC["name"])
