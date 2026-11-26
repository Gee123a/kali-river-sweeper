# AI Implementation Plan: Niki (VFX, UI & Audio/Narrative Lead)

> **Instructions for AI**: You are the dedicated AI Unity VFX, UI & Audio assistant for **Nicholas Gerwin Mawardji (Niki)** on **KALI: Indonesian River Sweeper** (`Unity 2022.3.46f1 LTS URP`). Work strictly inside `VFX/`, `UI/`, and `Audio/`. Read Ivan's C# event signatures in `RiverGameManager.cs` before wiring any Canvas or Particle script so UI and VFX subscribe cleanly with zero merge conflicts.

---

## 1. Identity & Scope Boundaries

- **Owner**: Nicholas Gerwin Mawardji (Niki)
- **Student ID**: `0706012410015`
- **Track**: URP VFX Systems, uGUI / TextMeshPro Interfaces, Audio Design & Sidang Demo Flow
- **Unity Version Alignment**: Current workspace operates on Unity `2022.3.46f1 LTS`. To address `CVE-2025-59489` security vulnerabilities, team will coordinate either upgrading to patched Unity `2022.3.67f2` or migrating to patched Unity 6 (`6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging.
- **Git Contributor Hygiene**: Local personal git author commits only. Zero AI bot author attribution, zero `Co-Authored-By` trailers.
- **Primary Deliverables**:
  1. 4 VFX prefabs inside `Assets/_Project/VFX/`: `VFX_MonsoonRain`, `VFX_WaterSplashMuddy`, `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche`.
  2. 3 Responsive UI Canvases inside `Assets/_Project/UI/`: `Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`.
  3. River/storm/siren/scoop audio clips & mixer triggers (`Assets/_Project/Audio/`).
  4. Polished 3-minute Sidang live presentation script aligned to `F9 + 1..4` demo jumps.

### Allowed Files & Directories (READ & WRITE)
- `unity/Assets/_Project/VFX/**`
- `unity/Assets/_Project/UI/**` (including UI glue scripts inside `UI/Scripts/` subscribing to `RiverGameManager.Instance`)
- `unity/Assets/_Project/Audio/**`

### Strictly Forbidden (DO NOT MODIFY OTHER FOLDERS)
- `unity/Assets/_Project/Scripts/**`, `Data/**` *(Owned by Ivan - subscribe via public events only)*
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/Environment/**`, `Shaders/**` *(Owned by Wesley)*

### Context Files to Read
1. `AGENTS.md` (Public C# event signatures in `RiverGameManager.cs`)
2. `docs/DESIGN.md` (Exact `Siaga 4 -> 1` alert colors `#22C55E`, `#FACC15`, `#F97316`, `#F43F5E`)
3. `docs/HUD_SPEC_NIKI.md` (*Lembar Kalkir Zona Cahaya*: `#F4F2EC` 90% vellum ground, `#E11D8F` dichroic alert accent, `Barlow Condensed` + `IBM Plex Mono`, empty bottom-left & bottom-center while sailing, `BC_StationDockSheet` `[1][2][3][E]` inside station zone, interactive preview `docs/hud_reference_lembar_kalkir.html?preview=1`)
4. `docs/PRD.md` (3 Choices, 3-class waste hazards, 3 stations vs Pengepul, Sell-Lock/`Q` dump, 4 Endings, SDG targets 6.3 / 11.5 / 14.1)

---

## 2. Public C# Event Contracts (`RiverGameManager.Instance`)

Your UI & VFX components subscribe cleanly to these public members in `RiverGameManager`:
- `OnStateChanged` (`Action`, throttled ~10 Hz on continuous ticks): Refresh HUD metrics whenever player scoops trash, trades/gets fined at stations, suffers Medical prick or Biohazard DoT, unlocks tools, or flood level changes.
  - **Health & Hazards**: `playerHealth` / `maxPlayerHealth` (`0..100`), `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `infectionIncidents`.
  - **3-Class Cargo & Economy**: `rupiah`, `cumulativeEarnings`, `cargoCount` / `cargoCapacity`, `normalCargo`, `medicalCargo`, `biohazardCargo`, `wrongDiscardCount`, `totalFinesPaid`, `pengepulHazardDumped`.
  - **Linear Water Rise & Monsoon**: `currentWaterLevelY` (`-0.25m` to `2.45m+`), `IsBankOverflowing` (`>= 1.40m`), `IsSellLocked` (`>= 1.85m`), `floodPressure`, `SiagaLevel` (`4..1`), `waterClarity`, `gunungSampahHealth`, `monsoonCountdownRemaining` (`MM:SS` timer), `communityTrust`, `medicalWasteSecured`, `biohazardWasteSecured`.
  - **Tools & Unlocks**: `equippedToolIndex` (`1..20`), `highestUnlockedToolIndex` (`1..20`), `EquippedTool`, `galahUnlocked`, `sampanUnlocked`, `trashBoomActive`, `excavatorUnlocked`, `kampungBinsInstalled`.
- `OnToolUnlocked` (`Action<ToolDefinition>`) & `OnEquippedToolChanged` (`Action<ToolDefinition>`): Drive auto-unlock celebration toasts (`#01..#20`) and bottom tool badge updates.
- `OnHazardOrAlert` (`Action<string msg, bool isDanger>`): Show immediate red/purple warning banner on Medical needle prick, Biohazard DoT, wrong-station fine, or Sell-Lock block.
- `OnWeatherChanged` (`Action<bool isMonsoonStorm>`): Enables/disables `VFX_MonsoonRain` and storm ambient sound.
- `OnWaterSplash` (`Action<Vector3 pos>`): fired when player scoops trash or paddles; subscribe `WaterSplashEffect` here.
- `OnGunungTierBreached` (`Action<Vector3 pos>`): fired when `DamageGunungSampah()` breaks a dam tier; subscribe `TrashAvalancheEffect` here.
- `OnEndingTriggered` (`Action<GameEnding ending>`): Displays `Canvas_SDGImpactReport` tailored to **`TrueSdgVictory`**, **`CompromisedOceanFlush`**, **`FloodFail`**, or **`HealthFail`** using `recycledKg`, `flushedKg`, `medicalWasteSecured`, `biohazardWasteSecured`, `totalFinesPaid`, `pengepulHazardDumped`, and `communityTrust`.

---

## 3. Milestone Tasks (Prioritized)

### Completed on origin/niki-vfx (Awaiting Merge to main)
- [x] `4 URP VFX Prefabs (Assets/_Project/VFX/)`: `VFX_MonsoonRain` (already subscribed to `OnWeatherChanged`), `VFX_WaterSplashMuddy`, `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche`.
- [x] Initial `Canvas_HUD` Prototype (`UI/Prefabs/Canvas_HUD.prefab`, `UI/Scripts/KaliHudController.cs`): Barlow Condensed & IBM Plex Mono installed, core telemetry hierarchy (`TL_SurvivalFloodSheet`, `TC_EcologicalHydroRail`, `TC_ContextualAlertRail`, `TR_EconomyCargoLedger`, `C_CrosshairReticle`, `TL_ToolUnlockToast`).

### Priority 1: MVP Blockers (Kerjakan Sekarang - `git pull origin main` dulu!)
- [ ] **Task 1A: Wire VFX Event Hooks (`91fa930`)**: run `git pull origin main` (merge `main` into `niki-vfx`), then subscribe `WaterSplashEffect` -> `RiverGameManager.OnWaterSplash(Vector3)` and `TrashAvalancheEffect` -> `RiverGameManager.OnGunungTierBreached(Vector3)` and push to `niki-vfx`. *(Note: run `Window > TextMeshPro > Import TMP Essential Resources` locally if TMP fonts warn.)*
- [ ] **Task 1B: Finish `Canvas_HUD` per `docs/HUD_SPEC_NIKI.md`**: add `UI_Vellum9Slice.png`, `UI_Hatch45_Tile.png`, `UI_CrossHatch90_Magenta.png` sprites; build `BR_VellumHydroMap` contour map sprite + rotating player chevron; implement `BC_StationDockSheet` (`[1][2][3][E]` hidden outside station collider, keeping bottom-left/bottom-center clean while sailing); verify `1920x1080` and `1280x720` with zero overlap.
- [ ] **Task 1C: Build `Canvas_SDGImpactReport` (Primary MVP Loop Closer)**: ending/victory modal handling all **4 endings** (`TrueSdgVictory`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`), summarizing recycled vs flushed kg, Medical/Biohazard secured, wrong-station fines, Pengepul hazard dumps, and **SDG 6.3 / 11.5 / 14.1** educational verdict.

### Priority 2: Economy Shop & Audio (Setelah HUD & SDG Report Selesai)
- [ ] **Task 2: `Canvas_ShopBankSampah` (`Assets/_Project/UI/`)**: `DiscardWasteAtStation` / `DiscardAllAtStation`, `Gudang Pengepul` (`SellAllAtPengepul`), Choice B upgrades (`BuyKampungBins()`, `BuyUpgrade(UpgradeTier)`), 20-tool milestone selector (`SelectTool`), and Choice C emergency floodgate (`TriggerEmergencyFlush()`).
- [ ] **Task 3: Audio (`Assets/_Project/Audio/`)**: looping calm river vs heavy monsoon storm SFX, wet scoop splashes, needle-prick/Biohazard Geiger warning chime, wrong-station fine buzzer, tool unlock chime, and `Siaga 2/1` siren.

### Priority 3: Sidang F9 Demo Flow
- [ ] **Task 4: 3-Minute Live Sidang Demo Script**: synchronized to `F9 + 1`, `F9 + 2`, `F9 + 3` (Monsoon Overflow + Sell-Lock), `F9 + 4`.

---

## 4. Verification & Live Sidang Talking Points
- Test every UI panel at `1920x1080` and `1280x720` with zero overlapping text.
- Be ready to explain VFX particle emission/collision parameters, how C# events drive the `Siaga` warning feedback without polling every frame, and how `Canvas_SDGImpactReport` proves SDG consequences (**10% Problem & Message + 10% Presentation**).
