"""Shared helpers for sign boards and atlas-mapped faces on Wesley's MeshKit buildings.

Atlas rects are (u0, v0, u1, v1) in 0..1 UV space; px() converts a PIL pixel box from
papan.py (top-left origin, 1024 px atlas) into that form. MeshKit.box() emits its faces
as: side 0 = -Z, side 1 = +X, side 2 = +Z, side 3 = -X, then top, bottom. On each side
face the first vertex is the viewer's bottom-left, so one UV pattern fits all four.
"""
import math

FACE = {"-z": 0, "+x": 1, "+z": 2, "-x": 3, "top": 4}
PALETTE_GRID = 4


def px(x0, y0, x1, y1, atlas=1024.0):
    return (x0 / atlas, 1 - y1 / atlas, x1 / atlas, 1 - y0 / atlas)


def rect_uv(rect):
    u0, v0, u1, v1 = rect
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def flat(k, start, rect):
    """Every face added since `start` samples the centre of `rect` (solid colour)."""
    u0, v0, u1, v1 = rect
    for f in range(start, len(k.faces)):
        k.uvs[f] = [((u0 + u1) * 0.5, (v0 + v1) * 0.5)] * len(k.faces[f])


def board(k, x0, x1, y0, y1, z0, z1, mat, face, rect, edge):
    """Box whose `face` shows `rect`; all other faces show the solid `edge` colour."""
    s = len(k.faces)
    k.box(x0, x1, y0, y1, z0, z1, mat)
    flat(k, s, edge)
    k.uvs[s + FACE[face]] = rect_uv(rect)


def stretch(k, start, rect):
    """Map each face added since `start` onto the whole `rect` (stripes, decals)."""
    for f in range(start, len(k.faces)):
        n = len(k.faces[f])
        k.uvs[f] = rect_uv(rect) if n == 4 else [((rect[0] + rect[2]) * 0.5, (rect[1] + rect[3]) * 0.5)] * n


def paint(k, start, swatch):
    """Point every face added since `start` at one T_Env_TrashPalette swatch."""
    cu, cv = (swatch % PALETTE_GRID + 0.5) / PALETTE_GRID, (swatch // PALETTE_GRID + 0.5) / PALETTE_GRID
    for f in range(start, len(k.faces)):
        n = len(k.faces[f])
        k.uvs[f] = [(cu + 0.02 * math.cos(2 * math.pi * j / n), cv + 0.02 * math.sin(2 * math.pi * j / n)) for j in range(n)]


def swap_uv(k, start):
    """Swap U/V on faces since `start` (makes corrugation run down a slope that falls along Z)."""
    for f in range(start, len(k.faces)):
        k.uvs[f] = [(v, u) for u, v in k.uvs[f]]


def tri_prism_x(k, x0, x1, tri_zy, mat):
    """Prism along X with a triangular (z, y) section - fills a gable under a roof ridge on X."""
    a, b, c = tri_zy
    k._face([(x1, y, z) for z, y in (a, b, c)], mat, [(z, y) for z, y in (a, b, c)])
    k._face([(x0, y, z) for z, y in (c, b, a)], mat, [(z, y) for z, y in (c, b, a)])
    pts = (a, b, c)
    for i in range(3):
        (za, ya), (zb, yb) = pts[i], pts[(i + 1) % 3]
        k._face([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], mat, [(x0, ya), (x1, ya), (x1, yb), (x0, yb)])


def tri_prism_z(k, z0, z1, tri_xy, mat):
    """Prism along Z with a triangular (x, y) section - fills a gable under a roof ridge on Z."""
    a, b, c = tri_xy
    k._face([(x, y, z1) for x, y in (a, b, c)], mat, [(x, y) for x, y in (a, b, c)])
    k._face([(x, y, z0) for x, y in (c, b, a)], mat, [(x, y) for x, y in (c, b, a)])
    pts = (a, b, c)
    for i in range(3):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % 3]
        k._face([(xa, ya, z0), (xa, ya, z1), (xb, yb, z1), (xb, yb, z0)], mat, [(z0, ya), (z1, ya), (z1, yb), (z0, yb)])


def mound(k, rng, cx, cz, rx, rz, h, y0, swatches, mat, seg=8):
    """Low-poly faceted heap; every facet takes a random T_Env_TrashPalette swatch."""
    rings = ((0.0, h), (0.5, h * 0.78), (0.86, h * 0.36), (1.0, 0.0))
    pts = []
    for ri, (rho, y) in enumerate(rings):
        if ri == 0:
            pts.append([(cx + rng.uniform(-0.1, 0.1), y0 + y, cz + rng.uniform(-0.1, 0.1))])
            continue
        row = []
        for j in range(seg):
            a = 2 * math.pi * (j + 0.5 * (ri % 2)) / seg
            jit = 1.0 + rng.uniform(-0.12, 0.1) * (ri < 3)
            row.append((cx + rx * rho * jit * math.cos(a), y0 + y + rng.uniform(-0.08, 0.08) * (ri < 3),
                        cz + rz * rho * jit * math.sin(a)))
        pts.append(row)
    s = len(k.faces)
    top = pts[0][0]
    for j in range(seg):
        k._face([top, pts[1][(j + 1) % seg], pts[1][j]], mat, [(0, 0)] * 3)
    for a, b in zip(pts[1:], pts[2:]):
        for j in range(seg):
            j1 = (j + 1) % seg
            k._face([a[j], a[j1], b[j1], b[j]], mat, [(0, 0)] * 4)
    k._face(list(pts[-1]), mat, [(0, 0)] * seg)
    for f in range(s, len(k.faces)):
        paint_one(k, f, rng.choice(swatches))


def paint_one(k, f, swatch):
    cu, cv = (swatch % PALETTE_GRID + 0.5) / PALETTE_GRID, (swatch // PALETTE_GRID + 0.5) / PALETTE_GRID
    n = len(k.faces[f])
    k.uvs[f] = [(cu + 0.02 * math.cos(2 * math.pi * j / n), cv + 0.02 * math.sin(2 * math.pi * j / n)) for j in range(n)]
