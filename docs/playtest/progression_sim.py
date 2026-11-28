"""KALI progression playtest simulator.

Replays a 300 s run with the real constants from RiverGameManager / ToolCatalog /
RiverTrashSpawner / RiverFlowBuoyancy / kali-river-map.json and a simple player
agent per archetype. Distances are metres along the river (+Z downstream) plus the
station's lateral offset. ponytail: 1-D river + lateral offsets, not a navmesh.

Usage: python3 docs/playtest/progression_sim.py [seeds]
"""
import random, sys, statistics as st

# ---- constants mirrored from code (keep in sync) ----
RUN, STORM_AT = 300.0, 120.0           # monsoonCountdownSeconds, monsoonStormTriggerRemaining
BASE_Y, RISE, SELL_LOCK, FATAL = -0.25, 0.020, 1.85, 2.45
SPAWN_INT, STORM_MULT, BINS_MULT = 4.2, 0.42, 2.5
DRIFT, STORM_DRIFT, BOOM_Z, BARRIER_Z = 0.75, 2.2, -18.125, 76.0
BOOM_INT, BOOM_PAY = 5.0, 1500
SURGE0, SURGE1 = 8.0, 3.0
PAY = {"N": 4000, "M": 9000, "B": 14000}
PENGEPUL = {"N": 2000, "M": 3000, "B": 4500}
FINE = {"N": 2500, "M": 5000, "B": 8000}
TOOLS = [  # idx, cost, reach, batch, cooldown, prick, gunungDmg
    (1, 0, 4.2, 1, .45, .60, 0), (2, 4000, 4.5, 1, .42, .55, 0), (3, 8000, 4.8, 1, .39, .50, 0),
    (4, 14000, 5.0, 2, .38, .45, 0), (5, 20000, 5.2, 2, .36, .42, 0), (6, 28000, 6.2, 2, .34, .35, 0),
    (7, 38000, 6.8, 3, .32, .30, 0), (8, 50000, 7.0, 2, .34, .25, 0), (9, 64000, 7.4, 3, .32, .22, 0),
    (10, 80000, 7.8, 2, .28, 0, 0), (11, 98000, 8.2, 3, .28, .14, 0), (12, 118000, 8.8, 4, .26, .12, 0),
    (13, 140000, 9.0, 3, .30, .08, .06), (14, 165000, 9.6, 4, .25, .10, .04), (15, 192000, 9.8, 4, .24, .06, .05),
    (16, 222000, 10.4, 4, .24, .06, .06), (17, 254000, 11.2, 3, .22, .04, .08), (18, 288000, 11.6, 5, .20, .05, .10),
    (19, 324000, 12.2, 5, .18, .05, .12), (20, 360000, 13.0, 6, .16, .03, .18)]
UPG = {"sampan": 40000, "boom": 75000, "bins": 30000, "excavator": 120000}
# station z (m) and lateral walk (m) from the river bank; from kali-river-map.json (z = (y-720)*0.125)
ST = {"bank": (58, 30), "kopdes": (46, 30), "pengepul": (70, 22), "medis": (0, 37), "karantina": (-31, 30)}
BRIDGE_Z, GUNUNG_Z = 2.5, -71.0
WALK, BOAT = 7.5, 10.0   # avg of walk 6.5 / sprint 10.5 on land; boatSpeed 10


class Run:
    def __init__(s, arch, seed):
        s.r = random.Random(seed); s.a = arch
        s.t = 0.0; s.rp = 0; s.cum = 0; s.hp = 100.0; s.trust = 40
        s.owned = {1}; s.eq = 1; s.unl = 1; s.upg = set(); s.cap = 8
        s.cargo = {"N": 0, "M": 0, "B": 0}; s.bio_t = 0.0
        s.gunung = [1.0, 1.0, 1.0]
        s.items = []          # [z, cls]
        s.piled = 4
        # Verified in Play Mode: the baked scene has NO pickable trash at start (map trash_pile
        # clusters are only VFX); the river fills only from the upstream spawner.
        if arch.__dict__.get("seed_clusters"):
            for y in (325, 345, 395, 515, 632, 820, 1190, 1295):
                for _ in range(5): s.items.append([(y - 720) * .125, s.cls()])
        s.spawn_t = s.surge_t = s.boom_t = 0.0
        s.z = 61.25; s.busy = 0.0
        s.ev = []; s.unlock_t = {}; s.buy_t = {}; s.pay_t = []; s.water_max = 0; s.siaga1 = None
        s.pricks = 0; s.dot = 0.0; s.fines = 0; s.end = None; s.lock_t = 0.0

    def cls(s, pile=False):
        r = s.r.random()
        a, b = (.70, .88) if pile else (.62, .85)
        return "N" if r < a else ("M" if r < b else "B")

    # --- world ---
    @property
    def remaining(s): return RUN - s.t
    @property
    def storm(s): return s.remaining <= STORM_AT
    @property
    def water(s): return BASE_Y + (len(s.items) + s.piled) * RISE
    @property
    def gh(s): return sum(s.gunung) / 3
    def tool(s, i=None): return TOOLS[(i or s.eq) - 1]
    def cargo_n(s): return sum(s.cargo.values())

    def earn(s, amt, milestone=True):
        s.rp += amt
        if milestone:
            s.cum += amt
            for t in TOOLS:
                if s.cum >= t[1] and t[0] > s.unl:
                    s.unl = t[0]; s.unlock_t[t[0]] = s.t
        if amt > 0: s.pay_t.append(s.t)

    def world(s, dt):
        # spawner
        iv = SPAWN_INT * (STORM_MULT if s.storm else 1) * (BINS_MULT if "bins" in s.upg else 1) * (2.4 + (1 - 2.4) * s.gh)
        s.spawn_t += dt
        if s.spawn_t >= iv and s.gh > .01:
            s.spawn_t = 0; s.items.append([s.r.uniform(-60, -46), s.cls()])
        # storm surge
        if s.storm:
            p = min(1, max(0, 1 - s.remaining / STORM_AT))
            s.surge_t += dt
            if s.surge_t >= SURGE0 + (SURGE1 - SURGE0) * p: s.surge_t = 0; s.piled += 1
        # boom
        if "boom" in s.upg:
            s.boom_t += dt
            if s.boom_t >= BOOM_INT:
                s.boom_t = 0; s.earn(BOOM_PAY, milestone=False)
                if s.piled: s.piled -= 1
        # drift
        sp = DRIFT * (STORM_DRIFT if s.storm else 1)
        keep = []
        for it in s.items:
            slow = .35 if "boom" in s.upg and abs(it[0] - BOOM_Z) < 4.5 else 1
            it[0] += sp * slow * dt
            if it[0] >= BARRIER_Z: s.piled += 1
            else: keep.append(it)
        s.items = keep
        # health
        if s.cargo["B"]:
            s.bio_t += dt
            if s.bio_t >= 10: d = min(12, 2.5 + 1.5 * s.cargo["B"]) * dt; s.hp -= d; s.dot += d
        else:
            s.bio_t = max(0, s.bio_t - 3 * dt)
            if s.water < 1.40: s.hp = min(100, s.hp + .8 * dt)
        s.water_max = max(s.water_max, s.water)
        fp = min(1, max(0, s.water) / FATAL)
        if fp >= .85 and s.siaga1 is None: s.siaga1 = s.t
        if s.water >= SELL_LOCK: s.lock_t += dt

    # --- player actions (each sets s.busy seconds) ---
    def travel(s, z, lateral=0.0, boat=False):
        dz = abs(s.z - z); s.z = z
        return (dz / (BOAT if boat else WALK)) + 2 * lateral / WALK

    def pickup(s, c):
        s.cargo[c] += 1
        tl = s.tool()
        prick = 0 if s.unl >= 10 else tl[5]
        if c == "M" and s.r.random() < prick:
            s.hp -= 18; s.pricks += 1

    def sell(s, where):
        if s.water >= SELL_LOCK and where != "pengepul":
            return
        if where == "pengepul":
            for c, q in s.cargo.items():
                if q: s.earn(q * PENGEPUL[c]); s.trust = max(0, s.trust - (8 if c == "M" else 12 if c == "B" else 0) * q)
            s.cargo = {k: 0 for k in s.cargo}; return
        want = {"bank": "N", "medis": "M", "karantina": "B"}[where]
        for c, q in list(s.cargo.items()):
            if not q: continue
            if c == want or s.a.dump_all_at_bank:
                if c == want:
                    mult = 1.15 if s.trust >= 70 else (.75 if s.trust < 25 else 1)
                    s.earn(int(q * PAY[c] * mult))
                    if c == "M": s.hp = min(100, s.hp + 10)
                    if c == "B": s.bio_t = 0
                else:
                    s.rp -= FINE[c] * q; s.fines += FINE[c] * q
                    s.trust = max(0, s.trust - (8 if c == "M" else 12) * q)
                s.cargo[c] = 0

    def shop(s):
        a = s.a
        bought = True
        while bought:
            bought = False
            for want in a.shopping(s):
                if want in UPG and want not in s.upg and s.rp >= UPG[want]:
                    s.rp -= UPG[want]; s.upg.add(want); s.buy_t[want] = s.t; bought = True
                    if want == "sampan": s.cap = max(s.cap, 22)
                    if want == "excavator": s.cap = 60
                    if want == "bins": s.trust = min(100, s.trust + 25)
                elif isinstance(want, int) and want not in s.owned and want <= s.unl:
                    best = max([i for i in s.owned if i < want and i >= 2], default=0)
                    price = max(0, TOOLS[want - 1][1] - (TOOLS[best - 1][1] // 2 if best else 0))
                    if s.rp >= price:
                        s.rp -= price; s.owned.add(want); s.eq = want; s.buy_t[want] = s.t; bought = True

    def decide(s):
        a = s.a
        boat = "sampan" in s.upg
        full = s.cargo_n() >= s.cap
        # dredge Gunung if able and the archetype wants to
        can_dredge = "excavator" in s.upg or s.tool()[6] > 0
        if can_dredge and a.dredges and s.gh > .01 and s.cargo["B"] == 0 and not full:
            t = s.travel(GUNUNG_Z, 0, boat)
            dmg = max(.20, s.tool()[6]) if "excavator" in s.upg else s.tool()[6]
            for i in range(3):
                if s.gunung[i] > 0:
                    swings = 3  # one burst per decision
                    s.gunung[i] = max(0, s.gunung[i] - dmg * 1.5 * swings)
                    t += swings * s.tool()[4] + 1.0
                    break
            return t
        # deliver
        need_bio = s.cargo["B"] > 0 and s.bio_t > a.bio_patience
        if full or need_bio or (s.cargo_n() and s.water >= SELL_LOCK):
            t = 0.0
            for where in a.route(s):
                z, lat = ST[where]
                if where == "karantina" and s.z > BRIDGE_Z: t += s.travel(BRIDGE_Z, 0, boat)
                t += s.travel(z, lat, boat and where != "karantina")
                s.sell(where); t += 1.5
                if where in ("bank", "pengepul", "kopdes") or abs(z - ST["kopdes"][0]) < 20:
                    pass
            # Kopdes visit when near (bank/pengepul trips)
            if any(w in ("bank", "pengepul") for w in a.route(s)) or True:
                t += s.travel(ST["kopdes"][0], ST["kopdes"][1] * .3, False); s.shop(); t += 2
            return t
        # collect
        tl = s.tool()
        pool = [it for it in s.items]
        if s.piled and (not pool or s.water > .8):
            t = s.travel(BARRIER_Z - 2, 0, boat)
            take = min(tl[3], s.piled, s.cap - s.cargo_n())
            for _ in range(take): s.piled -= 1; s.pickup(s.cls(True))
            return t + tl[4] + .6
        if not pool:
            return 1.0
        it = min(pool, key=lambda i: abs(i[0] - s.z))
        reach = tl[2] + (3.5 if "excavator" in s.upg and boat else 0)
        d = max(0, abs(it[0] - s.z) - reach)
        t = d / (BOAT if boat else WALK)
        s.z = it[0]
        n = 0
        for other in sorted(pool, key=lambda i: abs(i[0] - s.z)):
            if n >= tl[3] or s.cargo_n() >= s.cap or abs(other[0] - s.z) > reach: break
            s.items.remove(other); s.pickup(other[1]); n += 1
        return t + tl[4] + a.aim_time

    def play(s, dt=0.25):
        while s.t < RUN and s.end is None:
            s.world(dt)
            if s.busy <= 0: s.busy = s.decide()
            s.busy -= dt; s.t += dt
            if s.hp <= 0: s.end = "HealthFail"
            elif s.water >= FATAL: s.end = "FloodFail"
            elif s.gh <= .01: s.end = "TrueSdgVictory"
        if s.end is None: s.end = "TrueSdgVictory" if s.gh <= .01 else "PartialSurvival"
        return s


class Arch:
    dump_all_at_bank = False; dredges = False; bio_patience = 0.0; aim_time = 1.2
    def __init__(s, **k): s.__dict__.update(k)
    def route(s, r): return ["bank"]
    def shopping(s, r): return []


class Newbie(Arch):
    """Picks up everything, sells all at Bank Sampah (fines), buys the next tool when it can."""
    name = "Newbie (sells all at Bank Sampah)"; dump_all_at_bank = True; aim_time = 2.0; bio_patience = 30
    def shopping(s, r): return [max(r.owned) + 1] if max(r.owned) < 20 else []


class Lazy(Arch):
    """Sells everything at Gudang Pengepul (closest, low price, trust loss)."""
    name = "Lazy (Pengepul only)"; aim_time = 1.5; bio_patience = 30
    def route(s, r): return ["pengepul"]
    def shopping(s, r): return [max(r.owned) + 1] if max(r.owned) < 20 else []


class Sorter(Arch):
    """Sorts to the right stations, climbs tools one by one, buys bins + boom."""
    name = "Sorter (correct stations, step-by-step)"; aim_time = 1.2; dredges = True
    def route(s, r):
        out = []
        if r.cargo["B"]: out.append("karantina")
        if r.cargo["M"]: out.append("medis")
        if r.cargo["N"]: out.append("bank")
        return out or ["bank"]
    def shopping(s, r):
        nxt = max(r.owned) + 1
        return (["bins"] if "bins" not in r.upg and r.t > 60 else []) + ([nxt] if nxt <= 20 else []) + (["boom"] if r.t > 90 else [])


class Optimizer(Arch):
    """Knows the game: sorts, saves for #10 then #13, sampan, rushes the Gunung."""
    name = "Optimizer (save for #13, rush Gunung)"; aim_time = .8; dredges = True
    route = Sorter.route
    def shopping(s, r):
        for t in (10, 13):
            if t not in r.owned: return [t]
        return [u for u in ("sampan", "excavator", "boom") if u not in r.upg]


def summarize(arch, seeds):
    runs = [Run(arch, i).play() for i in range(seeds)]
    ends = {}
    for x in runs: ends[x.end] = ends.get(x.end, 0) + 1
    def med(v): v = [x for x in v if x is not None]; return f"{st.median(v):.0f}s" if v else "never"
    def gap(x):
        p = [0] + x.pay_t + [x.t]
        return max(b - a for a, b in zip(p, p[1:]))
    print(f"\n== {arch.name}  ({seeds} runs)")
    print("  endings:", ends)
    print(f"  final cum Rp {st.median(x.cum for x in runs):,.0f} | rupiah {st.median(x.rp for x in runs):,.0f} | tools owned {st.median(len(x.owned) for x in runs):.0f} | highest unlocked #{st.median(x.unl for x in runs):.0f}")
    print(f"  unlock #2 {med([x.unlock_t.get(2) for x in runs])}, #6 {med([x.unlock_t.get(6) for x in runs])}, #10 {med([x.unlock_t.get(10) for x in runs])}, #13 {med([x.unlock_t.get(13) for x in runs])}, #20 {med([x.unlock_t.get(20) for x in runs])}")
    print(f"  bought: boom {med([x.buy_t.get('boom') for x in runs])}, sampan {med([x.buy_t.get('sampan') for x in runs])}, excavator {med([x.buy_t.get('excavator') for x in runs])}, #13 {med([x.buy_t.get(13) for x in runs])}")
    print(f"  water max {st.median(x.water_max for x in runs):.2f} m | Siaga1 at {med([x.siaga1 for x in runs])} | sell-lock time {st.median(x.lock_t for x in runs):.0f}s | Gunung left {st.median(x.gh for x in runs):.2f}")
    print(f"  pricks {st.median(x.pricks for x in runs):.0f} | bio DoT {st.median(x.dot for x in runs):.0f} HP | fines Rp {st.median(x.fines for x in runs):,.0f} | trust {st.median(x.trust for x in runs):.0f}")
    print(f"  longest gap without a payout {st.median(gap(x) for x in runs):.0f}s | run length {st.median(x.t for x in runs):.0f}s")
    # unlock burstiness: toasts in the first 60 s
    print(f"  tool-unlock toasts in first 60 s: {st.median(sum(1 for t in x.unlock_t.values() if t <= 60) for x in runs):.0f}")
    return runs


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    for a in (Newbie(), Lazy(), Sorter(), Optimizer()):
        summarize(a, n)
    if "--clusters" in sys.argv:
        print("\n##### what-if: map trash clusters are live items #####")
        for a in (Newbie(seed_clusters=True), Sorter(seed_clusters=True), Optimizer(seed_clusters=True)):
            summarize(a, n)
