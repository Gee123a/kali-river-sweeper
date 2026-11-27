"""SM_Env_BankSampah (Wesley) - "Bank Sampah Berkah" drop-off station, 1,200-1,800 tris.

Look from Wesley's references: a real kampung bank-sampah cage (teal steel square-tube
frame, wire-mesh walls, maroon corrugated gable roof, green signs per bay) built with the
chunky, readable proportions of a stylised low-poly recycling yard. Sign/accent colours
follow docs/DESIGN.md 2.4 (Bank Sampah = #22C55E / #14B8A6), weathered like the rest of
the kampung.

Gameplay reading (plan_wesley / tracker: "drop-off bay, sorting scale, balance ledger"):
    - 4 sorting bays (BOTOL / PLASTIK / KERTAS / DAUN) filled with low-poly trash mounds
    - a rooftop "BANK SAMPAH BERKAH" sign that reads from the river (landmark)
    - a painted drop-off bay on the concrete apron with a platform scale (timbangan)
    - a "SALDO NASABAH" chalk ledger + counter table on the +Z end (faces the spawn path)

Contract (MapJsonImporter): node "Bank Sampah Berkah" map (195, 1185) -> Unity
(-40.6, 1.40, 58.1), rot 0, groundY = BankTopY 1.40. Pivot = bottom centre at Y 0;
the slab skirts down to -0.5 m to hide uneven bank edges. Front (+X) faces the river,
Dermaga Awal and the player spawn.
"""
import math
import random

from wesley_env.meshkit import MeshKit

NAME = "SM_Env_BankSampah"
TRI_BUDGET = (1200, 1800)

TEAL, SENG_MERAH, SENG_ZINC, KAWAT, BETON, KUNING, BESI, KAYU, PALET, PAPAN = range(10)
MATERIALS = (
    ("M_Env_BesiTeal", (0.11, 0.55, 0.49, 1.0)),
    ("M_Env_SengMerah", (0.56, 0.20, 0.19, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_KawatJaring", (0.30, 0.31, 0.31, 1.0)),
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
    ("M_Env_AtapKuning", (0.92, 0.70, 0.03, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanBankSampah", (0.13, 0.77, 0.37, 1.0)),
)

# ---- layout (metres, Unity axes, pivot at the bottom centre) ----
SLAB_TOP = 0.15
XB, XF = -3.9, -0.9               # cage back / front (front faces +X = river side)
XC = (XB + XF) * 0.5
ZS = (-4.8, -2.4, 0.0, 2.4, 4.8)  # 4 bays, 2.4 m each
FLOOR, TOP = 0.55, 2.5
TUBE = 0.055                      # half size of the square steel tube
EAVE_Y, RIDGE_Y, OVER = 2.42, 3.08, 0.55

# ---- texture atlas T_Env_PapanBankSampah (1024 px, see papan.py) ----
ATLAS = 1024.0


def _px(x0, y0, x1, y1):
    """Pixel box (top-left origin, as drawn by PIL) -> UV rect (u0, v0, u1, v1)."""
    return (x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS)


UV_BIG = _px(0, 0, 1024, 256)
UV_BAYS = [_px(0, 256, 512, 384), _px(512, 256, 1024, 384), _px(0, 384, 512, 512), _px(512, 384, 1024, 512)]
UV_LEDGER = _px(0, 512, 768, 896)
UV_DIAL = _px(768, 512, 1024, 768)
UV_EDGE = _px(800, 800, 992, 992)          # solid dark-teal block for board edges/backs

PALETTE_GRID = 4                           # T_Env_TrashPalette swatches (trash_pieces.PALETTE)
BAY_SWATCHES = (
    (5, 5, 5, 7, 6, 0),      # BOTOL: clear PET, green bottles, blue caps
    (0, 2, 3, 4, 1, 0),      # PLASTIK: white / black / red / blue kresek
    (10, 10, 11, 15, 10),    # KERTAS: cardboard, newspaper
    (6, 6, 14, 10, 6),       # DAUN: green + dry brown leaves
)
BAY_HEIGHT = (1.05, 1.2, 0.85, 0.75)


# ---------------- UV helpers ----------------
def _set_uv(k, face, uv):
    k.uvs[face] = list(uv)


def _rect_uv(rect):
    u0, v0, u1, v1 = rect
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _paint(k, start, swatch):
    """Point every face added since `start` at one flat palette swatch."""
    cu, cv = (swatch % PALETTE_GRID + 0.5) / PALETTE_GRID, (swatch // PALETTE_GRID + 0.5) / PALETTE_GRID
    for f in range(start, len(k.faces)):
        n = len(k.faces[f])
        _set_uv(k, f, [(cu + 0.02 * math.cos(2 * math.pi * j / n), cv + 0.02 * math.sin(2 * math.pi * j / n))
                       for j in range(n)])


def _edge(k, start):
    for f in range(start, len(k.faces)):
        u0, v0, u1, v1 = UV_EDGE
        _set_uv(k, f, [((u0 + u1) * 0.5, (v0 + v1) * 0.5)] * len(k.faces[f]))


# ---------------- parts ----------------
def _board_x(k, x, y0, y1, z0, z1, rect, t=0.06):
    """Sign board whose art faces +X (viewer's right = +Z)."""
    s = len(k.faces)
    k.box(x - t, x, y0, y1, z0, z1, PAPAN)
    _edge(k, s)
    _set_uv(k, s + 1, _rect_uv(rect))      # prism side 1 = the +X face


def _board_z(k, z, y0, y1, x0, x1, rect, t=0.05):
    """Sign board whose art faces +Z (viewer's right = -X)."""
    s = len(k.faces)
    k.box(x0, x1, y0, y1, z - t, z, PAPAN)
    _edge(k, s)
    _set_uv(k, s + 2, _rect_uv(rect))      # prism side 2 = the +Z face


def _dial_x(k, cx, cy, cz, r, depth, seg=12):
    """Round scale dial facing +X: side band + dial face mapped onto the atlas circle."""
    ring = [(cy + r * math.sin(2 * math.pi * i / seg), cz + r * math.cos(2 * math.pi * i / seg)) for i in range(seg)]
    x0, x1 = cx - depth, cx
    s = len(k.faces)
    for i in range(seg):
        (ya, za), (yb, zb) = ring[i], ring[(i + 1) % seg]
        k._face([(x0, ya, za), (x0, yb, zb), (x1, yb, zb), (x1, ya, za)], PAPAN, [(0, 0)] * 4)
    k._face([(x0, y, z) for y, z in reversed(ring)], PAPAN, [(0, 0)] * seg)
    _edge(k, s)
    u0, v0, u1, v1 = UV_DIAL
    cu, cv, ru, rv = (u0 + u1) * 0.5, (v0 + v1) * 0.5, (u1 - u0) * 0.47, (v1 - v0) * 0.47
    k._face([(x1, y, z) for y, z in ring], PAPAN, [(0, 0)] * seg)
    _set_uv(k, len(k.faces) - 1, [(cu + ru * (z - cz) / r, cv + rv * (y - cy) / r) for y, z in ring])


def _mound(k, rng, cx, cz, rx, rz, h, y0, swatches, seg=8):
    """Low-poly faceted heap of sorted trash; every facet takes a random palette swatch."""
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
        k._face([top, pts[1][(j + 1) % seg], pts[1][j]], PALET, [(0, 0)] * 3)
    for a, b in zip(pts[1:], pts[2:]):
        for j in range(seg):
            j1 = (j + 1) % seg
            k._face([a[j], a[j1], b[j1], b[j]], PALET, [(0, 0)] * 4)
    k._face(list(pts[-1]), PALET, [(0, 0)] * seg)            # base cap -> closed solid
    for f in range(s, len(k.faces)):              # each facet keeps its own swatch
        sw = rng.choice(swatches)
        cu, cv = (sw % PALETTE_GRID + 0.5) / PALETTE_GRID, (sw // PALETTE_GRID + 0.5) / PALETTE_GRID
        n = len(k.faces[f])
        _set_uv(k, f, [(cu + 0.02 * math.cos(2 * math.pi * j / n), cv + 0.02 * math.sin(2 * math.pi * j / n))
                       for j in range(n)])


def _wire_panel(k, corners):
    """Single quad of see-through wire mesh (two-sided alpha-clip material)."""
    (a, b, c, d) = corners
    if abs(a[0] - b[0]) < 1e-6 and abs(a[0] - c[0]) < 1e-6:   # panel in a YZ plane
        uv = [(p[2], p[1]) for p in corners]
    else:                                                     # panel in an XY plane
        uv = [(p[0], p[1]) for p in corners]
    k._face(list(corners), KAWAT, uv)


def _cage(k):
    h = TUBE
    for x in (XB, XF):                                        # posts
        for z in ZS:
            k.box(x - h, x + h, SLAB_TOP, TOP, z - h, z + h, TEAL)
    for x in (XB, XF):                                        # long rails
        for y in (FLOOR, 1.55, TOP):
            k.box(x - h, x + h, y - h, y + h, ZS[0], ZS[-1], TEAL)
    for z in ZS:                                              # cross rails
        for y in (FLOOR, TOP):
            k.box(XB, XF, y - h, y + h, z - h, z + h, TEAL)
    for x in (XB, XF):                                        # base plates under the posts
        for z in ZS:
            k.box(x - 0.13, x + 0.13, SLAB_TOP, SLAB_TOP + 0.025, z - 0.13, z + 0.13, BESI)
    for i in range(4):                                        # hinged drop door per bay + padlock
        zc = (ZS[i] + ZS[i + 1]) * 0.5
        d0, d1 = FLOOR + 0.32, 1.55
        for z in (zc - 0.6, zc + 0.6):
            k.box(XF + 0.02, XF + 0.07, d0, d1, z - 0.025, z + 0.025, TEAL)
        k.box(XF + 0.02, XF + 0.07, d0 + 0.32, d0 + 0.37, zc - 0.6, zc + 0.6, TEAL)
        k.box(XF + 0.07, XF + 0.12, 1.08, 1.2, zc + 0.5, zc + 0.6, BESI)
    k.box(XB, XF, FLOOR - 0.03, FLOOR + 0.03, ZS[0], ZS[-1], BESI)          # floor plate
    k.box(XF - 0.025, XF + 0.025, FLOOR, FLOOR + 0.32, ZS[0], ZS[-1], TEAL)  # front kick plate
    for i in range(4):                                        # back-wall diagonal braces
        z0, z1 = ZS[i], ZS[i + 1]
        k.beam((XB, FLOOR + 0.05, z0 + 0.05), (XB, TOP - 0.05, z1 - 0.05), 0.03, TEAL)
    # wire mesh: back, front (above kick plate), two ends, three bay dividers
    k_y0 = FLOOR + 0.32
    _wire_panel(k, [(XB, FLOOR, ZS[0]), (XB, FLOOR, ZS[-1]), (XB, TOP, ZS[-1]), (XB, TOP, ZS[0])])
    _wire_panel(k, [(XF, k_y0, ZS[0]), (XF, k_y0, ZS[-1]), (XF, TOP, ZS[-1]), (XF, TOP, ZS[0])])
    for z in ZS:
        _wire_panel(k, [(XB, FLOOR, z), (XF, FLOOR, z), (XF, TOP, z), (XB, TOP, z)])


def _roof(k):
    xe0, xe1, z0, z1 = XB - OVER, XF + OVER, ZS[0] - 0.5, ZS[-1] + 0.5

    def slope(xe, y_off0, y_off1, mat):
        a = (xe, EAVE_Y, z0)
        b = (XC, RIDGE_Y, z0)
        c = (XC, RIDGE_Y, z1)
        d = (xe, EAVE_Y, z1)
        bot = [(p[0], p[1] + y_off0, p[2]) for p in (a, b, c, d)]
        top = [(p[0], p[1] + y_off1, p[2]) for p in (a, b, c, d)]
        k.hexa(bot + top, mat)

    for xe in (xe0, xe1):
        slope(xe, 0.0, 0.045, SENG_MERAH)          # painted corrugated sheet
        slope(xe, -0.05, -0.008, SENG_ZINC)        # bare zinc underside
    k.box(XC - 0.16, XC + 0.16, RIDGE_Y + 0.02, RIDGE_Y + 0.1, z0 - 0.04, z1 + 0.04, SENG_ZINC)  # ridge cap
    for z in ZS:                                    # rafters
        for x in (XB, XF):
            k.beam((x, TOP, z), (XC, RIDGE_Y - 0.08, z), 0.045, TEAL)
    # rooftop landmark sign on two posts, readable from the river
    for z in (-1.25, 1.25):
        k.box(XC - 0.05, XC + 0.05, RIDGE_Y, RIDGE_Y + 0.42, z - 0.05, z + 0.05, TEAL)
    _board_x(k, XC + 0.04, RIDGE_Y + 0.32, RIDGE_Y + 1.22, -1.8, 1.8, UV_BIG, t=0.08)


def _bays(k, rng):
    for i in range(4):
        zc = (ZS[i] + ZS[i + 1]) * 0.5
        _mound(k, rng, XC + 0.05, zc, 1.25, 1.02, BAY_HEIGHT[i], FLOOR + 0.03, BAY_SWATCHES[i])
        _board_x(k, XF + 0.075, 1.93, 2.28, zc - 0.7, zc + 0.7, UV_BAYS[i], t=0.04)


def _apron(k):
    # concrete slab under everything (skirts to -0.5 to sit on uneven banks)
    k.box(XB - 0.55, 3.5, -0.5, SLAB_TOP, ZS[0] - 0.8, ZS[-1] + 2.1, BETON)
    # painted drop-off bay: yellow frame on the apron in front of the cage
    y0, y1 = SLAB_TOP, SLAB_TOP + 0.012
    bx0, bx1, bz0, bz1 = 0.15, 3.05, -3.1, 1.1
    w = 0.1
    k.box(bx0, bx1, y0, y1, bz0, bz0 + w, KUNING)
    k.box(bx0, bx1, y0, y1, bz1 - w, bz1, KUNING)
    k.box(bx1 - w, bx1, y0, y1, bz0 + w, bz1 - w, KUNING)
    k.box(3.38, 3.5, y0, y1, ZS[0] - 0.8, ZS[-1] + 2.1, KUNING)                # apron safety edge

    # platform scale (timbangan duduk) inside the bay
    sx, sz = 1.55, -1.0
    k.box(sx - 0.45, sx + 0.45, y0, y0 + 0.12, sz - 0.35, sz + 0.35, BESI)
    k.box(sx - 0.42, sx + 0.42, y0 + 0.12, y0 + 0.15, sz - 0.32, sz + 0.32, SENG_ZINC)
    k.box(sx - 0.52, sx - 0.42, y0, y0 + 1.02, sz - 0.05, sz + 0.05, BESI)       # column
    k.box(sx - 0.56, sx - 0.38, y0 + 0.98, y0 + 1.42, sz - 0.24, sz + 0.24, BESI)  # dial housing
    _dial_x(k, sx - 0.34, y0 + 1.2, sz, 0.2, 0.06)

    # colour-coded pilah bins (stylised, big lids) at the -Z corner of the apron
    for i, sw in enumerate((6, 9, 8)):                       # green / yellow / blue
        bxc, bzc = 1.25 + i * 0.75, ZS[0] - 0.25
        s = len(k.faces)
        k.box(bxc - 0.3, bxc + 0.3, y0, y0 + 0.78, bzc - 0.3, bzc + 0.3, PALET)
        k.hexa([(bxc - 0.34, y0 + 0.78, bzc - 0.34), (bxc + 0.34, y0 + 0.78, bzc - 0.34),
                (bxc + 0.34, y0 + 0.78, bzc + 0.34), (bxc - 0.34, y0 + 0.78, bzc + 0.34),
                (bxc - 0.34, y0 + 0.9, bzc - 0.34), (bxc + 0.34, y0 + 0.86, bzc - 0.34),
                (bxc + 0.34, y0 + 0.86, bzc + 0.34), (bxc - 0.34, y0 + 0.9, bzc + 0.34)], PALET)
        _paint(k, s, sw)


def _ledger(k):
    """Balance ledger on the +Z end: chalk board on the cage end + teller counter."""
    zb = ZS[-1] + 0.075
    _board_z(k, zb, 1.0, 2.15, XB + 0.35, XF - 0.35, UV_LEDGER, t=0.05)
    x0, x1, z0, z1, ty = XB + 0.6, XF - 0.6, ZS[-1] + 0.65, ZS[-1] + 1.35, 0.82
    k.box(x0, x1, ty - 0.06, ty, z0, z1, KAYU)
    for lx in (x0 + 0.07, x1 - 0.07):
        for lz in (z0 + 0.07, z1 - 0.07):
            k.box(lx - 0.04, lx + 0.04, SLAB_TOP, ty - 0.06, lz - 0.04, lz + 0.04, KAYU)
    s = len(k.faces)
    k.box(XC - 0.32, XC + 0.08, ty, ty + 0.05, z0 + 0.2, z0 + 0.5, PALET)       # buku tabungan
    _paint(k, s, 11)
    s = len(k.faces)
    k.box(XC + 0.25, XC + 0.43, ty, ty + 0.03, z0 + 0.25, z0 + 0.48, PALET)    # kalkulator
    _paint(k, s, 2)


def build():
    rng = random.Random(1185)
    k = MeshKit(uv_tile=2.0)
    _apron(k)
    _cage(k)
    _roof(k)
    _bays(k, rng)
    _ledger(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
