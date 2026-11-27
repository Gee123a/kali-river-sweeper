"""SM_Env_WarungMadura (Wesley) - 24-hour Warung Madura riverside kiosk, 600-1,000 tris.

From Wesley's reference illustration (without the pom mini, and rebuilt with correct 3D
proportions instead of the drawing's mixed perspective): an orange rendered kiosk under a
red corrugated gable roof, a wide open shop front packed with sembako shelves and
hanging sachet strips (rencengan), a glass etalase counter, water gallons, green 3 kg
LPG tubes, an ice freezer, a red-white striped awning, a "WARUNG MADURA" roof sign, a
"SEDIA PULSA / KUOTA / TOKEN / GAS / GALON / ES BATU" banner, a "BUKA 24 JAM" A-board and
a bench (tracker spec).

Contract (MapJsonImporter): 7 "warung" nodes, groundY = BankTopY 1.40, pivot bottom
centre Y 0. The importer hangs JC's PF_Lantern_Warung on (bounds.center.x, bounds.max.y,
bounds.center.z), so the plinth is symmetric about X = 0 and Z = 0 and the roof ridge
runs along Z exactly over X = 0 - the ridge is both the highest point and the bounds
centre, so the lantern sits on the ridge. The shop front faces +X (river on the west
bank); east-bank nodes need "rot": 180 in kali-river-map.json (Ivan's data).
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_WarungMadura"
TRI_BUDGET = (600, 1000)

TEMBOK, ATAP, KAYU, BESI, BETON, PALET, PAPAN = range(7)
MATERIALS = (
    ("M_Env_TembokOranye", (0.91, 0.63, 0.29, 1.0)),
    ("M_Env_PintuMerah", (0.70, 0.15, 0.16, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanWarung", (0.95, 0.90, 0.80, 1.0)),
)

UV_SIGN = pm.px(0, 0, 1024, 196)
UV_BANNER = pm.px(0, 212, 1024, 306)
UV_SHELF = pm.px(0, 320, 512, 832)
UV_ETALASE = pm.px(528, 320, 1024, 576)
UV_AFRAME = pm.px(528, 592, 784, 976)
UV_STRIPES = pm.px(800, 592, 1024, 816)
UV_SACHET = pm.px(0, 848, 512, 1024)
UV_LPG = pm.px(800, 832, 900, 932)
UV_WOOD = pm.px(900, 832, 1000, 932)

Y0 = 0.2
BX0, BX1, BZ = -2.0, 2.0, 3.0          # kiosk body (front face X = BX1)
X_IN = -0.7                            # back wall of the open shop
WALL_TOP, RIDGE, EAVE_X, EAVE_Y = 3.1, 4.2, 2.5, 2.9
HEAD = 2.55                            # underside of the shop-front header


def _roof_y(x):
    return RIDGE - abs(x) / EAVE_X * (RIDGE - EAVE_Y)


def _body(k):
    k.box(-3.5, 3.5, -0.5, Y0, -3.7, 3.7, BETON)                                        # tiled terrace / plinth
    k.box(BX0, X_IN, Y0, WALL_TOP, -BZ, BZ, TEMBOK)                                     # back block
    for z0, z1 in ((-BZ, -BZ + 0.4), (BZ - 0.4, BZ)):                                   # side walls of the shop
        k.box(X_IN - 0.02, BX1, Y0, WALL_TOP, z0, z1, TEMBOK)
    k.box(X_IN - 0.02, BX1, HEAD, WALL_TOP - 0.01, -BZ + 0.38, BZ - 0.38, TEMBOK)       # header over the opening
    pm.tri_prism_z(k, -BZ, BZ, ((BX0 - 0.02, WALL_TOP - 0.02), (BX1 + 0.02, WALL_TOP - 0.02), (0.0, _roof_y(0) - 0.04)), TEMBOK)
    k.box(BX0 - 0.03, BX0, Y0, 2.1, 0.5, 1.4, KAYU)                                     # back door
    k.box(-1.2, -0.85, 1.5, 1.85, -BZ - 0.08, -BZ, BESI)                                # electricity meter


def _roof(k):
    for xe in (-EAVE_X, EAVE_X):
        bot = [(xe, EAVE_Y, -BZ - 0.35), (0.0, RIDGE, -BZ - 0.35), (0.0, RIDGE, BZ + 0.35), (xe, EAVE_Y, BZ + 0.35)]
        k.hexa(bot + [(x, y + 0.06, z) for x, y, z in bot], ATAP)
    k.box(-0.14, 0.14, RIDGE, RIDGE + 0.08, -BZ - 0.38, BZ + 0.38, ATAP)                # ridge cap
    y = _roof_y(2.3)
    pm.board(k, 2.26, 2.34, y, y + 0.9, -2.3, 2.3, PAPAN, "+x", UV_SIGN, UV_WOOD)       # WARUNG MADURA roof sign


def _shop(k):
    for z0, z1 in ((-2.55, 0.0), (0.0, 2.55)):                                         # sembako shelves (back)
        pm.board(k, X_IN, X_IN + 0.04, Y0 + 0.05, HEAD - 0.05, z0, z1, PAPAN, "+x", UV_SHELF, UV_WOOD)
    pm.board(k, X_IN + 0.05, BX1 - 0.1, Y0 + 0.05, HEAD - 0.05, -BZ + 0.4, -BZ + 0.44, PAPAN, "+z", UV_SHELF, UV_WOOD)
    pm.board(k, X_IN + 0.05, BX1 - 0.1, Y0 + 0.05, HEAD - 0.05, BZ - 0.44, BZ - 0.4, PAPAN, "-z", UV_SHELF, UV_WOOD)
    for y in (0.95, 1.55, 2.15):                                                       # shelf lips for depth
        k.box(X_IN + 0.04, X_IN + 0.36, y, y + 0.04, -2.55, 2.55, KAYU)
    k.box(1.4, 2.1, Y0, 0.5, -1.4, 0.6, KAYU)                                           # etalase base
    pm.board(k, 1.4, 2.1, 0.5, 1.15, -1.4, 0.6, PAPAN, "+x", UV_ETALASE, UV_WOOD)       # glass case with goods
    # rencengan: hanging sachet strips under the header
    u0, v0, u1, v1 = UV_SACHET
    for i, z in enumerate((-2.3, -1.95, -1.6, 1.3, 1.65, 2.0, 2.35)):
        c = i % 8
        cu0, cu1 = u0 + (u1 - u0) * c / 8, u0 + (u1 - u0) * (c + 1) / 8
        k._face([(BX1 - 0.05, HEAD - 0.85, z - 0.07), (BX1 - 0.05, HEAD - 0.85, z + 0.07),
                 (BX1 - 0.05, HEAD, z + 0.07), (BX1 - 0.05, HEAD, z - 0.07)], PAPAN, [(0, 0)] * 4)
        k.uvs[-1] = [(cu0, v0), (cu1, v0), (cu1, v1), (cu0, v1)]
    s = len(k.faces)
    k.box(-0.2, 0.6, Y0, 1.05, 1.6, 2.5, PALET)                                         # ES BATU freezer
    pm.paint(k, s, 0)
    # banner over the opening
    pm.board(k, BX1, BX1 + 0.03, HEAD + 0.07, WALL_TOP - 0.05, -2.55, 2.55, PAPAN, "+x", UV_BANNER, UV_WOOD)


def _terrace(k):
    # striped awning + valance, on two thin posts
    pts = [(BX1, HEAD + 0.05, -BZ - 0.1), (3.3, 2.2, -BZ - 0.1), (3.3, 2.2, BZ + 0.1), (BX1, HEAD + 0.05, BZ + 0.1)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.03, z) for x, y, z in pts], PAPAN)
    pm.stretch(k, s, UV_STRIPES)
    s = len(k.faces)
    k.box(3.28, 3.31, 1.95, 2.2, -BZ - 0.1, BZ + 0.1, PAPAN)
    pm.stretch(k, s, UV_STRIPES)
    for z in (-BZ, BZ):
        k.box(3.22, 3.28, Y0, 2.2, z - 0.03, z + 0.03, BESI)
    # water gallons (3 standing + 1 on top) and green 3 kg LPG tubes
    for z in (1.6, 1.95, 2.3):
        s = len(k.faces)
        k.cylinder(2.4, z, 0.16, Y0, Y0 + 0.5, PALET, seg=8)
        pm.paint(k, s, 5)
    s = len(k.faces)
    k.cylinder(2.4, 1.95, 0.16, Y0 + 0.5, Y0 + 1.0, PALET, seg=8)
    pm.paint(k, s, 5)
    for x, z in ((2.3, -2.55), (2.3, -2.2), (2.6, -2.38)):
        s = len(k.faces)
        k.cylinder(x, z, 0.15, Y0, Y0 + 0.4, PAPAN, seg=6)
        pm.flat(k, s, UV_LPG)
    # BUKA 24 JAM A-board + its back leg
    pm.board(k, 3.0, 3.04, Y0, Y0 + 0.9, -3.5, -2.9, PAPAN, "+x", UV_AFRAME, UV_WOOD)
    k.beam((3.02, Y0 + 0.88, -3.2), (2.7, Y0, -3.2), 0.03, KAYU)
    # bench along the +Z side wall
    k.box(-1.5, 0.3, 0.42, 0.48, BZ + 0.15, BZ + 0.55, KAYU)
    for x in (-1.35, 0.15):
        k.box(x - 0.04, x + 0.04, Y0, 0.42, BZ + 0.2, BZ + 0.5, KAYU)
    # red plastic stools + a crate of bottled drinks by the counter
    for z in (-1.1, -0.5):
        s = len(k.faces)
        k.box(2.55, 2.85, Y0, Y0 + 0.42, z - 0.15, z + 0.15, PALET)
        pm.paint(k, s, 3)
    s = len(k.faces)
    k.box(2.25, 2.75, Y0, Y0 + 0.3, 0.75, 1.2, PALET)
    pm.paint(k, s, 9)
    # back service area: blue water drum
    s = len(k.faces)
    k.cylinder(-2.9, -2.0, 0.3, Y0, Y0 + 0.8, PALET, seg=8)
    pm.paint(k, s, 8)


def build():
    k = MeshKit(uv_tile=2.0)
    _body(k)
    _roof(k)
    _shop(k)
    _terrace(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    xs = [v.co.x for v in me.vertices]   # Blender X = -Unity X
    ys = [v.co.y for v in me.vertices]   # Blender Y = -Unity Z
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi,
            "bounds_centre_unity_xz": (round(-(max(xs) + min(xs)) / 2, 3), round(-(max(ys) + min(ys)) / 2, 3))}
