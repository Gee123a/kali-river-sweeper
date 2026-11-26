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
  1. Core state machine (`RiverGameManager.cs`, throttled ~10 Hz `NotifyState()`), linear `waterLevelY = f(trashInRiver)`, Overflow/Sell-Lock/`Q` high-ground dump, 3-class waste hazards (`Normal`, `Medical` prick, `Biohazard` DoT), 3 dedicated stations (`Bank Sampah`, `Pos Medis B3`, `Karantina Biohazard`) + fines vs `Gudang Pengepul`, Monsoon countdown, 20-tool auto-unlocks (`ToolCatalog.cs`), 4 endings (`TrueSdgVictory`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`), and `F9` Stage Jumps.
  2. River math, `+Z` buoyancy & downstream `Pintu Air` barrier pileup (`RiverFlowBuoyancy.cs`, `RiverTrashItem.cs`, `RiverTrashSpawner.cs`).
  3. First-person walk/boat controller with dynamic boat Y tracking, camera-aimed nearest-target scoop, bottom-anchored `Gunung Sampah` scaling, dual Input System + Legacy fallback, `1/2/3/E` station discard, `Q` dump, and `Scroll/[ ]` tool switch (`KaliPlayerController.cs`).
  4. 54-node purpose-built level data (`kali-river-map.json`) & 1-click spawner with split West/East banks, elevated `Jembatan Utama`, 3 waste stations + `Gudang Pengepul`, `RiverTrashSpawner`, and `PF_Trash_MedicalBag`/`SyringeBox` (`MapJsonImporter.cs`).
  5. Browser 3D prototype (`tools/play-3d.html`) implementing the complete finalized loop in Safari without Unity installed.
  6. Prefab wire-up when JC, Wesley, and Niki push their `.fbx` / `.prefab` / `.shadergraph` assets + Final ALP Report.

### Allowed Files & Directories (READ & WRITE)
- `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/**`
- `unity/Assets/_Project/Scripts/**` (`Core/`, `Player/`, `Editor/`)
- `unity/Assets/_Project/Data/kali-river-map.json`
- `unity/Assets/_Project/Scenes/**` *(Integration assembly)*
- `tools/**` (`play-3d.html`, `map-editor.html`)

### Strictly Forbidden (DO NOT MODIFY ARTISTS' FOLDERS)
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/Environment/**`, `Shaders/**` *(Owned by Wesley)*
- `unity/Assets/_Project/VFX/**`, `UI/**`, `Audio/**` *(Owned by Niki)*

### Context Files to Read
1. `AGENTS.md`
2. `docs/ARCHITECTURE.md` (Coordinate contracts, C# hooks, prefab paths)
3. `docs/PRD.md` (20-tool auto-unlocks, 3-class waste & 3 stations vs Pengepul, linear flood/Sell-Lock, 4 endings)
4. `docs/KALI_Asset_Master_Tracker.tsv`

---

## 2. Roadmap & Milestone Tasks (Prioritized)

- **Timeline Overview**: **Completed (`main`)** -> **Fase 1: MVP Blockers (Sekarang)** -> **Fase 2: Env/Trash/Shop Wiring (Setelah Prefab Tim Masuk)** -> **Fase 3: Sidang F9 & Final Build**.

### Completed Core Systems (main)
- [x] **Task 1: Core C# State Machine, 20-Tool Milestones & Linear Flood (`Scripts/Core/`)**
  - [x] Implement `ToolCatalog.cs` (all 20 official `SM_Tool_*` tools auto-unlocked by cumulative Rupiah), `RiverTrashItem.cs`, and `RiverTrashSpawner.cs`.
  - [x] Implement linear `currentWaterLevelY = -0.25f + TotalTrashInRiver * 0.020f`, Overflow (`1.40m`), Sell-Lock (`1.85m`), `DumpCargoOnHighGround()`, Fatal Flood (`2.45m` -> `FloodFail`), `playerHealth` (`HealthFail`), Monsoon countdown win & `0%` Gunung Sampah win, and ~10 Hz throttled `NotifyState()`.
  - [x] Broadcast `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` for Wesley's `SG_KaliWater`.
  - [x] Implement 3-class pickup (`Normal`, `Medical` prick mitigated by `#10 Capitan Ular`, `Biohazard` cargo DoT), 3 dedicated stations (`DiscardWasteAtStation` / `DiscardAllAtStation` with wrong-station fines) vs `SellAllAtPengepul`, `BuyKampungBins()`, `BuyUpgrade()`, `TriggerEmergencyFlush()`, and `F9 + 1..4` Stage Jumps.
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
  - [x] Verify Unity `2022.3.46f1 LTS` Play Mode (`MapJsonImporter.EnsureUrpPipelineAssigned()`, 54 greybox objects, 0 compile/runtime errors).
- [x] **Task 4A: Main Scene, URP Assets, Auto-Wiring Hooks, Generated Prefabs & Core QA**:
  - [x] Save `unity/Assets/_Project/Scenes/Main.unity` (`EditorBuildSettings` index 0) and push `URP_KaliPipeline.asset`, `URP_KaliRenderer.asset`, and 23 generated prefabs (`20 PF_Tool_*`, `PF_Trash_MedicalBag`, `PF_Trash_SyringeBox`, `PF_ExcavatorAmfibi`).
  - [x] Add prefab/material/UI/VFX auto-wiring table (`MapJsonImporter.cs`), extract `GunungNodeController.cs` & `RiverWaterSurfaceFollower.cs` for clean `.unity` serialization, fix `KaliPlayerController` child-collider lookup & `RiverGameManager` single-ending DoT guard, and pass `7/7` Unity batchmode QA suites (`KaliCoreQaTests.cs`).

### Priority 1: MVP Blockers (Kerjakan Sekarang)
- [x] **Task 4B (Part 1): Merge `origin/niki-vfx` (`d1f1914`) + Station Event & 4-VFX Importer Hooks**: merged `Canvas_HUD` (with station dock & map markers), `Canvas_SDGImpactReport` (4 endings), and all 4 VFX into `main`; added `KaliPlayerController.OnNearbyHubChanged` + `RiverMath` bounds + auto-wiring in `MapJsonImporter.cs`.
- [ ] **Task 4B (Part 2): Bake Merged UI & 4 VFX into `Main.unity`**: mount `UnitySSD` (`KYO 1 TB`), open Unity `2022.3.46f1`, run `KALI > Load Default Purpose-Built Map` + `KALI > QA > Run Core Verification`, test Play Mode end-to-end (`Canvas_HUD` + `Canvas_SDGImpactReport` + 4 VFX), and push updated `Main.unity`.
- [ ] **Task 4C: Team Unity Security Lock & Git History Hygiene**: finalize team agreement on staying on `2022.3.46f1 LTS` for dev vs patching `CVE-2025-59489` (`2022.3.67f2` or `Unity 6`) before final build packaging, and scrub earlier AI bot / `Co-Authored-By` commits if approved.

### Priority 2: Environment, Trash & Shop Integration (Setelah Prefab Tim Masuk)
- [ ] **Task 5: Prefab & Shader Wiring (`MapJsonImporter.cs`, `Main.unity`)**: wire Wesley's `SM_Env_*` + `SG_KaliWater` + 3 Station colliders, JC's 9 Normal trash + `SM_Trash_BiohazardDrum` + `PF_LightingRig`, and Niki's `Canvas_ShopBankSampah`.

### Priority 3: Sidang F9 Verification, Build & ALP Report
- [ ] **Task 6: Academic ALP Report & Sidang Defense Prep**: `F9` stage screenshots (`1..4`), WebGL/PlayMode verification, and final ALP Report.

---

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate live **`F9 + 1..4`** stage jumps cleanly in 3 minutes without fumbles.
