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
- [x] **Task 4I (Initial Landing): Dense Kampung Rows, Seeded Clutter, Low-Poly Trees, Backdrop Ring & Play Boundary** *(landed in `6ab0d43`; follow-up real-footprint clearance in Task 4I-B)*.
- [x] **Task 5A: Core Wiring Hardening** *(Play Mode verified at `1280x720`, 0 console errors)*.

### Priority 1: Map Layout, Ambient NPCs, Progression & QA (Active Track)
- [ ] **Task 4I-B: Kampung Rows Re-Layout (In Progress — separate active pass)**: finish real-footprint hub/dermaga/bridge/spawn clearance (`ab7b962` wip) across `kali-river-map.json`, `KaliKampungBuilder.cs`, `MapJsonImporter.cs`, and re-bake `Main.unity`.
  - *Blocks*: Task 4J (Ambient NPCs), Task 4K (QA-suite update), and Wesley's tree/hills/`tangga cuci`/jetty integrations (`plan_wesley.md`).
- [ ] **Task 4J: Ambient River NPC System (`/Users/mynamegee/kali-handoff/KALI_NPC_BRIEF.md`)** *(Depends on Task 4I-B kampung rows commit)*:
  - [ ] Add `npc_group` entries (`kids` 6–10, `fisher` 4–6, `washer` 4–6, `chatter` 3–5 across warungs/houses) to `kali-river-map.json` at real jetties, bank edges, and warungs (never on hubs, Dermaga boarding spots, spawn, footpaths, or boat lane).
  - [ ] Expand `npc_group` deterministically (seeded `System.Random`) in `MapJsonImporter.cs` under `_KALI_World/NPCs`, using JC's `SK_VillagerNPC` read-only (`0.6–0.7` uniform scale for kids, `MaterialPropertyBlock` clothing tints; procedural fallback if clip missing).
  - [ ] Add `KaliAmbientNpc.cs` in `Scripts/Core/`: zero per-frame allocations, `CullUpdateTransforms`, non-blocking/no colliders, `20:00–05:30` fade via `KaliDayNightCycle.Instance.CurrentHour`, and kids/washers exit water during `RiverGameManager.isMonsoonStorm`.
  - [ ] Validate in Unity + capture `npc_jetty`, `npc_washing`, `npc_kids`, `npc_overview` screenshots; hand off missing clip list to JC (`plan_jc.md` Task 4A).
- [ ] **Task 4K: QA-Suite Fixes (`Scripts/Editor/KaliCoreQaTests.cs`)** *(Depends on Task 4I-B, Task 4J & Task 4L)*:
  - [ ] Update `VerifyKampungRowsAndMapEdge` building count & real-footprint clearance assertions for the re-laid kampung rows (`ab7b962` pending QA update).
  - [ ] Add ambient NPC QA suite (`npc_group` deterministic expansion, per-role counts in range, zero overlap with hubs/Dermaga/spawn/boat lane, zero blocking colliders).
  - [ ] Add/adjust QA assertions for Task 4L progression balance fixes and verify all `KaliCoreQaTests` suites pass (`0` errors).
- [ ] **Task 4L: Progression Audit Fixes (`Scripts/Core/RiverGameManager.cs`, `ToolCatalog.cs`, `KaliPlayerController.cs`)**:
  - [ ] Audit & rebalance the **20-tool Kopdes `BuyTool(int)` ladder** (milestone vs purchase flow, cost/unlock pacing, and clear feedback so players climb tiers intentionally instead of skipping tools).
  - [ ] Rebalance **Trash Boom passive income & water relief** (`boomTimer` `4s` loop in `RiverGameManager.cs`) so it complements active river sweeping without breaking Kopdes tool progression.
  - [ ] Tune **monsoon storm pressure** (storm trigger, water-rise escalation, and cleanup urgency across the `300s` countdown) so mid-to-late game tension scales cleanly into `TrueSdgVictory` vs `PartialSurvival`.
- [ ] **Task 4C: Team Unity Version Decision & Git History Hygiene**: finalize team agreement on staying on `Unity 2022.3.46f1 LTS` for dev vs patching `CVE-2025-59489` (`2022.3.67f2` or `Unity 6` `6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging, and scrub earlier AI bot / `Co-Authored-By` commits if approved.

### Priority 2: Teammate Deliverable Wiring (`MapJsonImporter.cs`, `Main.unity`)
- [ ] **Task 5: Integrate Teammate Assets & Resolve Shared Decisions** *(Depends on `plan_jc.md`, `plan_wesley.md`, `plan_niki.md`)*:
  - [ ] **From JC (`plan_jc.md`)**: wire `PF_Prop_SolarInterceptor` into `MapJsonImporter.cs`; disable `KaliPlayerController.cs`'s own `32°` procedural `ToolSocket` swing once JC wires `Anim_PlayerToolSwing`; integrate new villager NPC clips/props into `KaliAmbientNpc.cs`; confirm clean `jc-products` closure.
  - [ ] **From Wesley (`plan_wesley.md`)**: swap procedural tree stand-ins (`CreateLowPolyTree`), `Backdrop_RollingHills` ring, and plank jetties for Wesley's `kelapa`/`pisang` trees, backdrop hills mesh, `tangga cuci` steps (re-snapping washer NPCs), extra jetties, and optional fences/footpaths.
  - [ ] **From Niki (`plan_niki.md`)**: integrate `Canvas_ShopBankSampah` (`OnShopRequested`, optionally retire Kopdes `[1-4]` keyboard fallback), `Audio/`, `Canvas_SDGImpactReport` (`PartialSurvival` + `"Main Lagi"`), and HUD P0 fixes; resolve shared open decisions (Equipped Tool `#XX` pill vs transient toast; 4-pin vs 6-pin minimap legend) and re-bake `Main.unity`.

### Priority 3: Academic ALP Report & Secondary Repo Maintenance
- [ ] **Task 6: Academic ALP Report & Final Sidang Build**: *Depends on Task 5 integrations + Niki's Sidang script (`plan_niki.md` Task 5)*. Capture demo screenshots (`T` time-of-day states + NPCs), run final Play Mode / build verification, and complete the ALP report.
- [ ] **Optional Post-MVP Repo Maintenance (`Task 4E` / `Task 5B` Ponytail Trim)**: only if time remains after Task 5 — prune merged remote branches, purge local `.impeccable/` + unused `.github` CI tracker churn, and trim unused C# shims / `manifest.json` packages / `tools/` boilerplate.

---

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate the live demo flow (**`T`** time-of-day cycle) cleanly in 3 minutes without fumbles.
