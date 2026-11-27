"""Styrofoam rice box (clamshell, 19 x 17 cm, 6 cm deep): chunky chamfered tray with a flat rim flange
and latch tab, lid hinged open on the back edge with a front corner broken off, front wall dented.
Inside faces carry leftover-food stains, outside faces grubby foam with a crack (labels.py "styrofoam").

Built around the origin; Geo.recentre puts the bbox centre at (0,0,0) as trash_common expects.
"""
import bpy  # must be first
import math
from mathutils import Matrix, Vector
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 9,
    "name": "SM_Trash_StyrofoamMakanan",
    "prefab": "PF_Trash_StyrofoamMakanan",
    "label": "Styrofoam food box (lid open, broken corner, dirty)",
    "head_dir": "-Z",  # not used by trash props; tools_common.assemble requires the key, build_trash pops it
    "label_art": {"name": "styrofoam", "rows": 3},
    "palette": [
        ("#e4e0d4", 0.0, 0.25),  # 0 foam (latch tab)
    ],
}

FW, FD, RIM = 0.19, 0.17, 0.062     # flange outline and rim height


def _octa(w, d, c, z, broken=0.0):
    """Chamfered rectangle (8 points, CCW from the front-left), z height. broken: front-right corner bitten in."""
    x, y = w / 2, d / 2
    pts = [(-x + c, -y, z), (x - c, -y, z), (x, -y + c, z), (x, y - c, z),
           (x - c, y, z), (-x + c, y, z), (-x, y - c, z), (-x, -y + c, z)]
    if broken:
        pts[1] = (x - c - broken * 1.3, -y + broken * 0.35, z - broken * 0.25)
        pts[2] = (x - broken * 0.4, -y + c + broken * 1.1, z - broken * 0.15)
    return pts


def _tray(geo, depth, broken=0.0):
    """Outer bottom -> walls -> flange (under, rim, top) -> inner walls -> inner floor. Returns ring list."""
    h = depth
    rings = [_octa(0.150, 0.130, 0.013, 0.0),
             _octa(0.176, 0.156, 0.016, h - 0.007),
             _octa(FW, FD, 0.019, h - 0.007, broken),
             _octa(FW, FD, 0.019, h, broken),
             _octa(0.164, 0.144, 0.015, h, broken * 0.4),
             _octa(0.140, 0.120, 0.012, 0.006)]
    inside = {3, 4}                       # bands facing into the box: flange top, inner walls
    idx = [[geo.vert(p) for p in r] for r in rings]
    for r in range(len(rings) - 1):
        for k in range(8):
            k1 = (k + 1) % 8
            pts = [rings[r][k], rings[r][k1], rings[r + 1][k1], rings[r + 1][k]]
            geo.face("label", [idx[r][k], idx[r][k1], idx[r + 1][k1], idx[r + 1][k]],
                     _uv(pts, "front" if r in inside else "back"))
    geo.face("label", list(reversed(idx[0])), _uv(list(reversed(rings[0])), "back"))
    geo.face("label", idx[-1], _uv(rings[-1], "front"))
    return idx


def _uv(pts, panel):
    """Planar projection on the face's dominant axis (foam texture, no seams to hide)."""
    p = [Vector(q) for q in pts]
    n = (p[1] - p[0]).cross(p[2] - p[0])
    ax = max(range(3), key=lambda a: abs(n[a]))
    a, b = [i for i in range(3) if i != ax]
    return [ts.panel_uv("pair", panel, q[a] / 0.2 + 0.5, q[b] / 0.2 + 0.5) for q in p]


def build():
    geo = ts.Geo()
    _tray(geo, RIM)
    # latch tab on the front flange
    y0 = -FD / 2
    ts.grid(geo, 0, (-0.015, y0 - 0.014, RIM - 0.002), (0.03, 0, 0), (0, 0.014, 0), 1, 1)
    ts.grid(geo, 0, (-0.015, y0 - 0.014, RIM - 0.006), (0, 0.014, 0), (0.03, 0, 0), 1, 1)
    ts.grid(geo, 0, (-0.015, y0 - 0.014, RIM - 0.006), (0.03, 0, 0), (0, 0, 0.004), 1, 1)
    ts.grid(geo, 0, (-0.015, y0, RIM - 0.006), (0, -0.014, 0), (0, 0, 0.004), 1, 1)
    ts.grid(geo, 0, (0.015, y0 - 0.014, RIM - 0.006), (0, 0.014, 0), (0, 0, 0.004), 1, 1)
    # lid: same tray, shallower, flipped onto the rim then swung open about the back flange edge
    lid_h = 0.034
    flip = Matrix.Translation((0, 0, RIM + lid_h)) @ Matrix.Rotation(math.pi, 4, "X")
    hinge = Matrix.Translation((0, FD / 2, RIM))
    geo.xform = hinge @ Matrix.Rotation(math.radians(-118), 4, "X") @ hinge.inverted() @ flip
    _tray(geo, lid_h, broken=0.028)
    geo.xform = None
    ts.dent(geo, (0.03, -0.075, 0.03), 0.05, (0, 0.008, -0.003))      # pressed-in front wall
    ts.crumple(geo, 0.0015, 20.0, seed=9)
    geo.recentre()
    return geo.objects(SPEC["name"])
