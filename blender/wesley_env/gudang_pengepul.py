"""SM_Env_GudangPengepul (Wesley) - informal bulk scrap collector warehouse, 800-1,200 tris.

From Wesley's reference ("just a warehouse"): a big barn under a rusty corrugated gable,
the right bay closed in grey galvanised zinc sheet with a sliding door, the left bays an
open two-storey timber rack crammed with stock (here: wire-strapped plastic bales, tied
cardboard bundles, woven sacks), diagonal timber braces under the eaves and a lean-to on
the side for loose scrap. Accent = Gudang Pengepul #A87018 amber rust (docs/DESIGN.md 2.4).

Readability for players: hand-painted "GUDANG PENGEPUL - TERIMA SEMUA SAMPAH - SEKALI
SETOR" board on the closed bay and a "HARGA BORONGAN" price board at the open drop-off
bay (Normal 2.000 / Medis 3.000 / Biohazard 4.500, no fine, but the kampung's trust drops
when B3 is mixed in) - the exact trade-off the station represents in the PRD.

Contract (MapJsonImporter): node "Gudang Pengepul" map (285, 1280) -> Unity
(-29.4, 1.40, 70.0) on the west bank near the spawn and Bank Sampah, rot 0, groundY =
BankTopY 1.40. Pivot = bottom centre Y 0, slab skirts to -0.5 m. Front (+X) faces the
river / Dermaga Awal; the lean-to sits on the -Z side (toward the spawn).
"""
import random

from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_GudangPengepul"
TRI_BUDGET = (800, 1200)

ZINC, KARAT, TIANG, KAYU, BETON, BESI, PALET, PAPAN = range(8)
MATERIALS = (
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_SengKarat", (0.54, 0.39, 0.27, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanPengepul", (0.66, 0.44, 0.09, 1.0)),
)

UV_SIGN = pm.px(0, 0, 1024, 400)
UV_PRICE = pm.px(0, 416, 640, 816)
UV_PLASTIK = pm.px(656, 416, 1024, 656)
UV_KARDUS = pm.px(656, 672, 1024, 912)
UV_KARUNG_A = pm.px(0, 832, 320, 1024)
UV_KARUNG_B = pm.px(320, 832, 640, 1024)
UV_DARK = pm.px(656, 928, 1024, 1024)

Y0 = 0.2
GX0, GX1, GZ0, GZ1 = -3.6, 3.0, -4.2, 4.2     # barn
Z_CLOSED = 1.4                                # closed zinc bay: Z_CLOSED..GZ1
WALL_TOP, RIDGE, RIDGE_X, OVER = 4.85, 6.4, -0.3, 0.4
LOFT = 2.55
BAYS = ((GZ0, -2.33), (-2.33, -0.47), (-0.47, Z_CLOSED))
OPEN_BAY = 1                                  # lower middle bay = drop-off with the scale


def _eave_y(x):
    run = (GX1 + OVER - RIDGE_X) if x > RIDGE_X else (RIDGE_X - (GX0 - OVER))
    return RIDGE - abs(x - RIDGE_X) / run * (RIDGE - (WALL_TOP - 0.05))


def _barn(k):
    k.box(GX0 - 0.4, 4.3, -0.5, Y0, -7.0, GZ1 + 0.4, BETON)                              # slab
    k.box(GX0, GX1, Y0, WALL_TOP, Z_CLOSED, GZ1, ZINC)                                   # closed zinc bay
    pm.tri_prism_z(k, Z_CLOSED, GZ1, ((GX0 - 0.02, WALL_TOP - 0.02), (GX1 + 0.02, WALL_TOP - 0.02),
                                      (RIDGE_X, RIDGE - 0.06)), ZINC)
    k.box(GX0, GX0 + 0.08, Y0, WALL_TOP, GZ0, Z_CLOSED + 0.02, ZINC)                     # back wall of the racks
    k.box(GX1, GX1 + 0.05, Y0, 3.2, 1.9, 3.9, KARAT)                                     # sliding door
    k.box(GX1, GX1 + 0.08, 3.2, 3.3, 1.6, 4.1, BESI)                                     # door rail
    k.box(-2.0, -0.6, 2.4, 3.2, GZ1, GZ1 + 0.04, BESI)                                   # louvre (+Z side)
    pm.board(k, GX1 + 0.05, GX1 + 0.1, 3.45, 4.6, 1.5, 4.1, PAPAN, "+x", UV_SIGN, UV_DARK)
    k.box(GX1 + 0.05, GX1 + 0.13, Y0, WALL_TOP - 0.1, GZ1 - 0.12, GZ1 - 0.04, ZINC)       # downpipe
    k.box(GX0 - 0.04, GX0, 2.4, 3.2, 2.2, 3.4, BESI)                                     # back window


def _frame(k):
    t = 0.11
    for z in (GZ0 + t, BAYS[0][1], BAYS[1][1], Z_CLOSED - t):                           # front posts
        k.box(GX1 - t, GX1 + t, Y0, WALL_TOP, z - t, z + t, TIANG)
    k.box(GX0 + 0.08, GX1, LOFT - 0.05, LOFT + 0.05, GZ0, Z_CLOSED, KAYU)                # loft floor
    k.box(GX1 - 0.1, GX1 + 0.12, LOFT - 0.1, LOFT + 0.08, GZ0, Z_CLOSED, TIANG)          # loft edge beam
    k.box(GX1 - 0.1, GX1 + 0.12, WALL_TOP - 0.16, WALL_TOP, GZ0, Z_CLOSED, TIANG)        # top plate
    for z in (GZ0 + t, BAYS[0][1], BAYS[1][1], Z_CLOSED - t):                           # eave braces
        k.beam((GX1, 3.9, z), (GX1 + OVER - 0.05, _eave_y(GX1 + OVER - 0.05) - 0.12, z), 0.05, TIANG)
    # open gable truss on the -Z end
    k.box(GX0, GX1, WALL_TOP - 0.16, WALL_TOP, GZ0 - 0.06, GZ0 + 0.06, TIANG)
    for x in (GX0, GX1):
        k.beam((x, WALL_TOP, GZ0), (RIDGE_X, RIDGE - 0.12, GZ0), 0.07, TIANG)
    k.box(RIDGE_X - 0.06, RIDGE_X + 0.06, WALL_TOP, RIDGE - 0.12, GZ0 - 0.06, GZ0 + 0.06, TIANG)


def _stock(k):
    """Rack cells filled with stacked stock; each cell = 2 stacked blocks with art on +X."""
    arts = {(0, 0): (UV_PLASTIK, UV_KARDUS), (2, 0): (UV_KARDUS, UV_PLASTIK),
            (0, 1): (UV_KARUNG_A, UV_PLASTIK), (1, 1): (UV_PLASTIK, UV_KARUNG_B), (2, 1): (UV_KARUNG_B, UV_KARDUS)}
    for (bay, level), (low, high) in arts.items():
        z0, z1 = BAYS[bay][0] + 0.16, BAYS[bay][1] - 0.16
        y0, y1 = (Y0, LOFT - 0.06) if level == 0 else (LOFT + 0.06, WALL_TOP - 0.18)
        ym = (y0 + y1) * 0.5
        xf = GX1 - 0.25 - 0.08 * level
        pm.board(k, GX0 + 0.1, xf, y0, ym, z0, z1, PAPAN, "+x", low, UV_DARK)
        pm.board(k, GX0 + 0.1, xf - 0.15, ym, y1, z0 + 0.05, z1 - 0.05, PAPAN, "+x", high, UV_DARK)
    # open drop-off bay: hanging dacin scale from the loft + loose sacks
    za, zb = BAYS[OPEN_BAY]
    zc = (za + zb) * 0.5
    k.box(1.95, 2.0, 1.75, LOFT - 0.05, zc - 0.025, zc + 0.025, BESI)
    k.box(1.6, 2.35, 1.7, 1.78, zc - 0.03, zc + 0.03, BESI)                             # balance beam
    k.box(1.7, 2.25, 1.0, 1.04, zc - 0.25, zc + 0.25, BESI)                             # pan
    for sw, (x, z) in ((11, (0.4, za + 0.5)), (12, (0.9, zb - 0.55))):
        s = len(k.faces)
        k.box(x - 0.4, x + 0.4, Y0, Y0 + 0.55, z - 0.3, z + 0.3, PALET)
        pm.paint(k, s, sw)


def _roof(k):
    z0, z1 = GZ0 - OVER, GZ1 + OVER
    for xe in (GX0 - OVER, GX1 + OVER):
        bot = [(xe, _eave_y(xe), z0), (RIDGE_X, RIDGE, z0), (RIDGE_X, RIDGE, z1), (xe, _eave_y(xe), z1)]
        k.hexa(bot + [(x, y + 0.07, z) for x, y, z in bot], KARAT)
    k.box(RIDGE_X - 0.18, RIDGE_X + 0.18, RIDGE + 0.04, RIDGE + 0.13, z0 - 0.04, z1 + 0.04, ZINC)


def _lean_to(k, rng):
    """Side lean-to on -Z for loose scrap, drums and a push cart."""
    zt, ze, yt, ye = GZ0, -6.6, 4.1, 3.0
    pts = [(GX0 - 0.2, yt, zt), (GX1 + 0.3, yt, zt), (GX1 + 0.3, ye, ze), (GX0 - 0.2, ye, ze)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.06, z) for x, y, z in pts], KARAT)
    pm.swap_uv(k, s)                                                                    # ribs run down the slope
    for x in (GX0 + 0.1, RIDGE_X, GX1):
        k.box(x - 0.09, x + 0.09, Y0, ye, ze + 0.15, ze + 0.33, TIANG)
    pm.mound(k, rng, -1.6, -5.4, 1.5, 0.95, 1.1, Y0, (1, 2, 14, 10, 1, 15, 12), PALET)  # scrap metal heap
    for x, sw in ((0.6, 12), (1.25, 8)):                                                # drums
        s = len(k.faces)
        k.cylinder(x, -6.0, 0.3, Y0, Y0 + 0.9, PALET, seg=8)
        pm.paint(k, s, sw)
    for i, sw in enumerate((0, 11, 4)):                                                 # stacked plastic bales
        s = len(k.faces)
        k.box(1.9, 2.8, Y0 + i * 0.55, Y0 + (i + 1) * 0.55, -5.6 + i * 0.05, -4.8 + i * 0.05, PALET)
        pm.paint(k, s, sw)
    # gerobak (push cart) for the collectors
    k.box(2.9, 4.0, 0.55, 0.95, -5.9, -5.0, KAYU)
    k.beam((2.9, 0.75, -5.75), (2.4, 1.0, -5.75), 0.03, KAYU)
    k.beam((2.9, 0.75, -5.15), (2.4, 1.0, -5.15), 0.03, KAYU)
    for z in (-5.92, -4.98):
        k.box(3.35, 3.75, Y0, 0.6, z - 0.03, z + 0.03, BESI)


def _yard(k):
    # HARGA BORONGAN board on two legs in front of the drop-off bay
    za, zb = BAYS[OPEN_BAY]
    pm.board(k, 3.7, 3.74, 0.9, 1.9, za + 0.1, zb - 0.1, PAPAN, "+x", UV_PRICE, UV_DARK)
    for z in (za + 0.2, zb - 0.2):
        k.box(3.66, 3.7, Y0, 1.85, z - 0.03, z + 0.03, TIANG)
    for i, (z, sw) in enumerate(((zb + 0.45, 11), (zb + 0.45, 0))):                     # sacks waiting to be weighed
        s = len(k.faces)
        k.box(3.35, 4.05, Y0 + i * 0.4, Y0 + (i + 1) * 0.4, z - 0.32 + i * 0.05, z + 0.32 + i * 0.05, PALET)
        pm.paint(k, s, sw)


def build():
    rng = random.Random(1280)
    k = MeshKit(uv_tile=2.0)
    _barn(k)
    _frame(k)
    _stock(k)
    _roof(k)
    _lean_to(k, rng)
    _yard(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
