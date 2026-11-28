"""Kotak jarum (quest 6B, Tangga Cuci): yellow sharps box with a red lid and slot, a red trefoil badge, and a
small cluster of used syringes lying round it on the steps.

Origin = centre of the bbox bottom (base pivot): it sits on the washing steps.
"""
import bpy  # must be first
import math
from mathutils import Matrix, Vector
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 10,
    "name": "SM_Prop_KotakJarum",
    "prefab": "PF_Prop_KotakJarum",
    "label": "Needle box (sharps container) with loose syringes",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (150, 400),
    "palette": [
        ("#eab308", 0.0, 0.45),  # 0 yellow box
        ("#dc2626", 0.0, 0.45),  # 1 red lid / badge / plungers
        ("#1f2937", 0.0, 0.3),   # 2 dark slot
        ("#f1f5f9", 0.0, 0.6),   # 3 white barrels
        ("#cbd5e1", 0.9, 0.7),   # 4 steel needles
    ],
}


def _syringe(geo, a, b):
    a, b = Vector(a), Vector(b)
    d = b - a
    geo.xform = Matrix.Translation(a) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    ts.lathe(geo, [(0.0, 0.009, 0.009), (d.length, 0.009, 0.009)], 6, lambda r: 3, cap0=3, cap1=3)
    ts.lathe(geo, [(d.length, 0.003, 0.003), (d.length + 0.04, 0.001, 0.001)], 4, lambda r: 4)
    ts.lathe(geo, [(-0.03, 0.007, 0.007), (0.0, 0.007, 0.007)], 4, lambda r: 1, cap0=1)
    geo.xform = None


def build():
    geo = ts.Geo()
    ts.box(geo, 0, (-0.11, -0.07, 0.0), (0.11, 0.07, 0.14), n=(2, 1, 1))
    ts.box(geo, 1, (-0.115, -0.075, 0.14), (0.115, 0.075, 0.175))
    ts.box(geo, 2, (-0.06, -0.012, 0.175), (0.06, 0.012, 0.18))
    for k in range(3):                                                    # trefoil badge lobes on the front
        a = math.radians(90 + k * 120)
        geo.xform = Matrix.Translation((0.025 * math.cos(a), -0.071, 0.07 + 0.025 * math.sin(a))) \
            @ Matrix.Rotation(math.radians(90), 4, "X")
        ts.lathe(geo, [(0.0, 0.014, 0.014), (0.004, 0.014, 0.014)], 6, lambda r: 1, cap0=1)
    geo.xform = None
    _syringe(geo, (0.16, -0.05, 0.01), (0.25, 0.02, 0.01))
    _syringe(geo, (-0.14, 0.06, 0.01), (-0.22, -0.03, 0.012))
    _syringe(geo, (0.03, 0.0, 0.18), (0.06, 0.03, 0.27))                   # one stuck in the slot
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
