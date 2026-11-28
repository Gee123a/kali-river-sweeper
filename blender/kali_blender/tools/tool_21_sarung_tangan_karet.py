"""Sarung tangan karet (Tier-0 Capit starter, plan_jc 7B): a pair of yellow household rubber gloves, fingers up,
held side by side - reads as "hands/grabbing" at a glance in the Capit slot.

Grip at the origin between the two cuffs (inside the hand); gloves run along +Z (head_dir +Z).
Borrows the free swatch rows 2-3 of tool cell 1 (Sendok uses 2 swatches): SPEC swatch_base 8.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 1,
    "swatch_base": 8,
    "name": "SM_Tool_SarungTanganKaret",
    "label": "Sarung tangan karet (rubber gloves, Capit starter)",
    "head_dir": "+Z",
    "palette": [
        ("#f5c518", 0.0, 0.7),   # 0 yellow rubber
        ("#e8a90f", 0.0, 0.6),   # 1 darker cuff roll
        ("#c2410c", 0.0, 0.5),   # 2 orange grip dots
    ],
}

FINGERS = [(-0.03, 0.105, 0.075), (-0.01, 0.115, 0.085), (0.01, 0.11, 0.08), (0.03, 0.095, 0.065)]  # x, z0, length


def _glove(geo, side):
    base = Matrix.Translation((side * 0.055, 0.0, 0.0)) @ Matrix.Rotation(math.radians(side * 6), 4, "Y")
    geo.xform = base
    ts.lathe(geo, [(-0.07, 0.04, 0.028), (-0.06, 0.042, 0.03), (-0.05, 0.036, 0.024)], 8, lambda r: 1, cap0=1)  # cuff roll
    ts.lathe(geo, [(-0.05, 0.036, 0.024), (0.02, 0.04, 0.02), (0.07, 0.045, 0.02), (0.10, 0.042, 0.018)], 8,
             lambda r: 0)                                                                                 # palm
    geo.xform = base @ Matrix.Translation((0, 0, 0.10))
    ts.lathe(geo, [(0.0, 0.042, 0.018), (0.008, 0.02, 0.012)], 8, lambda r: 0, cap1=0)                     # knuckle cap
    for x, z0, ln in FINGERS:
        geo.xform = base @ Matrix.Translation((x * 1.1, 0, z0 - 0.01))
        ts.lathe(geo, [(0.0, 0.009, 0.009), (ln * 0.6, 0.0085, 0.0085), (ln, 0.006, 0.006)], 5, lambda r: 0, cap1=0)
    geo.xform = base @ Matrix.Translation((side * -0.045, 0, 0.03)) @ Matrix.Rotation(math.radians(side * -40), 4, "Y")
    ts.lathe(geo, [(0.0, 0.01, 0.01), (0.045, 0.009, 0.009), (0.065, 0.006, 0.006)], 5, lambda r: 0, cap1=0)  # thumb
    for z in (0.03, 0.06):                                                                                  # grip dots
        geo.xform = base @ Matrix.Translation((0, -0.019, z)) @ Matrix.Rotation(math.radians(90), 4, "X")
        ts.lathe(geo, [(0.0, 0.008, 0.008), (0.002, 0.008, 0.008)], 5, lambda r: 2, cap0=2)
    geo.xform = None


def build():
    geo = ts.Geo()
    _glove(geo, -1)
    _glove(geo, 1)
    return geo.objects(SPEC["name"])
