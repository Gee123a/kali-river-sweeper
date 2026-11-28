# KALI — Progression Playtest (2026-11-28, after Task 4L)

How a 300 s run actually plays and feels, per player type. Method:
- **Live Play Mode probe** (Main.unity, idle player, 126 s): trash spawn rate, drift speed, start state.
- **Simulator** `docs/playtest/progression_sim.py`, which replays full runs with the real constants (RiverGameManager, ToolCatalog, RiverTrashSpawner, RiverFlowBuoyancy, map positions). It runs four player types, 30 seeds each. Spawn rate and drift were checked against the live probe.
- Simulator limits: the river is modelled in 1-D with station side-offsets, aim time is fixed, and swimming, boat steering and trust bonuses are simplified. Read the numbers as **pacing shape**, not exact seconds.

## Verified in the live game
| Check | Result |
|---|---|
| Trash in the river at t=0 | **0 pickable items**. The 8 map `trash_pile` clusters (including "Sampah Tutorial 1/2" beside spawn) bake as VFX only, with no `RiverTrashItem`. |
| Spawn rate | 1 item / ~4.4 s (code: 4.2 s × Gunung factor) ✔ |
| Drift | ~0.73 m/s (code 0.75). Upstream spawn z≈-53 → player spawn z≈61, so **the first trash reaches the spawn area at ~150 s**. |
| Water, idle | -0.17 m → +0.41 m at 126 s. A player who does nothing never sees danger before the storm. |

## Results (median of 30 runs)
| Player type | Ending | Cumulative Rp | Tools owned / highest | #13 unlock | Water max | Longest gap without pay | Main pain |
|---|---|---|---|---|---|---|---|
| Newbie: sells everything at Bank Sampah | 18 PartialSurvival / **12 HealthFail** | 89k | 2 / #10 | 274 s | 1.17 m | 56 s | Rp 88k in fines, 78 HP biohazard DoT, trust 0 |
| Lazy: Pengepul only | 22 Partial / 8 HealthFail | 160k | 9 / #13 | 272 s | 1.05 m | 52 s | trust 0, biohazard DoT |
| Sorter: correct stations, buys step by step | 30 PartialSurvival | 198k | 9 / #15 | 208 s | 0.78 m | 62 s | long trips to Pos Medis / Karantina |
| Optimizer: saves for #10 then #13, rushes Gunung | 28 Partial / **2 TrueSdgVictory** | 190k | 3 / #14 | 215 s (bought 266 s) | 1.72 m | 63 s | #13 arrives too late, Gunung is 132 m upstream mid-storm |

Across every type and seed:
- No run ever unlocks tools #16–#20.
- No run buys Trash Boom, Sampan or Excavator, because the tool ladder takes all the money.

## How a run feels today (Sorter timeline)
1. **0–30 s — "Where's the trash?"** The river is empty near spawn. The player has to discover that they must walk ~100 m upstream. This is the worst possible first impression.
2. **30–45 s — toast storm.** The first delivery pays 30k+, so tools #2–#6 unlock almost at once (6 toasts in under a minute). Cheap tools #2–#5 are meaningless; they are skipped or bought and replaced within seconds.
3. **45–200 s — the long middle.**
   - Each sorting run means a 62 m walk to Pos Medis and 108 m to Karantina across the bridge, giving ~60 s stretches with no reward.
   - Biohazard grace is **10 s**, but no Karantina trip is that short. Careful players still take damage, and newbies die from it: 12 of 30 newbie runs end in HealthFail.
4. **150–300 s — a storm that doesn't threaten.**
   - The warning and the surge work.
   - But a player who keeps sweeping peaks at 0.8–1.7 m, so Siaga 1 and Sell-Lock never appear unless they leave the river.
   - The climax is mostly visual.
5. **~210 s — the goal appears too late.**
   - #13, the first tool that can dredge the Gunung, unlocks at ~210 s.
   - The Gunung is 132 m upstream, in the storm.
   - So **TrueSdgVictory ≈ 7%, even for an expert.** About 93% of runs end PartialSurvival, which makes the SDG message feel unwinnable.

## How it *should* feel (targets)
- **First 15 s:** trash within reach of spawn, first sale in under 30 s, and **one** unlock toast that feels earned.
- **Reward cadence:** a payout or unlock every 20–30 s, with no gap longer than 40 s.
- **Mid-game choice (90–180 s):** "next tool vs Sampan vs Trash Boom" should be a real decision. Today nobody can afford the upgrades.
- **Storm climax:** a sweeping player should see Siaga 2 and briefly Siaga 1, and feel that one mistake means Sell-Lock.
- **Winnable SDG:** a good Sorter wins TrueSdgVictory in roughly 30–50% of runs; newbies rarely die from systems they don't understand yet.

## Proposed fixes (smallest first)
| # | Fix | Why (evidence) | Owner |
|---|---|---|---|
| P0-1 | Bake `trash_pile` clusters as live `RiverTrashItem`s (MapJsonImporter `SpawnTrashCluster`), at least the 2 tutorial piles near spawn | Empty start; the what-if run gives first unlock at 4–5 s instead of ~30 s | Ivan |
| P0-2 | Biohazard grace 10 s → ~25 s, or start the grace only after leaving the river | Karantina is 108 m away; DoT is unavoidable and newbies die | Ivan |
| P1-3 | Re-scale the tool ladder to what a run earns (~200k): spread #2–#6 so they don't all unlock on the first sale, and put #20 at ~220–250k | 6 toasts in 60 s, then #16–#20 never reached | Ivan |
| P1-4 | Make Gunung reachable earlier: #13 at ~90–100k, or Excavator cheaper / given as a milestone | TrueSdgVictory 2/30 even for an optimizer | Ivan |
| P1-5 | Make the upgrades affordable: Sampan and Trash Boom as milestone rewards, or ~40% cheaper | Never bought in 120 runs | Ivan + Niki (shop UI) |
| P2-6 | Stronger storm for active players (surge 5 s → 1.5 s, or a storm spawn multiplier of 0.30) | Sweepers peak at 0.8 m; Sell-Lock never appears | Ivan |
| P2-7 | Add a Pos Medis / Karantina drop-off near the Dermaga, or a boat delivery bonus | 60 s reward gaps come from long sorting trips | Ivan + Wesley |

Re-run after any change: `python3 docs/playtest/progression_sim.py 30` (add `--clusters` for the what-if).
