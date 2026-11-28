"""Garuk bambu (Tier-0 Garuk starter, plan_jc 7B): 1.7 m bamboo leaf rake - bamboo shaft with two nodes, rattan
binding, a fan of 11 flat bamboo tines bent at the tips, held by two cross bars. The fan silhouette reads "rake".

Grip at the origin on the shaft (lower third); the fan points +Z (head_dir +Z).
Borrows the free swatch rows 2-3 of tool cell 3 (Centong uses 2 swatches): SPEC swatch_base 8.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 3,
    "swatch_base": 8,
    "name": "SM_Tool_GarukBambu",
    "label": "Garuk bambu (bamboo rake, Garuk starter)",
    "head_dir": "+Z",
    "palette": [
        ("#c9a464", 0.0, 0.35),  # 0 bamboo shaft
        ("#d9bd7a", 0.0, 0.35),  # 1 light split-bamboo tines
        ("#7a5230", 0.0, 0.3),   # 2 rattan binding / cross bars
    ],
}

TINES = 11
FAN_Z = 1.30                 # where the tines leave the binding
TINE_L = 0.42
SPREAD = math.radians(70)    # full fan angle


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(-0.35, 0.016, 0.016), (0.25, 0.016, 0.016), (0.26, 0.019, 0.019), (0.27, 0.016, 0.016),
                   (0.80, 0.015, 0.015), (0.81, 0.018, 0.018), (0.82, 0.015, 0.015), (FAN_Z, 0.014, 0.014)], 6,
             lambda r: 0, cap0=0, cap1=0)
    geo.xform = Matrix.Translation((0, 0, FAN_Z - 0.06))
    ts.lathe(geo, [(0.0, 0.02, 0.02), (0.08, 0.02, 0.02)], 6, lambda r: 2, cap0=2, cap1=2)               # binding
    for i in range(TINES):
        a = -SPREAD / 2 + SPREAD * i / (TINES - 1)
        rot = Matrix.Translation((0, 0, FAN_Z)) @ Matrix.Rotation(a, 4, "Y")
        geo.xform = rot
        ts.box(geo, 1, (-0.007, -0.002, 0.0), (0.007, 0.002, TINE_L * 0.85))
        geo.xform = rot @ Matrix.Translation((0, 0, TINE_L * 0.85)) @ Matrix.Rotation(math.radians(35), 4, "X")
        ts.box(geo, 1, (-0.007, -0.002, 0.0), (0.007, 0.002, TINE_L * 0.18))                           # bent tip
    for z, half in ((FAN_Z + 0.16, 0.10), (FAN_Z + 0.30, 0.18)):                                       # cross bars
        geo.xform = None
        ts.box(geo, 2, (-half - 0.02, -0.006, z), (half + 0.02, 0.006, z + 0.012))
    geo.xform = None
    return geo.objects(SPEC["name"])
