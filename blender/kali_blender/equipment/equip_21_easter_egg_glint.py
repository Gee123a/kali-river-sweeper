"""Easter-egg glint (R4-J1): a 4-point sparkle star (0.32 m) built from three crossed double-sided planes at 60 deg, so
it reads from any angle without a billboard script; emissive pale gold (white in the Emission map). Placed above the
half-buried tool in PF_EasterEgg_<Tool>; spin or pulse it in Unity if wanted.

Origin = centre of the bbox bottom. Shares equipment atlas cell 20 with the mound, on swatch rows 2-3 (swatch_base 8).
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 20,
    "swatch_base": 8,
    "name": "SM_Prop_EasterEggGlint",
    "prefab": "PF_Prop_EasterEggGlint",
    "label": "Emissive sparkle glint for easter eggs",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (12, 100),
    "palette": [
        ("#fff3b0", 0.0, 0.9, True),   # 0 glowing pale gold
    ],
}

R, W = 0.16, 0.035              # star arm length and waist


def build():
    geo = ts.Geo()
    star = [(0, R), (W, W), (R, 0), (W, -W), (0, -R), (-W, -W), (-R, 0), (-W, W)]
    for k in range(3):
        geo.xform = Matrix.Translation((0, 0, R)) @ Matrix.Rotation(math.radians(60 * k), 4, "Z")
        idx = [geo.vert((x, 0.0, z)) for x, z in star]
        c = geo.vert((0.0, 0.0, 0.0))
        for i in range(len(idx)):
            tri = [c, idx[i], idx[(i + 1) % len(idx)]]
            geo.face(0, tri)
            geo.face(0, tri[::-1])
    geo.xform = None
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
