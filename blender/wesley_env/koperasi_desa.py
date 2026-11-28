"""SM_Env_KoperasiDesa (Wesley) - Koperasi Desa (Kopdes) upgrade & supply hall, 800-1,200 tris.

Look from Wesley's references (the new village co-op halls): one long single-storey
white rendered block under a low maroon gable with a bright galvanised zinc fascia and a
dark ventilation band; from left to right (seen from the river) an open carport with red
sliding doors at the back, a grey signage wall (red house emblem, KOPERASI DESA, MERAH
PUTIH) and a covered veranda with a row of red roller shutters on white columns.

Gameplay reading (tracker: "hub for vessels, Kampung Bins & Trash Boom"):
    - a wooden sampan on trestles in the carport  -> boat upgrades
    - one roller shutter open: counter + shelves  -> the shop
    - colour drum bins + an orange boom float out front -> Kampung Bins / Trash Boom
    - banner under the veranda: PERAHU / TONG KAMPUNG / TRASH BOOM

Contract (MapJsonImporter): node "Koperasi Desa (Kopdes)" map (195, 1085) -> Unity
(-40.6, 1.40, 45.6), rot 0, groundY = BankTopY 1.40. Pivot = bottom centre at Y 0, the
plinth skirts down to -0.5 m. Front (+X) faces the river; Bank Sampah sits 12.5 m to +Z.
"""
import math

from wesley_env.bank_sampah import _paint, _rect_uv, _set_uv
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_KoperasiDesa"
TRI_BUDGET = (800, 1200)

TEMBOK, SENG_MERAH, SENG_ZINC, PINTU, BESI, KAYU, PALET, PAPAN, BETON = range(9)
MATERIALS = (
    ("M_Env_TembokPutih", (0.86, 0.85, 0.82, 1.0)),
    ("M_Env_SengMerah", (0.56, 0.20, 0.19, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_PintuMerah", (0.70, 0.15, 0.16, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanKopdes", (0.55, 0.56, 0.57, 1.0)),
    ("M_Env_BetonPutih", (0.73, 0.71, 0.66, 1.0)),
)

# ---- layout (metres, Unity axes; viewer at +X sees -Z on the left, +Z on the right) ----
# Footprint ~8.5 x 16.8 m (~143 m2) = about 3x a Warung Madura (7.75 x 6.25 m, Wesley's brief).
# The hall grows toward -Z (free bank up to Rumah Kota Barat 3) because Bank Sampah's slab
# starts 6.9 m to +Z; Rumah Pak RT limits the back, the banana tree limits the front.
PLINTH = 0.25
XB, XF = -4.6, 2.6               # back wall / front face of carport + sign wall
CAR_DEPTH = 3.6                  # carport recess (back wall at XF - CAR_DEPTH)
X_SHOP = 1.0                     # set-back shutter wall behind the veranda
SHOP_DEPTH = 1.2                 # shutter bays / open shop recess depth
X_COL = 2.5                      # veranda column line
Z0, Z1 = -11.0, 5.0
Z_CAR, Z_SIGN = -6.0, -3.2       # carport | sign wall | shop bays
WALL_TOP, BAND_TOP = 3.3, 3.7
RIDGE_X, RIDGE_Y, EAVE_Y, OVER = (XB + XF) * 0.5, 4.7, 3.78, 0.5
N_BAYS = 5
BAYS = tuple((Z_SIGN + (Z1 - Z_SIGN) * i / N_BAYS, Z_SIGN + (Z1 - Z_SIGN) * (i + 1) / N_BAYS) for i in range(N_BAYS))
OPEN_BAY = 2
VER_HI, VER_LO = 3.05, 2.8       # veranda awning height at the wall / at the front

ATLAS = 1024.0


def _px(x0, y0, x1, y1):
    return (x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS)


UV_SIGN = _px(0, 0, 512, 640)            # sign wall art (portrait 0.8 : 1)
UV_BANNER = _px(0, 656, 1024, 728)       # veranda banner (14 : 1)
UV_GREY = _px(600, 100, 900, 500)        # plain grey render for the sign wall's other faces


def _uv_all(k, start, rect):
    u0, v0, u1, v1 = rect
    for f in range(start, len(k.faces)):
        _set_uv(k, f, [((u0 + u1) * 0.5, (v0 + v1) * 0.5)] * len(k.faces[f]))


def _tube_z(k, cx, cy, z0, z1, r, mat, seg=8):
    """Horizontal round tube along Z (boom float)."""
    ring = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    for i in range(seg):
        (xa, ya), (xb, yb) = ring[i], ring[(i + 1) % seg]
        k._face([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], mat, [(0, 0)] * 4)
    k._face([(x, y, z0) for x, y in reversed(ring)], mat, [(0, 0)] * seg)
    k._face([(x, y, z1) for x, y in ring], mat, [(0, 0)] * seg)


def _gable_end(k, z, t):
    """Triangular zinc-clad gable between the vent band and the roof, thickness t along Z."""
    tri = [(XB - 0.05, BAND_TOP), (XF + 0.05, BAND_TOP), (RIDGE_X, RIDGE_Y - 0.06)]
    za, zb = z - t * 0.5, z + t * 0.5
    k._face([(x, y, za) for x, y in tri], SENG_ZINC, [(x, y) for x, y in tri])
    k._face([(x, y, zb) for x, y in reversed(tri)], SENG_ZINC, [(x, y) for x, y in reversed(tri)])
    for i in range(3):
        (xa, ya), (xb, yb) = tri[i], tri[(i + 1) % 3]
        k._face([(xa, ya, za), (xa, ya, zb), (xb, yb, zb), (xb, yb, za)], SENG_ZINC,
                [(0, ya), (t, ya), (t, yb), (0, yb)])


def _shell(k):
    y0, xc = PLINTH, XF - CAR_DEPTH
    xs = X_SHOP - SHOP_DEPTH
    k.box(XB - 0.3, X_COL + 0.95, -0.5, PLINTH, Z0 - 0.3, Z1 + 0.3, BETON)            # plinth / step
    k.box(XB, xc, y0, WALL_TOP, Z0, Z_CAR, TEMBOK)                                    # behind the carport
    for z in (Z0, Z_CAR - 0.2):                                                       # carport side walls
        k.box(xc - 0.02, XF, y0, WALL_TOP, z, z + 0.2, TEMBOK)
    k.box(xc - 0.02, XF - 0.01, 2.95, WALL_TOP - 0.01, Z0 + 0.19, Z_CAR - 0.19, TEMBOK)  # carport lintel
    za, zb = Z0 + 0.5, Z_CAR - 0.5                                                    # red sliding doors
    k.box(xc, xc + 0.06, y0, 2.8, za, (za + zb) * 0.5 - 0.02, PINTU)
    k.box(xc, xc + 0.06, y0, 2.8, (za + zb) * 0.5 + 0.02, zb, PINTU)
    s = len(k.faces)                                                                  # grey sign wall
    k.box(XB, XF, y0, WALL_TOP, Z_CAR - 0.01, Z_SIGN + 0.01, PAPAN)
    _uv_all(k, s, UV_GREY)
    _set_uv(k, s + 1, _rect_uv(UV_SIGN))                                              # +X face = sign art
    k.box(XB, xs, y0, WALL_TOP, Z_SIGN, Z1, TEMBOK)                                   # shop block behind the bays
    for i, (za, zb) in enumerate(BAYS):
        if i == OPEN_BAY:
            k.box(xs - 0.02, X_SHOP, 2.85, WALL_TOP - 0.01, za - 0.01, zb + 0.01, TEMBOK)  # head over the open bay
        else:
            k.box(xs - 0.02, X_SHOP, y0, WALL_TOP, za, zb, TEMBOK)
            k.box(X_SHOP, X_SHOP + 0.04, y0, 2.86, za + 0.12, zb - 0.12, PINTU)       # closed roller shutter
        k.box(X_SHOP, X_SHOP + 0.16, 2.84, 3.04, za + 0.08, zb - 0.08, PINTU)        # shutter roll box
    k.box(XB - 0.01, XF + 0.01, WALL_TOP - 0.01, BAND_TOP, Z0 - 0.01, Z1 + 0.01, BESI)  # dark ventilation band


def _roof(k):
    xe0, xe1, z0, z1 = XB - OVER, XF + OVER, Z0 - 0.35, Z1 + 0.35

    def slope(xe, a, b, mat):
        pts = [(xe, EAVE_Y, z0), (RIDGE_X, RIDGE_Y, z0), (RIDGE_X, RIDGE_Y, z1), (xe, EAVE_Y, z1)]
        k.hexa([(x, y + a, z) for x, y, z in pts] + [(x, y + b, z) for x, y, z in pts], mat)

    for xe in (xe0, xe1):
        slope(xe, 0.0, 0.05, SENG_MERAH)
        slope(xe, -0.055, -0.008, SENG_ZINC)
        k.box(xe - 0.04 if xe > 0 else xe, xe + 0.04 if xe > 0 else xe + 0.08,
              EAVE_Y - 0.26, EAVE_Y + 0.08, z0, z1, SENG_ZINC)                        # bright zinc fascia
    for z in (Z0, Z1):
        _gable_end(k, z, 0.06)
    k.box(RIDGE_X - 0.18, RIDGE_X + 0.18, RIDGE_Y + 0.03, RIDGE_Y + 0.11, z0 - 0.03, z1 + 0.03, SENG_ZINC)


def _veranda(k):
    za, zb = Z_SIGN, Z1 + 0.1
    hi, lo, xe = VER_HI, VER_LO, X_COL + 0.3
    pts = [(X_SHOP, hi, za), (xe, lo, za), (xe, lo, zb), (X_SHOP, hi, zb)]
    k.hexa([(x, y, z) for x, y, z in pts] + [(x, y + 0.045, z) for x, y, z in pts], SENG_MERAH)
    k.hexa([(x, y - 0.05, z) for x, y, z in pts] + [(x, y - 0.008, z) for x, y, z in pts], SENG_ZINC)
    cols = [Z_SIGN + 0.15] + [b for _, b in BAYS[:-1]] + [Z1 - 0.15]
    for z in cols:                                                                    # white columns
        k.box(X_COL - 0.14, X_COL + 0.14, PLINTH, lo - 0.05, z - 0.14, z + 0.14, TEMBOK)
    k.box(X_COL - 0.1, X_COL + 0.1, lo - 0.2, lo - 0.05, za, zb, TEMBOK)              # beam over the columns
    s = len(k.faces)                                                                   # banner on the beam
    bz = (BAYS[OPEN_BAY][0] + BAYS[OPEN_BAY][1]) * 0.5
    k.box(X_COL + 0.16, X_COL + 0.2, lo - 0.45, lo - 0.1, bz - 2.45, bz + 2.45, PAPAN)
    _uv_all(k, s, UV_GREY)
    _set_uv(k, s + 1, _rect_uv(UV_BANNER))


def _shop_goods(k):
    za, zb = BAYS[OPEN_BAY]
    xb = X_SHOP - SHOP_DEPTH
    k.box(X_SHOP - 0.15, X_SHOP + 0.25, PLINTH, 1.0, za + 0.2, zb - 0.2, KAYU)         # counter
    for y in (1.15, 1.75, 2.35):                                                      # back shelves
        k.box(xb + 0.02, xb + 0.42, y, y + 0.05, za + 0.1, zb - 0.1, KAYU)
    goods = ((1.2, 8, 0.25), (1.2, 12, 0.22), (1.8, 9, 0.26), (1.8, 4, 0.2), (2.4, 6, 0.24), (2.4, 3, 0.2))
    for i, (y, sw, h) in enumerate(goods):                                            # paint cans / boxes
        s = len(k.faces)
        zc = za + 0.4 + (i % 2) * 0.8
        k.box(xb + 0.08, xb + 0.36, y + 0.05, y + 0.05 + h, zc - 0.17, zc + 0.17, PALET)
        _paint(k, s, sw)
    # Kampung Bins: three colour drum bins on the veranda, last bay
    for i, sw in enumerate((6, 9, 8)):
        s = len(k.faces)
        k.cylinder(X_COL - 0.6, BAYS[-1][0] + 0.4 + i * 0.42, 0.18, PLINTH, PLINTH + 0.62, PALET, seg=8)
        _paint(k, s, sw)
    # Trash Boom: orange floats on the plinth in front of the first bays
    for i in range(3):
        s = len(k.faces)
        z0 = Z_SIGN + 0.3 + i * 1.5
        _tube_z(k, X_COL + 0.62, PLINTH + 0.16, z0, z0 + 1.4, 0.16, PALET)
        _paint(k, s, 12)


def _sampan(k):
    """Small wooden sampan on two trestles in the carport (boat upgrades)."""
    cx, cz, y = XF - CAR_DEPTH * 0.5, (Z0 + Z_CAR) * 0.5, PLINTH + 0.55
    for tz in (cz - 1.0, cz + 1.0):
        k.box(cx - 0.55, cx + 0.55, y - 0.08, y, tz - 0.06, tz + 0.06, KAYU)
        for tx in (cx - 0.45, cx + 0.45):
            k.box(tx - 0.04, tx + 0.04, PLINTH, y - 0.08, tz - 0.04, tz + 0.04, KAYU)
    hb, ht, half = 0.2, 0.52, 1.3
    k.hexa([(cx - hb, y, cz - half), (cx + hb, y, cz - half), (cx + hb, y, cz + half), (cx - hb, y, cz + half),
            (cx - ht, y + 0.42, cz - half), (cx + ht, y + 0.42, cz - half),
            (cx + ht, y + 0.42, cz + half), (cx - ht, y + 0.42, cz + half)], KAYU)
    for s in (-1, 1):                                                                 # raised pointed ends
        zt, ze = cz + s * (half + 0.55), cz + s * (half - 0.003)
        k.hexa([(cx - hb, y, ze), (cx + hb, y, ze), (cx + 0.02, y + 0.12, zt), (cx - 0.02, y + 0.12, zt),
                (cx - ht, y + 0.42, ze), (cx + ht, y + 0.42, ze),
                (cx + 0.03, y + 0.58, zt), (cx - 0.03, y + 0.58, zt)], KAYU)


def _details(k):
    y0 = PLINTH
    for z in (Z0 + 0.12, Z1 - 0.12):                                                  # white PVC downpipes
        k.box(XF + 0.03, XF + 0.13, y0, EAVE_Y - 0.1, z - 0.05, z + 0.05, TEMBOK)
    k.box(XF - 2.2, XF - 0.8, 1.0, 2.15, Z_CAR - 0.04, Z_CAR - 0.01, BESI)            # dark window in the carport
    k.box(XB + 0.8, XB + 1.8, y0, 2.4, Z1, Z1 + 0.03, PINTU)                          # side door on the +Z end
    k.hexa([(XF, PLINTH, Z0 + 0.2), (XF + 0.9, -0.02, Z0 + 0.2), (XF + 0.9, -0.02, Z_CAR - 0.2), (XF, PLINTH, Z_CAR - 0.2),
            (XF, PLINTH + 0.01, Z0 + 0.2), (XF + 0.9, 0.0, Z0 + 0.2), (XF + 0.9, 0.0, Z_CAR - 0.2), (XF, PLINTH + 0.01, Z_CAR - 0.2)],
           BETON)                                                                     # carport ramp
    for za, zb in BAYS[1::2]:                                                         # veranda lamps
        z = (za + zb) * 0.5
        k.box(X_SHOP + 0.02, X_SHOP + 0.14, 2.55, 2.7, z - 0.08, z + 0.08, SENG_ZINC)


def build():
    k = MeshKit(uv_tile=2.0)
    _shell(k)
    _roof(k)
    _veranda(k)
    _shop_goods(k)
    _sampan(k)
    _details(k)
    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
