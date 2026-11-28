"""SM_Env_KarantinaBiohazard (Wesley) - biohazard / radioactive quarantine bunker, 1,000-1,600 tris.

Wesley chose the signage (yellow quarantine / biohazard warning signs) and left the
building to me; the form is a sealed, low reinforced-concrete bunker so it reads as the
most dangerous station at a glance: chamfered roof, an airlock with a hazard-striped
steel blast door, filtered exhaust stacks + HEPA box, a lime warning beacon, a purple
accent band (docs/DESIGN.md 2.4: Karantina = #A855F7 + #84CC16), yellow B3 drums on
pallets at the drop-off and a chain-link fence with PERINGATAN signs and a striped boom.

Readability for players: "KARANTINA BIOHAZARD / SETOR DRUM BIOHAZARD & RADIOAKTIF DI SINI"
board over the airlock, PERINGATAN biohazard signs on the fence and the bunker, a
RADIOAKTIF sign beside the door.

Contract (MapJsonImporter): node "Karantina Biohazard" map (760, 475) -> Unity
(30.0, 1.40, -30.6) on the EAST bank, rot 0, groundY = BankTopY 1.40. The river is on the
building's -X side, so the bunker is authored facing +X and turned 180 degrees about Y at
the end (TURN_180): the airlock, signs and fence gate face the river. Pivot = bottom
centre at Y 0, slab skirts to -0.5 m.
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_KarantinaBiohazard"
TRI_BUDGET = (1000, 1600)
TURN_180 = True

BETON, BESI, ZINC, KAWAT, KAYU, PALET, PAPAN = range(7)
MATERIALS = (
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_KawatJaring", (0.30, 0.31, 0.31, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanKarantina", (0.92, 0.70, 0.03, 1.0)),
)

UV_MAIN = pm.px(0, 0, 1024, 180)
UV_WARN = pm.px(0, 224, 512, 736)
UV_RAD = pm.px(528, 224, 784, 480)
UV_STRIPES = pm.px(528, 496, 1024, 752)
UV_PURPLE = pm.px(800, 800, 900, 900)
UV_LIME = pm.px(900, 800, 1000, 900)
UV_DARK = pm.px(800, 900, 1000, 1000)

Y0 = 0.2
BX0, BX1, BZ = -4.2, 1.4, 4.6          # bunker
WALL_TOP, ROOF_TOP, CHAMFER = 4.0, 4.6, 0.5
AX1, AZ = 3.4, 1.5                     # airlock front / half width
FX = 5.0                               # fence line
FENCE_Z = (-5.4, -3.6, -1.8, 1.8, 3.6, 5.4)


def _sub(rect, fu, fv):
    u0, v0, u1, v1 = rect
    return (u0, v0, u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv)


def _wire(k, corners):
    a, b = corners[0], corners[1]
    uv = [(p[2], p[1]) for p in corners] if abs(a[0] - b[0]) < 1e-6 else [(p[0], p[1]) for p in corners]
    k._face(list(corners), KAWAT, uv)


def _bunker(k):
    k.box(BX0, BX1, Y0, WALL_TOP, -BZ, BZ, BETON)
    c = CHAMFER
    k.hexa([(BX0, WALL_TOP - 0.02, -BZ), (BX1, WALL_TOP - 0.02, -BZ), (BX1, WALL_TOP - 0.02, BZ), (BX0, WALL_TOP - 0.02, BZ),
            (BX0 + c, ROOF_TOP, -BZ + c), (BX1 - c, ROOF_TOP, -BZ + c), (BX1 - c, ROOF_TOP, BZ - c), (BX0 + c, ROOF_TOP, BZ - c)],
           BETON)                                                                       # chamfered blast roof
    s = len(k.faces)
    k.box(BX0 - 0.03, BX1 + 0.03, 2.85, 3.1, -BZ - 0.03, BZ + 0.03, PAPAN)              # purple accent band
    pm.flat(k, s, UV_PURPLE)
    for z in (-3.2, -1.6, 1.6, 3.2):                                                   # exhaust louvres (back)
        k.box(BX0 - 0.05, BX0, 1.6, 2.2, z - 0.45, z + 0.45, BESI)
    # roof plant: two filtered exhaust stacks + HEPA box
    for z in (-2.6, 2.6):
        k.cylinder(-3.0, z, 0.18, ROOF_TOP - 0.02, 5.7, ZINC, seg=6)
        k.cylinder(-3.0, z, 0.28, 5.7, 5.85, ZINC, seg=6)
    k.box(-1.9, -0.6, ROOF_TOP - 0.02, 5.25, -0.7, 0.7, ZINC)
    # signs on the bunker face
    pm.board(k, BX1, BX1 + 0.06, 3.3, 3.95, -1.85, 1.85, PAPAN, "+x", UV_MAIN, UV_DARK)
    pm.board(k, BX1, BX1 + 0.04, 1.3, 2.1, 2.2, 3.0, PAPAN, "+x", UV_RAD, UV_DARK)
    pm.board(k, BX1, BX1 + 0.04, 1.15, 2.15, -3.1, -2.1, PAPAN, "+x", UV_WARN, UV_DARK)


def _airlock(k):
    k.box(BX1 - 0.02, AX1, Y0, 2.9, -AZ, AZ, BETON)
    k.box(BX1 - 0.02, AX1 + 0.15, 2.9, 3.1, -AZ - 0.15, AZ + 0.15, BETON)             # canopy slab
    k.box(AX1, AX1 + 0.07, Y0, 2.3, -0.8, 0.8, BESI)                                  # blast door
    k.box(AX1 + 0.07, AX1 + 0.15, 1.0, 1.5, 0.45, 0.6, BESI)                          # locking lever
    for z0, z1 in ((-1.05, -0.8), (0.8, 1.05)):                                       # striped door jambs
        s = len(k.faces)
        k.box(AX1, AX1 + 0.1, Y0, 2.55, z0, z1, PAPAN)
        pm.stretch(k, s, _sub(UV_STRIPES, 0.14, 1.0))
    s = len(k.faces)
    k.box(AX1, AX1 + 0.1, 2.3, 2.55, -0.8, 0.8, PAPAN)                                # striped header
    pm.stretch(k, s, _sub(UV_STRIPES, 1.0, 0.16))
    s = len(k.faces)
    k.cylinder(FX + 0.02, -1.875, 0.13, 1.15, 1.45, PAPAN, seg=6)                     # lime warning beacon on the boom housing
    pm.flat(k, s, UV_LIME)


def _dropoff(k):
    """Yellow B3 drums on pallets either side of the airlock (where players unload)."""
    for zs in (-1, 1):
        k.box(1.75, 3.2, Y0, Y0 + 0.14, zs * 1.85, zs * 3.4, KAYU)
        for dx in (2.1, 2.8):
            for dz in (2.25, 2.95):
                s = len(k.faces)
                k.cylinder(dx, zs * dz, 0.28, Y0 + 0.14, Y0 + 1.0, PALET, seg=8)
                pm.paint(k, s, 9)


def _fence(k):
    for z in FENCE_Z:
        k.box(FX - 0.05, FX + 0.05, Y0, 2.35, z - 0.05, z + 0.05, BESI)
    for x in (2.2, 3.6):
        for z in (-5.4, 5.4):
            k.box(x - 0.05, x + 0.05, Y0, 2.35, z - 0.05, z + 0.05, BESI)
    for za, zb in ((-5.4, -1.8), (1.8, 5.4)):
        k.box(FX - 0.03, FX + 0.03, 2.2, 2.28, za, zb, BESI)
        _wire(k, [(FX, Y0 + 0.05, za), (FX, Y0 + 0.05, zb), (FX, 2.2, zb), (FX, 2.2, za)])
    for z in (-5.4, 5.4):
        k.box(BX1, FX, 2.2, 2.28, z - 0.03, z + 0.03, BESI)
        _wire(k, [(BX1, Y0 + 0.05, z), (FX, Y0 + 0.05, z), (FX, 2.2, z), (BX1, 2.2, z)])
    for z in (-3.6, 3.6):                                                             # PERINGATAN signs
        pm.board(k, FX + 0.05, FX + 0.09, 1.0, 1.9, z - 0.45, z + 0.45, PAPAN, "+x", UV_WARN, UV_DARK)
    s = len(k.faces)                                                                   # raised striped boom
    k.beam((FX + 0.1, 1.1, -1.8), (FX + 0.1, 3.2, -2.7), 0.06, PAPAN)                 # leans away from the gate
    pm.stretch(k, s, _sub(UV_STRIPES, 1.0, 0.12))
    k.box(FX - 0.2, FX + 0.25, Y0, 1.15, -2.1, -1.65, BESI)                           # boom housing
    k.box(4.55, 4.65, Y0, 4.4, 5.0, 5.1, BESI)                                        # floodlight pole
    k.box(4.2, 4.7, 4.25, 4.5, 4.85, 5.25, ZINC)


def _extras(k):
    for z in (-2.9, 0.0, 2.9):                                                        # buttresses on the back wall
        k.hexa([(BX0, Y0, z - 0.35), (BX0, Y0, z + 0.35), (BX0 - 0.9, Y0, z + 0.35), (BX0 - 0.9, Y0, z - 0.35),
                (BX0, 2.4, z - 0.35), (BX0, 2.4, z + 0.35), (BX0 - 0.05, 2.4, z + 0.35), (BX0 - 0.05, 2.4, z - 0.35)], BETON)
    gx = 4.3                                                                          # decontamination shower arch at the gate
    for z in (-1.3, 1.3):
        k.box(gx - 0.06, gx + 0.06, Y0, 2.6, z - 0.06, z + 0.06, ZINC)
    k.box(gx - 0.06, gx + 0.06, 2.5, 2.62, -1.3, 1.3, ZINC)
    for z in (-0.6, 0.6):
        k.box(gx - 0.08, gx + 0.08, 2.32, 2.5, z - 0.08, z + 0.08, ZINC)
    for za, zb in ((-5.4, -1.8), (1.8, 5.4)):                                         # razor wire zig-zag on the fence
        n = 4
        for i in range(n):
            z0, z1 = za + (zb - za) * i / n, za + (zb - za) * (i + 1) / n
            k.beam((FX, 2.3 + 0.18 * (i % 2), z0), (FX, 2.3 + 0.18 * ((i + 1) % 2), z1), 0.02, ZINC)


def build():
    k = MeshKit(uv_tile=2.0)
    k.box(-4.8, 5.6, -0.5, Y0, -5.8, 5.8, BETON)                                      # slab
    _bunker(k)
    _airlock(k)
    _dropoff(k)
    _fence(k)
    _extras(k)
    if TURN_180:                                                                       # face the river (-X)
        k.verts = [(-x, y, -z) for x, y, z in k.verts]
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
