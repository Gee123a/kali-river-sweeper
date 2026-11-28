"""SM_Env_RumahPanggung (Wesley) - kampung river stilt house, 800-1,500 tris (11 nodes).

From Wesley's river-village photos: a timber plank house raised on tall wooden stilts with
X-bracing, weathered grey board walls with a teal-painted river facade and a dark window
band, a rusty corrugated zinc roof with newer galvanised patch sheets, a railed front
veranda under its own lean-to, a steep stair down to the ground, an orange water tank,
a clothesline and a small kitchen lean-to at the back (tracker: "bamboo stilts, wooden
planks, rusted zinc roof").

Contract (MapJsonImporter): 11 "rumah" nodes, groundY = BankTopY 1.40, pivot bottom
centre Y 0; the stilts start at -0.5 so they bite into uneven bank ground. Facade and
stair face +X (river on the west bank); east-bank nodes need "rot": 180 in
kali-river-map.json (Ivan's data).
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_RumahPanggung"
TRI_BUDGET = (800, 1500)

ABU, TEAL, TIANG, KARAT, ZINC, KACA, KAYU, PALET = range(8)
MATERIALS = (
    ("M_Env_KayuAbu", (0.64, 0.61, 0.56, 1.0)),
    ("M_Env_PapanTeal", (0.25, 0.67, 0.61, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_SengKarat", (0.54, 0.39, 0.27, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_Kaca", (0.11, 0.21, 0.31, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
)

STILT_Y = -0.5
FLOOR = 2.0                              # top of the floor deck
HX0, HX1, HZ = -3.0, 1.2, 2.6            # house body, front facade at X = HX1
VX1, PZ = 3.3, 2.8                       # veranda edge, platform half width
WALL_TOP, RIDGE, RIDGE_X, OVER = 4.35, 5.55, -0.9, 0.45
POSTS_X, POSTS_Z = (-2.8, -0.9, 1.0, 3.1), (-2.6, 0.0, 2.6)


def _roof_y(x):
    run = (HX1 + OVER - RIDGE_X) if x > RIDGE_X else (RIDGE_X - (HX0 - OVER))
    return RIDGE - abs(x - RIDGE_X) / run * (RIDGE - (WALL_TOP - 0.05))


def _stilts(k):
    for x in POSTS_X:
        for z in POSTS_Z:
            k.box(x - 0.08, x + 0.08, STILT_Y, FLOOR - 0.15, z - 0.08, z + 0.08, TIANG)
        k.box(x - 0.1, x + 0.1, FLOOR - 0.33, FLOOR - 0.15, -PZ, PZ, TIANG)             # bearers
    yb, yt = 0.15, FLOOR - 0.4
    for za, zb in ((-2.6, 0.0), (0.0, 2.6)):                                           # X-braces under the veranda
        k.beam((3.1, yb, za), (3.1, yt, zb), 0.045, TIANG)
        k.beam((3.1, yt, za), (3.1, yb, zb), 0.045, TIANG)
    for z in (-2.6, 2.6):                                                              # side braces
        for xa, xb in ((-2.8, -0.9), (-0.9, 1.0), (1.0, 3.1)):
            k.beam((xa, yb, z), (xb, yt, z), 0.045, TIANG)
    k.box(HX0, VX1, FLOOR - 0.15, FLOOR, -PZ, PZ, ABU)                                # floor deck


def _house(k):
    k.box(HX0, HX1, FLOOR, WALL_TOP, -HZ, HZ, ABU)                                     # weathered plank body
    k.box(HX1, HX1 + 0.04, FLOOR, WALL_TOP, -HZ, HZ, TEAL)                             # teal river facade
    k.box(HX1 + 0.04, HX1 + 0.07, 2.85, 3.75, -2.1, 0.5, KACA)                         # dark window band
    for z0, z1 in ((-2.32, -2.1), (0.5, 0.72)):                                        # teal shutters
        k.box(HX1 + 0.04, HX1 + 0.1, 2.85, 3.75, z0, z1, TEAL)
    k.box(HX1 + 0.04, HX1 + 0.08, FLOOR, 3.95, 1.05, 1.95, KAYU)                       # door to the veranda
    pm.tri_prism_z(k, -HZ, HZ, ((HX0 - 0.02, WALL_TOP - 0.02), (HX1 + 0.06, WALL_TOP - 0.02),
                                (RIDGE_X, RIDGE - 0.06)), ABU)                          # board gables
    k.box(HX0 - 0.04, HX0, 2.9, 3.6, -0.8, 0.4, KACA)                                  # back window
    # kitchen lean-to at the back on two stilts
    k.box(HX0 - 1.1, HX0 + 0.02, FLOOR - 0.15, 3.55, -1.5, 1.1, ABU)
    for z in (-1.4, 1.0):
        k.box(HX0 - 1.0, HX0 - 0.84, STILT_Y, FLOOR - 0.15, z - 0.08, z + 0.08, TIANG)
    pts = [(HX0 - 1.3, 3.45, -1.7), (HX0 + 0.02, 3.95, -1.7), (HX0 + 0.02, 3.95, 1.3), (HX0 - 1.3, 3.45, 1.3)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.05, z) for x, y, z in pts], KARAT)
    pm.swap_uv(k, s)


def _roof(k):
    z0, z1 = -HZ - 0.4, HZ + 0.4
    for xe in (HX0 - OVER, HX1 + OVER):
        bot = [(xe, _roof_y(xe), z0), (RIDGE_X, RIDGE, z0), (RIDGE_X, RIDGE, z1), (xe, _roof_y(xe), z1)]
        k.hexa(bot + [(x, y + 0.06, z) for x, y, z in bot], KARAT)
    k.box(RIDGE_X - 0.16, RIDGE_X + 0.16, RIDGE + 0.03, RIDGE + 0.11, z0 - 0.03, z1 + 0.03, ZINC)
    for (xa, xb, za, zb) in ((-2.6, -1.4, -1.6, -0.6), (0.0, 1.2, 0.8, 1.9)):         # newer galvanised patches
        bot = [(xa, _roof_y(xa) + 0.065, za), (xb, _roof_y(xb) + 0.065, za), (xb, _roof_y(xb) + 0.065, zb), (xa, _roof_y(xa) + 0.065, zb)]
        k.hexa(bot + [(x, y + 0.02, z) for x, y, z in bot], ZINC)


def _veranda(k):
    yh, yl = 3.95, 3.35                                                                # lean-to roof
    pts = [(HX1 + 0.05, yh, -PZ - 0.1), (VX1 + 0.25, yl, -PZ - 0.1), (VX1 + 0.25, yl, PZ + 0.1), (HX1 + 0.05, yh, PZ + 0.1)]
    k.hexa(pts + [(x, y + 0.05, z) for x, y, z in pts], KARAT)
    for z in (-PZ + 0.1, PZ - 0.1):
        k.box(VX1 - 0.12, VX1 + 0.02, FLOOR, yl, z - 0.07, z + 0.07, TIANG)
    for z0, z1 in ((-PZ + 0.1, -0.55), (0.55, PZ - 0.1)):                             # front railing (gap for the stair)
        k.box(VX1 - 0.1, VX1, FLOOR + 0.95, FLOOR + 1.02, z0, z1, KAYU)
        k.box(VX1 - 0.1, VX1, FLOOR + 0.45, FLOOR + 0.5, z0, z1, KAYU)
    for z in (-PZ + 0.07, PZ - 0.07):                                                  # side railings
        k.box(HX1, VX1, FLOOR + 0.95, FLOOR + 1.02, z - 0.035, z + 0.035, KAYU)
    # steep stair down to the bank
    for i in range(6):
        x0 = VX1 + 0.38 * i
        top = FLOOR - (FLOOR / 6) * (i + 1)
        k.box(x0, x0 + 0.4, top - 0.06, top, -0.5, 0.5, KAYU)
    for z in (-0.55, 0.55):
        k.beam((VX1, FLOOR - 0.05, z), (VX1 + 2.4, -0.05, z), 0.05, TIANG)
    # orange water tank + clothesline with laundry
    s = len(k.faces)
    k.cylinder(2.7, 2.2, 0.38, FLOOR, FLOOR + 1.0, PALET, seg=8)
    k.cylinder(2.7, 2.2, 0.28, FLOOR + 1.0, FLOOR + 1.1, PALET, seg=8)
    pm.paint(k, s, 12)
    k.beam((HX1 + 0.1, 3.3, -2.5), (VX1 - 0.1, 3.3, -2.5), 0.012, ZINC)
    for i, (x, sw) in enumerate(((1.6, 3), (2.15, 4), (2.65, 9))):
        s = len(k.faces)
        k.box(x - 0.2, x + 0.2, 2.75 - 0.05 * i, 3.28, -2.52, -2.48, PALET)
        pm.paint(k, s, sw)


def build():
    k = MeshKit(uv_tile=2.0)
    _stilts(k)
    _house(k)
    _roof(k)
    _veranda(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
