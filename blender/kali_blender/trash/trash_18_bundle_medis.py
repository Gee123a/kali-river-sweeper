"""Medical waste bundle (~0.45 m): a knotted yellow B3 bag with a red band, five used syringes poking out of it and
two loose ones caught against it. Name contains "Medis", so RiverTrashItem infers WasteClass.Medical.

Origin = WATERLINE: the bag floats with half of it under water.
"""
import bpy  # must be first
import math
from mathutils import Matrix, Vector
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 18,
    "name": "SM_Trash_BundleMedis",
    "prefab": "PF_Trash_BundleMedis",
    "label": "Medical waste bundle: yellow B3 bag full of syringes",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "pivot": "waterline",
    "tris": (200, 600),
    "palette": [
        ("#eab308", 0.0, 0.5),   # 0 hazard yellow bag
        ("#dc2626", 0.0, 0.45),  # 1 red B3 band / plungers
        ("#f1f5f9", 0.0, 0.6),   # 2 white syringe barrels
        ("#cbd5e1", 0.9, 0.7),   # 3 steel needles
    ],
}


def _syringe(geo, a, b):
    """Barrel a -> b with plunger and needle, built along the segment."""
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    geo.xform = Matrix.Translation(a) @ rot
    L = d.length
    ts.lathe(geo, [(0.0, 0.011, 0.011), (L, 0.011, 0.011)], 6, lambda r: 2, cap0=2)
    ts.lathe(geo, [(L, 0.004, 0.004), (L + 0.05, 0.0015, 0.0015)], 4, lambda r: 3)
    ts.lathe(geo, [(-0.04, 0.009, 0.009), (0.0, 0.009, 0.009)], 4, lambda r: 1, cap0=1)
    geo.xform = None


def build():
    geo = ts.Geo()
    geo.xform = Matrix.Scale(1.0, 4)
    ts.lathe(geo, [(-0.12, 0.08, 0.07), (-0.08, 0.16, 0.13), (0.0, 0.18, 0.15), (0.06, 0.15, 0.12),
                   (0.10, 0.07, 0.06), (0.13, 0.03, 0.03), (0.18, 0.05, 0.04)], 8, lambda r: 1 if r == 2 else 0,
             cap0=0, cap1=0)
    for i in range(5):                                       # syringes poking out of the knot and the sides
        a = math.radians(i * 72 + 20)
        start = (0.08 * math.cos(a), 0.07 * math.sin(a), 0.06 + 0.02 * (i % 2))
        end = (0.20 * math.cos(a), 0.18 * math.sin(a), 0.16 + 0.03 * (i % 3))
        _syringe(geo, start, end)
    _syringe(geo, (0.17, -0.12, -0.01), (0.30, -0.06, 0.0))  # loose ones caught against the bag
    _syringe(geo, (-0.18, 0.10, 0.0), (-0.28, 0.20, 0.01))
    ts.crumple(geo, 0.012, 9.0, seed=18)
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
