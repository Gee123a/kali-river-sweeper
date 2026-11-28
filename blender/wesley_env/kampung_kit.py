"""SM_Env_KampungKit (Wesley, plan Steps 4C + 4D) - rustic jetty, bamboo fence and footpath tiles.

Unity coordinates, one object per piece:
  SM_Env_JettyKayu            drop-in for KaliKampungBuilder's plank jetty: SAME pivot and footprint
                              (pivot on the bank edge at y 0, +X toward the river, deck x -1.2..2.6,
                              z -0.8..0.8, deck top y 1.46, ladder on the +X tip down to the water) so the
                              boats Ivan ties at (1.65, 0.05, +/-1.65) and his deck BoxCollider still fit.
                              Weathered planks of uneven width with gaps, one short broken plank, joists,
                              octagonal posts lashed with rope, two taller mooring posts, bamboo ladder.
  SM_Env_PagarBambu           2.0 m bamboo fence bay along +Z (post at z 0 only, so bays chain), two
                              rails, woven split-bamboo slats of uneven height, rope lashings. Pivot ground.
  SM_Env_PagarBambu_Tiang     lone end post to close a run.
  SM_Env_JalanSetapak         1.2 x 2.0 m cement path tile (+Z) with a brick kerb; top y 0.06.
  SM_Env_JalanSetapak_Tangga  same width, 3 steps climbing 0.45 m over 1.2 m (+Z) for the bank slopes.
"""
import math
import random

from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_KampungKit"
NAME = "SM_Env_JettyKayu"
TRI_BUDGET = (12, 2600)

PAPAN, TIANG, TALI, BAMBU, BESI, SEMEN, BATA = range(7)
MATERIALS = (
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_Tali", (0.70, 0.62, 0.45, 1.0)),
    ("M_Env_Bambu", (0.70, 0.72, 0.40, 1.0)),
    ("M_Env_BesiKarat", (0.45, 0.28, 0.18, 1.0)),
    ("M_Env_TaludBeton", (0.62, 0.62, 0.60, 1.0)),
    ("M_Env_TembokOranye", (0.72, 0.38, 0.22, 1.0)),
)

DECK_TOP = 1.46
DECK_X = (-1.2, 2.6)
DECK_HALF_Z = 0.8


def lash(k, x, y, z, r):
    """Rope wrapped twice round a post at height y."""
    for dy in (0.0, 0.045):
        k.torus_y(x, y + dy, z, r + 0.018, 0.016, TALI, seg=8, ring=4)


def post(k, x, z, y0, y1, r=0.09):
    k.cylinder(x, z, r, y0, y1, TIANG, seg=8)


# ---------------- 4C jetty ----------------

def jetty():
    k = MeshKit(uv_tile=1.0)
    rng = random.Random(23)
    # planks across Z, uneven widths and gaps; one short broken plank near the tip
    x = DECK_X[0]
    i = 0
    while x < DECK_X[1] - 0.05:
        w = min(rng.uniform(0.2, 0.3), DECK_X[1] - x)
        gap = rng.uniform(0.015, 0.04)
        y = DECK_TOP - 0.05 + rng.uniform(-0.008, 0.008)
        z0, z1 = -DECK_HALF_Z + rng.uniform(-0.04, 0.03), DECK_HALF_Z + rng.uniform(-0.03, 0.04)
        if i == 9:
            z1 = 0.25                                                    # broken plank
        k.box(x, x + w, y, y + 0.05, z0, z1, PAPAN)
        x += w + gap
        i += 1
    # joists + cross beams
    for z in (-0.62, 0.0, 0.62):
        k.box(DECK_X[0] - 0.05, DECK_X[1] + 0.05, DECK_TOP - 0.17, DECK_TOP - 0.05, z - 0.05, z + 0.05, TIANG)
    for xb in (-0.8, 0.7, 2.2):
        k.box(xb - 0.06, xb + 0.06, DECK_TOP - 0.3, DECK_TOP - 0.17, -0.78, 0.78, TIANG)
    # posts (same x/z as Ivan's pilings, plus a middle pair), rope lashings at the beams
    for xb in (-0.8, 0.7, 2.2):
        for z in (-0.68, 0.68):
            post(k, xb, z, -1.5, DECK_TOP - 0.02)
            lash(k, xb, DECK_TOP - 0.26, z, 0.09)
    # two taller mooring posts at the tip, rope coils on top
    for z in (-0.74, 0.74):
        post(k, 2.5, z, -1.5, 2.05, r=0.075)
        lash(k, 2.5, 1.72, z, 0.075)
        k.torus_y(2.5, DECK_TOP + 0.02, z + (0.22 if z > 0 else -0.22), 0.13, 0.025, TALI, seg=10, ring=4)
    # bamboo ladder on the tip down into the water
    for z in (-0.38, 0.38):
        k.beam((2.68, DECK_TOP, z), (2.74, -0.35, z), 0.035, BAMBU)
    for y in (1.08, 0.72, 0.36, 0.0):
        k.beam((2.7, y, -0.42), (2.7, y, 0.42), 0.028, BAMBU)
    # rusty plate + bolt on the tip beam
    k.box(2.27, 2.29, DECK_TOP - 0.29, DECK_TOP - 0.18, -0.2, 0.2, BESI)
    return k


# ---------------- 4D fence ----------------

def pagar():
    k = MeshKit(uv_tile=1.0)
    rng = random.Random(7)
    k.cylinder(0.0, 0.0, 0.05, -0.2, 1.18, BAMBU, seg=6)
    lash(k, 0.0, 0.33, 0.0, 0.05)
    lash(k, 0.0, 0.83, 0.0, 0.05)
    for y in (0.35, 0.85):
        k.beam((0.07, y, -0.02), (0.07, y + rng.uniform(-0.02, 0.02), 2.02), 0.03, BAMBU)
    z = 0.1
    n = 0
    while z < 1.95:
        h = rng.uniform(0.92, 1.06)
        xo = 0.07 + (0.035 if n % 2 else -0.035)                      # woven in front of / behind the rails
        k.box(xo - 0.01, xo + 0.01, 0.04, h, z, z + 0.07, BAMBU)
        z += rng.uniform(0.075, 0.09)
        n += 1
    return k


def pagar_tiang():
    k = MeshKit(uv_tile=1.0)
    k.cylinder(0.0, 0.0, 0.05, -0.2, 1.18, BAMBU, seg=6)
    lash(k, 0.0, 0.33, 0.0, 0.05)
    lash(k, 0.0, 0.83, 0.0, 0.05)
    return k


# ---------------- 4D footpath ----------------

def kerb(k, x, z0, z1, top, rng):
    z = z0
    while z < z1 - 0.02:
        ln = min(0.23, z1 - z)
        k.box(x - 0.055, x + 0.055, -0.1, top + rng.uniform(-0.01, 0.006), z, z + ln, BATA)
        z += ln + 0.012


def jalan():
    k = MeshKit(uv_tile=1.0)
    rng = random.Random(3)
    k.box(-0.5, 0.5, -0.12, 0.05, 0.0, 2.0, SEMEN)
    for x in (-0.555, 0.555):
        kerb(k, x, 0.0, 2.0, 0.07, rng)
    return k


def jalan_tangga():
    k = MeshKit(uv_tile=1.0)
    rng = random.Random(5)
    for s in range(3):
        y = 0.05 + s * 0.15
        k.box(-0.5, 0.5, -0.12, y, s * 0.4, 1.2 if s < 2 else 1.6, SEMEN)
    for x in (-0.555, 0.555):
        for s in range(3):
            kerb(k, x, s * 0.4, s * 0.4 + 0.4 if s < 2 else 1.6, 0.07 + s * 0.15, rng)
    return k


PIECES = {
    "SM_Env_JettyKayu": jetty,
    "SM_Env_PagarBambu": pagar,
    "SM_Env_PagarBambu_Tiang": pagar_tiang,
    "SM_Env_JalanSetapak": jalan,
    "SM_Env_JalanSetapak_Tangga": jalan_tangga,
}


def build():
    return [fn().build(name, MATERIALS) for name, fn in PIECES.items()]


def stats(obs):
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs}
    lo, hi = TRI_BUDGET
    return {"name": FBX_NAME, "tris": tris, "in_budget": all(lo <= t <= hi for t in tris.values())}
