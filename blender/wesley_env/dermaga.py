"""SM_Env_Dermaga (Wesley) - kampung river port sized for ONE boat: fixed timber jetty +
floating finger pier + a moored wooden boat with two paddles. Dock 400-800 tris.

From Wesley's references: weathered grey timber planks on piles from the bank (pier
photo), a stair down to a floating finger pier with terracotta composite decking, light
grey edging and grey bollards riding on blue HDPE floats (marina photo), tyre bumpers on
the berth side (tracker spec) and one orange-and-teal kampung boat (river-village photos)
moored alongside with two paddles in it. The "DERMAGA / NAIK & TURUN PERAHU DI SINI /
TEKAN [E]" board is an overhead gateway on the bank with 2.4 m of head room.

One FBX, three objects:
    SM_Env_Dermaga          fixed jetty, stair, piles, guide piles, overhead gateway sign
    SM_Env_Dermaga_Ponton   floating finger pier (floats, deck, edging, bollards, tyres, ring)
    SM_Env_Dermaga_Perahu   moored boat + 2 paddles + mooring line
The pontoon and boat origins are the waterline, so PF_Env_Dermaga gives them Ivan's
RiverWaterSurfaceFollower and they rise with the flood.

Contract (MapJsonImporter): 2 "dermaga" nodes (Dermaga Awal west bank, Dermaga Tengah
east bank), groundY 0 = waterline. Bank on local -X (bank top +1.40), river on +X; the
east-bank node needs "rot": 180 in kali-river-map.json to look right (Ivan's data).
"""
import math
import random

from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

NAME = "SM_Env_Dermaga"
PONTON = "SM_Env_Dermaga_Ponton"
PERAHU = "SM_Env_Dermaga_Perahu"
TRI_BUDGET = (400, 800)                  # jetty + pontoon (the boat is a prop on top)

KAYU, TIANG, PONTON_MAT, BESI, PALET, PAPAN, DEK, ZINC, KAYU_PERAHU = range(9)
MATERIALS = (
    ("M_Env_KayuAbu", (0.64, 0.61, 0.56, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_PontonHDPE", (0.16, 0.40, 0.78, 1.0)),
    ("M_Env_BesiGelap", (0.23, 0.24, 0.26, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanUmum", (0.11, 0.42, 0.39, 1.0)),
    ("M_Env_DekKomposit", (0.75, 0.44, 0.29, 1.0)),
    ("M_Env_SengGalvanis", (0.66, 0.68, 0.69, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
)

UV_NAME = pm.px(0, 352, 1024, 512)      # "DERMAGA" board in T_Env_PapanUmum (papan.py)
UV_EDGE = pm.px(800, 800, 1000, 1000)

BED_Y = -2.0
DECK = 1.55                              # jetty deck top (bank top is +1.40)
JX0, JX1, JW = -4.2, 0.0, 1.0            # jetty from the bank to the stair head, half width
PX0, PX1, PW = 1.4, 6.2, 1.05            # floating finger pier: X range, half width
P_TOP = 0.45                             # pier deck above the water
BOAT_Z, BOAT_X0, BOAT_X1 = PW + 0.85, 1.55, 6.15


def _planks(k, rng):
    n = 10
    for i in range(n):
        xa = JX0 + (JX1 - JX0) * (i + 0.05) / n
        xb = JX0 + (JX1 - JX0) * (i + 0.95) / n
        dz, dy, hw = rng.uniform(-0.08, 0.08), rng.uniform(-0.02, 0.02), JW + rng.uniform(-0.06, 0.06)
        k.hexa([(xa, DECK - 0.12, -hw + dz), (xb, DECK - 0.12, -hw + dz), (xb, DECK - 0.12, hw + dz), (xa, DECK - 0.12, hw + dz),
                (xa, DECK + dy, -hw + dz), (xb, DECK - dy, -hw + dz), (xb, DECK - dy, hw + dz), (xa, DECK + dy, hw + dz)], KAYU)


def _jetty(k):
    under = DECK - 0.12
    for z in (-0.75, 0.75):                                                             # stringers
        k.box(JX0, JX1, under - 0.18, under, z - 0.09, z + 0.09, TIANG)
    for x in (-1.3, -0.15):                                                             # piles + cap beams
        for z in (-0.85, 0.85):
            k.box(x - 0.1, x + 0.1, BED_Y, under - 0.18, z - 0.1, z + 0.1, TIANG)
        k.box(x - 0.12, x + 0.12, under - 0.32, under - 0.18, -JW, JW, TIANG)
    k.box(-4.1, -3.8, 1.25, under - 0.18, -JW, JW, TIANG)                               # bank sleeper
    for i in range(4):                                                                  # stair down to the pier
        x0 = JX1 + 0.35 * i
        top = DECK - 0.275 * (i + 1)
        k.box(x0, x0 + 0.37, top - 0.1, top, -0.9, 0.9, KAYU)
    for z in (-0.95, 0.95):
        k.beam((JX1, under, z), (PX0, 0.2, z), 0.07, TIANG)
    for x, z in ((PX1 + 0.25, -PW - 0.2), (PX1 + 0.25, PW + 0.2), (PX0 + 0.3, -PW - 0.2)):  # guide piles
        k.box(x - 0.12, x + 0.12, BED_Y, 2.9, z - 0.12, z + 0.12, TIANG)
        k.box(x - 0.16, x + 0.16, 2.9, 3.0, z - 0.16, z + 0.16, BESI)
    # overhead gateway on the bank: board bottom 2.4 m above the deck (clears a player's head)
    gx = -3.6
    for z in (-1.35, 1.35):
        k.box(gx - 0.11, gx + 0.11, 1.3, 4.75, z - 0.11, z + 0.11, TIANG)
    k.box(gx - 0.13, gx + 0.13, 4.6, 4.78, -1.75, 1.75, TIANG)                         # cross beam
    s = len(k.faces)
    pm.board(k, gx - 0.06, gx + 0.06, DECK + 2.4, DECK + 2.95, -1.76, 1.76, PAPAN, "-x", UV_NAME, UV_EDGE)
    k.uvs[s + pm.FACE["+x"]] = pm.rect_uv(UV_NAME)                                      # readable from the river too
    for z in (-1.1, 1.1):                                                               # hangers
        k.box(gx - 0.02, gx + 0.02, DECK + 2.95, 4.6, z - 0.02, z + 0.02, BESI)


def _tyre_z(k, cx, cy, z0, z1, r, seg=8):
    """Old tyre bumper: octagonal disc with its axis along Z (faces the berth)."""
    ring = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    for i in range(seg):
        (xa, ya), (xb, yb) = ring[i], ring[(i + 1) % seg]
        k._face([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], PALET, [(0, 0)] * 4)
    k._face([(x, y, z0) for x, y in reversed(ring)], PALET, [(0, 0)] * seg)
    k._face([(x, y, z1) for x, y in ring], PALET, [(0, 0)] * seg)


def _ponton(k):
    k.box(PX0 + 0.1, PX1 - 0.1, -0.28, P_TOP - 0.12, -PW + 0.12, PW - 0.12, PONTON_MAT)  # blue HDPE floats
    k.box(PX0, PX1, P_TOP - 0.12, P_TOP, -PW, PW, DEK)                                 # terracotta composite deck
    for z0, z1 in ((-PW - 0.05, -PW + 0.07), (PW - 0.07, PW + 0.05)):                  # light grey edging
        k.box(PX0, PX1, P_TOP - 0.2, P_TOP + 0.02, z0, z1, ZINC)
    k.box(PX1 - 0.07, PX1 + 0.05, P_TOP - 0.2, P_TOP + 0.02, -PW, PW, ZINC)
    for x in (2.1, 4.0, 5.85):                                                          # bollards on the berth side
        k.cylinder(x, PW - 0.2, 0.09, P_TOP, P_TOP + 0.38, ZINC, seg=6)
        k.cylinder(x, PW - 0.2, 0.13, P_TOP + 0.38, P_TOP + 0.45, BESI, seg=6)
    for x in (2.6, 3.9, 5.2):                                                           # tyre bumpers facing the boat
        s = len(k.faces)
        _tyre_z(k, x, 0.15, PW + 0.05, PW + 0.25, 0.28)
        pm.paint(k, s, 2)
    s = len(k.faces)                                                                    # yellow life ring
    k.torus_y(PX1 - 0.55, P_TOP + 0.06, -PW + 0.45, 0.3, 0.07, PALET, seg=8, ring=4)
    pm.paint(k, s, 9)


def _perahu(k):
    """Kampung wooden boat: orange hull, teal gunwale, plank floor, two thwarts, two paddles."""
    zc, xm0, xm1 = BOAT_Z, 2.75, 4.95
    yb, yt, hb, ht = -0.22, 0.42, 0.3, 0.62
    s = len(k.faces)
    k.hexa([(xm0, yb, zc - hb), (xm1, yb, zc - hb), (xm1, yb, zc + hb), (xm0, yb, zc + hb),
            (xm0, yt, zc - ht), (xm1, yt, zc - ht), (xm1, yt, zc + ht), (xm0, yt, zc + ht)], PALET)
    for xe, xm, sg in ((BOAT_X1, xm1, 1), (BOAT_X0, xm0, -1)):                         # upswept pointed ends
        xm_in = xm - sg * 0.003
        k.hexa([(xm_in, yb, zc - hb), (xe - sg * 0.25, yb + 0.25, zc - 0.03), (xe - sg * 0.25, yb + 0.25, zc + 0.03), (xm_in, yb, zc + hb),
                (xm_in, yt, zc - ht), (xe, yt + 0.22, zc - 0.04), (xe, yt + 0.22, zc + 0.04), (xm_in, yt, zc + ht)], PALET)
    pm.paint(k, s, 12)
    for f in (s + 1, s + 7, s + 13):                                                    # top faces = plank floor
        k.mats[f] = KAYU_PERAHU
        k.uvs[f] = [(p[0] * 0.5, p[2] * 0.5) for p in (k.verts[i] for i in k.faces[f])]
    for z in (zc - ht + 0.04, zc + ht - 0.04):                                          # teal gunwale strakes
        s = len(k.faces)
        k.box(xm0 - 0.3, xm1 + 0.3, yt - 0.02, yt + 0.08, z - 0.05, z + 0.05, PALET)
        pm.paint(k, s, 13)
    for x in (3.3, 4.4):                                                                # thwart seats
        k.box(x - 0.13, x + 0.13, yt + 0.02, yt + 0.07, zc - ht + 0.05, zc + ht - 0.05, KAYU_PERAHU)
    for i, (x0, x1, z) in enumerate(((2.55, 4.85, zc - 0.22), (2.9, 5.15, zc + 0.2))):  # two paddles (dayung)
        y = yt + 0.1 + i * 0.03
        k.beam((x0, y, z), (x1 - 0.5, y, z + 0.05 * (1 - 2 * i)), 0.025, TIANG)
        k.box(x1 - 0.55, x1, y - 0.015, y + 0.015, z - 0.09, z + 0.09, KAYU_PERAHU)
    k.beam((BOAT_X1 - 0.2, yt + 0.25, zc), (5.85, P_TOP + 0.3, PW - 0.2), 0.02, TIANG)  # mooring line to the bollard


def build():
    rng = random.Random(1210)
    jetty = MeshKit(uv_tile=2.0)
    _planks(jetty, rng)
    _jetty(jetty)
    ponton = MeshKit(uv_tile=2.0)
    _ponton(ponton)
    perahu = MeshKit(uv_tile=2.0)
    _perahu(perahu)
    return [jetty.build(NAME, MATERIALS), ponton.build(PONTON, MATERIALS), perahu.build(PERAHU, MATERIALS)]


def stats(obs):
    tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs}
    dock = tris.get(NAME, 0) + tris.get(PONTON, 0)
    lo, hi = TRI_BUDGET
    return {"name": NAME, "tris": tris, "dock_total": dock, "in_budget": lo <= dock <= hi}
