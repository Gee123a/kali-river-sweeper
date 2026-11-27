"""Gudang Gula International cigarette pack (parody brand, 5.5 x 2.2 x 8.8 cm flip-top): card box crushed in the
middle, bent and twisted, bottom corner caved in, lid ajar over the white inner collar and crumpled
foil. Red print with gold border, gold emblem and GUDANG GULA lettering on the front and back,
lettering up the sides (labels.py "gudang_gula", box layout). Lies on its back, print up.

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 11,
    "name": "SM_Trash_KotakRokok",
    "prefab": "PF_Trash_KotakRokok",
    "label": "Gudang Gula cigarette pack (crushed)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "gudang_gula", "rows": 3},
    "palette": [
        ("#c3c3bd", 0.7, 0.55),  # 0 crumpled foil
        ("#e9e2d2", 0.0, 0.3),   # 1 white card (collar, inside of the lid)
        ("#8e1420", 0.0, 0.35),  # 2 red card (bottom, lid top)
    ],
}

W, D, H = 0.055, 0.022, 0.088
HB = 0.066                       # lid line


def _uv(panel, t0, t1, mirror=False):
    return lambda s, t: ts.panel_uv("box", panel, 1 - s if mirror else s, t0 + (t1 - t0) * t)


def _shell(geo, z0, z1, nz, top_key, inner_key=None):
    """Four printed walls from z0 to z1 (+ top), front/back on the front panel, sides on the side panels."""
    t0, t1 = z0 / H, z1 / H
    h = z1 - z0
    walls = [((-W / 2, -D / 2, z0), (W, 0, 0), 4, _uv("front", t0, t1)),            # front (-Y)
             ((W / 2, D / 2, z0), (-W, 0, 0), 4, _uv("front", t0, t1)),             # back, reads from behind
             ((-W / 2, D / 2, z0), (0, -D, 0), 2, _uv("side_l", t0, t1)),           # left (-X)
             ((W / 2, -D / 2, z0), (0, D, 0), 2, _uv("side_r", t0, t1))]            # right (+X)
    for origin, du, nu, uv in walls:
        ts.grid(geo, "label", origin, du, (0, 0, h), nu, nz, uv)
        if inner_key is not None:          # inside of the lid: same quads, reversed
            ts.grid(geo, inner_key, (origin[0] + du[0], origin[1] + du[1], origin[2]), (-du[0], -du[1], 0), (0, 0, h), nu, nz)
    ts.grid(geo, top_key, (-W / 2, -D / 2, z1), (W, 0, 0), (0, D, 0), 4, 2)
    if inner_key is not None:
        ts.grid(geo, inner_key, (-W / 2, D / 2, z1), (W, 0, 0), (0, -D, 0), 4, 2)


def build():
    geo = ts.Geo()
    _shell(geo, 0.0, HB, 4, 0)                                                     # body, foil on top
    ts.grid(geo, 2, (-W / 2, D / 2, 0), (W, 0, 0), (0, -D, 0), 4, 2)               # bottom
    # white inner collar standing out of the body (both faces)
    e, ch = 0.0012, 0.011
    for o, du in (((-W / 2 + e, -D / 2 + e, HB), (W - 2 * e, 0, 0)),        # front
                  ((-W / 2 + e, -D / 2 + e, HB), (0, D * 0.6, 0)),          # left
                  ((W / 2 - e, -D / 2 + e, HB), (0, D * 0.6, 0))):          # right
        ts.grid(geo, 1, o, du, (0, 0, ch), 1, 1)
        ts.grid(geo, 1, (o[0] + du[0], o[1] + du[1], o[2]), (-du[0], -du[1], 0), (0, 0, ch), 1, 1)
    # lid ajar, hinged on the back top edge of the body
    hinge = Matrix.Translation((0, D / 2, HB))
    geo.xform = hinge @ Matrix.Rotation(math.radians(-34), 4, "X") @ hinge.inverted()
    _shell(geo, HB, H, 1, 2, inner_key=1)
    geo.xform = None
    # crushed: waist pinched, corner caved in, upper half bent back and twisted
    ts.dent(geo, (0.008, -0.011, 0.036), 0.03, (0, 0.006, 0.0))
    ts.dent(geo, (-0.01, 0.011, 0.042), 0.028, (0, -0.004, 0.0))
    ts.dent(geo, (0.0275, -0.011, 0.0), 0.022, (-0.006, 0.004, 0.006))
    ts.bend(geo, (1, 0, 0), (0, 0, 0.03), 12, 0.03, 0.066)
    ts.bend(geo, (0, 0, 1), (0, 0, 0), 9, 0.0, 0.066)
    ts.crumple(geo, 0.0012, 60.0, seed=11)
    ts.lay_flat(geo, (5, -4))
    geo.recentre()
    return geo.objects(SPEC["name"])
