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
  4. Polished 3-minute Sidang live presentation script aligned to the normal-play demo flow (`T` time-of-day cycle).

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

### Priority 2: Economy Shop, Audio & End-Run SDG Parity
- [ ] **Task 2: `Canvas_ShopBankSampah` + `KaliShopController` (`Assets/_Project/UI/`)**: build `KaliShopController.cs` + `Canvas_ShopBankSampah.prefab` (`Sort Order = 20`, with `GraphicRaycaster`) for `Koperasi Desa (Kopdes)` & stations:
  - [ ] Subscribe to `KaliPlayerController.OnShopRequested` (`[E]` at `Koperasi Desa / Kopdes`), replacing the temporary `[1-4]` Kopdes keyboard fallback in `KaliPlayerController.cs`.
  - [ ] Wire 20-tool shop (`BuyTool(int)`, `SelectTool(int)`, `IsToolUnlocked(int)`, `IsToolOwned(int)`, reading `ToolDefinition.UnlockRupiah`), `BuyKampungBins()` (`RiverGameManager.KampungBinsCost`), `BuyUpgrade(UpgradeTier)` (`RiverGameManager.GetUpgradeCost(UpgradeTier)`), and Choice A/C `TriggerEmergencyFlush()`.
  - *Dependency*: Uses Ivan's `RiverGameManager` & `KaliPlayerController.OnShopRequested` already in `main`; notify Ivan once merged so `Main.unity` is re-baked and the fallback notice can retire.
- [ ] **Task 3: Audio (`Assets/_Project/Audio/`)**: create/wire ambient & SFX clips with clean event subscriptions (zero per-frame polling):
  - [ ] Calm river ambience loop vs heavy monsoon rain loop (`OnWeatherChanged`).
  - [ ] Kids laughter ambient bank SFX (for `Bocah-bocah` `npc_group` river zones).
  - [ ] Medical needle-prick warning SFX (`OnHazardOrAlert` / prick), Biohazard Geiger warning ticks (`IsBiohazardDotActive` / `BiohazardGraceRemaining`), and `Siaga 2 / 1` flood siren.
  - [ ] Wet scoop splashes (`OnWaterSplash`), wrong-station fine buzzer (`OnStationAuditReceipt`), and tool unlock chime (`OnToolUnlocked`).
  - *Dependency*: Subscribes to Ivan's `RiverGameManager` events + optional kid-zone anchors from Ivan's Ambient NPC system (`plan_ivan.md`).
- [ ] **Task 4A: `Canvas_SDGImpactReport` — `PartialSurvival` + `"Main Lagi"` Button (`UI/Scripts/SdgImpactReportController.cs`, `UI/Prefabs/Canvas_SDGImpactReport.prefab`)**:
  - [ ] Add `GameEnding.PartialSurvival` headline/body/SDG verdict in `FillCopy()` (currently handles only 4 endings).
  - [ ] Add `GraphicRaycaster` + `"Main Lagi"` button wired to `RiverGameManager.Instance.RestartRun()`, and auto-hide modal when `activeEnding == GameEnding.None` (fixes stuck overlay on `[R]` / retry).
  - [ ] Fix `TMP_EndingBody` word wrap and `Row_6` / `TMP_Sdg63` `2px` overlap; surface `ComputeSdgScorecard()` rank (`S/A/B/C/F`), `Rupiah`, `Tools Unlocked / 20`, and `infectionIncidents` parity.
  - *Dependency*: Consumes Ivan's `RestartRun()` & `ComputeSdgScorecard()` (already on `main`).

### Priority 3: HUD P0 Fixes & Sidang Demo Flow
- [ ] **Task 4B: HUD P0 Fixes (`UI/Scripts/KaliHudController.cs`, `HudMapLayout.cs`, `KaliHudPrefabBuilder.cs`)**:
  - [ ] Wire `Img_Hatch45Fill` (`Gunung Sampah`) via `RectMask2D` over tiled `RawImage` driven by `gunungSampahHealth`, and widen `Box_Cleared` so `"GUNUNG SAMPAH"` never spills onto hatch.
  - [ ] Fix `Strip_BiohazardTimer`: replace stretched `Image.Type.Filled` with tiled `RawImage` + `RectMask2D`, add `"BIOHAZARD · KE KARANTINA (K)"` label, and keep bar visible in `"PAPARAN AKTIF!"` state when `IsBiohazardDotActive == true` (instead of hiding at `0s`).
  - [ ] Wire `OnHazardOrAlert(string msg, bool isDanger)` into a visible contextual alert strip (stop dropping medical pricks, wrong-station fines, Sell-Lock, and `#13` dredge blocks).
  - [ ] Fix `BC_StationDockSheet`: hide `[1][2][3]` discard keys at `Kopdes` & `Dermaga` (`[E] Buka Kopdes`, `[E] Turun/Naik Sungai`), add clear `#F4F2EC` vellum box behind `DENDA` (`#B50E6F`), and sync `player.HasNearbyHub` immediately inside `TrySubscribePlayer()`.
  - [ ] Fix minimap coordinate alignment (`HudMapLayout.cs` matching `MapJsonImporter.cs` `(item.x, item.y)` origins) and add FIFO queue + word-wrap/ellipsis for `OnToolUnlocked` toasts.
  - *Dependency / Coordination*: Resolve open spec decisions with Ivan (Equipped Tool `#XX` pill vs transient toast, 4-pin vs 6-pin minimap legend) and apply P1/P2 uGUI hygiene (`raycastTarget = false` on non-interactive graphics, `Layer 5 (UI)`, zero-alloc `TMP_Text.SetText`, safe-area fitter) if time permits.
- [ ] **Task 5: 3-Minute Sidang Script with `T` Time-of-Day Demo (`docs/SIDANG_DEMO_SCRIPT.md`)**: finalize/sync the Bahasa Indonesia 3-minute live Sidang presentation script covering cleanup -> Kopdes -> **`T`** time-of-day cycling (`Golden Hour 17:24 -> Dusk 18:40 -> Night 22:00 -> Dawn 05:50 -> Noon 12:00`) -> `Siaga` HUD warnings -> `Canvas_SDGImpactReport` (`PartialSurvival` vs `TrueSdgVictory`).
  - *Dependency*: Reconcile baseline in `agy/sidang-play3d` with Ivan's final `Main.unity` bake and ALP report (`plan_ivan.md` Task 6).

---

### Priority 0-A: Core Mechanics v2 UI ([docs/MECHANICS_SPEC.md](./docs/MECHANICS_SPEC.md) §B, C, F)
- [ ] **Task 7A: Restyle what Ivan ships functional-first**: Accepts card replacing the `[1][2][3]`/DENDA dock sheet (station name, accepted class icon + price, cargo preview from `GetDepositPreview`; pink only for real harm like Pengepul hazards); 4-slot hotbar HUD bound to `OnHotbarChanged` (icon, name, reach/batch, prick %); shop trade-in slot picker + upgrades tab polish; objective pill bound to `OnObjectiveChanged`. Ivan made minimal edits in `KaliHudController.cs` / `KaliShopController.cs` marked `TODO(Niki)` — pull first to avoid conflicts.

- [ ] **Task 7B: Start, Pause & End menus + one visual system ([MECHANICS_SPEC.md](./docs/MECHANICS_SPEC.md) §I)**: `Canvas_StartMenu` (Mulai/Kontrol/Kredit/Keluar over a river fly-over), `Canvas_PauseMenu` (Lanjut/Kontrol/Pengaturan volume+sensitivity/Ulang/Keluar ke Menu), extend `Canvas_SDGImpactReport` (all 5 endings, rank, quests, Main Lagi/Menu). All bound to Ivan's `RiverGameManager.State` / `OnGameStateChanged` (replace his IMGUI fallback). Restyle the shop + Accepts card + role hotbar (role icon per slot, greyed "Beli di Kopdes" when empty) so every screen uses the same `docs/DESIGN.md` fonts, panels, colors and buttons.

### Priority 0: Progression & Village Life — Dialogue, Quest HUD & Audio
Spec: [docs/PROGRESSION_REDESIGN.md](./docs/PROGRESSION_REDESIGN.md) (evidence: [docs/PLAYTEST_PROGRESSION.md](./docs/PLAYTEST_PROGRESSION.md)). Goal: rewards are EARNED (trust tiers + quests), the village reacts and talks, and the SDG win is reachable for good play.
- [ ] **Task 6A: Dialogue UI (`UI/`)**: world-space speech bubble + `[E] Bicara` prompt, 1–2 lines, auto-hide after 4 s; subscribes to Ivan's `KaliNpcInteractable` events (no per-frame polling).
- [ ] **Task 6B: Quest HUD**: quest tracker pill (title + progress `2/3` + timer), "!" marker sync, Quest Complete / Failed stamp, **one** "Tier Baru Terbuka!" banner per tier (replaces 20 tool toasts), Kepercayaan Warga bar with tier ticks 30/50/70/85, combo "Setoran Bersih ×N" chip.
- [ ] **Task 6C: Bahasa script (`KaliNpcDialogue` line table, deliver as text/CSV for Ivan)**: 5 named villagers (Pak RT, Bu Siti, Pak Darto, Raka, Mbok Nah) × states (calm, dirty, storm, high trust, low trust) × quest offer/progress/done lines + chatter gossip pairs; short, natural kampung Bahasa.
- [ ] **Task 6D: Village audio**: talk blips / short voice barks per villager, kids cheer + splash, quest accept/complete stingers, combo tick, tier-open fanfare, evacuation shout in storm.
- [ ] **Task 6E: SDG report**: add "Misi Warga" section (quests done, trust tier reached, best combo) to `Canvas_SDGImpactReport`.

## 4. Verification & Live Sidang Talking Points
- Test every UI panel at `1920x1080` and `1280x720` with zero overlapping text.
- Be ready to explain VFX particle emission/collision parameters, how C# events drive the `Siaga` warning feedback without polling every frame, and how `Canvas_SDGImpactReport` proves SDG consequences (**10% Problem & Message + 10% Presentation**).
