"""SM_Env_PosMedisB3 (Wesley) - medical B3 waste station with incinerator, 800-1,400 tris.

Look from Wesley's reference (the "Mekanisme Pengelolaan Limbah B3" facility): a blue
steel-clad hall under a blue gable roof with skylight strips, a big loading bay on the
gable end, a lighter office annex, a tall white incinerator stack with hazard bands, a
storage tank with a red pipe and yellow medical waste bins. Sign/accent colours follow
docs/DESIGN.md 2.4 (Pos Medis = #EAB308 + red cross #DC2626).

Readability for players: "POS MEDIS B3" board over the loading bay, a red cross on the
gable, a "SETOR LIMBAH MEDIS / WAJIB PAKAI CAPIT ULAR" instruction board on the annex and
the striped stack as a landmark visible from the bridge.

Contract (MapJsonImporter): node "Pos Medis B3" map (220, 720) -> Unity (-37.5, 1.40, 0),
rot 0, groundY = BankTopY 1.40. Pivot = bottom centre at Y 0, the slab skirts to -0.5 m.
Front (+X) faces the river next to the Jembatan Utama west ramp.
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_PosMedisB3"
TRI_BUDGET = (800, 1400)

DINDING, SENG_BIRU, KACA, TEMBOK, BESI, KUNING, ZINC, MERAH, BETON, PALET, PAPAN = range(11)
MATERIALS = (
    ("M_Env_DindingBiru", (0.12, 0.31, 0.55, 1.0)),
    ("M_Env_SengBiru", (0.23, 0.50, 0.77, 1.0)),
    ("M_Env_Kaca", (0.11, 0.21, 0.31, 1.0)),
    ("M_Env_TembokPutih", (0.86, 0.85, 0.82, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_AtapKuning", (0.92, 0.70, 0.03, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_PintuMerah", (0.70, 0.15, 0.16, 1.0)),
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanPosMedis", (0.92, 0.70, 0.03, 1.0)),
)

UV_MAIN = pm.px(0, 0, 1024, 224)
UV_INFO = pm.px(0, 240, 512, 752)
UV_CROSS = pm.px(528, 240, 784, 496)
UV_EDGE = pm.px(800, 800, 1000, 1000)

Y0 = 0.2                               # slab top
HX0, HX1, HZ0, HZ1 = -4.2, 1.8, -5.0, 1.6
WALL_TOP, RIDGE = 4.6, 6.0
Z_R = (HZ0 + HZ1) * 0.5                # ridge runs along X, gable end faces the river
EAVE_OVER, END_OVER = 0.4, 0.3
BAY_Z0, BAY_Z1, BAY_TOP = -3.4, 0.0, 3.6
AX0, AX1, AZ0, AZ1, A_TOP = -3.0, 1.4, 1.58, 5.2, 3.4


def _slope_y(z):
    half = (HZ1 - HZ0) * 0.5 + EAVE_OVER
    return RIDGE - abs(z - Z_R) / half * (RIDGE - (WALL_TOP - 0.05))


def _hall(k):
    k.box(HX0, 0.6, Y0, WALL_TOP, HZ0, HZ1, DINDING)                                   # main volume
    k.box(0.58, HX1, Y0, WALL_TOP, HZ0, BAY_Z0, DINDING)                               # gable wall left of bay
    k.box(0.58, HX1, Y0, WALL_TOP, BAY_Z1, HZ1, DINDING)                               # right of bay
    k.box(0.58, HX1, BAY_TOP, WALL_TOP - 0.01, BAY_Z0 - 0.02, BAY_Z1 + 0.02, DINDING)  # lintel
    k.box(0.6, 0.63, Y0, BAY_TOP, BAY_Z0, BAY_Z1, BESI)                                # dark bay interior
    k.box(1.5, 1.56, 2.75, BAY_TOP, BAY_Z0 + 0.02, BAY_Z1 - 0.02, ZINC)               # half-open shutter
    pm.tri_prism_x(k, HX0, HX1, ((HZ0, WALL_TOP - 0.02), (HZ1, WALL_TOP - 0.02), (Z_R, RIDGE - 0.03)), DINDING)
    k.box(-3.6, 0.3, 3.0, 3.6, HZ0 - 0.03, HZ0, KACA)                                  # clerestory windows (-Z)
    # signage: POS MEDIS B3 over the bay, red cross on the gable
    pm.board(k, HX1, HX1 + 0.06, 3.68, 4.5, Z_R - 1.84, Z_R + 1.84, PAPAN, "+x", UV_MAIN, UV_EDGE)
    pm.board(k, HX1, HX1 + 0.04, 4.72, 5.5, Z_R - 0.39, Z_R + 0.39, PAPAN, "+x", UV_CROSS, UV_EDGE)


def _roof(k):
    x0, x1 = HX0 - END_OVER, HX1 + END_OVER
    for ze in (HZ0 - EAVE_OVER, HZ1 + EAVE_OVER):
        bot = [(x0, _slope_y(ze), ze), (x1, _slope_y(ze), ze), (x1, RIDGE, Z_R), (x0, RIDGE, Z_R)]
        s = len(k.faces)
        k.hexa(bot + [(x, y + 0.08, z) for x, y, z in bot], SENG_BIRU)
        pm.swap_uv(k, s)                                                                 # ribs run down the slope
    k.box(x0 - 0.02, x1 + 0.02, RIDGE + 0.02, RIDGE + 0.12, Z_R - 0.2, Z_R + 0.2, ZINC)  # ridge cap
    # skylight strips (3 on the +Z slope seen from the approach, 2 on the -Z slope)
    for zs, xs in ((1, (-3.5, -2.2, -0.9)), (-1, (-3.0, -1.4))):
        za, zb = Z_R + zs * 0.55, Z_R + zs * 2.6
        for xa in xs:
            xb = xa + 0.95
            bot = [(xa, _slope_y(za) + 0.09, za), (xb, _slope_y(za) + 0.09, za),
                   (xb, _slope_y(zb) + 0.09, zb), (xa, _slope_y(zb) + 0.09, zb)]
            k.hexa(bot + [(x, y + 0.08, z) for x, y, z in bot], KACA)


def _annex(k):
    k.box(AX0, AX1, Y0, A_TOP, AZ0, AZ1, TEMBOK)
    k.box(AX0 - 0.15, AX1 + 0.25, A_TOP, A_TOP + 0.25, AZ0, AZ1 + 0.15, DINDING)       # blue roof band
    k.box(AX1, AX1 + 0.04, 0.9, 2.9, 1.8, 2.9, KACA)                                  # office window
    k.box(AX1, AX1 + 0.04, Y0, 2.4, 3.05, 3.85, KACA)                                 # glass door
    pm.board(k, AX1, AX1 + 0.05, 1.0, 2.2, 3.95, 5.1, PAPAN, "+x", UV_INFO, UV_EDGE)  # SETOR LIMBAH MEDIS
    k.box(-1.5, -0.6, A_TOP + 0.25, A_TOP + 0.75, 3.6, 4.4, ZINC)                     # AC / exhaust unit


def _incinerator(k):
    k.box(-4.9, -2.6, Y0, 2.4, -7.0, -5.15, BESI)                                     # burner unit
    k.box(-3.3, -2.8, 1.2, 1.8, -5.2, -4.95, BESI)                                    # feed duct into the hall
    cx, cz = -3.75, -6.07
    k.cylinder(cx, cz, 0.42, 2.4, 11.5, TEMBOK, seg=8)                                # white stack
    for y in (8.4, 9.9):
        k.cylinder(cx, cz, 0.46, y, y + 0.6, KUNING, seg=8)                           # hazard bands
    k.cylinder(cx, cz, 0.49, 11.3, 11.62, BESI, seg=8)                                # soot cap


def _yard(k):
    k.box(-5.2, 5.0, -0.5, Y0, -7.4, 6.2, BETON)                                      # slab
    k.cylinder(-4.3, 4.0, 0.8, Y0, 3.3, ZINC, seg=10)                                 # storage tank
    k.cylinder(-4.3, 4.0, 0.55, 3.3, 3.55, ZINC, seg=10)
    k.cylinder(-4.4, 5.6, 0.52, Y0, 2.6, ZINC, seg=8)                                  # second, smaller tank
    k.beam((-4.15, 2.9, 3.4), (-4.15, 2.9, 1.5), 0.08, MERAH)                         # red pipe into the hall
    k.beam((-4.15, 2.9, 3.4), (-4.15, 3.6, 3.4), 0.08, MERAH)
    # yellow medical waste dumpsters with red lids + red-cross decals
    for zc in (-6.05, -4.75):
        s = len(k.faces)
        k.box(2.6, 3.6, Y0, 1.25, zc - 0.55, zc + 0.55, PALET)
        pm.paint(k, s, 9)
        s = len(k.faces)
        k.hexa([(2.55, 1.25, zc - 0.6), (3.65, 1.25, zc - 0.6), (3.65, 1.25, zc + 0.6), (2.55, 1.25, zc + 0.6),
                (2.55, 1.48, zc - 0.6), (3.65, 1.36, zc - 0.6), (3.65, 1.36, zc + 0.6), (2.55, 1.48, zc + 0.6)], PALET)
        pm.paint(k, s, 3)
        pm.board(k, 3.6, 3.63, 0.45, 1.05, zc - 0.3, zc + 0.3, PAPAN, "+x", UV_CROSS, UV_EDGE)
    # painted loading zone in front of the bay + bollards
    y1 = Y0 + 0.012
    k.box(1.9, 4.9, Y0, y1, BAY_Z0 - 0.1, BAY_Z0, KUNING)
    k.box(1.9, 4.9, Y0, y1, BAY_Z1, BAY_Z1 + 0.1, KUNING)
    k.box(4.8, 4.9, Y0, y1, BAY_Z0, BAY_Z1, KUNING)
    for z in (BAY_Z0 - 0.3, BAY_Z1 + 0.3):
        k.cylinder(2.05, z, 0.12, Y0, 1.1, KUNING, seg=6)
    # street lamp like the reference
    k.box(4.15, 4.27, Y0, 4.4, 2.6, 2.72, BESI)
    k.box(3.5, 4.27, 4.3, 4.4, 2.6, 2.72, BESI)
    k.box(3.35, 3.75, 4.18, 4.32, 2.5, 2.82, ZINC)


def _details(k):
    k.box(-3.4, 0.0, 3.85, 4.35, HZ1, HZ1 + 0.03, KACA)                                # windows above the annex roof
    for x, z in ((HX1 + 0.05, HZ0 + 0.1), (HX1 + 0.05, HZ1 - 0.1)):                    # downpipes on the gable
        k.box(x, x + 0.1, Y0, WALL_TOP - 0.1, z - 0.05, z + 0.05, ZINC)
    k.box(AX1, AX1 + 0.6, Y0, Y0 + 0.15, 2.95, 3.95, BETON)                           # step at the office door
    k.box(AX1, AX1 + 0.9, 2.55, 2.65, 2.9, 4.0, DINDING)                              # door canopy
    for x in (-3.2, -0.4):                                                            # ridge ventilators
        k.box(x - 0.3, x + 0.3, RIDGE + 0.1, RIDGE + 0.45, Z_R - 0.3, Z_R + 0.3, ZINC)


def build():
    k = MeshKit(uv_tile=2.0)
    _yard(k)
    _hall(k)
    _roof(k)
    _annex(k)
    _incinerator(k)
    _details(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    zs = [v.co.z for v in me.vertices]
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi,
            "height_m": round(max(zs), 2)}
