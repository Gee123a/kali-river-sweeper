# AI Implementation Plan: Ivan (Coordinator & Core Lead)

> **Instructions for AI**: You are the dedicated AI coding assistant for **Stevanus Ivan Santoso (Ivan)**, Coordinator and Lead Core Architect of **KALI: Indonesian River Sweeper**. Focus strictly on C# gameplay systems, physics math, level data, integration hooks, browser prototypes, and academic ALP deliverables. Do not edit Blender models/lighting (`JC`), environment/shaders (`Wesley`), or VFX/UI/audio (`Niki`) inside their folders.

---

## 1. Identity & Scope Boundaries

- **Owner**: Stevanus Ivan Santoso (Ivan)
- **Student ID**: `0706012410029` | **Email**: `ssantoso04@student.ciputra.ac.id` | **GitHub**: [@Gee123a](https://github.com/Gee123a)
- **Track**: Coordinator, Core C# Systems, Buoyancy/Flow Physics, Level Data & Integration
- **Primary Deliverables**:
  1. Core state machine (`RiverGameManager.cs`), flood gauge (`Siaga 4 -> 1`), 3 Trade-off choices, Medical Biohazard Waste hook (`SecureMedicalWaste`), and `F9` Stage Jump hotkeys.
  2. River math & buoyancy (`RiverFlowBuoyancy.cs` / `RiverMath` `130m × 180m` spline projection).
  3. First-person walk/boat controller & scoop/dredge interaction (`KaliPlayerController.cs`).
  4. 51-node purpose-built level data (`kali-river-map.json`) & 1-click spawner (`MapJsonImporter.cs`).
  5. Browser 3D prototype & map editor (`tools/play-3d.html`, `tools/map-editor.html`) for testing without Unity installed.
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
3. `docs/PRD.md` (20-tool progression, Medical Waste mechanic, 3 choices, 3 endings)
4. `docs/KALI_Asset_Master_Tracker.tsv`

---

## 2. Step-by-Step Task Checklist

- [x] **Task 1: Core C# State Machine & Economy (`Scripts/Core/RiverGameManager.cs`)**
  - [x] Implement `UpgradeTier` progression (`Galah4m`, `WoodenSampan`, `TrashBoomAndPosSortir`, `AmphibiousExcavator`).
  - [x] Implement `SiagaLevel` (`4 -> 1`) driven by `floodPressure` + `isMonsoonStorm`.
  - [x] Broadcast `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` for Wesley's `SG_KaliWater`.
  - [x] Implement Choice A (`DumpAtBurnPit` vs `SellAtBankSampah`), Choice B (`BuyKampungBins`), Choice C (`TriggerEmergencyFlush` vs `CompleteCleanBreach`), and Medical Waste B3 safety (`SecureMedicalWaste`).
  - [x] Implement `F9` Stage Jump (`F9` arm + keys `1`, `2`, `3`, `4`).

- [x] **Task 2: River Math & Buoyancy Simulation (`Scripts/Core/RiverFlowBuoyancy.cs`)**
  - [x] Define `RiverMath` (`WorldW = 1040`, `WorldH = 1440`, `MapScale = 0.125` = `130m × 180m`).
  - [x] Implement `ToWorld3D()`, `RiverCenterMapX()`, `RiverHalfWidthMap()`, `IsInRiver()`.
  - [x] Implement sinusoidal wave bobbing + `-Z` current drift toward `Gunung Sampah`.

- [x] **Task 3: Player Controller & Level Spawner (`KaliPlayerController.cs`, `MapJsonImporter.cs`)**
  - [x] Build FP walk/sprint/boat toggle (`E`), FreeCam (`F`), Weather toggle (`R`), Scoop/Dredge (`Left Click`).
  - [x] Build `KALI > Load Default Purpose-Built Map` spawning 51 nodes from `kali-river-map.json` + JC prefabs.

- [ ] **Task 4: Prefab Integration & 20-Tool Extension (`Scripts/`) — *Awaiting Art Drop***
  - [ ] Extend `KaliPlayerController.TryScoopOrDredge()` to detect `MedicalWaste` tags/components and pass `usingSnakeGrabber` into `RiverGameManager.Instance.SecureMedicalWaste(bool)`.
  - [ ] Update `MapJsonImporter.cs` to swap building/terrain greybox primitives with Wesley's `SM_Env_*` prefabs + `SG_KaliWater` material, and attach Niki's `Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`, and `VFX_MonsoonRain`.
  - [ ] Build Playable Scene inside `unity/Assets/_Project/Scenes/` once all prefabs land.

- [ ] **Task 5: Academic ALP Report & Sidang Defense Prep**
  - [ ] Export screenshots from `F9` stages (`1..4`) and WebGL preview (`tools/play-3d.html`).
  - [ ] Finalize Academic ALP Report (SDG 6.3/11.5/14.1, Beer-Lambert + `RiverMath` equations, team split).

---

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate live **`F9 + 1..4`** stage jumps cleanly in 3 minutes without fumbles.
