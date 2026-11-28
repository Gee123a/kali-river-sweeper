"""KALI progression playtest simulator.

Replays a run capped at 900 s with repeating monsoon storms (no timer ending) and the real
constants from RiverGameManager / ToolCatalog /
RiverTrashSpawner / RiverFlowBuoyancy / kali-river-map.json and a simple player
agent per archetype. Distances are metres along the river (+Z downstream) plus the
station's lateral offset. ponytail: 1-D river + lateral offsets, not a navmesh.

Usage: python3 docs/playtest/progression_sim.py [seeds]
"""
import random, sys, statistics as st

# ---- constants mirrored from code (keep in sync) ----
RUN = 900.0                             # sim cap; the game has no timer ending
FIRST_STORM, STORM_LEN, STORM_PERIOD = 180.0, 45.0, 180.0   # monsoonFirstStormDelay, monsoonStormDuration, monsoonStormPeriod
BASE_Y, SELL_LOCK, FATAL = -0.25, 1.85, 2.45
# spec D water: base + piled*0.022 + floating*0.004 + rainRise (0 -> 0.55 m across each storm, drains in ~20 s)
PILE_RISE, FLOAT_RISE, RAIN_MAX, RAIN_DECAY = 0.022, 0.004, 0.55, 0.0275
SPAWN_INT, STORM_MULT, BINS_MULT = 4.0, 0.5, 2.5   # 2.0 s floods every archetype by ~195-212 s (cargo 8 can't keep up)
VISUAL_CAP, MAX_BARRIER_PROPS = 120, 22   # RiverTrashSpawner.maxVisualFloatingTrash, GM.MaxVisualBarrierProps
UNITS = (2, 4)                            # trashUnits per spawned bundle
NORMAL_SHARE, MEDICAL_SHARE = 0.80, 0.14  # spec E mix (river spawns and barrier piles)
PRICK_DMG, PRICK_SCALE = 10, 0.5          # medicalPrickDamage, ToolCatalog.PrickChanceScale
BIO_GRACE = 30.0
SEED_BUNDLES, SEED_Z = 3, (-35.0, 55.0)  # RiverTrashSpawner.SeedDriftingTrash: 1-unit drifting bundles at run start
def bio_dot(n): return min(4.0, 1.5 + 0.5 * max(0, n - 1))
# map trash_pile clusters baked as snagged live items (1 unit each): (map y, tutorial?)
PILES = [(325, False), (345, False), (395, False), (515, False), (632, False), (820, False), (1190, True), (1295, True)]
DRIFT, STORM_DRIFT, BOOM_Z, BARRIER_Z = 0.75, 1.5, -18.125, 76.0
BOOM_INT, BOOM_PAY = 5.0, 1500
SURGE0, SURGE1 = 8.0, 3.0
PAY = {"N": 4000, "M": 9000, "B": 14000}
PENGEPUL = {"N": 2000, "M": 3000, "B": 4500}
FINE = {"N": 2500, "M": 5000, "B": 8000}
# spec C2 role ladders: role 0 Serok (Normal, batch), 1 Capit (only Medical; prick per tier), 2 Ganco (only Biohazard; #13+ dredge),
# 3 Garuk (only the Pintu Air barrier pile). Non-Serok roles take 1 Normal unit per scoop.
TOOLS = [  # idx, cost, reach, batch, cooldown, prick, gunungDmg, role
    (1, 0, 4.2, 1, .45, 0, 0, 0), (2, 3000, 4.5, 2, .42, 0, 0, 0), (3, 5000, 4.8, 1, .39, .50, 0, 1),
    (4, 22000, 5.0, 1, .38, .24, 0, 1), (5, 9000, 5.2, 2, .36, 0, 0, 0), (6, 18000, 6.2, 3, .34, 0, 0, 0),
    (7, 30000, 6.8, 3, .32, 0, 0, 0), (8, 6000, 7.0, 1, .34, 0, 0, 2), (9, 45000, 7.4, 4, .32, 0, 0, 0),
    (10, 55000, 7.8, 2, .28, 0, 0, 1), (11, 6000, 5.5, 2, .40, 0, 0, 3), (12, 75000, 8.8, 5, .26, 0, 0, 0),
    (13, 65000, 9.0, 2, .30, 0, .06, 2), (14, 120000, 9.6, 6, .25, 0, 0, 0), (15, 50000, 9.8, 4, .24, 0, 0, 3),
    (16, 150000, 10.4, 2, .24, 0, .08, 2), (17, 210000, 11.2, 3, .22, 0, .10, 2), (18, 110000, 11.6, 5, .20, 0, 0, 3),
    (19, 180000, 12.2, 6, .18, 0, 0, 3), (20, 280000, 13.0, 8, .16, 0, 0, 3)]
ROLE_OF = {"N": 0, "M": 1, "B": 2}
def ladder(role): return sorted((t for t in TOOLS if t[7] == role), key=lambda t: t[1])
UPG = {"sampan": 40000, "boom": 75000, "bins": 30000, "excavator": 120000}
# station z (m) and lateral walk (m) from the river bank; from kali-river-map.json (z = (y-720)*0.125)
ST = {"bank": (58, 30), "kopdes": (46, 30), "pengepul": (70, 22), "medis": (0, 37), "karantina": (-31, 30)}
BRIDGE_Z = 2.5
# Gunung Sampah nearest collider face on the river (+Z) side, measured in the open scene (Unity bounds of the 3 nodes:
# z -58.0 / -56.2 / -55.5). Dredge stand point = face + tool reach (+3.5 in a boat with excavator) + 0.5 (GM aim test).
GUNUNG_FACE_Z = -55.5
WALK, BOAT = 8.5, 10.0   # 50/50 walk 6.5 / sprint 10.5 on land (KaliPlayerController); boatSpeed 10


class Run:
    def __init__(s, arch, seed):
        s.r = random.Random(seed); s.a = arch
        s.t = 0.0; s.rp = 0; s.cum = 0; s.hp = 100.0; s.trust = 40; s.audit = False; s.debt = 0
        s.slot = [1, 0, 0, 0]; s.eq = 1; s.unl = 1; s.upg = set(); s.cap = 8
        s.cargo = {"N": 0, "M": 0, "B": 0}; s.bio_t = 0.0
        s.gunung = [1.0, 1.0, 1.0]
        s.items = []          # [z, cls, units, drifts]
        s.piled = 4
        s.rain = 0.0
        # Map trash_pile clusters are live at t=0: 5 snagged 1-unit items each (bob in place, no drift),
        # mix as MapJsonImporter.SpawnTrashCluster: tutorial piles all Normal, i==4 Medical, i==3 drum if y < 350.
        for y, tut in PILES:
            for i in range(5):
                c = "N" if tut or i < 3 else ("B" if i == 3 and y < 350 else ("M" if i == 4 else "N"))
                s.items.append([(y - 720) * .125, c, 1, False])
        # Run start seed: drifting 1-unit bundles; the same units are skipped from the earliest upstream spawns.
        for _ in range(SEED_BUNDLES): s.items.append([s.r.uniform(*SEED_Z), s.cls(), 1, True])
        s.suppress = SEED_BUNDLES
        s.spawn_t = s.surge_t = s.boom_t = 0.0
        s.z = 61.25; s.busy = 0.0
        s.ev = []; s.unlock_t = {}; s.buy_t = {}; s.pay_t = []; s.water_max = 0; s.siaga1 = None; s.siaga2 = None
        s.pricks = 0; s.dot = 0.0; s.fines = 0; s.end = None; s.lock_t = 0.0

    def cls(s, pile=False):
        r = s.r.random()
        return "N" if r < NORMAL_SHARE else ("M" if r < NORMAL_SHARE + MEDICAL_SHARE else "B")

    # --- world ---
    @property
    def storm(s): return s.t >= FIRST_STORM and (s.t - FIRST_STORM) % STORM_PERIOD < STORM_LEN
    @property
    def water(s): return BASE_Y + s.piled * PILE_RISE + sum(i[2] for i in s.items) * FLOAT_RISE + s.rain
    @property
    def gh(s): return sum(s.gunung) / 3
    def tool(s, i=None): return TOOLS[(i or s.eq) - 1]
    @property
    def owned(s): return {i for i in s.slot if i}
    def unlocked(s, i): return s.cum >= TOOLS[i - 1][1]
    def price(s, i):   # net of the automatic 50% trade-in of the tool in that role slot
        held = s.slot[TOOLS[i - 1][7]]
        return TOOLS[i - 1][1] - (TOOLS[held - 1][1] // 2 if held else 0)
    def next_in(s, role):
        cur = TOOLS[s.slot[role] - 1][1] if s.slot[role] else -1
        return next((t[0] for t in ladder(role) if t[1] > cur), None)
    def cargo_n(s): return sum(s.cargo.values())

    def earn(s, amt, milestone=True):
        s.rp += amt
        if milestone:
            s.cum += amt
            for t in TOOLS:
                if s.cum >= t[1] and t[0] not in s.unlock_t and t[0] != 1:
                    s.unl = max(s.unl, t[0]); s.unlock_t[t[0]] = s.t
        if amt > 0: s.pay_t.append(s.t)

    def world(s, dt):
        # spawner
        iv = SPAWN_INT * (STORM_MULT if s.storm else 1) * (BINS_MULT if "bins" in s.upg else 1) * (2.4 + (1 - 2.4) * s.gh)
        s.spawn_t += dt
        if s.spawn_t >= iv and s.gh > .01:
            s.spawn_t = 0
            u = s.r.randint(*UNITS)
            if s.suppress > 0: u = min(u, s.suppress); s.suppress -= u
            visual = sum(1 for i in s.items if i[3]) + min(s.piled, MAX_BARRIER_PROPS)
            if visual >= VISUAL_CAP: s.piled += u   # over the visual cap the bundle goes straight to the pile
            else: s.items.append([s.r.uniform(-60, -46), s.cls(), u, True])
        # storm surge + rain
        if s.storm:
            p = (s.t - FIRST_STORM) % STORM_PERIOD / STORM_LEN
            s.rain = RAIN_MAX * p
            s.surge_t += dt
            if s.surge_t >= SURGE0 + (SURGE1 - SURGE0) * p: s.surge_t = 0; s.piled += 1
        else: s.rain = max(0.0, s.rain - RAIN_DECAY * dt)
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
            if not it[3]: keep.append(it); continue
            slow = .35 if "boom" in s.upg and abs(it[0] - BOOM_Z) < 4.5 else 1
            it[0] += sp * slow * dt
            if it[0] >= BARRIER_Z: s.piled += it[2]
            else: keep.append(it)
        s.items = keep
        # health
        if s.cargo["B"]:
            s.bio_t += dt
            if s.bio_t >= BIO_GRACE: d = bio_dot(s.cargo["B"]) * dt; s.hp -= d; s.dot += d
        else:
            s.bio_t = max(0, s.bio_t - 3 * dt)
            if s.water < 1.40: s.hp = min(100, s.hp + .8 * dt)
        s.water_max = max(s.water_max, s.water)
        fp = min(1, max(0, s.water) / FATAL)
        if fp >= .85 and s.siaga1 is None: s.siaga1 = s.t
        if fp >= .60 and s.siaga2 is None: s.siaga2 = s.t
        if s.water >= SELL_LOCK: s.lock_t += dt

    # --- player actions (each sets s.busy seconds) ---
    def travel(s, z, lateral=0.0, boat=False):
        dz = abs(s.z - z); s.z = z
        return (dz / (BOAT if boat else WALK)) + 2 * lateral / WALK

    def can_pick(s, c): return c == "N" or s.slot[ROLE_OF[c]] > 0   # ponytail: the agent switches slots for free

    def pickup(s, c, units=1, via=None):
        units = min(units, s.cap - s.cargo_n())   # GM.TryPickupWaste clamps; the rest of the bundle is lost
        s.cargo[c] += units
        tl = s.tool(via or (s.slot[1] if c == "M" else s.slot[0]))
        prick = tl[5] * PRICK_SCALE if tl[7] == 1 else 0   # prick only on Capit tools
        for _ in range(units if c == "M" else 0):
            if s.r.random() < prick: s.hp -= PRICK_DMG; s.pricks += 1

    def trust_add(s, n):
        s.trust = min(100, s.trust + n) if n > 0 else max(0, s.trust + n)
        if s.trust < 25: s.audit = True            # UpdateTrustAuditState: on below 25, off at 30+
        elif s.trust >= 30: s.audit = False
    def trust_mult(s): return 1.15 if s.trust >= 70 else (.75 if s.audit else 1.0)

    def sell(s, where):
        if s.water >= SELL_LOCK: return           # SELL-LOCK refuses every station AND the pengepul (only Q dump works)
        if where == "pengepul":
            for c, q in s.cargo.items():
                if q: s.earn(q * PENGEPUL[c]); s.trust_add(-{"N": 0, "M": 8, "B": 12}[c] * q)
            s.cargo = {k: 0 for k in s.cargo}; return
        want = {"bank": "N", "medis": "M", "karantina": "B"}[where]
        for c, q in list(s.cargo.items()):
            if not q: continue
            if c == want or s.a.dump_all_at_bank:
                if c == want:
                    gross = int(q * PAY[c] * s.trust_mult())
                    paid_debt = min(s.debt, gross); s.debt -= paid_debt
                    s.earn(gross - paid_debt)     # GM: netPayout = gross - debtPaid; cumulative counts net
                    s.trust_add(4 * q)            # GM: trustGain = qty * 4 at a correct station
                    if c == "M": s.hp = min(100, s.hp + 10)
                    if c == "B": s.bio_t = 0
                else:
                    fine = q * FINE[c]
                    paid = min(max(s.rp, 0), fine); short = fine - paid
                    s.rp -= paid; s.fines += fine; s.debt += short
                    extra = max(2, (short // 5000) * 2) if short > 0 else 0   # GM extraDebtTrustLoss
                    s.trust_add(-({"N": 4, "M": 8, "B": 12}[c] * q + extra))
                s.cargo[c] = 0

    def can_afford_any(s):
        for want in s.a.shopping(s):
            if want in UPG and want not in s.upg and s.rp >= UPG[want]: return True
            if isinstance(want, int) and want not in s.owned and s.unlocked(want) and s.rp >= s.price(want): return True
        return False

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
                    if want == "bins": s.trust_add(25)
                elif isinstance(want, int) and want not in s.owned and s.unlocked(want):
                    price = s.price(want)
                    if s.rp >= price:
                        s.rp -= price; s.slot[TOOLS[want - 1][7]] = want; s.buy_t[want] = s.t; bought = True

    def decide(s):
        a = s.a
        boat = "sampan" in s.upg
        full = s.cargo_n() >= s.cap
        # dredge Gunung if able and the archetype wants to
        ganco = s.tool(s.slot[2]) if s.slot[2] else None
        can_dredge = "excavator" in s.upg or (ganco is not None and ganco[6] > 0)
        if can_dredge and a.dredges and s.gh > .01 and s.cargo["B"] == 0 and not full:
            tl = ganco or s.tool()
            reach = tl[2] + (3.5 if "excavator" in s.upg and boat else 0)
            t = s.travel(GUNUNG_FACE_Z + reach + .5, 0, boat)     # stand where the aim test (dist <= reach + 0.5) passes
            g = ganco[6] if ganco else 0
            dmg = max(.20, g) if "excavator" in s.upg else g
            swings = 3  # one burst per decision
            for _ in range(swings):                              # each swing: node takes dmg*1.5 (GunungNodeController), overflow lost
                for i in range(3):
                    if s.gunung[i] > 0:
                        s.gunung[i] = max(0, s.gunung[i] - dmg * 1.5); break
            t += swings * tl[4] + a.aim_time
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
            # Kopdes visit only when something on the list is affordable (no wasted detours)
            if s.can_afford_any():
                t += s.travel(ST["kopdes"][0], ST["kopdes"][1] * .3, False); s.shop(); t += 2
            return t
        # collect
        tl = s.tool(s.slot[0])
        pool = [it for it in s.items if s.can_pick(it[1])]
        garuk = s.tool(s.slot[3]) if s.slot[3] else None   # only Garuk clears the barrier pile
        if garuk and s.piled and (not pool or s.water > .8 or s.piled >= a.pile_at or (s.storm and s.piled >= a.storm_pile_at)):
            t = s.travel(BARRIER_Z - 2, 0, boat)
            take = min(garuk[3], s.piled, s.cap - s.cargo_n())
            for _ in range(take): s.piled -= 1; s.pickup("N", via=garuk[0])
            return t + garuk[4] + .6
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
            s.items.remove(other); s.pickup(other[1], other[2]); n += 1   # Serok batch; hazards via their role slot
        return t + tl[4] + a.aim_time

    def play(s, dt=0.25):
        while s.t < RUN and s.end is None:
            s.world(dt)
            if s.busy <= 0: s.busy = 1.0 if isinstance(s.a, Idle) else s.decide()
            s.busy -= dt; s.t += dt
            if s.hp <= 0: s.end = "HealthFail"
            elif s.water >= FATAL: s.end = "FloodFail"
            elif s.gh <= .01: s.end = "TrueSdgVictory"
        if s.end is None: s.end = "TimeCap900"
        return s


def cheapest_next(r):
    """Next ladder step of each role, cheapest net price first (role starters come first naturally)."""
    nxt = [n for n in (r.next_in(role) for role in range(4)) if n]
    return sorted(nxt, key=r.price)


class Arch:
    dump_all_at_bank = False; dredges = False; bio_patience = 0.0; aim_time = 1.2
    pile_at = 999; storm_pile_at = 999   # when to go clear the Pintu Air barrier pile (units)
    def __init__(s, **k): s.__dict__.update(k)
    def route(s, r): return ["bank"]
    def shopping(s, r): return []


class Idle(Arch):
    """Never touches anything: measures how long the river takes to flood on its own."""
    name = "Idle (AFK)"


class Newbie(Arch):
    """Picks up what it can, sells all at Bank Sampah (fines), buys the cheapest next tool of any role."""
    name = "Newbie (sells all at Bank Sampah)"; dump_all_at_bank = True; aim_time = 2.0; bio_patience = 30
    def shopping(s, r): return cheapest_next(r)


class Lazy(Arch):
    """Sells everything at Gudang Pengepul (closest, low price, trust loss)."""
    name = "Lazy (Pengepul only)"; aim_time = 1.5; bio_patience = 30
    def route(s, r): return ["pengepul"]
    def shopping(s, r): return cheapest_next(r)


class Sorter(Arch):
    """Sorts to the right stations, buys the 3 role starters, then climbs ladders cheapest-first, buys bins + boom."""
    name = "Sorter (correct stations, step-by-step)"; aim_time = 1.2; dredges = True; pile_at = 12; storm_pile_at = 6
    bio_patience = 25   # uses most of the 30 s safe carry instead of running to Karantina at once
    def route(s, r):
        # Storm: defend Pintu Air. Sell Normal at the nearby Bank Sampah, keep hazards aboard until they matter.
        if r.storm and not (r.cargo["B"] and r.bio_t > s.bio_patience) and r.cargo["M"] + r.cargo["B"] < r.cap // 2:
            return ["bank"]
        out = []
        if r.cargo["B"]: out.append("karantina")
        if r.cargo["M"]: out.append("medis")
        if r.cargo["N"]: out.append("bank")
        return out or ["bank"]
    def shopping(s, r):
        return (["bins"] if "bins" not in r.upg and r.t > 60 else []) + cheapest_next(r)[:1] + (["boom"] if r.t > 90 else [])


class Defender(Sorter):
    """Sorter who buys the Sampan first (cargo 22) and then defends Pintu Air in the storm."""
    name = "Defender (Sorter + Sampan)"
    def shopping(s, r):
        starters = [i for i in (11, 3, 8) if r.slot[TOOLS[i - 1][7]] == 0]
        if starters: return starters[:1]
        if "sampan" not in r.upg: return ["sampan"]
        return (["bins"] if "bins" not in r.upg else []) + cheapest_next(r)[:1]


class Optimizer(Arch):
    """Knows the game: sorts, buys the Garuk/Ganco/Capit tier-0 starters, saves for Ganco #13 (Gunung dredge), then sampan/boom and cheapest ladder rungs."""
    name = "Optimizer (save for #13, rush Gunung)"; aim_time = .8; dredges = True; pile_at = 12; storm_pile_at = 6; bio_patience = 25
    route = Sorter.route
    def shopping(s, r):
        for t in (11, 8, 3):   # ToolCatalog tier-0 role starters: empty role slot
            if r.slot[TOOLS[t - 1][7]] == 0: return [t]
        if 13 not in r.owned: return [13]   # Ganco ladder #8 -> #13 unlocks Gunung dredge
        return [u for u in ("sampan", "excavator", "boom") if u not in r.upg] + cheapest_next(r)[:1]


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
    print(f"  water max {st.median(x.water_max for x in runs):.2f} m | Siaga2 at {med([x.siaga2 for x in runs])}, Siaga1 at {med([x.siaga1 for x in runs])} | sell-lock time {st.median(x.lock_t for x in runs):.0f}s | Gunung left {st.median(x.gh for x in runs):.2f}")
    print(f"  first sale {med([x.pay_t[0] if x.pay_t else None for x in runs])} | flood-fail time {med([x.t if x.end == 'FloodFail' else None for x in runs])}")
    print(f"  pricks {st.median(x.pricks for x in runs):.0f} | bio DoT {st.median(x.dot for x in runs):.0f} HP | fines Rp {st.median(x.fines for x in runs):,.0f} | trust {st.median(x.trust for x in runs):.0f}")
    print(f"  longest gap without a payout {st.median(gap(x) for x in runs):.0f}s | run length {st.median(x.t for x in runs):.0f}s")
    # unlock burstiness: toasts in the first 60 s
    print(f"  tool-unlock toasts in first 60 s: {st.median(sum(1 for t in x.unlock_t.values() if t <= 60) for x in runs):.0f}")
    return runs


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    archs = (Idle(), Newbie(), Lazy(), Sorter(), Defender(), Optimizer())
    results = [(a, summarize(a, n)) for a in archs]
    print(f"\n== Flood vs victory ({n} seeds, cap {RUN:.0f} s)")
    print(f"{'archetype':<44}{'flood n':>8}{'flood med':>10}{'victory n':>10}{'victory med':>12}")
    for a, runs in results:
        fl = [x.t for x in runs if x.end == "FloodFail"]
        vi = [x.t for x in runs if x.end == "TrueSdgVictory"]
        fm = f"{st.median(fl):.0f}s" if fl else "-"
        vm = f"{st.median(vi):.0f}s" if vi else "-"
        print(f"{a.name:<44}{len(fl):>8}{fm:>10}{len(vi):>10}{vm:>12}")
