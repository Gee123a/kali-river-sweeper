# KALI — Core Mechanics Spec v2 (2026-11-28, from Ivan's playthrough)

Low-poly look, **real-world logic**. A player should be able to guess every rule from what they see.
Builds on [PROGRESSION_REDESIGN.md](./PROGRESSION_REDESIGN.md) and [PLAYTEST_PROGRESSION.md](./PLAYTEST_PROGRESSION.md).

## Playthrough findings → root cause
| What Ivan felt | Root cause (code) |
|---|---|
| Spawned and had no idea what to do | No objective. `KaliFieldGuideOverlay` is hidden until [H]. |
| Could sell "from a mile away" | Hub detection = 7.5 m `OverlapSphere` that also matches the `*_RiverDockTrigger` boxes, which span from the station to the river (`MapJsonImporter.cs:838`). |
| [1]/[3] pink lines meaningless | The `BC_StationDockSheet` quick-discard keys use a magenta "DENDA" hatch for wrong-station classes, and nothing explains it. |
| Buying tools doesn't work | `Canvas_ShopBankSampah.prefab` was never built (importer skips it silently). The [1–4] Kopdes fallback sells only upgrades, never tools. |
| Can't switch tools | Only scroll / `[ ]` cycles **owned** tools, and nothing can be bought, so the player only ever has #1. No hotbar. |
| Trash too small and too few to flood | Prefabs are real scale (7–22 cm). 1 unit per 4.2 s, cap 72. Every floating item raises water 2 cm (not physical). |
| Biohazard too frequent and punishing | 15% of spawns, a 10 s grace, then 4–12 HP/s. |

## A. Stations — "stand at the counter"
- Every station gets one **service point**: a small trigger in front of its door/counter, named `<Station>_ServicePoint`, sphere r = 2.0 m, at ground level.
- An interaction is valid only if:
  - the player is inside the service point, **and**
  - they are facing it (dot ≥ 0.5), **and**
  - they are on foot or docked.
- River dock triggers are used only for boat docking at Dermaga, never for selling.
- The prompt shows only when valid: `[E] Setor di Bank Sampah`.

## B. Selling — auto-sort, no fine keys
- **[E] at a station** deposits only the waste that station accepts. Everything else stays in cargo. The [1]/[2]/[3] discard keys are **removed**.
- **The prompt tells the truth before you press:**
  - `Bank Sampah menerima: Normal ×5 → Rp 20.000`
  - grey line: `Medis ×2 → bawa ke Pos Medis`
- **No accidental fines.** Fines and trust loss happen only from deliberate bad choices:
  - Gudang Pengepul "jual semua" (hold [E] 1 s; cheap rates; trust -8 per medical item / -12 per biohazard item)
  - [Q] dump on land
- **The dock sheet becomes an "Accepts" card:**
  - station name
  - accepted class with an icon and price
  - a cargo preview
  - no hatch or pink, unless the player is actually about to do something harmful (Pengepul hazard).

## C. Tools — hotbar + Kopdes shop (realistic carrying)
- **Hotbar of 4 slots** (you can't carry 20 tools):
  - Keys **1–4** select a slot.
  - Scroll / `[ ]` cycle.
  - Slot 1 starts with #1 Sendok.
  - The HUD shows slot icon, name, reach/batch, and the prick-risk %.
- **The Kopdes shop opens with [E] at its service point** (mouse UI, cursor unlocked, movement paused while open).
  - It lists tools whose tier is open (tier rules: PROGRESSION_REDESIGN §2).
  - Each entry shows price, stats (reach, batch, cooldown, prick %, can dredge Gunung) and state (owned / locked: reason / affordable).
- **Buying puts the tool in a free slot.** If all 4 are full, the player picks which slot to **trade in**: that tool is returned and 50% of its price is credited. This makes the Task 4L trade-in literal.
- **Upgrades** (Kampung bins, Sampan, Trash Boom, Excavator) sit in a second tab. Sampan and Trash Boom later become quest rewards (redesign §2).
- `RiverGameManager` owns the hotbar state (`int[] hotbar`, `SelectSlot`, `OnHotbarChanged`). The UI only listens.

## D. Trash & water — readable and physical
- **Readable size:** river trash spawns as floating **bundles** (kresek bag, bottle raft, styrofoam slab). Each visual bundle is ~0.5–1.0 m and is scaled up 2.2× from prop scale. The low-poly exaggeration stays honest: each bundle carries 2–4 `trashUnits`.
- **Floats on top:** trash sits +0.06 m above the water surface with a bob. Turbid water must never hide it.
- **Volume:**
  - spawn interval 4.2 s → ~2.0 s
  - visual cap 72 → 120 (check FPS)
  - storm interval × 0.5
  - 30–40 units seeded at start from the map `trash_pile` clusters (P0)
- **Water rises from blockage, not from floating trash.** This is the real backwater mechanism:
  - `waterY = base + piledAtBarrier × 0.022 + floating × 0.004 + rainRise`
  - `rainRise` ramps 0 → +0.55 m over the storm.
  - Clearing the **barrier pile** (Pintu Air / Trash Boom) is what lowers the river, which makes it a real place to defend.
- **Thresholds stay:** bank overflow 1.40, Sell-Lock 1.85, fatal 2.45. Retune so an idle player floods at ~200–240 s and an active sweeper peaks at Siaga 2–1 in the storm. Check with `docs/playtest/progression_sim.py` (update its water model).

## E. Hazards — rare and fair
- **Spawn mix** (household plastic dominates real Indonesian rivers): Normal 80%, Medical 14%, Biohazard 6%.
- **Medical prick:** damage 18 → 10, and the chance per tool is halved. #10 Capitan Ular stays at 0%.
- **Biohazard:**
  - 30 s safe carry, then 1.5 HP/s + 0.5 per extra drum (cap 4 HP/s).
  - Geiger ticks speed up through the last 10 s.
  - The grace timer pauses in a boat (sealed hold).

## F. Onboarding — an objective, always
- **Objective pill** (top-left, always visible), driven by `RiverGameManager.CurrentObjective` + `OnObjectiveChanged`. First-run chain:
  1. `Ambil sampah di sungai — klik kiri saat dekat (lihat tumpukan di depan)`
  2. `Bawa ke Bank Sampah — berdiri di depan loket, tekan [E]`
  3. `Sampah medis → Pos Medis, biohazard → Karantina (ikuti papan arah)`
  4. `Beli alat lebih baik di Kopdes [E] — pilih slot 1–4`
  5. `Badai datang! Bersihkan tumpukan di Pintu Air agar air turun`

  The chain then continues into the quests (Pak RT Q1).
- The controls panel auto-shows for the first 15 s, then folds into the [H] pill.
- Pak RT stands at spawn and delivers step 1 as dialogue once Task 6D lands.

## G. Money & progression (summary — full rules in PROGRESSION_REDESIGN)
- **Income:** correct station deposits (4k / 9k / 14k × trust mult × clean-combo), quests, Trash Boom (rupiah only).
- **Tools** need an open tier (trust + quest) **and** rupiah.

## H. NPC wiring (summary — Task 6D)
- [E] Bicara, state-based lines, reactions to clarity and storm, quest givers.

## Ownership
| Part | Owner |
|---|---|
| A, B, C, D, E, F logic and events (`RiverGameManager`, `KaliPlayerController`, `RiverTrashSpawner`, `MapJsonImporter`, `KaliFieldGuideOverlay`) | Ivan |
| Shop UI polish, hotbar HUD art, Accepts card art, objective pill art | Niki. A minimal functional version ships from Ivan first so the game is playable; Niki restyles. |
| Bundle trash meshes (kresek bundle, bottle raft, styrofoam slab) | JC |
| Water shader readability (trash visible on turbid water), service-point floor decals at each counter | Wesley |

## C2. Tool roles — why 4 slots (v2.1, replaces the "any tool in any slot" hotbar)
One slot per **role**; each role is the only way to handle one kind of trash, so the player switches for a reason.
| Slot | Role | Only this role can… | Ladder (existing indices, re-tagged; prices re-tuned) |
|---|---|---|---|
| 1 | **Serok** (scoop/net) | lift floating Normal bundles fast (batch grows with tier) | #1 Sendok → #2 Gayung → #6 Saringan Bambu → #7 Serokan Waring → #12 Serokan Jumbo → #14 Jala Lempar |
| 2 | **Capit** (grabber) | pick up Medical waste (other roles: blocked with hint) — prick risk falls per tier, #10 = 0% | #3 → #4 → #10 Capitan Ular → … |
| 3 | **Ganco** (hook) | haul Biohazard drums / heavy items; from #13 also dredge Gunung Sampah | #8 Ganco 1-Mata → #13 Ganco Ganda Winch → #17 Senapan Panah Tali … |
| 4 | **Garuk/Pompa** (rake/pump) | clear the jammed barrier pile (`TryScoopPiledBarrierTrash`) — the thing that lowers the water | #11 → #15 Pompa Siphon → #18 → #20 Skimmer Hidrolik … |
- Any role can still pick up Normal one item at a time; Serok is just much better at it.
- Buying a tool puts it in **its role's slot**; the old tool in that slot is traded in automatically for 50% credit.
- Each role has a cheap Tier-0 starter at Kopdes so no trash type is impossible early.
- The HUD hotbar shows the role icon/name per slot, greyed when empty ("Beli di Kopdes").

## I. Game states & menus (v2.1)
`RiverGameManager.State`: `Title → Playing ⇄ Paused → Ended`, `OnGameStateChanged`. Gameplay `Tick` and player input run only in `Playing`; `Paused` and the open shop freeze time (`timeScale 0`) and unlock the cursor.
| Menu | Content |
|---|---|
| Start (Title) | KALI title, Mulai, Kontrol, Kredit, Keluar; slow camera fly-over of the river |
| Pause (Esc) | Lanjut, Kontrol (tool roles + which station takes what), Pengaturan (volume, mouse sensitivity), Ulang, Keluar ke Menu |
| End | Extend `Canvas_SDGImpactReport`: all 5 endings, score/rank, quests done, Main Lagi / Menu |
**Consistency:** all menus, the shop and the Accepts card use the HUD design system in `docs/DESIGN.md` (*Lembar Kalkir Zona Cahaya*): same fonts, vellum panels, color tokens and button style. Ivan ships state logic + a minimal functional fallback; Niki owns the real menu UI.
