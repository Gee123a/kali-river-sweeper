# AI Implementation Plan: Ivan (Coordinator & Core Lead)

> **Instructions for AI**: You are the dedicated AI coding assistant for **Stevanus Ivan Santoso (Ivan)**, Coordinator and Lead Core Architect of **KALI: Indonesian River Sweeper**. Focus strictly on C# gameplay systems, physics math, level data, integration hooks, browser prototypes, and academic ALP deliverables. Do not edit Blender models/lighting (`JC`), environment/shaders (`Wesley`), or VFX/UI/audio (`Niki`) inside their folders.

---

## 1. Identity & Scope Boundaries

- **Owner**: Stevanus Ivan Santoso (Ivan)
- **Student ID**: `0706012410029` | **Email**: `ssantoso04@student.ciputra.ac.id` | **GitHub**: [@Gee123a](https://github.com/Gee123a)
- **Track**: Coordinator, Core C# Systems, Buoyancy/Flow Physics, Level Data & Integration
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

## 2. Step-by-Step Task Checklist

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

- [ ] **Task 4: Prefab Integration (`Scripts/`) — *Awaiting Remaining Art Drops***
  - [ ] Swap remaining greybox buildings/water in `MapJsonImporter.cs` with Wesley's `SM_Env_*` prefabs + `SG_KaliWater` material, and attach Niki's `Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`, and `VFX_MonsoonRain`.
  - [ ] Build Playable Scene inside `unity/Assets/_Project/Scenes/` once all prefabs land.

- [ ] **Task 5: Academic ALP Report & Sidang Defense Prep**
  - [ ] Export screenshots from `F9` stages (`1..4`) and WebGL preview (`tools/play-3d.html`).
  - [ ] Finalize Academic ALP Report (SDG 6.3/11.5/14.1, Beer-Lambert + `RiverMath` equations, team split).

---

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate live **`F9 + 1..4`** stage jumps cleanly in 3 minutes without fumbles.
