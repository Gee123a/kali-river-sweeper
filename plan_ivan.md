# AI Implementation Plan: Ivan (Coordinator & Core Lead)

> **Instructions for AI**: You are the dedicated AI coding assistant for **Stevanus Ivan Santoso (Ivan)**, Coordinator and Lead Core Architect of **KALI: Indonesian River Sweeper**. Focus strictly on C# gameplay systems, physics math, level data, integration hooks, browser prototypes, and academic ALP deliverables. Do not edit Blender models/lighting (`JC`), environment/shaders (`Wesley`), or VFX/UI/audio (`Niki`) inside their folders.

---

## 1. Identity & Scope Boundaries

- **Owner**: Stevanus Ivan Santoso (Ivan)
- **Student ID**: `0706012410029` | **Email**: `ssantoso04@student.ciputra.ac.id` | **GitHub**: [@Gee123a](https://github.com/Gee123a)
- **Track**: Coordinator, Core C# Systems, Buoyancy/Flow Physics, Level Data & Integration
- **Unity Version Alignment**: Current workspace operates on Unity `2022.3.46f1 LTS`. To address `CVE-2025-59489` security vulnerabilities, team will coordinate either upgrading to patched Unity `2022.3.67f2` or migrating to patched Unity 6 (`6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging.
- **Git Contributor Hygiene**: Local personal git author commits only. Zero AI bot author attribution, zero `Co-Authored-By` trailers.
- **Primary Deliverables**:
  1. Core state machine (`RiverGameManager.cs`, throttled ~10 Hz `NotifyState()`), linear `waterLevelY = f(trashInRiver)`, Overflow/Sell-Lock/`Q` high-ground dump, 3-class waste hazards (`Normal`, `Medical` prick, `Biohazard` DoT), swim stamina & drowning (`swimStamina`, `IsSwimming`, `IsDrowning`), 3 dedicated stations (`Bank Sampah`, `Pos Medis B3`, `Karantina Biohazard`) + fines vs `Gudang Pengepul`, Monsoon countdown, 20-tool Kopdes milestones & `BuyTool(int)` (`ToolCatalog.cs`), 5 endings (`TrueSdgVictory`, `PartialSurvival`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`).
  2. River math, `+Z` buoyancy & downstream `Pintu Air` barrier pileup (`RiverFlowBuoyancy.cs`, `RiverTrashItem.cs`, `RiverTrashSpawner.cs`).
  3. First-person walk/sprint/surface-swim/boat controller with dynamic boat Y tracking, surface-only swimming + bank/dock climb-out, camera-aimed nearest-target scoop (`SafeClosestPoint` for non-convex `MeshCollider`), bottom-anchored `Gunung Sampah` scaling, dual Input System + Legacy fallback, `1/2/3/E` station discard, `Q` dump, `Scroll/[ ]` tool switch (`KaliPlayerController.cs`), and `[H]` field guide + live toast (`KaliFieldGuideOverlay.cs`).
  4. 53-node purpose-built level data (`kali-river-map.json`) & 1-click spawner with split West/East banks, elevated `Jembatan Utama`, 3 waste stations + `Gudang Pengepul`, `Koperasi Desa (Kopdes)`, Dermaga-only river ports, `RiverTrashSpawner`, and `PF_Trash_MedicalBag`/`SyringeBox` (`MapJsonImporter.cs`).
  5. Browser 3D prototype (`tools/play-3d.html`) implementing the complete finalized loop in Safari without Unity installed.
  6. Prefab wire-up when JC, Wesley, and Niki push their `.fbx` / `.prefab` / `.shadergraph` assets + Final ALP Report.

### Allowed Files & Directories (READ & WRITE)
- `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/**`
- `unity/Assets/_Project/Scripts/**` (`Core/`, `Player/`, `Editor/`)
- `unity/Assets/_Project/Data/kali-river-map.json`
- `unity/Assets/_Project/Scenes/**` *(Integration assembly)*
- `tools/**` (`play-3d.html`, `map-editor.html`) *(whole `tools/` folder is gitignored: `play-3d.html` and `map-editor.html` are local-only, not tracked in git)*

### Strictly Forbidden (DO NOT MODIFY ARTISTS' FOLDERS)
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/Environment/**`, `Shaders/**` *(Owned by Wesley)*
- `unity/Assets/_Project/VFX/**`, `UI/**`, `Audio/**` *(Owned by Niki)*

### Context Files to Read
1. `AGENTS.md`
2. `docs/ARCHITECTURE.md` (Coordinate contracts, C# hooks, prefab paths)
3. `docs/PRD.md` (20 Kopdes milestone tools `BuyTool`, surface swimming/stamina/drowning, 3-class waste & 3 stations vs Pengepul, linear flood/Sell-Lock, 5 endings)
4. `docs/KALI_Asset_Master_Tracker.tsv`

---

## 2. Roadmap & Milestone Tasks (Prioritized)

- **Timeline Overview**: **Completed (`main`)** -> **Fase 1: MVP Blockers (Sekarang)** -> **Fase 2: Env/Trash/Shop Wiring (Setelah Prefab Tim Masuk)** -> **Fase 3: Sidang Demo & Final Build**.

### Completed Core Systems (main)
- [x] **Task 1: Core C# State Machine, 20-Tool Milestones & Linear Flood (`Scripts/Core/`)**
  - [x] Implement `ToolCatalog.cs` (all 20 official `SM_Tool_*` tools unlocked via cumulative Rupiah milestones & purchased via `BuyTool` at Kopdes), `RiverTrashItem.cs`, and `RiverTrashSpawner.cs`.
  - [x] Implement linear `currentWaterLevelY = -0.25f + TotalTrashInRiver * 0.020f`, Overflow (`1.40m`), Sell-Lock (`1.85m`), `DumpCargoOnHighGround()`, Fatal Flood (`2.45m` -> `FloodFail`), `playerHealth` (`HealthFail`), Monsoon countdown win & `0%` Gunung Sampah win, and ~10 Hz throttled `NotifyState()`.
  - [x] Broadcast `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` for Wesley's `SG_KaliWater`.
  - [x] Implement 3-class pickup (`Normal`, `Medical` prick mitigated by `#10 Capitan Ular`, `Biohazard` cargo DoT), 3 dedicated stations (`DiscardWasteAtStation` / `DiscardAllAtStation` with wrong-station fines) vs `SellAllAtPengepul`, `BuyKampungBins()`, `BuyUpgrade()`, `TriggerEmergencyFlush()`, and stage jumps (removed).
- [x] **Task 2: River Math & `+Z` Downstream Buoyancy (`Scripts/Core/RiverFlowBuoyancy.cs`)**
  - [x] Define `RiverMath` (`WorldW = 1040`, `WorldH = 1440`, `MapScale = 0.125` = `130m × 180m`).
  - [x] Flip drift toward **`+Z`** from upstream `-Z` `Gunung Sampah` toward downstream `+Z` `Pintu Air` barrier, dynamically tracking `currentWaterLevelY` + `GunungNodeController` bottom-anchored scaling.
- [x] **Task 3: Player Controller, Level Spawner & 3D Prototype (`KaliPlayerController.cs`, `MapJsonImporter.cs`, `tools/play-3d.html`)**
  - [x] Implement dual Input System / Legacy fallback, camera-aimed nearest-target scoop, dynamic boat Y tracking, `1/2/3/E` station quick-discard, `Q` high-ground dump, and `Scroll / [ ]` tool switching.
  - [x] Split left/right `Ground_Daratan` banks, elevate `Jembatan Utama`, move `Pintu Air` to `+Z` & `Gudang Pengepul` near Spawn, add `Pos Medis B3` & `Karantina Biohazard`, attach `RiverTrashSpawner`, and include `PF_Trash_MedicalBag` / `PF_Trash_SyringeBox`.
  - [x] Sync `tools/play-3d.html` with full playable `+Z` loop, 3 waste classes, 3 stations + fines vs Pengepul, linear flood / Sell-Lock / `Q` dump, 20 tools, Monsoon timer, and End-Run SDG Report.
- [x] **Task 3b: Visual Spec, VFX Event Contracts & Unity 2022.3.46f1 Verification**
  - [x] Push `docs/HUD_SPEC_NIKI.md` (`063ccad`, *Lembar Kalkir Zona Cahaya*).
  - [x] Add `OnWaterSplash(Vector3)` and `OnGunungTierBreached(Vector3)` to `RiverGameManager.cs` and triggers in `KaliPlayerController.cs` (`91fa930`).
  - [x] Verify Unity `2022.3.46f1 LTS` Play Mode (`MapJsonImporter.EnsureUrpPipelineAssigned()`, 53 greybox objects, 0 compile/runtime errors).
- [x] **Task 4A: Main Scene, URP Assets, Auto-Wiring Hooks, Generated Prefabs & Core QA**:
  - [x] Save `unity/Assets/_Project/Scenes/Main.unity` (`EditorBuildSettings` index 0) and push `URP_KaliPipeline.asset`, `URP_KaliRenderer.asset`, and 23 generated prefabs (`20 PF_Tool_*`, `PF_Trash_MedicalBag`, `PF_Trash_SyringeBox`, `PF_ExcavatorAmfibi`).
  - [x] Add prefab/material/UI/VFX auto-wiring table (`MapJsonImporter.cs`), extract `GunungNodeController.cs` & `RiverWaterSurfaceFollower.cs` for clean `.unity` serialization, fix `KaliPlayerController` child-collider lookup & `RiverGameManager` single-ending DoT guard, and pass `7/7` Unity batchmode QA suites (`KaliCoreQaTests.cs`).
- [x] **Task 4B (Parts 1 & 2): Merge `origin/niki-vfx`, 4-VFX Importer Hooks & `Main.unity` Bake**: merged `Canvas_HUD` + `Canvas_SDGImpactReport` + 4 VFX, added `KaliPlayerController.OnNearbyHubChanged` + `RiverMath` bounds, baked `Main.unity` (`75473b5` / `e9e6820`, QA 7/7), and verified Play Mode at `1280x720`.
- [x] **Task 4D: Game Flow UX Overhaul — Pickup/Sell, Live Audit & Fail/Retry (`Scripts/Core/`, `Scripts/Player/`, `KaliCoreQaTests.cs`, `tools/play-3d.html`)** *(Landed in `e7a8de3` & `8dd27dd`; 11/11 QA suites, 524 asserts)*
  - [x] **P0 Fail & Retry Loop**: `RestartRun()` + `[R]` retry hotkey, full `ResetStageState()` reset, `IsSellLocked` + confirm guard on `TriggerEmergencyFlush()`, `PartialSurvival` vs `TrueSdgVictory` split, `EndingDiagnosis`, and `tools/play-3d.html` in-place `resetGame()`.
  - [x] **P0 Safe `[E]` Deposit & Pickup Fixes**: `DiscardLegalAtStation()`, full-cargo scoop guard, `#10+` Medical prick `0%` lock, and pointer-lock click guard.
  - [x] **P1 Live Auditing, Trust Stakes & Dynamic SDG Scorecard**: `OnStationAuditReceipt`, `communityTrust` `+15%`/`-25%` modifiers, unpaid fine debt tracking, and `ComputeSdgScorecard()` (`S/A/B/C/F` + SDG `6.3`/`11.5`/`14.1`).
  - [x] **P1 Ergonomics, Navigation & Shop Polish**: `OnAimTargetChanged`, extended dock triggers + bank climb-out recovery, `0.5s` `[Q]` dump hold, `Pos Medis B3` emergency triage during `Sell-Lock`, Kopdes `1–4` selection fallback, and QA + browser smoke tests.
- [x] **Task 4E (Partial): Sync `main`, Task 5A & SSOT Docs**: pulled/rebased `main`, committed Task 5A + parent `.meta`s (`75f4d42`), and synced SSOT docs (`AGENTS.md`, `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `KALI_Asset_Master_Tracker`).
- [x] **Task 4F (Ivan Core Scope Complete)**: fixed `ApplyCargoGainAndMedicalCheck` event-ordering race, `IsToolUnlocked(index >= 1)`, duplicate `BuyUpgrade` guard, `sampanUnlocked` boat gate, `piledRiverTrashCount` sync, exposed `isInBoat`/`isFreeCam`/cooldown state, added `EventSystem` (`InputSystemUIInputModule`) + UI raycast guard, and reconciled `DESIGN.md` with `HUD_SPEC_NIKI.md`. *(Remaining UI prefab/controller items are tracked in `plan_niki.md` Tasks 4A–4B.)*
- [x] **Task 4G: Kopdes `BuyTool`, `SafeClosestPoint`, Field Guide Overlay (`8dd27dd`), SSOT Sync & Surface Swimming / Stamina / Drowning** *(12/12 QA suites, 550 asserts)*.
- [x] **Task 4H: Procedural Skybox, 12-Min Day/Night Cycle (`KaliDayNightCycle.cs`), Water Sun Glint & HUD Clock (`T` phase cycle)** *(12/12 QA suites, 563+ asserts)*.
- [x] **Task 4I (Initial Landing & Real-Footprint Re-Layout)**: dense kampung rows (`6ab0d43`) + real-footprint hub/dermaga/bridge/spawn clearance (`d7cdd17`, 61 houses across West/East banks, 5 jetties, 70 rear trees, 13/13 QA suites).
- [x] **Task 4J: Ambient River NPC System + Polish (`Scripts/Core/KaliAmbientNpc.cs`, `Scripts/Editor/KaliNpcBuilder.cs`, `kali-river-map.json`, `Main.unity`)** *(commit `d8dcad1`)*: `12 npc_group` entries expanding deterministically into **22 ambient NPCs** (`8` kids, `5` fishers, `5` washers, `4` chatters), using JC's `SK_VillagerNPC` read-only, `AnimatorCullingMode.CullUpdateTransforms` `PlayableGraph`, non-blocking zero-collider setup, `20:00–05:30` day/night fade, monsoon water evacuation. **Polish pass** added:
  - Rod-line & bobber world-space tracking (`rodTip`/`rodLine`/`rodBobber`), pivot angle `−8°`, all bobbers at `y ≈ −0.17` (water surface)
  - Foot/arm bones cached in `CacheComponents()` — ready for JC animation clip integration
  - `KidWader` hop amplitude `0.11f`, shallow-only guard; `KidChaser` oval track + `ClampOutsideBoatLane()`
  - Visibility fade `0.85f → 1.4f`; `ChatterBinCarrier` clip selection removed (now `KidChaser` only)
  - East warung chatters re-grounded: `(598, 1058, r=0.55)` on flat grass tile (`groundY=1.41`)
  - `KidJettyJumper` Jetty 05: anchor `(2.15, 0, −0.60)`, yaw `−28°`, jump target riverward — clears boat lane
  - `CrouchedWasher` footplant `pos.y -= 0.215f`; wash tub float bias removed (`Mathf.Max(−0.08f, binGroundY)`)
  - **14/14 QA suites, 1,909 asserts PASS**, `0` console errors, Play Mode verified `1280×720`

  > **📢 JC — Animation Clips Needed (blocks Task 5):** `SK_VillagerNPC` only has `Idle`, `CarryBin`, `ThrowTrash`. Missing:
  > `Anim_Fisher_SittingCast`, `Anim_Fisher_SittingIdle`, `Anim_Fisher_StandingIdle`,
  > `Anim_Washer_CrouchedScrub`, `Anim_Kid_WadeShallow`, `Anim_Kid_Splash`, `Anim_Kid_JettyJump`, `Anim_Chatter_TalkingIdle`.
  > Foot/arm bones are already cached — just drop clips into `Rigging/` and Ivan will wire them in Task 5.

  > **📢 Wesley — Washer Re-Snap After `tangga cuci`:** When wash steps land in `Environment/`, washer NPC Y positions need updating in `kali-river-map.json`. Ivan's `PlaceWashers()` reads `npc_group` `y` from JSON and applies `Mathf.Max(−0.08f, binGroundY)`. Just provide the world-space Y of each step tier and Ivan will update the JSON — no changes to `Environment/` files from Ivan's side.

  > **📢 Niki — NPC Splash Audio Hook:** `OnWaterSplash(Vector3 worldPos)` exists in `RiverGameManager.cs` and fires on player splash. Wire your `Audio/` splash clip to this event — no `Scripts/` edits needed from Niki's side.
- [x] **Task 5A: Core Wiring Hardening** *(Play Mode verified at `1280x720`, 0 console errors)*.

### Priority 1: Progression, QA & Unity Version Decision (Active Track)
- [x] **Task 4K: QA-Suite Fixes (`Scripts/Editor/KaliCoreQaTests.cs`)** *(Depends on Task 4L)*:
  - [x] Added `VerifyAmbientRiverNpcs` suite (`npc_group` determinism, per-role counts, hub/Dermaga/spawn/boat-lane clearance, zero blocking colliders, day/night & monsoon checks; `14/14` suites, `1,888` asserts PASS).
  - [x] Verify/update `VerifyKampungRowsAndMapEdge` & progression assertions alongside Task 4L progression balance fixes (`0` errors). *(Done: editor QA run `22/22` core suites, `2304` Assert calls, 0 compile errors.)*
- [x] **Task 4L: Progression Audit Fixes (`Scripts/Core/RiverGameManager.cs`, `ToolCatalog.cs`, `KaliPlayerController.cs`)**:
  - [x] *(Done: `BuyTool` now rejects locked tools with a "kumpulkan Rp X lagi" alert, shows a "Rupiah kurang" alert, and `GetToolPrice(int)` credits 50% of the best owned lower tool so stepping tier-by-tier is never worse than saving to skip — Niki's shop should display `GetToolPrice`.)* Audit & rebalance the **20-tool Kopdes `BuyTool(int)` ladder** (milestone vs purchase flow, cost/unlock pacing, and clear feedback so players climb tiers intentionally instead of skipping tools).
  - [x] *(Done: Rp 1,500 per 5 s, rupiah-only — no longer counts toward tool milestones; still drains 1 piled unit per cycle.)* Rebalance **Trash Boom passive income & water relief** (`boomTimer` `4s` loop in `RiverGameManager.cs`) so it complements active river sweeping without breaking Kopdes tool progression.
  - [x] *(Done: 30 s pre-storm warning alert; during the storm an upstream surge adds 1 piled unit every 8 s → 3 s as the countdown runs out, which Trash Boom partly offsets.)* Tune **monsoon storm pressure** (storm trigger, water-rise escalation, and cleanup urgency across the `300s` countdown) so mid-to-late game tension scales cleanly into `TrueSdgVictory` vs `PartialSurvival`.
- [ ] **Task 4C: Team Unity Version Decision & Git History Hygiene**: finalize team agreement on staying on `Unity 2022.3.46f1 LTS` for dev vs patching `CVE-2025-59489` (`2022.3.67f2` or `Unity 6` `6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging, and scrub earlier AI bot / `Co-Authored-By` commits if approved.

### Priority 2: Teammate Deliverable Wiring (`MapJsonImporter.cs`, `Main.unity`)
- [ ] **Task 5: Integrate Teammate Assets & Resolve Shared Decisions** *(Depends on `plan_jc.md`, `plan_wesley.md`, `plan_niki.md`)*:
  - [ ] **From JC (`plan_jc.md`)** *(partial: done `PF_Prop_SolarInterceptor` mapped in `MapJsonImporter.cs:165` and "Solar Interceptor" instance in `Main.unity`, villager clips/props integrated, `jc-products` closed and branch deleted on origin; left: disable the procedural `ToolSocket` swing once JC wires `Anim_PlayerToolSwing`)*: wire `PF_Prop_SolarInterceptor` into `MapJsonImporter.cs`; disable `KaliPlayerController.cs`'s own `32°` procedural `ToolSocket` swing once JC wires `Anim_PlayerToolSwing`; integrate new villager NPC clips/props into `KaliAmbientNpc.cs`; confirm clean `jc-products` closure.
  - [ ] **From Wesley (`plan_wesley.md`)**: swap procedural tree stand-ins (`CreateLowPolyTree`), `Backdrop_RollingHills` ring, and plank jetties for Wesley's `kelapa`/`pisang` trees, backdrop hills mesh, `tangga cuci` steps (re-snapping washer NPCs), extra jetties, and optional fences/footpaths. *(partial: `PF_Env_KampungDressing.prefab` (797 nested instances) exists, but `Main.unity` has no instance of it and `MapJsonImporter.cs` never places it, so lamps and plants are not in the game; tree/hills/steps swap not done)*
  - [ ] **From Niki (`plan_niki.md`)**: integrate `Canvas_ShopBankSampah` (`OnShopRequested`, optionally retire Kopdes `[1-4]` keyboard fallback), `Audio/`, `Canvas_SDGImpactReport` (`PartialSurvival` + `"Main Lagi"`), and HUD P0 fixes; resolve shared open decisions (Equipped Tool `#XX` pill vs transient toast; 4-pin vs 6-pin minimap legend) and re-bake `Main.unity`. *(partial: done shop, audio, SDG report, Kopdes keyboard fallback retired, HUD alert/biohazard fixes and re-bake; left the two open UI decisions and HUD minimap alignment check)*

### Priority 3: Academic ALP Report & Secondary Repo Maintenance
- [ ] **Task 6: Academic ALP Report & Final Sidang Build**: *Depends on Task 5 integrations + Niki's Sidang script (`plan_niki.md` Task 5)*. Capture demo screenshots (`T` time-of-day states + NPCs), run final Play Mode / build verification, and complete the ALP report.
- [ ] **Optional Post-MVP Repo Maintenance (`Task 4E` / `Task 5B` Ponytail Trim)**: only if time remains after Task 5 — prune merged remote branches, purge local `.impeccable/` + unused `.github` CI tracker churn, and trim unused C# shims / `manifest.json` packages / `tools/` boilerplate.

---

### Priority 0-A: Core Mechanics v2 from playthrough ([docs/MECHANICS_SPEC.md](./docs/MECHANICS_SPEC.md))
- [x] **Task 7A (Wave 1, done d5e4a09)**: counter service points (r 2 m, must face the counter), [E] auto-sort deposit with a truthful preview (remove [1][2][3] fine keys), 4-slot hotbar (keys 1–4 + scroll), literal trade-in when full, Kopdes shop wired (`Canvas_ShopBankSampah`) incl. upgrades tab.
- [x] **Task 7B (Wave 2, done 0cb3222)**: readable trash bundles (2.2× scale, 2–4 units, float +0.06 m), spawn ~2 s / cap 120, seeded start piles; water rises from **barrier blockage + storm rain**, not floating items; hazard mix 80/14/6, prick 10 dmg, biohazard 30 s grace + gentle DoT; always-visible objective chain (`CurrentObjective`, `OnObjectiveChanged`). Update `docs/playtest/progression_sim.py` to the new water model.

- [x] **Task 7C (done): Tool roles + game states ([MECHANICS_SPEC.md](./docs/MECHANICS_SPEC.md) §C2, §I)**: `ToolRole` per tool (Serok/Capit/Ganco/Garuk), slot = role, buy → role slot with auto trade-in, pickup rules per role (Medical needs Capit, Biohazard needs Ganco, barrier pile needs Garuk), re-tuned role ladders + Tier-0 starters; `State` Title/Playing/Paused/Ended + `OnGameStateChanged`, Esc pause, shop freezes time, restart re-seeds map piles; minimal fallback menus until Niki's UI lands.

### Priority 0: Progression & Village Life Redesign (Core Systems — do first)
Spec: [docs/PROGRESSION_REDESIGN.md](./docs/PROGRESSION_REDESIGN.md) (evidence: [docs/PLAYTEST_PROGRESSION.md](./docs/PLAYTEST_PROGRESSION.md)). Goal: rewards are EARNED (trust tiers + quests), the village reacts and talks, and the SDG win is reachable for good play.
- [ ] **Task 6A: Playtest P0 fixes** *(partial: `trash_pile` clusters baked and biohazard grace is 30 s via Task 7B; storm surge still 8 s → 3 s in code, not 5 s → 1.5 s)*: bake `trash_pile` clusters as live `RiverTrashItem`s in `MapJsonImporter.SpawnTrashCluster` (tutorial piles near spawn first); biohazard grace `10s → 25s` (or timer only on land); stronger storm surge (`5s → 1.5s`).
- [ ] **Task 6B: Earned tier progression (`RiverGameManager`, `ToolCatalog`)**: remove cumulative-Rp auto unlocks; add `GetToolTier(int)`, `IsTierOpen(int)` (trust threshold 30/50/70/85 + quest flags), tier gating in `BuyTool`, one `OnTierOpened` event (replaces 20 tool toasts); trust deltas per action (correct sort +2, quest +10–20, prick -5); "Setoran Bersih" combo streak (+5%/step, cap +25%, reset on mistake). Sampan and Trash Boom become quest rewards; Excavator stays Rp + Tier 3.
- [ ] **Task 6C: Quest system**: `Scripts/Core/KaliQuestCatalog.cs` (static table: Q1 Belajar Memilah, Q2 Jarum di Tangga Cuci, Q3 Kail Nyangkut, Q4 Bola Hanyut, Q5 Gotong Royong, Q6 Evakuasi, side Es Teh) + `KaliQuestManager.cs` (listens to existing GM events, `ActiveQuest`, `OnQuestStarted/Progress/Completed/Failed`, max 1 active + 1 storm quest). Quest spawn points in `kali-river-map.json` (`quest_marker` items) and the ball/snag spawns.
- [ ] **Task 6D: NPC interaction (`KaliAmbientNpc`, new `KaliNpcInteractable.cs`, `KaliNpcDialogue.cs`)** *(partial: `[E]` talk with facing and state-based lines in `KaliNpcInteractable.cs` (no `KaliNpcDialogue.cs`), `OnSpoke` event; not built: head-look, reactive behaviours, NPC↔NPC chains)*: `[E] Bicara` within 2.5 m, state-based line pick (calm/dirty/storm/high-low trust) from Niki's Bahasa table; reactive behaviour (washers leave below clarity 0.25, kids swim only at clarity ≥ 0.4, fishers drop a "sampah nyangkut" pickable every ~20 s while dirty, head-look within 4 m, cheer on a nearby clean combo); NPC↔NPC chains (chatter gossip pairs, kid→fisher point-and-follow every ~45 s, washer calls kids out in storm → Q6).
- [ ] **Task 6E: QA + balance**: `KaliCoreQaTests` suites for tier gating, each quest's complete/fail path, combo reset, NPC talk prompt; re-run `docs/playtest/progression_sim.py` (add tiers + quests) to hit good-Sorter TrueSdgVictory 30–50%, no reward gap > 40 s, Tier 3 by ~150–170 s. *(Depends on 6B–6D; supersedes Task 4K.)*

### Playtest-2 Fixes (merged to `main`, `3b77747`..`6e88c16`; not Play Mode tested)
- [x] **Waypoint chevrons**: `KaliWaypointChevrons.cs` points at the current objective target; QA token tests in code, one instance in `Main.unity`.
- [x] **Objective pill under the HUD**: IMGUI in `KaliFieldGuideOverlay.cs`, bound to `CurrentObjective`. Niki's HUD binding is still open (`plan_niki.md` Task 7A).
- [x] **One end-screen restart**: IMGUI `Main Lagi` shows only when `Canvas_SDGImpactReport` has no `Card/Btn_PlayAgain`.
- [x] **`[E]` talk needs facing**: `KaliNpcInteractable.FacingDot = 0.5`, QA `VerifyNpcFacingTalkRule`.
- [x] **Five named villagers** (Pak RT, Bu Siti, Pak Darto, Raka, Mbok Nah) from `KaliNpcBuilder.cs`, with role clips and `Talk_Gesture` (clip names confirmed in `SK_VillagerNPC.fbx`).
- [x] **Mbok Nah sells Es Teh**: Rp 5.000 for +30 HP (`EsTehPrice`, `EsTehHeal`). Differs from `docs/PROGRESSION_REDESIGN.md` (free, once-per-run side quest): pick one.
- [x] **Trash bundles in importer lists** at authored scale (`PF_Trash_BundleKresek`, `PF_Trash_RaftBotol`, `PF_Trash_SlabStyrofoam`, `PF_Trash_BundleMedis`).
- [x] **Visible sampan** (boat stays free), **decorative clusters**, **3 seeded start bundles** (kept; more would change flood difficulty), **tutorial piles near the bank**: per commit `3b77747`, not re-checked in code.
- [x] **`KaliBillboard`** script exists; not attached until quests.
- [x] **`Audio_Director`**: referenced by the importer (`Audio_Director.prefab`); drives Geiger.

Open follow-ups:
- Old 2.2× trash props look ~3× smaller than new bundles (JC/Ivan decision).
- Es Teh charges full price even for 1 HP.
- Wash tub may sit slightly under ground.
- Wesley decals and trash visibility on turbid water still open (`plan_wesley.md`).

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate the live demo flow (**`T`** time-of-day cycle) cleanly in 3 minutes without fumbles.
