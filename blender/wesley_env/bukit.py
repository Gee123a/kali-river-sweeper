"""SM_Env_BackdropHills (Wesley, plan Step 4B) - 840 m low-poly horizon ring around the 130 x 180 m map.

Replaces the procedural ring from KaliMapBackdropBuilder.BuildBackdropHillsMesh(). Heights use the SAME
function as Ivan's SampleBackdropHeight() (ported 1:1 below), so the backdrop houses and trees he drops at
SampleBackdropHeight(x, z) still sit on this mesh, and the upstream/downstream river valleys still line up
with his continuation ribbons. What changes is the look:
  * denser sampling near the play edge (4 m instead of 10 m) and jittered far vertices -> faceted low-poly
    hills instead of a smooth stretched grid, matching the low-poly trees and houses;
  * four material zones by distance: riverbed mud in the carved valleys, M_Env_TanahBantaran next to the
    play area (seamless with the bank), M_Env_BukitHijau on the near hills (same tint, so no
    saw-tooth at the border), slightly blue-green M_Env_BukitJauh past 150 m where fog already hides the seam.
Pivot = world origin (place the prefab at 0,0,0). The 0.5 m overlap into the play area is kept.
"""
import math
import random

from wesley_env import terrain as T
from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_BackdropHills"
NAME = "SM_Env_BackdropHills"
TRI_BUDGET = (2000, 16000)

LUMPUR, BANTARAN, HIJAU, JAUH = range(4)
MATERIALS = (
    ("M_Env_LumpurDasar", (0.30, 0.24, 0.17, 1.0)),
    ("M_Env_TanahBantaran", (0.42, 0.50, 0.28, 1.0)),
    ("M_Env_BukitHijau", (0.27, 0.40, 0.20, 1.0)),
    ("M_Env_BukitJauh", (0.42, 0.52, 0.50, 1.0)),
)

# KaliMapBackdropBuilder constants
PLAY_HALF_X, PLAY_HALF_Z = 65.0, 90.0
OVERLAP = 0.5
OUTER = 420.0
BANK_LIP_Y = 1.38
RIVERBED_Y = -2.2
MAP_SCALE, WORLD_W, WORLD_H = T.MAP_SCALE, T.WORLD_W, T.WORLD_H


def smoothstep(e0, e1, x):
    if abs(e1 - e0) < 1e-9:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def ext_center_x(wz):
    if wz < -PLAY_HALF_Z:
        dz = wz + PLAY_HALF_Z
        cx0 = (T.center_map_x(0.0) - WORLD_W * 0.5) * MAP_SCALE
        slope0 = 58.0 * math.pi * 1.6 / WORLD_H
        return cx0 + math.sin(dz * 0.012) * (slope0 / 0.012)
    if wz > PLAY_HALF_Z:
        dz = wz - PLAY_HALF_Z
        cx1 = (T.center_map_x(WORLD_H) - WORLD_W * 0.5) * MAP_SCALE
        slope1 = 58.0 * math.pi * 1.6 / WORLD_H * math.cos(math.pi * 1.6)
        return cx1 + math.sin(dz * 0.011) * (slope1 / 0.011) + (1.0 - math.cos(dz * 0.008)) * 10.0
    map_y = wz / MAP_SCALE + WORLD_H * 0.5
    return (T.center_map_x(map_y) - WORLD_W * 0.5) * MAP_SCALE


def ext_half_width(wz):
    if wz < -PLAY_HALF_Z:
        hw0 = T.half_width_map(0.0) * MAP_SCALE
        return hw0 + (15.0 - hw0) * smoothstep(0.0, 180.0, -PLAY_HALF_Z - wz)
    if wz > PLAY_HALF_Z:
        hw1 = T.half_width_map(WORLD_H) * MAP_SCALE
        return hw1 + (15.0 - hw1) * smoothstep(0.0, 180.0, wz - PLAY_HALF_Z)
    map_y = wz / MAP_SCALE + WORLD_H * 0.5
    return T.half_width_map(map_y) * MAP_SCALE


def edge_dist(wx, wz):
    dx = max(0.0, abs(wx) - PLAY_HALF_X)
    dz = max(0.0, abs(wz) - PLAY_HALF_Z)
    return math.sqrt(dx * dx + dz * dz)


def height(wx, wz):
    """Exact port of KaliMapBackdropBuilder.SampleBackdropHeight."""
    ed = edge_dist(wx, wz)
    blend = smoothstep(0.0, 55.0, ed)
    in_cont = wz < -(PLAY_HALF_Z - OVERLAP) or wz > (PLAY_HALF_Z - OVERLAP)
    dist_river, ridge_atten, ext_hw = 0.0, 1.0, 0.0
    if in_cont:
        ext_hw = ext_half_width(wz)
        dist_river = abs(wx - ext_center_x(wz))
        ridge_atten = smoothstep(ext_hw, ext_hw + 48.0, dist_river)
    ridge_n = max(0.0, -(wz + PLAY_HALF_Z) / 330.0) * ridge_atten
    hill_a = math.sin(wx * 0.011 + 0.4) * math.cos(wz * 0.010 - 0.3) * 9.5
    hill_b = math.sin((wx + wz) * 0.019 + 1.1) * 5.2
    hill_c = math.cos(wx * 0.031 - wz * 0.027) * 2.4
    dist_rise = smoothstep(20.0, 340.0, ed) * 16.0 + ridge_n * 14.0
    raw = 2.0 + dist_rise + hill_a + hill_b + hill_c
    h = BANK_LIP_Y + (max(1.6, raw) - BANK_LIP_Y) * blend
    if in_cont:
        bank_outer = ext_hw + 28.0
        if dist_river < bank_outer:
            bt = smoothstep(ext_hw, bank_outer, dist_river)
            h = RIVERBED_Y + (h - RIVERBED_Y) * bt
    return h


OUTER_OFFSETS = [0, 4, 9, 15, 22, 30, 40, 52, 66, 82, 100, 122, 148, 178, 212, 250, 292]


def axis(hole, inner_step):
    outs = [hole + o for o in OUTER_OFFSETS] + [OUTER]
    n = max(2, round(2 * hole / inner_step))
    inner = [-hole + 2 * hole * i / n for i in range(1, n)]
    return [-v for v in reversed(outs)] + inner + outs


def zone(cx, cz, cy):
    ed = edge_dist(cx, cz)
    if cy < 0.6 and (abs(cz) > PLAY_HALF_Z - OVERLAP):
        return LUMPUR
    if ed < 34.0:
        return BANTARAN
    if ed < 150.0:
        return HIJAU
    return JAUH


def hills():
    k = MeshKit(uv_tile=12.5)                     # world-planar UV, 12.5 m tiles like Ivan's ring
    hx, hz = PLAY_HALF_X - OVERLAP, PLAY_HALF_Z - OVERLAP
    xs, zs = axis(hx, 4.0), axis(hz, 6.0)
    rng = random.Random(4)
    grid = {}
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            px, pz = x, z
            on_seam = abs(abs(x) - hx) < 1e-6 or abs(abs(z) - hz) < 1e-6
            outer_edge = i in (0, len(xs) - 1) or j in (0, len(zs) - 1)
            if not on_seam and not outer_edge and edge_dist(x, z) > 12.0:
                sx = (xs[min(i + 1, len(xs) - 1)] - xs[max(i - 1, 0)]) * 0.5
                sz = (zs[min(j + 1, len(zs) - 1)] - zs[max(j - 1, 0)]) * 0.5
                px += rng.uniform(-0.28, 0.28) * sx
                pz += rng.uniform(-0.28, 0.28) * sz
            grid[i, j] = (px, height(px, pz), pz)
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            xc, zc = (xs[i] + xs[i + 1]) * 0.5, (zs[j] + zs[j + 1]) * 0.5
            if abs(xc) < hx and abs(zc) < hz:
                continue                          # the play area has its own terrain
            a, b, c, d = grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]
            # alternate the diagonal so the facets don't line up into stripes
            tris = [(a, d, b), (b, d, c)] if (i + j) % 2 else [(a, d, c), (a, c, b)]
            for t in tris:
                cx = sum(p[0] for p in t) / 3
                cy = sum(p[1] for p in t) / 3
                cz = sum(p[2] for p in t) / 3
                k._face(list(t), zone(cx, cz, cy), [(p[0], p[2]) for p in t])
    return k


def build():
    ob = hills().build(NAME, MATERIALS)
    return ob


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    zs = [v.co.z for v in me.vertices]
    return {"name": FBX_NAME, "tris": tris, "in_budget": lo <= tris <= hi,
            "height_range_m": [round(min(zs), 2), round(max(zs), 2)],
            "faces_pointing_down": sum(1 for p in me.polygons if p.normal.z <= 0)}
