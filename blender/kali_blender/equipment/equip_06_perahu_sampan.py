"""Perahu Sampan (player boat tier 2): 3.7 m wooden kampung fishing sampan, pointed at both ends with sheer and
rocker, four painted plank strakes per side (labels.py "sampan_planks": tar, blue, white, red), open hull with
seven ribs, two thwarts, a gunwale rail, a forked oar rest on the right side and a paddle-oar resting on it.

Origin = WATERLINE (centred, on the water surface): the keel draws ~0.13 m.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 6,
    "name": "SM_Prop_PerahuSampan",
    "prefab": "PF_Prop_PerahuSampan",
    "label": "Wooden kampung sampan: painted plank strakes, ribs, thwarts, oar rest + oar",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (700, 1200),
    "max_size": 4.0,
    "label_art": {"name": "sampan_planks", "rows": 3},
    "palette": [
        ("#8a6440", 0.0, 0.3),   # 0 bare wood inside
        ("#5a3d24", 0.0, 0.3),   # 1 dark wood: ribs, thwarts, rail
        ("#a57a4c", 0.0, 0.35),  # 2 oar
    ],
}

HALF_L = 1.85
N = 18                                        # stations along the hull
FY = (0.0, 0.55, 0.85, 0.97, 1.0)             # section shape: keel -> gunwale (fraction of half beam)
FZ = (0.0, 0.08, 0.30, 0.65, 1.0)             # (fraction of keel-to-sheer height)


def _station(i):
    t = -1.0 + 2.0 * i / N
    b = 0.56 * max(0.0, 1 - abs(t) ** 2.2) ** 0.6
    zk = -0.13 + 0.10 * abs(t) ** 3           # rocker
    zs = 0.30 + 0.14 * t * t                  # sheer rises to the ends
    return t * HALF_L, b, zk, zs


def build():
    geo = ts.Geo()
    P = {}                                   # (i, side, j) -> vertex
    for i in range(N + 1):
        x, b, zk, zs = _station(i)
        for side in (-1, 1):
            for j in range(5):
                P[i, side, j] = geo.vert((x, side * b * FY[j], zk + (zs - zk) * FZ[j]))
    for i in range(N):
        s0, s1 = i / N, (i + 1) / N
        for side in (-1, 1):
            for j in range(4):
                q = [P[i, side, j], P[i + 1, side, j], P[i + 1, side, j + 1], P[i, side, j + 1]]
                uv = [(s0, j / 4), (s1, j / 4), (s1, (j + 1) / 4), (s0, (j + 1) / 4)]
                if side > 0:                                # +Y side: flip winding, mirror the print
                    q, uv = q[::-1], [(1 - s, t) for s, t in uv[::-1]]
                geo.face("label", q, [ts.panel_uv("pack", "front", s, t) for s, t in uv])
                geo.face(0, q[::-1])                       # inside of the planks
    # gunwale rail: flat cap + inner lip along both sheers
    for side in (-1, 1):
        for i in range(N):
            a, b_ = geo.v[P[i, side, 4]], geo.v[P[i + 1, side, 4]]
            ai = geo.vert((a.x, a.y * 0.9, a.z)); bi = geo.vert((b_.x, b_.y * 0.9, b_.z))
            al = geo.vert((a.x, a.y * 0.9, a.z - 0.04)); bl = geo.vert((b_.x, b_.y * 0.9, b_.z - 0.04))
            cap = [P[i, side, 4], P[i + 1, side, 4], bi, ai]
            lip = [ai, bi, bl, al]
            geo.face(1, cap if side < 0 else cap[::-1])
            geo.face(1, lip if side < 0 else lip[::-1])
    # ribs: strips along the inside at every other station
    for i in range(3, N - 2, 2):
        x, b, zk, zs = _station(i)
        pts = [(side, j) for side in (-1,) for j in range(4, -1, -1)] + [(1, j) for j in range(1, 5)]
        for (sa, ja), (sb, jb) in zip(pts[:-1], pts[1:]):
            va, vb = geo.v[P[i, sa, ja]], geo.v[P[i, sb, jb]]
            lift = 0.02
            quad = [geo.vert((x - 0.025, va.y * 0.97, va.z + lift)), geo.vert((x - 0.025, vb.y * 0.97, vb.z + lift)),
                    geo.vert((x + 0.025, vb.y * 0.97, vb.z + lift)), geo.vert((x + 0.025, va.y * 0.97, va.z + lift))]
            geo.face(1, quad[::-1])
    # thwarts
    for x in (-0.65, 0.6):
        i = round((x / HALF_L + 1) * N / 2)
        _, b, zk, zs = _station(i)
        ts.box(geo, 1, (x - 0.09, -b * 0.93, zs - 0.09), (x + 0.09, b * 0.93, zs - 0.06))
    # forked oar rest on the right (+Y) gunwale and the oar lying in it
    x0 = 0.3
    _, b, zk, zs = _station(round((x0 / HALF_L + 1) * N / 2))
    ts.box(geo, 1, (x0 - 0.02, b - 0.03, zs - 0.02), (x0 + 0.02, b + 0.01, zs + 0.10))
    ts.box(geo, 1, (x0 - 0.02, b - 0.03, zs + 0.10), (x0 + 0.02, b - 0.015, zs + 0.15))
    ts.box(geo, 1, (x0 - 0.02, b - 0.005, zs + 0.10), (x0 + 0.02, b + 0.01, zs + 0.15))
    geo.xform = Matrix.Translation((x0 - 1.2, b - 0.008, zs + 0.125)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    ts.lathe(geo, [(0.0, 0.018, 0.018), (1.75, 0.018, 0.018)], 6, lambda r: 2, cap0=2)
    ts.box(geo, 2, (-0.012, -0.07, 1.75), (0.012, 0.07, 2.25))   # blade
    geo.xform = None
    geo.recentre(keep_z=True)                                  # waterline stays at z = 0
    return geo.objects(SPEC["name"])
