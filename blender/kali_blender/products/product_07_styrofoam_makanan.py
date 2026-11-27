"""Styrofoam rice box (clamshell, 19 x 17 x 8 cm), NEW: the trash box's chamfered tray and lid, closed on
the rim (lid flipped down, no break, no dent), latch tab at the front. Clean unused foam (labels.py
"styrofoam_new", dirty=False).

Origin = centre of the bbox bottom (products_common): Geo.recentre(base=True).
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts
from kali_blender.trash import trash_09_styrofoam_makanan as box   # same tray builder

SPEC = {
    "index": 7,
    "name": "SM_Product_StyrofoamMakanan",
    "prefab": "PF_Product_StyrofoamMakanan",
    "label": "Styrofoam food box (new, closed)",
    "head_dir": "-Z",  # not used by products; tools_common.assemble requires the key, build_product pops it
    "label_art": {"name": "styrofoam_new", "rows": 3, "dirty": False},
    "palette": [("#ece9e0", 0.0, 0.25)],   # 0 foam (latch tab)
}

LID_H = 0.034


def build():
    geo = ts.Geo()
    box._tray(geo, box.RIM)
    y0, rim = -box.FD / 2, box.RIM                   # latch tab on the front flange
    ts.grid(geo, 0, (-0.015, y0 - 0.014, rim - 0.002), (0.03, 0, 0), (0, 0.014, 0), 1, 1)
    ts.grid(geo, 0, (-0.015, y0 - 0.014, rim - 0.006), (0, 0.014, 0), (0.03, 0, 0), 1, 1)
    ts.grid(geo, 0, (-0.015, y0 - 0.014, rim - 0.006), (0.03, 0, 0), (0, 0, 0.004), 1, 1)
    ts.grid(geo, 0, (-0.015, y0, rim - 0.006), (0, -0.014, 0), (0, 0, 0.004), 1, 1)
    ts.grid(geo, 0, (0.015, y0 - 0.014, rim - 0.006), (0, 0.014, 0), (0, 0, 0.004), 1, 1)
    geo.xform = Matrix.Translation((0, 0, rim + LID_H)) @ Matrix.Rotation(math.pi, 4, "X")   # lid shut on the rim
    box._tray(geo, LID_H)
    geo.xform = None
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
