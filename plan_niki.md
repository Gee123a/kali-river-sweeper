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
4. `docs/PRD.md` (3 Choices, 3-class waste hazards, surface swimming/stamina/drowning, 3 stations vs Pengepul, Sell-Lock/`Q` dump, 5 Endings, SDG targets 6.3 / 11.5 / 14.1)

---

## 2. Public C# Event Contracts (`RiverGameManager.Instance`)

Your UI & VFX components subscribe cleanly to these public members in `RiverGameManager`:
- `OnStateChanged` (`Action`, throttled ~10 Hz on continuous ticks): Refresh HUD metrics whenever player scoops trash, trades/gets fined at stations, suffers Medical prick or Biohazard DoT, unlocks tools, or flood level changes.
  - **Health & Hazards**: `playerHealth` / `maxPlayerHealth` (`0..100`), `swimStamina` / `maxSwimStamina` (`0..100`), `SwimStaminaNormalized`, `isPlayerSwimming`, `IsSwimming`, `IsDrowning`, `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `infectionIncidents`.
  - **3-Class Cargo & Economy**: `rupiah`, `cumulativeEarnings`, `cargoCount` / `cargoCapacity`, `normalCargo`, `medicalCargo`, `biohazardCargo`, `wrongDiscardCount`, `totalFinesPaid`, `unpaidFineDebt`, `pengepulHazardDumped`.
  - **Linear Water Rise & Monsoon**: `currentWaterLevelY` (`-0.25m` to `2.45m+`), `IsBankOverflowing` (`>= 1.40m`), `IsSellLocked` (`>= 1.85m`), `floodPressure`, `SiagaLevel` (`4..1`), `waterClarity`, `gunungSampahHealth`, `monsoonCountdownRemaining` (`MM:SS` timer), `communityTrust`, `medicalWasteSecured`, `biohazardWasteSecured`.
  - **Tools & Unlocks**: `equippedToolIndex` (`1..20`), `highestUnlockedToolIndex` (`1..20`), `EquippedTool`, `IsToolUnlocked(int)`, `IsToolOwned(int)`, `galahUnlocked`, `sampanUnlocked`, `trashBoomActive`, `excavatorUnlocked`, `kampungBinsInstalled`.
- `OnToolUnlocked` (`Action<ToolDefinition>`) & `OnEquippedToolChanged` (`Action<ToolDefinition>`): Drive Kopdes milestone-availability toast (`"Alat Baru Tersedia di Kopdes"`; bought via `BuyTool(int)`, no free auto-equip) and bottom tool badge updates.
- `OnHazardOrAlert` (`Action<string msg, bool isDanger>`) & `OnStationAuditReceipt` (`Action<StationAuditReceipt>`): Show immediate warning banner on Medical needle prick, Biohazard DoT, swim stamina / drowning alert, wrong-station fine, or Sell-Lock block.
- `OnWeatherChanged` (`Action<bool isMonsoonStorm>`): Enables/disables `VFX_MonsoonRain` and storm ambient sound.
- `OnWaterSplash` (`Action<Vector3 pos>`): fired when player scoops trash, paddles, or enters/swims in water; subscribe `WaterSplashEffect` here.
- `OnGunungTierBreached` (`Action<Vector3 pos>`): fired when `DamageGunungSampah()` breaks a dam tier; subscribe `TrashAvalancheEffect` here.
- `OnEndingTriggered` (`Action<GameEnding ending>`) & `OnEndingWithDiagnosisTriggered` (`Action<GameEnding, string>`): Displays `Canvas_SDGImpactReport` tailored to **`TrueSdgVictory`**, **`PartialSurvival`**, **`CompromisedOceanFlush`**, **`FloodFail`**, or **`HealthFail`** using `recycledKg`, `flushedKg`, `medicalWasteSecured`, `biohazardWasteSecured`, `totalFinesPaid`, `pengepulHazardDumped`, `communityTrust`, and `ComputeSdgScorecard()`.
- `KaliPlayerController` (`OnNearbyHubChanged`, `Action<bool isNear, DiscardStationType stationType, bool isKopdes, string hubName>` + `OnNearbyDermagaChanged`, `Action<bool isNear, bool isInBoat, string dermagaName>` + `OnSwimStateChanged` `Action<bool isSwimming>` + read-only `HasNearbyHub`, `NearbyStationType`, `NearbyIsKopdes`, `NearbyHubName`, `HasNearbyDermaga`, `NearbyDermagaIsInBoat`, `NearbyDermagaName`, `IsSwimming`): Emitted at ~10 Hz / on transitions when entering/exiting a station, Koperasi Desa (Kopdes), Dermaga boat port, or river swim state.
- `RiverMath` (`RiverFlowBuoyancy.cs`): World bounds `MinWorldX = -65f`, `MaxWorldX = 65f`, `MinWorldZ = -90f`, `MaxWorldZ = 90f` (`130m x 180m`).

---

## 3. Milestone Tasks (Prioritized)

### Merged to `main` (`a982cb1`)
- [x] `4 URP VFX Prefabs & Event Scripts (Assets/_Project/VFX/)`: `VFX_MonsoonRain` (`OnWeatherChanged`), `VFX_WaterSplashMuddy` (`OnWaterSplash`), `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche` (`OnGunungTierBreached`) - auto-placed by `MapJsonImporter.cs`.
- [x] `Canvas_HUD` Core + Sprites + Minimap (`UI/Prefabs/Canvas_HUD.prefab`, `UI/Scripts/KaliHudController.cs`): Barlow Condensed + IBM Plex Mono, `UI_Vellum9Slice`, `UI_Hatch45_Tile`, `UI_CrossHatch90_Magenta`, `UI_Contour`, `UI_Chevron`, HP ramp cells, Siaga dot/ruler, clarity fill, cargo counts, and alerts.

### Priority 1: MVP Blockers (Selesai di branch Niki — siap push ke `niki-vfx`)
- [x] **Task 1A: Wire `BC_StationDockSheet`, Minimap `RiverMath` & 720p/TMP Fixes**: subscribed `KaliHudController.cs` to `KaliPlayerController.OnNearbyHubChanged` and `OnNearbyDermagaChanged`, wrapped `DENDA` / `[E] JUAL SEMUA` onto 2 lines (`96x40px`, auto-size) for `1280x720`, wired `BiohazardGraceRemaining` to `Image.Type.Filled`, anchored `UI_Contour.png` to `RiverMath` with solid `B/M/K/P` + outline `KD` (Kopdes) pin & `DAM` at `y = 237.5`, regenerated 8.4 MB SDF fonts (`BarlowCondensed-Bold` & `IBMPlexMono-SemiBold`), and imported `Assets/TextMesh Pro/` (TMP Essentials). *(Run `Build HUD Sprites` + `Build Canvas_HUD` in Unity before final push.)*
- [x] **Task 1B: Build `Canvas_SDGImpactReport` (`SdgImpactReportController.cs`, `Canvas_SDGImpactReport.prefab`)**: initial ending/victory modal covering core 4 endings (`TrueSdgVictory`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`; `PartialSurvival` pending UI Task 2/4F sync), summarizing recycled vs flushed kg, Medical/Biohazard secured, wrong-station fines, Pengepul hazard dumps, and **SDG 6.3 / 11.5 / 14.1** educational verdict.

### Priority 2: Economy Shop & Audio (Kerjakan Sekarang)
- [ ] **Task 2: `Canvas_ShopBankSampah` (`Assets/_Project/UI/`)**: `KaliShopController.cs` + `Canvas_ShopBankSampah.prefab` for `Koperasi Desa (Kopdes)` & stations (`BuyKampungBins()`, `BuyUpgrade(UpgradeTier)`, 20-tool shop `BuyTool(int)` / `SelectTool(int)` / `IsToolUnlocked(int)` / `IsToolOwned(int)`, Choice A/C `TriggerEmergencyFlush()`, replacing the `[1-4]` Kopdes keyboard fallback in `KaliPlayerController.cs`). Hook: subscribe to `KaliPlayerController.OnShopRequested` to open the modal; read prices via `RiverGameManager.KampungBinsCost` / `GetUpgradeCost(UpgradeTier)` / `ToolDefinition.UnlockRupiah`.
- [ ] **Task 3: Audio (`Assets/_Project/Audio/`)**: looping calm river vs heavy monsoon storm SFX, wet scoop splashes, needle-prick/Biohazard Geiger warning chime, wrong-station fine buzzer, tool unlock chime, and `Siaga 2/1` siren.

### Priority 3: Sidang F9 Demo Flow
- [ ] **Task 4: 3-Minute Live Sidang Demo Script**: synchronized to `F9 + 1`, `F9 + 2`, `F9 + 3` (Monsoon Overflow + Sell-Lock), `F9 + 4`.

---

## 4. Verification & Live Sidang Talking Points
- Test every UI panel at `1920x1080` and `1280x720` with zero overlapping text.
- Be ready to explain VFX particle emission/collision parameters, how C# events drive the `Siaga` warning feedback without polling every frame, and how `Canvas_SDGImpactReport` proves SDG consequences (**10% Problem & Message + 10% Presentation**).
