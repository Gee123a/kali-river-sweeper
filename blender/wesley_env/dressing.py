"""Kampung dressing layout (Wesley): where every street lamp and plant goes.

Reads Ivan's kali-river-map.json (items + footpaths) and the RiverMath river profile, and
writes Environment/Data/env_dressing.json, which the Unity menu
KALI > Environment > Build Kampung Dressing turns into PF_Env_KampungDressing.

Rules (all in Unity metres, bank top Y = 1.40):
  * street lamps every ~16 m along the footpaths (alternating sides), along both river
    edges where people live, and at the bridge, dermaga and pintu air ends; arm faces the path
  * nothing inside a building footprint, on a footpath, in the river or on the talud
  * plants follow the place: reeds, bamboo and stones on the river edge; banana and shrubs
    around rumah/warung; ketapang shade trees and grass in the open; coconuts on the
    east-downstream bank; only dry grass and stones around the Gunung Sampah
Seeded, so the layout is identical every run.
"""
import json
import math
import os
import random

from wesley_env import terrain as T

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP = os.path.join(ROOT, "unity", "Assets", "_Project", "Data", "kali-river-map.json")
OUT = os.path.join(ROOT, "unity", "Assets", "_Project", "Environment", "Data", "env_dressing.json")
BANK_Y = T.BANK_Y
HALF_X = T.WORLD_W * T.MAP_SCALE * 0.5 - 1.5
HALF_Z = T.WORLD_H * T.MAP_SCALE * 0.5 - 1.5

# exclusion radius (m) around each map item type; the dressing never enters these
KEEP_OUT = {"bank_sampah": 8.5, "kopdes": 10.5, "pengepul": 7.5, "pos_medis": 7.5, "karantina_biohazard": 8.0,
            "warung": 5.5, "rumah": 5.2, "dermaga": 5.0, "spawn": 3.5, "pohon": 3.0, "excavator": 6.0,
            "gunung_node": 0.0, "trash_pile": 0.0, "interceptor": 0.0, "trash_boom": 0.0}


# Bohlam wall lamps per building prefab: (x, y, z, yaw) in the building's own mesh space.
# yaw 0 = the arm points +X (out of a +X facing wall). Chosen beside doors / under eaves so
# they light the entrance without covering a sign.
WALL_LAMPS = {
    "PF_Env_BankSampah": [(-0.84, 2.12, -2.4, 0), (-0.84, 2.12, 2.4, 0)],
    "PF_Env_KoperasiDesa": [(1.02, 2.45, -1.0, 0), (1.02, 2.45, 3.0, 0), (-0.98, 2.6, -8.5, 0)],
    "PF_Env_PosMedisB3": [(1.42, 2.75, 3.45, 0), (1.82, 3.72, -1.7, 0)],
    "PF_Env_KarantinaBiohazard": [(-3.42, 2.75, 0.0, 180)],
    "PF_Env_WarungMadura": [(2.02, 2.78, -2.3, 0), (2.02, 2.78, 2.3, 0)],
    "PF_Env_GudangPengepul": [(3.02, 3.4, -3.2, 0), (3.02, 3.4, 2.8, 0)],
    "PF_Env_RumahPanggung": [(1.25, 3.55, 0.85, 0)],
}


def world(mx, my):
    return ((mx - T.WORLD_W * 0.5) * T.MAP_SCALE, (my - T.WORLD_H * 0.5) * T.MAP_SCALE)


def river(z):
    """(centre x, half width incl. talud) of the channel at world z."""
    my = z / T.MAP_SCALE + T.WORLD_H * 0.5
    cx = (T.center_map_x(my) - T.WORLD_W * 0.5) * T.MAP_SCALE
    return cx, T.half_width_map(my) * T.MAP_SCALE + T.SLOPE_OUT


def edge_dist(x, z):
    """Metres from the talud top edge onto the bank (negative = talud / river)."""
    cx, hw = river(z)
    return abs(x - cx) - hw


def seg_dist(p, a, b):
    ax, az = a; bx, bz = b; px, pz = p
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz or 1.0)))
    return math.hypot(px - ax - t * dx, pz - az - t * dz)


class Layout:
    def __init__(self, data):
        self.items = data["items"]
        self.paths = [[world(p["x"], p["y"]) for p in fp] for fp in data["footpaths"]]
        self.blocks = []                                    # (x, z, r)
        self.rects = []                                     # (x0, x1, z0, z1)
        self.gunung = []
        self.rows, self.npcs = [], []
        for it in self.items:
            t = it["type"]
            if t == "kampung_row":                          # 61-house rows (Ivan): keep the strip clear
                a, b = world(it["x1"], it["y1"]), world(it["x2"], it["y2"])
                self.rows.append((a, b, 4.6 + (it.get("depth", 1) - 1) * 6.3, it))
                continue
            x, z = world(it["x"], it["y"])
            if t == "npc_group":
                self.npcs.append((x, z, it))
                self.blocks.append((x, z, 2.6))
                continue
            if t in KEEP_OUT and KEEP_OUT[t] > 0:
                self.blocks.append((x, z, KEEP_OUT[t]))
            elif t == "jembatan":
                self.rects.append((x - 24.0, x + 24.0, z - 3.6, z + 3.6))
            elif t == "sluice_gate":
                self.rects.append((x - 30.0, x + 30.0, z - 4.5, z + 6.0))
            elif t == "gunung_node":
                self.gunung.append((x, z, it["w"] * T.MAP_SCALE * 0.5 + 2.0))
        self.lamps, self.plants, self.used = [], [], []

    @staticmethod
    def row_dist(x, z, a, b):
        """Distance to a kampung row, measured landward (rows grow away from the river)."""
        d = seg_dist((x, z), a, b)
        cx, _ = river((a[1] + b[1]) * 0.5)
        mx = (a[0] + b[0]) * 0.5
        riverward = (x - mx) * (1 if cx > mx else -1)
        return d if riverward < 0 else d * 1.6 + 2.0       # thin margin on the river side

    def house_spots(self):
        """Approximate front-row house centres along every kampung row."""
        out = []
        for a, b, _, it in self.rows:
            ln = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(ln / it.get("spacing", 6.3)))
            out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
        return out

    def path_dist(self, x, z):
        return min((seg_dist((x, z), a, b) for fp in self.paths for a, b in zip(fp, fp[1:])), default=99.0)

    def free(self, x, z, r, path_clear=1.8, edge_min=0.6):
        if abs(x) > HALF_X or abs(z) > HALF_Z or edge_dist(x, z) < edge_min:
            return False
        if any(math.hypot(x - bx, z - bz) < br + r for bx, bz, br in self.blocks):
            return False
        if any(x0 - r < x < x1 + r and z0 - r < z < z1 + r for x0, x1, z0, z1 in self.rects):
            return False
        if any(math.hypot(x - gx, z - gz) < gr + r for gx, gz, gr in self.gunung):
            return False
        if any(self.row_dist(x, z, a, b) < w + r for a, b, w, _ in self.rows):
            return False
        if self.path_dist(x, z) < path_clear + r:
            return False
        return all(math.hypot(x - ux, z - uz) >= r + ur for ux, uz, ur in self.used)

    def near_gunung(self, x, z, extra=14.0):
        return any(math.hypot(x - gx, z - gz) < gr + extra for gx, gz, gr in self.gunung)

    def lamp(self, x, z, face_x, face_z):
        yaw = math.degrees(math.atan2(-(face_z - z), face_x - x))       # local +X (the arm) -> target
        self.lamps.append({"p": [round(x, 3), BANK_Y, round(z, 3)], "yaw": round(yaw, 1)})
        self.used.append((x, z, 1.2))

    def plant(self, kind, x, z, r, rng, scale=(0.85, 1.2)):
        self.plants.append({"m": kind, "p": [round(x, 3), BANK_Y, round(z, 3)], "yaw": round(rng.uniform(0, 360), 1),
                            "s": round(rng.uniform(*scale), 3)})
        self.used.append((x, z, r))


def place_lamps(L):
    # 1) along footpaths, every ~16 m, alternating sides 1.7 m off the path
    side = 1
    for fp in L.paths:
        carry = 6.0
        for a, b in zip(fp, fp[1:]):
            ln = math.hypot(b[0] - a[0], b[1] - a[1])
            nx, nz = -(b[1] - a[1]) / ln, (b[0] - a[0]) / ln
            d = carry
            while d < ln:
                px, pz = a[0] + (b[0] - a[0]) * d / ln, a[1] + (b[1] - a[1]) * d / ln
                for s in (side, -side):
                    x, z = px + nx * 1.7 * s, pz + nz * 1.7 * s
                    if L.free(x, z, 1.0, path_clear=0.6) and all(math.hypot(x - l["p"][0], z - l["p"][2]) > 11 for l in L.lamps):
                        L.lamp(x, z, px, pz)
                        side = -side
                        break
                d += 16.0
            carry = d - ln
    # 2) river-edge promenade on both banks through the kampung (z -36 .. +84), lamps face the water
    for bank in (-1, 1):
        z = -34.0
        while z < 84.0:
            cx, hw = river(z)
            x = cx + bank * (hw + 2.2)
            if L.free(x, z, 1.0, path_clear=0.8, edge_min=1.5) and all(math.hypot(x - l["p"][0], z - l["p"][2]) > 12 for l in L.lamps):
                L.lamp(x, z, cx, z)
            z += 18.0
    # 3) bridge, dermaga and pintu air ends
    for it in L.items:
        if "x" not in it:
            continue
        x, z = world(it["x"], it["y"])
        if it["type"] == "jembatan":
            for sx in (-1, 1):
                for sz in (-1, 1):
                    px, pz = x + sx * 24.8, z + sz * 3.0
                    if edge_dist(px, pz) > 0.8:
                        L.lamp(px, pz, px, z)
        elif it["type"] == "dermaga":
            cx, hw = river(z)
            bank = 1 if x > cx else -1
            px = cx + bank * (hw + 1.4)
            for pz in (z - 3.6, z + 3.6):
                if all(math.hypot(px - l["p"][0], pz - l["p"][2]) > 5 for l in L.lamps):
                    L.lamp(px, pz, cx, pz)
        elif it["type"] == "sluice_gate":
            for bank in (-1, 1):
                cx, hw = river(z)
                px = cx + bank * (hw + 2.5)
                L.lamp(px, z - 5.5, cx, z - 5.5)


def scatter(L, rng, kind, n, r, accept, tries=40, scale=(0.85, 1.2)):
    placed = 0
    for _ in range(n * tries):
        if placed >= n:
            break
        x, z = rng.uniform(-HALF_X, HALF_X), rng.uniform(-HALF_Z, HALF_Z)
        if accept(x, z) and L.free(x, z, r):
            L.plant(kind, x, z, r, rng, scale)
            placed += 1
    return placed


def place_plants(L):
    rng = random.Random(2026)
    houses = L.house_spots()
    near_house = lambda x, z, lo, hi: any(lo < math.hypot(x - hx, z - hz) < hi for hx, hz in houses)
    kampung = lambda z: -36.0 < z < 86.0
    # banana + shrubs hug the houses and warung
    for hx, hz in houses:
        for kind, n, r, lo, hi in (("PohonPisang", 1, 1.6, 6.0, 11.0), ("Semak", 1, 1.0, 5.8, 10.0)):
            for _ in range(n):
                for _t in range(30):
                    a, d = rng.uniform(0, 2 * math.pi), rng.uniform(lo, hi)
                    x, z = hx + math.cos(a) * d, hz + math.sin(a) * d
                    if L.free(x, z, r):
                        L.plant(kind, x, z, r, rng)
                        break
    # coconuts on the east-downstream bank (map: "Pohon Kelapa Timur") + a few west
    scatter(L, rng, "PohonKelapa", 7, 2.5, lambda x, z: x > 8 and z > 30)
    scatter(L, rng, "PohonKelapa", 3, 2.5, lambda x, z: x < -20 and z > 50)
    # bamboo clumps on the river edge and the far bank edges
    scatter(L, rng, "Bambu", 6, 3.5, lambda x, z: 1.5 < edge_dist(x, z) < 5 and not L.near_gunung(x, z) and abs(z) < 80)
    scatter(L, rng, "Bambu", 6, 3.5, lambda x, z: abs(x) > HALF_X - 6 and not L.near_gunung(x, z))
    # ketapang shade trees in the open kampung
    scatter(L, rng, "PohonKetapang", 9, 5.5, lambda x, z: edge_dist(x, z) > 7 and kampung(z) and not L.near_gunung(x, z))
    # reeds + stones along the talud edge
    scatter(L, rng, "Alang", 90, 0.7, lambda x, z: 0.6 < edge_dist(x, z) < 3.2 and not L.near_gunung(x, z, 4))
    scatter(L, rng, "Batu", 26, 1.0, lambda x, z: 0.6 < edge_dist(x, z) < 4)
    # shrubs and wild grass across the bank
    scatter(L, rng, "Semak", 40, 1.0, lambda x, z: edge_dist(x, z) > 3 and not L.near_gunung(x, z))
    scatter(L, rng, "Rumput", 420, 0.45, lambda x, z: not L.near_gunung(x, z), tries=20)
    # around the Gunung Sampah: only dry grass and stones
    scatter(L, rng, "RumputKering", 160, 0.45, lambda x, z: L.near_gunung(x, z), tries=30)
    scatter(L, rng, "Batu", 10, 1.0, lambda x, z: L.near_gunung(x, z, 8))


def bank_edge_x(z, bank):
    """World x of the talud top edge on a bank (-1 west, +1 east) at z."""
    cx, hw = river(z)
    return cx + bank * hw


def facing_yaw(dx, dz):
    """Unity yaw that turns local +X toward (dx, dz)."""
    return round(math.degrees(math.atan2(-dz, dx)), 1)


def place_landmarks(L):
    """Priority 0 quest landmarks at the npc_group spots of docs/PROGRESSION_REDESIGN.md."""
    npc = {it["id"]: (x, z) for x, z, it in L.npcs}
    out = []
    # Q2 Tangga Cuci - Bu Siti (npc_washer_west_mid): pivot on the west talud top edge, +X = river
    _, z = npc["npc_washer_west_mid"]
    x = bank_edge_x(z, -1)
    slope = (bank_edge_x(z + 1, -1) - bank_edge_x(z - 1, -1)) / 2.0              # edge drift per metre of z
    out.append({"prefab": "PF_Env_TanggaCuci", "p": [round(x, 3), 0.0, round(z, 3)], "yaw": facing_yaw(1.0, -slope)})
    # Q3 Kail Nyangkut - Pak Darto (npc_fisher_jetty2): pilings in the shallows just downstream of
    # jetty 2, strung along the shore (yaw -90: local +X runs downstream) and out of the boat lane
    _, z = npc["npc_fisher_jetty2"]
    cx, hw = river(z)
    water_edge = cx - (hw - T.SLOPE_OUT)
    out.append({"prefab": "PF_Env_TiangNyangkut", "p": [round(water_edge + 0.95, 3), 0.0, round(z + 3.6, 3)], "yaw": -90.0})
    # warung stalls next to the two chatter pairs; the counter opens toward them along the bank
    for gid, prefab, bank in (("npc_chatter_west_warung", "PF_Env_WarungStall_Barat", -1),
                              ("npc_chatter_east_warung", "PF_Env_WarungStall_Timur", 1)):
        x, z = npc[gid]
        edge = bank_edge_x(z, bank)
        px = edge + bank * 1.65                                                   # whole stall on the bank top
        out.append({"prefab": prefab, "p": [round(px, 3), BANK_Y, round(z - 2.45, 3)], "yaw": -90.0})
    # Pak RT's pos ronda + notice board beside the spawn plaza, facing the player
    sx, sz = [world(it["x"], it["y"]) for it in L.items if it["type"] == "spawn"][0]
    rx, rz = sx - 3.6, sz + 5.2
    out.append({"prefab": "PF_Env_PosRonda", "p": [round(rx, 3), BANK_Y, round(rz, 3)], "yaw": facing_yaw(sx - rx, sz - rz)})
    for o in out:
        L.used.append((o["p"][0], o["p"][2], 3.2))
    return out


SIGN_ROUTES = [
    # junction (map), side offset (m), {arrow prefab: next waypoint toward that station (map)}
    ((310, 1210), (-1.9, -1.9), {"PF_Env_PanahBankSampah": (195, 1185), "PF_Env_PanahMedis": (318, 1030), "PF_Env_PanahKarantina": (318, 1030)}),
    ((365, 760), (-1.9, 1.9), {"PF_Env_PanahMedis": (220, 720), "PF_Env_PanahKarantina": (445, 740), "PF_Env_PanahBankSampah": (325, 880)}),
    ((735, 615), (1.9, 1.9), {"PF_Env_PanahKarantina": (760, 475), "PF_Env_PanahMedis": (660, 740), "PF_Env_PanahBankSampah": (660, 740)}),
]


def place_signposts(L):
    out = []
    for (jx, jy), (ox, oz), routes in SIGN_ROUTES:
        x, z = world(jx, jy)
        x, z = x + ox, z + oz
        arrows = []
        for i, (prefab, (wx, wy)) in enumerate(routes.items()):
            tx, tz = world(wx, wy)
            arrows.append({"prefab": prefab, "yaw": facing_yaw(tx - x, tz - z), "y": round(2.05 - 0.32 * i, 2)})
        out.append({"p": [round(x, 3), BANK_Y, round(z, 3)], "arrows": arrows})
        L.used.append((x, z, 1.2))
    return out


def build():
    with open(MAP) as f:
        data = json.load(f)
    L = Layout(data)
    landmarks = place_landmarks(L)
    signposts = place_signposts(L)
    place_lamps(L)
    place_plants(L)
    walls = [{"prefab": k, "spots": [{"p": [x, y, z], "yaw": yaw} for x, y, z, yaw in v]} for k, v in WALL_LAMPS.items()]
    out = {"source": "blender/wesley_env/dressing.py", "lamps": L.lamps, "plants": L.plants, "wall_lamps": walls,
           "landmarks": landmarks, "signposts": signposts}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    counts = {}
    for p in L.plants:
        counts[p["m"]] = counts.get(p["m"], 0) + 1
    return {"lamps": len(L.lamps), "plants": counts, "landmarks": landmarks, "signposts": len(signposts), "out": os.path.relpath(OUT, ROOT)}


if __name__ == "__main__":
    print(build())
