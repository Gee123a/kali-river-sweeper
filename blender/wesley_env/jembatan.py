"""SM_Env_JembatanUtama (Wesley) - low-poly wooden rope bridge, 1,200-2,000 tris.

Style from Wesley's references (stylised low-poly game bridges): jittered wooden deck
planks, chunky square timber posts with stepped caps and rope wraps, sagging rope hand
rails with vertical hangers, and guy ropes to wooden stakes on the banks. Colours follow
docs/DESIGN.md "Split River Bamboo & Weathered Teak" (weathered, not saturated orange).

Contract (MapJsonImporter / RiverMath): node "Jembatan Utama" map (551, 740) -> Unity
(3.875, 0, 2.5), rot 0, groundY 0, concave MeshCollider. Same footprint as Ivan's
greybox: walking deck top ~3.8 m (>= 3.6 boat clearance) over a 28.75 m span, 8.5 m
plank ramps down to the +1.40 banks. Timber pile bents stand at +-7.2 m, so the centre
14.4 m (>= 12 m) stays free for boats.
"""
import math
import random

from wesley_env.meshkit import MeshKit

NAME = "SM_Env_JembatanUtama"
TRI_BUDGET = (1200, 2000)

WOOD, WOOD_DARK, POST, ROPE = range(4)
MATERIALS = (
    ("M_Env_KayuPapan", (0.55, 0.40, 0.27, 1.0)),
    ("M_Env_KayuPapanGelap", (0.42, 0.30, 0.20, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_Tali", (0.72, 0.60, 0.42, 1.0)),
)

BANK_Y, BED_Y = 1.40, -2.0
DECK_TOP = 3.8
PLANK_T = 0.14
HALF_SPAN, HALF_W = 14.375, 1.9        # walking deck 3.8 m wide
RAMP_LEN = 8.5
PIER_X, BANK_BENT_X = 7.2, 12.0
PLANK_W = 0.9


def _plank_row(k, rng, x0, x1, y0, y1, n):
    """n planks from (x0, y0) to (x1, y1) along X, each spanning the deck width (Z)."""
    for i in range(n):
        t0, t1 = (i + 0.06) / n, (i + 0.94) / n
        xa, xb = x0 + (x1 - x0) * t0, x0 + (x1 - x0) * t1
        ya, yb = y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1
        dz = rng.uniform(-0.12, 0.12)
        dy = rng.uniform(-0.03, 0.03)
        hw = HALF_W + rng.uniform(-0.08, 0.08)
        mat = WOOD if rng.random() < 0.6 else WOOD_DARK
        top_a, top_b = ya + dy, yb - dy
        k.hexa([(xa, top_a - PLANK_T, -hw + dz), (xb, top_b - PLANK_T, -hw + dz),
                (xb, top_b - PLANK_T, hw + dz), (xa, top_a - PLANK_T, hw + dz),
                (xa, top_a, -hw + dz), (xb, top_b, -hw + dz), (xb, top_b, hw + dz), (xa, top_a, hw + dz)], mat)


def _bent(k, x, top, bottom):
    """Timber pile bent: two square piles + cap beam under the deck stringers."""
    for z in (-HALF_W + 0.35, HALF_W - 0.35):
        k.box(x - 0.18, x + 0.18, bottom, top, z - 0.18, z + 0.18, POST)
    k.box(x - 0.22, x + 0.22, top, top + 0.25, -HALF_W - 0.15, HALF_W + 0.15, POST)


def _big_post(k, x, z, base, height, fancy=True):
    k.box(x - 0.3, x + 0.3, base, base + height, z - 0.3, z + 0.3, POST)
    top = base + height
    k.box(x - 0.38, x + 0.38, top, top + 0.18, z - 0.38, z + 0.38, POST)        # cap
    if fancy:
        k.box(x - 0.22, x + 0.22, top + 0.18, top + 0.42, z - 0.22, z + 0.22, POST)   # stepped topper
        k.box(x - 0.34, x + 0.34, base + height * 0.55, base + height * 0.55 + 0.22, z - 0.34, z + 0.34, ROPE)  # rope wrap


def _rope_span(k, p0, p1, sag, segs, half=0.075):
    pts = []
    for i in range(segs + 1):
        t = i / segs
        pts.append((p0[0] + (p1[0] - p0[0]) * t,
                    p0[1] + (p1[1] - p0[1]) * t - sag * 4 * t * (1 - t),
                    p0[2] + (p1[2] - p0[2]) * t))
    for a, b in zip(pts, pts[1:]):
        k.beam(a, b, half, ROPE)
    return pts


def build():
    rng = random.Random(740)
    k = MeshKit(uv_tile=1.5)

    # ---- deck + ramps (planks across the width) ----
    _plank_row(k, rng, -HALF_SPAN, HALF_SPAN, DECK_TOP, DECK_TOP, int(round(2 * HALF_SPAN / PLANK_W)))
    for s in (-1, 1):
        _plank_row(k, rng, s * HALF_SPAN, s * (HALF_SPAN + RAMP_LEN), DECK_TOP, BANK_Y, int(round(RAMP_LEN / PLANK_W)))

    # ---- stringers under the planks ----
    deck_under = DECK_TOP - PLANK_T
    for z in (-HALF_W + 0.35, HALF_W - 0.35):
        k.box(-HALF_SPAN, HALF_SPAN, deck_under - 0.3, deck_under, z - 0.15, z + 0.15, POST)
        for s in (-1, 1):
            a = (s * HALF_SPAN, deck_under, z)
            b = (s * (HALF_SPAN + RAMP_LEN), BANK_Y - PLANK_T, z)
            k.beam((a[0], a[1] - 0.15, z), (b[0], b[1] - 0.15, z), 0.15, POST)

    # ---- pile bents: in the river (+-7.2), on the banks (+-12), under the ramps ----
    for s in (-1, 1):
        _bent(k, s * PIER_X, deck_under - 0.55, BED_Y)
        _bent(k, s * BANK_BENT_X, deck_under - 0.55, 0.6)
        rx = s * (HALF_SPAN + RAMP_LEN * 0.5)
        _bent(k, rx, (DECK_TOP + BANK_Y) * 0.5 - PLANK_T - 0.55, 0.6)

    # ---- posts, rope rails and hangers ----
    rail_h = 1.15
    for zs in (-1, 1):
        z = zs * (HALF_W + 0.25)
        for x in (-HALF_SPAN, HALF_SPAN):
            _big_post(k, x, z, DECK_TOP - 0.6, 2.3, fancy=True)
        for x in (-PIER_X, PIER_X):
            _big_post(k, x, z, DECK_TOP - 0.4, 1.6, fancy=False)
        xs = (-HALF_SPAN, -PIER_X, PIER_X, HALF_SPAN)
        for (xa, xb), segs, sag in zip(zip(xs, xs[1:]), (4, 8, 4), (0.25, 0.55, 0.25)):
            top_a = DECK_TOP + (rail_h + 0.35 if abs(xa) == HALF_SPAN else rail_h)
            top_b = DECK_TOP + (rail_h + 0.35 if abs(xb) == HALF_SPAN else rail_h)
            pts = _rope_span(k, (xa, top_a, z), (xb, top_b, z), sag, segs)
            for p in pts[1:-1]:                               # vertical hangers down to the deck edge
                k.beam(p, (p[0], DECK_TOP - 0.05, z * 0.97), 0.045, ROPE)
        # guy ropes from the end posts down to stakes on the banks
        for s in (-1, 1):
            stake = (s * (HALF_SPAN + RAMP_LEN + 1.2), BANK_Y, z * 1.6)
            k.beam((s * HALF_SPAN, DECK_TOP + 1.7, z), (stake[0], stake[1] + 0.35, stake[2]), 0.06, ROPE)
            k.box(stake[0] - 0.12, stake[0] + 0.12, stake[1] - 0.3, stake[1] + 0.45, stake[2] - 0.12, stake[2] + 0.12, POST)

    return k.build(NAME, MATERIALS)


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
