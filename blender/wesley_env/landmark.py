"""SM_Env_Landmark (Wesley) - Priority 0 quest landmarks + wayfinding (docs/PROGRESSION_REDESIGN.md).

One FBX, one object per piece (Unity coordinates, +X = toward the river / the reader):
  SM_Env_TanggaCuci            Bu Siti's concrete washing steps (Q2 Jarum di Tangga Cuci).
                               Pivot: x = 0 on the talud top edge, y = 0 = waterline, z = centre.
                               Treads TIERS_Y step down the 45 deg talud to a washing landing.
  SM_Env_TanggaCuci_Sampah     litter + scum on the steps, shown only while the river is dirty
  SM_Env_TiangNyangkut         Pak Darto's snag at jetty 2 (Q3 Kail Nyangkut): old pilings, a
                               bamboo stake, a sunken branch and a torn net; pivot y = 0 waterline.
                               SNAG_POSTS are the wrap points for JC's PF_Prop_KailKusut.
  SM_Env_TiangNyangkut_Sampah  plastic caught on the snag (dirty river only)
  SM_Env_WarungStall_Barat/_Timur  lapak: counter, long bench, striped tarp on bamboo poles,
                               jars + thermos; pivot ground centre, customers stand on +X.
  SM_Env_PosRonda              Pak RT's pos ronda (raised bale-bale, seng roof, kentongan) with
                               the RT notice board (sorting poster = tutorial); pivot ground centre.
  SM_Env_TiangPapanArah        wayfinding post (pivot ground centre)
  SM_Env_PanahMedis/_Karantina/_BankSampah  arrow boards pointing +X (pivot on the post axis,
                               y = 0 = board bottom); the Unity builder stacks and aims them.
Signs read from both sides (the back face mirrors U so the text is never reversed).
"""
import math
import random

from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_Landmark"
NAME = "SM_Env_TanggaCuci"
TRI_BUDGET = (12, 1600)

BETON, KAYU, TIANG, BESI, SENG, BAMBU, PALET, PAPAN, JARING, BATU = range(10)
MATERIALS = (
    ("M_Env_TaludBeton", (0.62, 0.62, 0.60, 1.0)),
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_BesiGelap", (0.16, 0.17, 0.18, 1.0)),
    ("M_Env_SengKarat", (0.54, 0.39, 0.27, 1.0)),
    ("M_Env_Bambu", (0.70, 0.72, 0.40, 1.0)),
    ("M_Env_TrashPieces", (0.70, 0.70, 0.70, 1.0)),
    ("M_Env_PapanLandmark", (0.93, 0.93, 0.93, 1.0)),
    ("M_Env_KawatJaring", (0.60, 0.60, 0.60, 1.0)),
    ("M_Env_BatuKali", (0.62, 0.60, 0.56, 1.0)),
)

R = {k: pm.px(*v) for k, v in {
    "tangga": (0, 0, 1024, 160), "ronda": (0, 176, 1024, 336),
    "warung_barat": (0, 352, 512, 480), "warung_timur": (512, 352, 1024, 480),
    "arah_medis": (0, 496, 512, 624), "arah_karantina": (512, 496, 1024, 624),
    "arah_bank": (0, 640, 512, 768), "awas_tiang": (512, 640, 1024, 768),
    "pengumuman": (0, 784, 640, 1024),
    "edge_wood": (672, 784, 848, 904), "edge_dark": (848, 784, 1024, 904),
}.items()}

BANK_Y = 1.40
TIERS_Y = [1.40, 1.20, 1.00, 0.80, 0.60, 0.40, 0.18]      # top slab .. washing landing (world Y)
STEP_RUN = 0.32
LANDING_X = (6 * STEP_RUN, 6 * STEP_RUN + 1.5)           # landing in front of the last riser
NEEDLE_SPOT = (LANDING_X[0] + 1.05, TIERS_Y[-1], -1.15)  # clear corner for JC's PF_Prop_KotakJarum
SNAG_POSTS = [(0.0, 0.0, 1.05), (0.95, 0.55, 0.62), (0.35, -0.85, 0.88), (1.55, -0.2, 0.40), (-0.45, 0.95, 0.55)]


def mirrored(rect):
    u0, v0, u1, v1 = rect
    return [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]


def sign(k, x0, x1, y0, y1, z0, z1, face, rect, edge=R["edge_wood"]):
    """Board readable from `face` and (mirrored) from the opposite face."""
    s = len(k.faces)
    pm.board(k, x0, x1, y0, y1, z0, z1, PAPAN, face, rect, edge)
    back = {"+x": "-x", "-x": "+x", "+z": "-z", "-z": "+z"}[face]
    k.uvs[s + pm.FACE[back]] = mirrored(rect)


def swatch(k, start, idx):
    pm.paint(k, start, idx)


# ---------------- Tangga Cuci ----------------

def tangga_cuci():
    k = MeshKit(uv_tile=1.0)
    hw = 1.0                                                                               # stair half width
    k.box(-0.7, 0.0, -0.4, TIERS_Y[0] + 0.04, -hw - 0.25, hw + 0.25, BETON)                 # top slab on the bank
    for i in range(1, 7):
        x0, x1 = (i - 1) * STEP_RUN, i * STEP_RUN
        k.box(x0, x1, -1.2, TIERS_Y[i] + 0.02, -hw, hw, BETON)
        k.box(x0, x0 + 0.05, TIERS_Y[i] + 0.02 - 0.03, TIERS_Y[i] + 0.025, -hw, hw, BATU)  # worn nosing
    lx0, lx1 = LANDING_X
    k.box(lx0, lx1, -1.6, TIERS_Y[-1] + 0.02, -1.6, 1.6, BETON)                            # washing landing
    for z in (-hw - 0.13, hw + 0.13):                                                      # cheek walls on the slope
        c = [(-0.7, -0.4, z - 0.12), (lx0, -1.2, z - 0.12), (lx0, -1.2, z + 0.12), (-0.7, -0.4, z + 0.12)]
        top = [(-0.7, TIERS_Y[0] + 0.3, z - 0.12), (lx0, TIERS_Y[-1] + 0.42, z - 0.12), (lx0, TIERS_Y[-1] + 0.42, z + 0.12), (-0.7, TIERS_Y[0] + 0.3, z + 0.12)]
        k.hexa(c + top, BETON)
    for x in (-0.4, 0.95, lx0 - 0.05):                                                     # galvanised handrail (river right)
        y = TIERS_Y[0] + 0.3 - (x + 0.7) / (lx0 + 0.7) * (TIERS_Y[0] - TIERS_Y[-1] - 0.12)
        k.box(x - 0.025, x + 0.025, y, y + 0.85, hw + 0.105, hw + 0.155, BESI)
    k.beam((-0.4, TIERS_Y[0] + 1.17, hw + 0.13), (lx0 - 0.05, TIERS_Y[-1] + 1.27, hw + 0.13), 0.025, BESI)
    for z, tilt in ((0.55, 0.10), (-0.3, 0.07)):                                           # flat scrubbing stones
        x = lx0 + 0.55
        c = [(x - 0.32, TIERS_Y[-1] + 0.02, z - 0.26), (x + 0.32, TIERS_Y[-1] + 0.02, z - 0.26),
             (x + 0.32, TIERS_Y[-1] + 0.02, z + 0.26), (x - 0.32, TIERS_Y[-1] + 0.02, z + 0.26)]
        top = [(x - 0.32, TIERS_Y[-1] + 0.18, z - 0.26), (x + 0.32, TIERS_Y[-1] + 0.18 - tilt, z - 0.26),
               (x + 0.32, TIERS_Y[-1] + 0.18 - tilt, z + 0.26), (x - 0.32, TIERS_Y[-1] + 0.18, z + 0.26)]
        k.hexa(c + top, BATU)
    s = len(k.faces)                                                                       # ember (bucket) + gayung
    k.cylinder(lx0 + 0.35, 1.05, 0.17, TIERS_Y[-1] + 0.02, TIERS_Y[-1] + 0.36, PALET, seg=10)
    swatch(k, s, 4)
    s = len(k.faces)
    k.cylinder(lx0 + 0.25, 1.32, 0.07, TIERS_Y[-1] + 0.02, TIERS_Y[-1] + 0.12, PALET, seg=8)
    k.box(lx0 + 0.25, lx0 + 0.5, TIERS_Y[-1] + 0.09, TIERS_Y[-1] + 0.11, 1.30, 1.34, PALET)
    swatch(k, s, 12)
    for z in (-hw - 0.6, -hw - 0.6 + 1.3):                                                 # sign posts beside the top slab
        k.box(-0.55, -0.45, -0.2, BANK_Y + 1.35, z - 0.05, z + 0.05, TIANG)
    sign(k, -0.53, -0.47, BANK_Y + 0.85, BANK_Y + 1.3, -hw - 0.75, -hw + 0.85, "+x", R["tangga"])
    return k


def tangga_sampah():
    k, rng = MeshKit(uv_tile=1.0), random.Random(31)
    lx0, lx1 = LANDING_X
    for i in range(16):                                                                    # sachets / bottles on the treads + landing
        step = rng.randint(1, 7)
        if step == 7:
            x, y = rng.uniform(lx0 + 0.1, lx1 - 0.15), TIERS_Y[-1] + 0.02
        else:
            x, y = (step - 0.5) * STEP_RUN + rng.uniform(-0.08, 0.08), TIERS_Y[step] + 0.02
        z = rng.uniform(-0.9, 0.9)
        s = len(k.faces)
        if i % 3 == 0:
            k.box_yaw(x, z, 0.035, 0.11, rng.uniform(0, 180), y, y + 0.07, PALET)        # bottle lying down
        else:
            k.box_yaw(x, z, rng.uniform(0.06, 0.11), rng.uniform(0.04, 0.08), rng.uniform(0, 180), y, y + 0.012, PALET)
        swatch(k, s, rng.choice((3, 4, 9, 12, 5, 0, 13)))
    s = len(k.faces)                                                                       # brown scum line at the landing edge
    k.box(lx1 - 0.02, lx1 + 0.45, TIERS_Y[-1] - 0.06, TIERS_Y[-1] - 0.03, -1.6, 1.6, PALET)
    swatch(k, s, 14)
    return k


# ---------------- Tiang Nyangkut (jetty 2 snag) ----------------

def tiang_nyangkut():
    k = MeshKit(uv_tile=1.0)
    for i, (x, z, top) in enumerate(SNAG_POSTS):
        lean = (0.12 if i % 2 else -0.08, 0.0, 0.1 if i == 2 else -0.05)
        mat = BAMBU if i == 2 else TIANG
        k.beam((x - lean[0], -2.0, z - lean[2]), (x + lean[0], top, z + lean[2]), 0.075 if i != 2 else 0.055, mat)
    k.beam((0.0, 0.48, 0.0), (0.95, 0.32, 0.55), 0.04, KAYU)                               # broken cross rail
    k.beam((-0.9, -0.6, -0.6), (1.2, 0.35, 0.3), 0.09, TIANG)                              # sunken branch
    k.beam((0.6, -0.05, -0.05), (0.95, 0.25, -0.35), 0.035, TIANG)                         # twig
    pts = [(0.0, 0.78, 0.0), (0.35, 0.62, -0.85), (0.35, -0.25, -0.85), (0.0, -0.2, 0.0)]  # torn net post 0 -> post 2
    k.hexa(pts + [(x + 0.012, y, z + 0.012) for x, y, z in pts], JARING)
    sign(k, -0.42, 0.42, 0.98, 1.2, 0.08, 0.12, "+z", R["awas_tiang"], R["edge_dark"])      # warning board on post 0
    return k


def tiang_sampah():
    k, rng = MeshKit(uv_tile=1.0), random.Random(37)
    for x, z, sw in ((0.1, 0.12, 0), (0.85, 0.5, 3), (0.32, -0.72, 9), (1.45, -0.12, 4), (0.2, -0.4, 12), (-0.35, 0.85, 5)):
        s = len(k.faces)
        k.box_yaw(x, z, rng.uniform(0.12, 0.22), rng.uniform(0.1, 0.18), rng.uniform(0, 90), -0.05, rng.uniform(0.08, 0.22), PALET)
        swatch(k, s, sw)
    return k


# ---------------- Warung stall ----------------

def warung_stall(rect):
    k = MeshKit(uv_tile=1.0)
    for x, h in ((-1.0, 2.45), (1.35, 2.15)):                                              # bamboo awning poles
        for z in (-1.35, 1.35):
            k.cylinder(x, z, 0.05, 0.0, h, BAMBU, seg=6)
    for i in range(6):                                                                     # striped tarp, sloping to the front
        z0, z1 = -1.5 + i * 0.5, -1.5 + (i + 1) * 0.5
        pts = [(-1.15, 2.45, z0), (1.55, 2.1, z0), (1.55, 2.1, z1), (-1.15, 2.45, z1)]
        s = len(k.faces)
        k.hexa(pts + [(x, y + 0.025, z) for x, y, z in pts], PALET)
        swatch(k, s, 3 if i % 2 else 0)
    sign(k, 1.5, 1.56, 1.66, 2.08, -1.3, 1.3, "+x", rect)                                  # name board under the tarp edge
    k.box(0.2, 0.75, 0.0, 0.88, -1.2, 1.2, KAYU)                                           # counter body
    k.box(0.15, 0.82, 0.88, 0.94, -1.26, 1.26, KAYU)                                       # counter top
    k.box(-0.9, -0.82, 0.0, 1.7, -1.2, 1.2, KAYU)                                          # back shelf board
    k.box(-0.9, -0.6, 1.0, 1.04, -1.2, 1.2, KAYU)                                          # back shelf
    for z, sw in ((-0.85, 11), (-0.5, 11), (0.6, 5)):                                      # toples kerupuk + thermos
        s = len(k.faces)
        k.cylinder(0.45, z, 0.11, 0.94, 1.2, PALET, seg=8)
        swatch(k, s, sw)
    s = len(k.faces)
    k.cylinder(0.45, 0.95, 0.08, 0.94, 1.28, PALET, seg=8)
    swatch(k, s, 3)
    for i in range(5):                                                                     # hanging sachet strip
        s = len(k.faces)
        k.box(0.78, 0.8, 1.98 - i * 0.12, 2.08 - i * 0.12, 0.2, 0.36, PALET)
        swatch(k, s, (9, 12, 3, 6, 4)[i])
    k.box(1.22, 1.62, 0.42, 0.48, -1.1, 1.1, KAYU)                                         # long bench (bangku panjang)
    for x in (1.28, 1.56):
        for z in (-0.95, 0.95):
            k.box(x - 0.03, x + 0.03, 0.0, 0.42, z - 0.03, z + 0.03, KAYU)
    return k


# ---------------- Pos Ronda + papan pengumuman ----------------

def pos_ronda():
    k = MeshKit(uv_tile=1.0)
    x0, x1, z0, z1 = -1.0, 1.0, -1.2, 1.2
    for x, h in ((x0, 2.55), (x1, 2.3)):
        for z in (z0, z1):
            k.box(x - 0.06, x + 0.06, -0.2, h, z - 0.06, z + 0.06, TIANG)
    k.box(x0, x1, 0.45, 0.55, z0, z1, KAYU)                                                # bale-bale floor
    k.box(x0, x0 + 0.05, 0.55, 1.15, z0, z1, KAYU)                                         # back rail board
    for z in (z0, z1):
        k.box(x0, x1, 0.95, 1.0, z - 0.03, z + 0.03, KAYU)                                 # side rails
    pts = [(x0 - 0.35, 2.55, z0 - 0.3), (x1 + 0.45, 2.28, z0 - 0.3), (x1 + 0.45, 2.28, z1 + 0.3), (x0 - 0.35, 2.55, z1 + 0.3)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.05, z) for x, y, z in pts], SENG)                              # seng shed roof
    pm.swap_uv(k, s)
    sign(k, x1 + 0.44, x1 + 0.5, 1.9, 2.26, z0 - 0.1, z1 + 0.1, "+x", R["ronda"])          # POS RONDA fascia board
    k.cylinder(x1 + 0.2, z1 - 0.2, 0.085, 1.15, 1.75, BAMBU, seg=8)                        # kentongan
    k.box(x1 + 0.27, x1 + 0.3, 1.25, 1.65, z1 - 0.23, z1 - 0.17, TIANG)                    # its slit
    k.beam((x1 + 0.2, 1.75, z1 - 0.2), (x1 + 0.2, 2.25, z1 - 0.15), 0.012, BESI)           # hanging cord
    nz = z1 + 0.9                                                                          # notice board beside the hut
    for z in (nz, nz + 1.5):
        k.box(0.2, 0.3, -0.2, 2.15, z - 0.05, z + 0.05, TIANG)
    sign(k, 0.3, 0.36, 1.0, 1.95, nz - 0.02, nz + 1.52, "+x", R["pengumuman"], R["edge_dark"])
    pts = [(0.05, 2.15, nz - 0.2), (0.62, 2.02, nz - 0.2), (0.62, 2.02, nz + 1.7), (0.05, 2.15, nz + 1.7)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.04, z) for x, y, z in pts], SENG)                              # little rain cap
    pm.swap_uv(k, s)
    return k


# ---------------- wayfinding ----------------

def tiang_arah():
    k = MeshKit(uv_tile=1.0)
    k.box(-0.06, 0.06, -0.3, 2.45, -0.06, 0.06, TIANG)
    k.hexa([(-0.08, 2.45, -0.08), (0.08, 2.45, -0.08), (0.08, 2.45, 0.08), (-0.08, 2.45, 0.08),
            (-0.02, 2.55, -0.02), (0.02, 2.55, -0.02), (0.02, 2.55, 0.02), (-0.02, 2.55, 0.02)], TIANG)
    return k


def panah(rect):
    """Arrow board pointing +X, 1.15 m long, 0.28 m tall, 4 cm thick; tip in the plain 18 %."""
    k = MeshKit(uv_tile=1.0)
    L, H, T, TIP = 1.2, 0.28, 0.02, 0.2
    u0, v0, u1, v1 = rect
    outline = [(0.07, 0.0), (L - TIP, 0.0), (L, H / 2), (L - TIP, H), (0.07, H)]
    uv = lambda x, y: (u0 + (u1 - u0) * (x - 0.07) / (L - 0.07), v0 + (v1 - v0) * y / H)
    front = [(x, y, T) for x, y in outline]
    back = [(x, y, -T) for x, y in reversed(outline)]
    # Unity is left-handed: a viewer on +Z sees +X on the LEFT, so the +Z face takes the mirrored
    # U and the -Z face the plain one - both then read left-to-right with the tip ahead of the text.
    k._face(front, PAPAN, [])
    k.uvs[-1] = [(u1 - (uv(x, y)[0] - u0), uv(x, y)[1]) for x, y in outline]
    k._face(back, PAPAN, [])
    k.uvs[-1] = [uv(x, y) for x, y in reversed(outline)]
    for i in range(len(outline)):                                                          # rim in frame colour
        (xa, ya), (xb, yb) = outline[i], outline[(i + 1) % len(outline)]
        k._face([(xa, ya, -T), (xb, yb, -T), (xb, yb, T), (xa, ya, T)], PAPAN, [])
        pm.flat(k, len(k.faces) - 1, R["edge_wood"])
    k.box(-0.08, 0.08, 0.04, 0.24, -0.035, 0.035, BESI)                                    # clamp to the post
    return k


PIECES = {
    "SM_Env_TanggaCuci": tangga_cuci,
    "SM_Env_TanggaCuci_Sampah": tangga_sampah,
    "SM_Env_TiangNyangkut": tiang_nyangkut,
    "SM_Env_TiangNyangkut_Sampah": tiang_sampah,
    "SM_Env_WarungStall_Barat": lambda: warung_stall(R["warung_barat"]),
    "SM_Env_WarungStall_Timur": lambda: warung_stall(R["warung_timur"]),
    "SM_Env_PosRonda": pos_ronda,
    "SM_Env_TiangPapanArah": tiang_arah,
    "SM_Env_PanahMedis": lambda: panah(R["arah_medis"]),
    "SM_Env_PanahKarantina": lambda: panah(R["arah_karantina"]),
    "SM_Env_PanahBankSampah": lambda: panah(R["arah_bank"]),
}


def build():
    return [fn().build(name, MATERIALS) for name, fn in PIECES.items()]


def stats(obs):
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs}
    lo, hi = TRI_BUDGET
    return {"name": FBX_NAME, "tris": tris, "in_budget": all(lo <= t <= hi for t in tris.values()),
            "tangga_tiers_y": TIERS_Y, "needle_spot": NEEDLE_SPOT, "snag_posts": SNAG_POSTS}
