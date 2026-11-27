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
  4. 53-node purpose-built level data (`kali-river-map.json`) & 1-click spawner with split West/East banks, elevated `Jembatan Utama`, 3 waste stations + `Gudang Pengepul`, `Koperasi Desa (Kopdes)`, Dermaga-only river ports, `RiverTrashSpawner`, and `PF_Trash_MedicalBag`/`SyringeBox` (`MapJsonImporter.cs`).
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
  - [x] Verify Unity `2022.3.46f1 LTS` Play Mode (`MapJsonImporter.EnsureUrpPipelineAssigned()`, 53 greybox objects, 0 compile/runtime errors).
- [x] **Task 4A: Main Scene, URP Assets, Auto-Wiring Hooks, Generated Prefabs & Core QA**:
  - [x] Save `unity/Assets/_Project/Scenes/Main.unity` (`EditorBuildSettings` index 0) and push `URP_KaliPipeline.asset`, `URP_KaliRenderer.asset`, and 23 generated prefabs (`20 PF_Tool_*`, `PF_Trash_MedicalBag`, `PF_Trash_SyringeBox`, `PF_ExcavatorAmfibi`).
  - [x] Add prefab/material/UI/VFX auto-wiring table (`MapJsonImporter.cs`), extract `GunungNodeController.cs` & `RiverWaterSurfaceFollower.cs` for clean `.unity` serialization, fix `KaliPlayerController` child-collider lookup & `RiverGameManager` single-ending DoT guard, and pass `7/7` Unity batchmode QA suites (`KaliCoreQaTests.cs`).

### Priority 1: MVP Blockers (Kerjakan Sekarang)
- [x] **Task 4B (Part 1): Merge `origin/niki-vfx` + Station Event & 4-VFX Importer Hooks**: merged `origin/niki-vfx` (`Canvas_HUD` + `Canvas_SDGImpactReport` + 4 VFX), added `KaliPlayerController.OnNearbyHubChanged` + `RiverMath` bounds, and added all 4 VFX prefabs + 3 UI prefab paths to `NikiRootPrefabs` / node hooks in `MapJsonImporter.cs` (re-run `KALI > Load Default Purpose-Built Map` after pulling Niki's 720p/minimap/TMP Essentials push).
- [x] **Task 4B (Part 2): Bake Merged UI & 4 VFX into `Main.unity`**: mount `UnitySSD` (`KYO 1 TB`), open Unity `2022.3.46f1`, run `KALI > Load Default Purpose-Built Map` + `KALI > QA > Run Core Verification`, test Play Mode end-to-end (`Canvas_HUD` + `Canvas_SDGImpactReport` + 4 VFX), and push updated `Main.unity`. Done: `75473b5` (9 JC trash prefabs + Main.unity bake, QA 7/7) and `e9e6820` (FBX metas); Play Mode verified at 1280x720 (HUD, station dock, ending pause `timeScale=0`).
- [ ] **Task 4C: Team Unity Security Lock & Git History Hygiene**: finalize team agreement on staying on `2022.3.46f1 LTS` for dev vs patching `CVE-2025-59489` (`2022.3.67f2` or `Unity 6`) before final build packaging, and scrub earlier AI bot / `Co-Authored-By` commits if approved.
- [ ] **Task 4D: Game Flow UX Overhaul — Pickup/Sell, Live Audit & Fail/Retry (`Scripts/Core/`, `Scripts/Player/`, `KaliCoreQaTests.cs`, `tools/play-3d.html`)**
  - **Scope**: *In* = Ivan's C# core/player/QA scripts, `kali-river-map.json`, `tools/play-3d.html`, and C# event hooks for Niki. *Out* = direct edits to Niki's `UI/**` prefabs/controllers (handoff contracts only).
  - **P0 — Fail & Retry Loop (Eliminate Hard-Locks & Accidental Loss)**:
    - [ ] Add `RiverGameManager.RestartRun()` resetting all gameplay/SDG/audit counters, water level, cargo, `GunungNodeController` nodes, active/piled trash, spawner, `Time.timeScale = 1f`, and player/boat spawn transform; bind `[R]` instant retry hotkey when `activeEnding != GameEnding.None` and expose `RestartRun()` callback for Niki's `Canvas_SDGImpactReport`.
    - [ ] Fix `ResetStageState()` (`F9`) to reset all run metrics (`recycledKg`, `flushedKg`, `totalScooped`, `medicalWasteSecured`, `biohazardWasteSecured`, `infectionIncidents`, `wrongDiscardCount`, `totalFinesPaid`, `pengepulHazardDumped`, `communityTrust`).
    - [ ] Guard `TriggerEmergencyFlush()` (`Shift + X` in `KaliPlayerController.cs` + button in `play-3d.html`) behind `IsSellLocked` (`waterY >= 1.85m`) AND a `1.5s` hold or 2-step confirmation check so calm-weather misclicks cannot end a run.
    - [ ] Split `300s` Monsoon survival from `TrueSdgVictory` (require `gunungSampahHealth <= 0.01f` for `TrueSdgVictory`; `300s` survival with Gunung intact triggers `PartialSurvival` / partial-win state) to prevent AFK-camping exploits.
    - [ ] Add `EndingDiagnosis` (exact cause-of-death + 1-line counterplay tip) to `OnEndingTriggered` payload; in `tools/play-3d.html`, replace `window.location.reload()` with fast in-place `resetGame()` skipping `#introModal`, fix `rawDt` → `dt` movement leak while modals are open, and add `"Lihat Sungai"` fail inspection toggle.
  - **P0 — Safe `[E]` Deposit & Core Pickup Fixes**:
    - [ ] Fix `[E]` footgun: add `RiverGameManager.DiscardLegalAtStation()` so `[E]` at `Bank Sampah`, `Pos Medis B3`, and `Karantina Biohazard` deposits **only** the legal matching waste class (matching Niki's `"[E] Setor Aman"` label with zero accidental fines); keep `[1]/[2]/[3]` for explicit class discard (with fine on mismatch) and `[E]` = `SellAllAtPengepul()` at `Gudang Pengepul` (sync both C# and `play-3d.html`).
    - [ ] Stop full-cargo scoop fall-through in `KaliPlayerController.TryScoopOrDredge()`: return early with `"Kargo penuh!"` alert instead of silently hitting barrier pile or dredging `Gunung Sampah`.
    - [ ] Fix `#11–#20` Medical prick regression (`ToolCatalog.cs` / `RiverGameManager.cs`): once `#10 Capitan Ular` is unlocked (`highestUnlockedToolIndex >= 10`), enforce `0%` Medical prick risk so auto-equipping higher tools never strips safety.
    - [ ] Prevent click-to-lock pointer in `play-3d.html` from immediately firing `performScoop()` on the first canvas click.
  - **P1 — Live Auditing, Trust Stakes & Dynamic SDG Scorecard**:
    - [ ] Emit `OnStationAuditReceipt` (Pass `LOLOS SORTIR` vs Violation `PELANGGARAN B3` + Rupiah/Trust delta) on every station transaction for instant micro-feedback (wire toast/badge in `play-3d.html` + handoff hook for Niki's `KaliHudController`).
    - [ ] Add live `communityTrust` (`0–100`) economic stakes: `Trust >= 70` (**Terpercaya**) grants `+15%` legal station payout; `Trust < 25` (**Sidak DLH / Audit Alert**) imposes `-25%` payout penalty until Trust recovers `>= 30` via legal sorting.
    - [ ] Close the `0 Rp` fine loophole: track unpaid fine debt (deducted from next legal payout or escalating directly into Trust Audit penalty) instead of logging unpaid fines as `totalFinesPaid`.
    - [ ] Add `RiverGameManager.ComputeSdgScorecard()` returning dynamic `S/A/B/C/F` rank and real pass/fail verdicts for SDG `6.3`, `11.5`, and `14.1` from actual run stats (`waterClarity`, `wrongDiscardCount`, `pengepulHazardDumped`, `communityTrust`, `gunungSampahHealth`); expose to Niki's `SdgImpactReportController` and sync all missing stats (`wrongDiscardCount`, `waterClarity`, `flushedKg`) into `play-3d.html`'s report grid.
  - **P1 — Ergonomics, Navigation & Shop Polish**:
    - [ ] Emit `KaliPlayerController.OnAimTargetChanged` (target waste class, reach state, active Medical prick `%`) so crosshair previews hazard class before clicking (implement live reticle badge in `play-3d.html` + hook for Niki).
    - [ ] Extend station dock triggers/buoys toward riverbanks (`kali-river-map.json` + `play-3d.html`) so players can sell directly from boat without sprinting `24–45m` inland during a `10s` Biohazard DoT timer, and add bank climb-out recovery so walking off into `-2.0m` riverbed cannot trap the player.
    - [ ] Require `0.5s` hold on `[Q]` High-Ground Dump, surface pre-Sell-Lock Trust penalty in toast, and keep `Pos Medis B3` emergency triage (`+10 HP`, `Rp 0`) accessible during `Sell-Lock` (`>= 1.85m`) to avoid unhealable death spirals.
    - [ ] Replace blind `Koperasi Desa (Kopdes)` auto-buy fallback (`KaliPlayerController.cs`) with explicit upgrade selection keys (`1–4`, reconciling `sampanUnlocked` vessel gating; aligns with Task 5B removal of dead `Galah4m`) until Niki's `Canvas_ShopBankSampah` subscribes to `OnShopRequested`; clamp/demo-gate `F` Free-Cam so players cannot clip inside terrain.
  - **Validation (`KaliCoreQaTests.cs` & Browser Smoke Test)**:
    - [ ] Add Unity QA assertions covering `RestartRun()`, safe `[E]` legal-only deposit, `#11–#20` prick safety lock, `Trust < 25` / `>= 70` audit payout modifiers, `EmergencyFlush` Sell-Lock + confirm guard, and dynamic `ComputeSdgScorecard()` ranks; verify all `KaliCoreQaTests` suites pass in batchmode and smoke-test full pickup → sell → audit → fail → retry loop in `tools/play-3d.html`.
- [ ] **Task 4E: Repo Tidiness, Branch Sync & Team Alignment (Ponytail Audit)**
  - [x] **Sync `main` & commit dirty Task 5A**: pull/rebase `origin/main`, commit Task 5A C# hardening + `unity/ProjectSettings/ProjectVersion.txt` + missing parent folder metas (`unity/Assets/_Project/{Lighting,UI,VFX}.meta`) to stop teammate GUID churn. Done in `75f4d42` (Task 5A + folder metas); verified: Unity batch QA 10/10 suites, 436 asserts, 0 compile errors.
  - [x] **Merge Wesley & build JC Trash/Product prefabs**: merged `origin/wesley-env-shaders` (`SG_KaliWater`, `SG_TrashTriplanar`, `SG_EnvWeathered`, `PintuAirSiaga1`, `JembatanUtama`, `GunungSampah_3Tiers`), built `PF_Trash_AquaBottle_600ml`, `PF_Trash_AquaGalon_19L`, and 9 `PF_Product_*` prefabs, re-baked `Main.unity`, and passed `10/10` `KaliCoreQaTests` (`508` asserts). *(Remaining branch cleanup: prune merged remote branches `jc-excavator-tools`, `jc-trash-brands`, `niki-vfx`, `wesley-env-shaders`; salvage `jc-local-props` `Lighting/` + equipment FBXs onto a fresh branch.)*
  - [ ] **Purge local/repo clutter & tighten `.gitignore`**: delete `.impeccable/` (`25.98 MB`), `PRODUCT.md` (wrongly states `Platform: web`), `docs/hud_reference_lembar_kalkir.html`, empty `src/` & `assets/`, `unity/Assets/_Project/Shaders/.gitkeep`, local `__pycache__`; move 19 ignored `docs/` renders out of repo & `git rm --cached` the 3 legacy tracked `docs/*.png`s; add `.impeccable/`, `PRODUCT.md`, `docs/*.html`, `blender/**/*.png` to `.gitignore`.
  - [ ] **Fix CI tracker flapping & duplicate formats**: (sorted `matched` + ext_rank priority landed in `75f4d42`; xlsx decision still open) sort `matched` deterministically in `.github/scripts/sync_tracker.py` (fixes random status flips), drop duplicate `docs/KALI_Asset_Master_Tracker.xlsx` ONLY if unused (CRITICAL: keep `docs/KALI_Asset_Master_Tracker.csv` — the live Google Sheet `A1` uses `=IMPORTDATA("https://raw.githubusercontent.com/Gee123a/kali-river-sweeper/main/docs/KALI_Asset_Master_Tracker.csv")`), and stop `.github/workflows/sync-asset-tracker.yml` from auto-committing to `main` on every branch push (`19/73` = 26% of history).
  - [ ] **Fix doc/tracker/QA drift**: replace 9 legacy generic trash names (`PF_Trash_AquaBottle_600ml`, etc.) with the 9 shipped parody-brand prefabs across `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `plan_jc.md`, `KALI_Asset_Master_Tracker.tsv`, and `KaliCoreQaTests.cs:154`; keep tracker node counts (`53` nodes) synced, remove `Pos Sortir`, rename `Toko Alat` -> `Koperasi Desa (Kopdes)`, specify `Warung Madura`, and document `Dermaga` exclusive river ports.
  - [ ] **Enforce team guardrails & MVP freeze**: delete remote branches on merge, never edit another member's `plan_*.md` on feature branches, always commit parent folder `.meta`s, and freeze decorative props until the 4 MVP blockers land — **Wesley** (3 stations + Pengepul + `KoperasiDesa`), **JC** (`PF_Trash_BiohazardDrum`, `PF_LightingRig` + `VolumeProfile_*`, `PF_Prop_TrashBoomSegment`), **Niki** (`Canvas_ShopBankSampah` -> `OnShopRequested`, minimal `Audio/`).
- [ ] **Task 4F: HUD Wiring, Resource Parity & Unity uGUI Framework Remediation (Full HUD Audit)**
  - **Open Decisions (Resolve Before Touching `UI/`)**:
    - [ ] Decide **Equipped Tool UX** (`OnEquippedToolChanged`): compact `#XX` pill vs transient switch toast (reconciles `plan_niki.md` L46 vs `HUD_SPEC_NIKI.md` L93 empty bottom-left).
    - [ ] Decide **Minimap Pin Scope**: keep 6 pins (`B/M/K/P + S/T`) vs strict 4 pins (`B/M/K/P`) in `HUD_SPEC_NIKI.md` L89.
    - [ ] Confirm **Ownership Split**: Ivan handles Core C# + `Main.unity` `EventSystem` + spec alignment; hand off `UI/**` items to Niki (or coordinate joint PR if Niki approves).
  - **P0 — Core Contract & Scene Blockers (Ivan Owned: `Scripts/Core/`, `Scripts/Player/`, `Main.unity`, `docs/`)**:
    - [ ] **Fix event-ordering race (`RiverGameManager.cs` L299-333)**: move `totalScooped++` and `SyncCargoTotal()` *before* `ApplyPlayerDamage()` / `RaiseAlert()` so `OnHazardOrAlert` / `HealthFail` never broadcast stale `cargoCount` alongside updated per-class counts.
    - [ ] **Fix core resource bugs (`RiverGameManager.cs`, `KaliPlayerController.cs`)**: change `IsToolUnlocked(int index)` (`L570`) from `index >= 0` to `index >= 1`; guard `BuyUpgrade(UpgradeTier)` (`L583-591`) against duplicate purchase spend; gate `TryToggleBoat()` (`L364-402`) on `gm.sampanUnlocked` (or align with Task 4D); fix `piledRiverTrashCount` (`L169, L269`) desync with physical barrier `RiverTrashItem`s; clear `activeRiverTrashCount`/`piledRiverTrashCount` on `CompleteCleanBreach()` (`L671-683`). *(Note: `ResetStageState()` SDG reset & `RestartRun()` tracked in Task 4D.)*
    - [ ] **Expose missing player states for HUD (`KaliPlayerController.cs`)**: add change events/properties for `isInBoat`, `isFreeCam`, and tool scoop cooldown progress (`nextScoopTime`).
    - [ ] **Add `EventSystem` (`InputSystemUIInputModule`) to `Main.unity` / `MapJsonImporter.cs`**: currently 0 `EventSystem` in scene (breaks all clickable UI); guard `KaliPlayerController` mouse scoop/lock with `EventSystem.current?.IsPointerOverGameObject()`.
    - [ ] **Reconcile HUD spec drift (`docs/DESIGN.md`, `docs/HUD_SPEC_NIKI.md`)**: remove conflicting dark-navy tokens (`#0F172A`, `#F43F5E`) from `DESIGN.md` so *Lembar Kalkir Zona Cahaya* (`#F4F2EC`, `#E11D8F`/`#B50E6F`) is the single source of truth; fix `+Z` compass arrow direction in reference docs.
  - **P0 — Broken HUD Wiring & Missing UI (Niki Handoff / `UI/`)**:
    - [ ] **Wire `Img_Hatch45Fill` (`Gunung Sampah`)**: scale via `RectMask2D` over tiled `RawImage` driven by `gunungSampahHealth` (currently static 100%) and widen `Box_Cleared` (`132px` -> full label width) so `"GUNUNG SAMPAH"` never spills onto hatch.
    - [ ] **Fix `Strip_BiohazardTimer` (`KaliHudController.cs` L385-397, `KaliHudPrefabBuilder.cs` L178-195)**: replace 24.4× stretched `Image.Type.Filled` with tiled `RawImage` + `RectMask2D`; add `"BIOHAZARD · KE KARANTINA (K)"` label; when `IsBiohazardDotActive == true` (`grace == 0`), keep bar visible in active `"PAPARAN AKTIF!"` state instead of hiding at `fillAmount = 0` / `"0s"`.
    - [ ] **Wire `OnHazardOrAlert(string msg, bool isAlert)` (`KaliHudController.cs` L217-220)**: stop dropping payload; render medical pricks (`-18 HP`), wrong-station fines, Sell-Lock, `#13` dredge blocks, and `F9` prompts in a contextual alert strip.
    - [ ] **Fix `BC_StationDockSheet` (`KaliHudController.cs` L223-258)**: hide `[1][2][3]` discard keys at `Koperasi Desa (Kopdes)` and `Dermaga` (`[E] Buka Kopdes`, `[E] Turun/Naik Sungai`); add cleared `#F4F2EC` vellum box behind `DENDA` text & switch `#F43F5E` -> `#B50E6F`; sync `player.HasNearbyHub` immediately inside `TrySubscribePlayer()`.
    - [ ] **Fix minimap coordinate alignment (`HudMapLayout.cs` L13-30)**: match `MapJsonImporter.cs` L465 `(item.x, item.y)` origins (removes `+34..+48` map-unit pin drift and `+87.5` unit / `~11m` Dam marker offset).
    - [ ] **Fix `Canvas_SDGImpactReport` (`SdgImpactReportController.cs`)**: add `GraphicRaycaster` + `[Main Lagi]` button wired to `RiverGameManager.RestartRun()`; auto-hide modal when `activeEnding == GameEnding.None` (fixes stuck overlay on `F9` reset); enable word wrap on `TMP_EndingBody` (stops horizontal overflow); fix `2px` gap between `Row_6` and `TMP_Sdg63`; add `Rupiah`, `Tools Unlocked / 20`, and `Infection Pricks` parity.
    - [ ] **Build missing `Canvas_ShopBankSampah.prefab` + `KaliShopController.cs`** (`Sort Order = 20`, with `GraphicRaycaster`): subscribe to `KaliPlayerController.OnShopRequested` so `Koperasi Desa (Kopdes)` stops silent auto-buying.
    - [ ] **Queue `OnToolUnlocked` toasts & fix clipping**: add FIFO toast queue so multi-tool milestone unlocks never overwrite each other; enable word wrap/ellipsis on `TMP_ToastText` (fixes `#19 Penebas Gergaji Ganda · BISA KERUK` overflow).
  - **P1 — Unity 2022.3 URP uGUI Framework & Performance Hygiene (Niki Handoff / `UI/`)**:
    - [ ] **Split monolithic `Canvas_HUD` (118 GOs)**: separate into `Canvas_HUD_Static` (vellum sheets, tape, contour map, static labels), `Canvas_HUD_Dynamic` (bars, live TMP counters, chevron), and `Canvas_HUD_Contextual` (dock, toast, alerts) so 10 Hz / 15 Hz updates stop rebuilding the entire HUD mesh.
    - [ ] **Fix `raycastTarget`, `GraphicRaycaster` & `Layer 5 (UI)`**: disable `raycastTarget` by default on all non-interactive graphics (currently `116/116` HUD + `23/23` SDG = `true`); add `GraphicRaycaster` *only* on interactive canvases (`Shop`, `SDGReport`, clickable `Dock`); assign `Layer 5 (UI)` recursively to all UI prefabs; replace `Clear` container `Image`s (`TC_ContextualAlertRail`, `C_CrosshairReticle`, `Key_0..3`, strips) with pure `RectTransform` holders.
    - [ ] **Eliminate 10 Hz GC allocs & layout rebuilds (`KaliHudController.cs`)**: cache last-rendered primitives and update via `TMP_Text.SetText()` only on delta (stops ~14+ string allocs/tick); convert `clarityFill` from `sizeDelta` mutation to `Image.Type.Filled` (`fillAmount`); read `RiverGameManager.BaseWaterLevelY` & `fatalFloodWaterY` instead of hardcoded `-0.25f`/`2.45f`; pause `UpdateMap()`/`UpdateToast()` when `activeEnding != GameEnding.None`; add `OnEnable()` symmetry & reset `toast` on `OnDisable()`.
    - [ ] **Fix TMP shader channels, font assignment & serialization (`KaliHudPrefabBuilder.cs`)**: enable `AdditionalCanvasShaderChannels.TexCoord1` on all Canvases; replace `HasDigit()` font heuristic (which wrongly gives Mono font to `"MEDIS B3"` labels and Sans to `#XX` toasts) with explicit `FontRole.Display` / `FontRole.Mono`; bake full ASCII + `·—•≥` fallback glyphs; serialize `[SerializeField]` refs in prefab builder instead of 40+ runtime `transform.Find()` paths.
    - [ ] **Responsive layout & safe area**: wrap HUD root in `Screen.safeArea` fitter; collapse `TC_ContextualAlertRail` dynamically (remove 32px gap when Biohazard strip is hidden while Sell-Lock is active).
  - **P2 — Spec Polish & Game HUD UX Parity (Niki Handoff / `UI/`)**:
    - [ ] Wire **Equipped Tool indicator** (`OnEquippedToolChanged`: `#01..#20`, Medical prick `%`, Gunung dredge badge) per Open Decision #1.
    - [ ] Add missing visual states from `HUD_SPEC_NIKI.md`: `CeilToInt` for living HP (`0.1..0.49` never shows `"0"`), Bank Overflow (`+1.40m..+1.84m`) amber warning, full-cargo magenta highlight (`cargoCount >= cargoCapacity`), `3px` colored cargo class top-borders, `BADAI` cell magenta tint, `#F4F2EC` crosshair light halo, minimap `20%` River Teal sightline cone, and `180ms` (`scale 0.97 -> 1`) entrances + `360ms` wrong-station fine shake.

### Priority 2: Environment, Trash & Shop Integration (Setelah Prefab Tim Masuk)
- [ ] **Task 5: Prefab & Shader Wiring (`MapJsonImporter.cs`, `Main.unity`)**: wire Wesley's `SM_Env_*` + `SG_KaliWater` + 3 Station colliders, JC's 9 Normal trash + `SM_Trash_BiohazardDrum` + `PF_LightingRig`, and Niki's `Canvas_ShopBankSampah` + `Audio/`. Shop hook ready: KaliPlayerController.OnShopRequested (fires on [E] at Koperasi Desa / Kopdes; legacy auto-buy fallback only when no UI subscribes), RiverGameManager.KampungBinsCost / GetUpgradeCost(UpgradeTier) / IsToolUnlocked(int); tools auto-unlock by cumulative Rupiah (no BuyTool).
- [x] **Task 5A: Core wiring hardening**: free-cam gates on station keys + Shift+X, scoop falls through to pile/Gunung when nothing scooped, R monsoon toggle demo-gated (F9 armed), F9 stage jumps clear live trash, deterministic Tick(dt) for QA, spawner collider fitted to mesh, Pintu Air pile trigger spans full water range, deterministic trash clusters, terrain MeshCollider, prefab hitbox proportionality QA. Play Mode verified at 1280x720 after Kopdes/Dermaga merge: 5 hubs resolve (Kopdes shop event, no spend), Dermaga Awal board/disembark, on-foot river guard blocks 30.5m step, scoop -> Pengepul sell, gravity single-applied (duplicate HandleMove block removed), 0 console errors.
- [ ] **Task 5B: Ponytail Codebase Trim (C#, Packages, Tools & Docs)**
  - [ ] **Unity C# (`Scripts/`)**:
    - [ ] `native` (`~179L`): pick one Unity input API and delete dual `#if ENABLE_INPUT_SYSTEM` / `ENABLE_LEGACY_INPUT_MANAGER` shims + `KeyAction` enum (`KaliPlayerController.cs`, `RiverGameManager.cs`).
    - [ ] `shrink` (`~62L`): merge `DiscardSingleAtPengepul`/`SellAllAtPengepul` into `DiscardAtPengepul(WasteClass?)` + 4-row `F9` stage config table (`RiverGameManager.cs`).
    - [ ] `shrink` (`~55L`): share one `Renderer.bounds` & fallback trash primitive helper across `MapJsonImporter.cs` and `RiverTrashSpawner.cs`.
    - [ ] `delete` (`~47L`): remove dead `BuildSplitBanksAndRiver` greybox terrain fallback in `MapJsonImporter.cs` (`SM_Env_RiverValleyTerrain.fbx` shipped).
    - [ ] `delete` (`~43L`): delete zero-caller legacy APIs (`TryAddCargo`, `SecureMedicalWaste`, `DumpAtBurnPit`, `SellAtBankSampah`, `UnlockSandboxDemo`, `galahUnlocked`/`Galah4m`, `ToolCatalog.IsSnakeGrabber`).
    - [ ] `stdlib` (`~23L`): replace custom `Assert`/`AssertApprox` in `KaliCoreQaTests.cs` with `UnityEngine.Assertions.Assert`.
    - [ ] `yagni` (`~17L`): delete `RiverWaterSurfaceFollower.cs` (+ `.meta`); sync water `y` directly in `RiverGameManager.NotifyState()`.
  - [ ] **Unity Packages (`unity/Packages/manifest.json`)**: after confirming zero team use, prune 9 unused packages/modules (`animation.rigging`, `cinemachine`, `collab-proxy`, `probuilder`, `splines`, `timeline`, `visualeffectgraph`, `modules.ai`, `modules.terrain`; optionally `ide.rider`, `ide.visualstudio`, and `inputsystem` if standardizing on legacy input).
  - [ ] **Web Tools (`tools/`)**:
    - [ ] `tools/map-editor.html` (`~1,212L`): delete speculative 2.5D iso renderer (`drawIso`), delete unimported `zones`/circle-lasso + `footpaths`/`flowSteps`, fetch `kali-river-map.json` instead of hardcoded builders, replace 14-branch `drawItem2D()` with data table.
    - [ ] `tools/play-3d.html` (`~140L`): fetch `kali-river-map.json` directly (drop hardcoded map + `localStorage` shim), replace 6 station wrappers with `STATION_SPECS` table.
  - [ ] **Docs & Blender Coordination** *(keep `blender/*.blend` for 30% Process rubric)*:
    - [ ] `shrink` (`~76+L`): consolidate overlapping onboarding docs (`CLAUDE.md`, `docs/NIKI_UNITY_QUICKSTART.md`, repeated team tables) into `AGENTS.md` / `PRD.md` / `ARCHITECTURE.md` / `DESIGN.md`.
    - [ ] Coordinate with JC/Wesley on `blender/` cuts (`~604L`): hoist duplicated mesh helpers (`_add/_cyl/_seg/_box/_torus/_cone/_ball/_disc_y/_recentre`) into `tools_common.py`, fold `qa_spec_check.py` into `test_export.py`, use `mathutils.Vector` in `excavator_mesh.py`, make `head_dir` optional in `tools_common.assemble()`, remove 13 unused imports.

### Priority 3: Sidang F9 Verification, Build & ALP Report
- [ ] **Task 6: Academic ALP Report & Sidang Defense Prep**: `F9` stage screenshots (`1..4`), WebGL/PlayMode verification, and final ALP Report.

---

## 3. Verification & Live Sidang Talking Points
- Explain **Beer-Lambert turbidity interpolation** (`_WaterClarity` global float driving shader opacity/absorption).
- Explain **`RiverMath` spline projection** (`CenterX` sinusoid, bridge chokepoint compression, `2.2x` monsoon current multiplier).
- Demonstrate live **`F9 + 1..4`** stage jumps cleanly in 3 minutes without fumbles.
