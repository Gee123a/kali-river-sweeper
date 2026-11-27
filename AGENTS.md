# AGENTS.md — Master AI Agent Rules (KALI: Indonesian River Sweeper)

> **AI Agent Instructions**: Read this file before modifying any script, prefab, 3D model, shader, UI, or scene in this repository. This project is the **IMT01303501 Computer Graphics** Final Project (ALP, Universitas Ciputra Surabaya — **GAME Track**, targeting Grade A **85–100%** against `20261-CG-Penilaian ALP.pdf`).

---

## 1. Team & Ownership Architecture

To eliminate Unity/Blender merge conflicts (especially `.unity`, `.prefab`, `.meta`, `.fbx`) and ensure every member owns verifiable proof for the **30% Understanding of the Process** defense criterion, every agent and contributor must work strictly inside their assigned directories inside `unity/Assets/_Project/`:

| Member | Role | Student ID | Primary Scope & Owned Directories |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso (Ivan)** | **Coordinator & Core Lead** | `0706012410029` | Scope, schedule, docs, shared C# contracts lock, Git integration, gameplay physics & level spawner:<br>• `unity/Assets/_Project/Scripts/` (`Core/`, `Player/`, `Editor/` — incl. `KaliFieldGuideOverlay` `[H]` guide + 11-suite `KaliCoreQaTests`)<br>• `unity/Assets/_Project/Data/` (`kali-river-map.json`)<br>• `tools/` (`play-3d.html`, `map-editor.html`) |
| **Jason Christopher (JC)** | **Props, 3D, Rigging & Lighting Lead** | — | Authentic Indonesian trash props (`Normal`, `MedicalBag`, `SyringeBox`, `Biohazard`), 20 scavenging tools (`PF_Tool_*` trigger/disabled while equipped), vessels, hydraulic IK rig, Unity lighting & Post-FX:<br>• `blender/**` (`blender -b -P blender/build_all.py`)<br>• `unity/Assets/_Project/Props/` (`Trash/`, `Tools/`, `Equipment/`)<br>• `unity/Assets/_Project/Rigging/` (`SK_ExcavatorAmfibi.fbx`, IK arm, pistons)<br>• `unity/Assets/_Project/Lighting/` (`KaliLightingBuilder.cs`, `PF_LightingRig`, `VolumeProfile_*`, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`) |
| **Wesley Goeinawan (Wesley)** | **Environment Architecture & Shaders Lead** | `0706012410011` | Custom 3D Indonesian riverbank architecture (`SM_Env_*` FBX meshes incl. `+Z` `Pintu Air`, `Pos Medis B3`, `Karantina Biohazard`, `Gudang Pengepul`) + URP Shader Graphs:<br>• `unity/Assets/_Project/Environment/` (`Meshes/`, `Materials/`, `Textures/`, `Prefabs/`)<br>• `unity/Assets/_Project/Shaders/` (`SG_KaliWater.shadergraph` `+V` flow, `SG_TrashTriplanar.shadergraph`) |
| **Nicholas Gerwin Mawardji (Niki)** | **VFX, UI & Audio/Narrative Lead** | `0706012410015` | URP particle systems, Canvas HUD (`playerHealth`, `swimStamina`, 3-class cargo, DoT/Sell-Lock/`Q` dump, Monsoon timer, Kopdes tool milestone toast)/shops/end-run SDG report (`5` endings), sound effects, Sidang presentation flow:<br>• `unity/Assets/_Project/VFX/` (`VFX_MonsoonRain`, `VFX_WaterSplashMuddy`, `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche`)<br>• `unity/Assets/_Project/UI/` (`Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`)<br>• `unity/Assets/_Project/Audio/` |

**Zero-Touch Scene Rule**: Only **Ivan** edits shared main scene hierarchy or `MapJsonImporter.cs` integration hooks directly unless explicitly coordinated. Other members build self-contained **Prefabs**, **Materials**, **Shaders**, and **FBX** assets inside their own owned folders so `MapJsonImporter.cs` or Ivan's integration branch wires them cleanly with zero `.unity` YAML merge conflicts.

---

## 2. Shared Contracts & Single Source of Truth

All scripts, shaders, 3D meshes, colliders, and UI panels must obey these hard-coded contracts already live in `unity/Assets/_Project/Scripts/`:

1. **World Scale & River Channel Math (`RiverMath` in `Scripts/Core/RiverFlowBuoyancy.cs`)**:
   - `MapScale = 0.125f`, `WorldW = 1040f`, `WorldH = 1440f` $\rightarrow$ **Exact Unity terrain size: `130m (X) × 180m (Z)`**, centered at origin `(0, 0, 0)`.
   - Mapping formula: `ToWorld3D(mapX, mapY, elev) = ((mapX - 520) * 0.125, elev, (mapY - 720) * 0.125)`.
   - River centerline curve: `CenterX(mapY) = 520 + sin((mapY / 1440) * PI * 1.6) * 58`, base width `22.5m` (`180 * 0.125`), narrowing at central bridge choke (`mapY = 740`), widening at `southBay` (`mapY = 1220`) and northern retention basin (`mapY < 320`).
   - Current direction: Debris floats toward **`+Z`** downstream (from upstream `-Z` `Gunung Sampah` toward downstream `+Z` `Pintu Air` pile-up barrier at `Z = +76m`..`+83.75m`). Baseline water sits at `Y = 0.0f` and scales linearly with `TotalTrashInRiver` (`waterLevelY = -0.25f + trashInRiver * 0.020f`); dry riverbank land sits at `Y = +1.40m` (`Overflow >= 1.40m`, `Sell-Lock >= 1.85m`, `Fatal Flood >= 2.45m`).
2. **Global Water Shader Contract (`RiverGameManager.cs`)**:
   - `RiverGameManager` broadcasts `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` on startup and throttled (`~10 Hz`) `NotifyState()` updates (`0.05f` polluted muddy brown $\rightarrow$ `1.0f` pristine turquoise).
   - **Wesley's `SG_KaliWater`** Shader Graph Blackboard MUST declare a Float property with exact Reference Name **`_WaterClarity`** and scroll dual normals along **`+V`** (`+Z` downstream).
3. **Collider & Prefab Path Contracts (`KaliPlayerController.cs` & `MapJsonImporter.cs`)**:
   - **Discard Station, Port & Shop Interaction (`1 / 2 / 3 / E` keys)**:
     - `"Bank Sampah"` (`Normal` waste) with `Collider`.
     - `"Pos Medis"` / `"Pos Medis B3"` (`Medical` waste) with `Collider`.
     - `"Karantina Biohazard"` (`Biohazard`/Radioactive waste) with `Collider`.
     - `"Gudang Pengepul"` (located near Spawn / `Bank Sampah`; cheap all-in-one bulk collector with Trust penalty on hazardous waste) with `Collider`.
     - `"Koperasi Desa"` / `"Kopdes"` (vessels, `Kampung Bins`, `Trash Boom`, and 20-tool shop `BuyTool(int)`) with `Collider` (`MapJsonImporter` maps legacy `toko_alat` JSON entries to `KoperasiDesa`).
     - `"Dermaga"` (`Dermaga Awal`, `Dermaga Tengah`) with solid `Collider` — exclusive port for `[E]` boat embark/disembark (`OnNearbyDermagaChanged`) and dry-dock stamina recovery; on foot, players can walk/sprint (`6.5/10.5 m/s`) or enter `RiverMath.IsInRiver` to **swim on the water surface** (`swimSpeed = 4.2`, `swimSprintSpeed = 6.2`, `swimStamina` `100` draining `8/16/4 s⁻¹`, recovering `18 s⁻¹` on land/`Jembatan`/`Dermaga`/boat, and dealing `14 HP/s` drowning damage when exhausted to `0` -> `HealthFail`), climbing out at banks or `Dermaga`.
     - Wrong-station discards incur Rupiah fines + Trust loss (`[E]` calls safe `DiscardLegalAtStation`); during `Sell-Lock` (`waterLevelY >= 1.85m`) hubs lock and player holds **`Q`** (`0.5s`) to dump cargo on high ground (`Pos Medis B3` triage stays accessible).
   - **Dredging Interaction (`Left Click`, camera-aimed nearest target)**:
     - Floating waste prefabs must have a `Collider` + `RiverFlowBuoyancy` + `RiverTrashItem` (`WasteClass`: `Normal`, `Medical`, or `Biohazard`).
     - Dismantlable `Gunung Sampah` nodes must have a `Collider` + `GunungNodeController` (bottom-anchored scale) on a GameObject whose name contains `"Gunung Sampah"`.
     - **Equipped Tool Colliders & Safe Closest Point**: Every `PF_Tool_*` `BoxCollider` must be set to **`isTrigger = true` or disabled while equipped** (enforced by `KaliPlayerController`), and collider distance queries must handle non-convex `MeshCollider`s safely (`SafeClosestPoint`).
   - **Auto-Spawned Prefab Paths in `MapJsonImporter.cs`**:
     - `Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab`
     - `Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab`
     - `Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab`
     - `Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab`
     - `Assets/_Project/Props/Trash/Prefabs/PF_Trash_{BotolLifeman,BotolSprit,BungkusIndomy,BungkusRisol,BungkusSariBoti,KotakRokok,SachetKecapBingo,SachetMoli,StyrofoamMakanan,AquaBottle_600ml,AquaGalon_19L,MedicalBag,SyringeBox}.prefab` (plus `SandalSwallow`, `PopMieCup`, `KresekBag`, `KasurKapuk`, `BanBekas`, `EcengGondok`, `BatangPisang`, `BiohazardDrum` / `RadioactiveBarrel` with runtime fallback).
     - `Assets/_Project/Props/Tools/Prefabs/PF_Tool_<Name>.prefab` (`#01 SendokMakanBengkok` .. `#20 GarukSkimmerHidrolik`).
4. **C# UI / VFX Events (`RiverGameManager.cs` & `KaliPlayerController.cs`)**:
   - `OnStateChanged` (`Action`, throttled ~10 Hz on continuous ticks): Subscribe UI gauges (`rupiah`, `cumulativeEarnings`, `playerHealth`, `swimStamina`, `maxSwimStamina`, `SwimStaminaNormalized`, `isPlayerSwimming`, `IsSwimming`, `IsDrowning`, `cargoCount/cargoCapacity`, `normalCargo`, `medicalCargo`, `biohazardCargo`, `currentWaterLevelY`, `IsBankOverflowing`, `IsSellLocked`, `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `SiagaLevel` `4..1`, `monsoonCountdownRemaining`, `equippedToolIndex`, `highestUnlockedToolIndex`, `waterClarity`, `floodPressure`, `gunungSampahHealth`, `communityTrust`, `medicalWasteSecured`, `biohazardWasteSecured`, `infectionIncidents`, `wrongDiscardCount`, `totalFinesPaid`, `unpaidFineDebt`, `pengepulHazardDumped`).
   - `OnWeatherChanged` (`Action<bool>`): Fires when `isMonsoonStorm` toggles (`VFX_MonsoonRain`, `VolumeProfile_MonsoonStorm`).
   - `OnEndingTriggered` (`Action<GameEnding>`) & `OnEndingWithDiagnosisTriggered` (`Action<GameEnding, string>`): Fires on `TrueSdgVictory` (`0% Gunung Sampah`), `PartialSurvival` (`Monsoon Countdown 0` with Gunung intact), `CompromisedOceanFlush`, `FloodFail` (`waterLevelY >= 2.45m`), or `HealthFail` (`playerHealth <= 0` from Medical prick, Biohazard DoT, or drowning).
   - `OnToolUnlocked` (`Action<ToolDefinition>` — fires when milestone unlocks purchase availability at Kopdes without auto-equipping), `OnEquippedToolChanged` (`Action<ToolDefinition>`), `OnHazardOrAlert` (`Action<string, bool>`), `OnStationAuditReceipt` (`Action<StationAuditReceipt>`), `KaliPlayerController.OnSwimStateChanged` (`Action<bool>`), `KaliPlayerController.OnAimTargetChanged`.
   - Core APIs: `TryPickupWaste(WasteClass, int)`, `DiscardLegalAtStation(DiscardStationType)`, `DiscardWasteAtStation(DiscardStationType, WasteClass)`, `DiscardAllAtStation(DiscardStationType)`, `DumpCargoOnHighGround()`, `BuyKampungBins()`, `BuyUpgrade(UpgradeTier)`, `BuyTool(int)`, `IsToolOwned(int)`, `IsToolUnlocked(int)`, `SelectTool(int)`, `CycleTool(int)`, `SetPlayerSwimming(bool, bool, bool)`, `DamageGunungSampah(float)`, `TriggerEmergencyFlush(bool)`, `CompleteCleanBreach()`, `RestartRun()`, `ComputeSdgScorecard()`.

---

## 3. Non-Negotiable Guardrails (Rubric & Technical)

1. **Zero Raw Primitives / Asset-Store Flips**: Every visible hero prop, tool, building, and terrain mesh must be custom modeled in **Blender 5.3.0** with unwrapped UVs and PBR materials matching Indonesian cultural style (no default Unity cubes/spheres in final scenes).
2. **Blender 5.3.0 $\rightarrow$ Unity 2022.3 LTS Scale Rule**: Always use metric `1 Blender Unit = 1 Meter`, run `Ctrl + A -> All Transforms` (`Scale = 1,1,1`, `Rotation = 0,0,0`), export FBX as `-Z Forward`, `Y Up`, and **uncheck `Add Leaf Bones`** on rigged meshes (`SK_ExcavatorAmfibi`).
3. **Zero-Redundancy 20-Tool, 3-Class Waste & Station Progression**: All 20 official JC tools (`#01 SendokMakanBengkok` .. `#20 GarukSkimmerHidrolik`) unlock Kopdes purchase availability as cumulative Rupiah crosses milestones and are bought via `BuyTool(int)` (`#01` starts owned; `CheckToolMilestones` does not auto-equip). All 3 waste classes (`Normal`, `Medical`, `Biohazard`) can be scooped with any tool: `Medical` carries needle-prick HP risk mitigated to `0%` once `#10 Capitan Ular` is unlocked; `Biohazard`/Radioactive waste deals DoT if held in cargo past grace period (`10s`). Players must route each class to its dedicated station (`Bank Sampah`, `Pos Medis B3`, `Karantina Biohazard`) or face wrong-station fines, vs. cheap bulk dumping at `Gudang Pengepul` (near Spawn) with Trust/SDG penalties.
4. **Interacting Systems & Meaningful Choices**:
   - `+Z` buoyancy + surface-only swimming/stamina/drowning + 20-tool Kopdes purchases + 3-station sorting vs `Gudang Pengepul` + linear water rise (`Overflow -> Sell-Lock -> FloodFail`) + `Q` high-ground anti-deadlock dump + Monsoon countdown (`0%` Gunung Sampah for `TrueSdgVictory`, or survive countdown for `PartialSurvival`).
   - All **3 Dilemmas** (Dedicated Station Sorting vs `Gudang Pengepul` Cheap Dump; Vessel/Equipment vs Kampung Bins Root-Cause; Monsoon `Sell-Lock` `Q`-Dump & Hold vs Emergency Ocean Flush) visibly shift world state, fog/water clarity, and the End-Run SDG Impact Report (SDGs **6.3**, **11.5**, **14.1**).
5. **Local Concept Renders Stay Local**: Never commit or push generated reference images or web pitch renders (`docs/*.jpg`, `docs/*.png` already listed in `.gitignore` remain untracked). Only push clean source assets, markdown docs, scripts, and small repo blueprints already tracked.
6. **60+ FPS Target & Strict Poly Budgets**: Keep trash props `150–400 tris`, tools `300–1,200 tris`, buildings `600–3,000 tris`, terrain `3,000–5,000 tris`, and `SK_ExcavatorAmfibi` `4,000–6,000 tris`.

---

## 4. Standard Commands & Workflow

```bash
# 1. Sync latest team work without touching other folders
git pull origin main

# 2. Playable 3D WebGL prototype & map editor (no Unity install needed)
open -a Safari tools/play-3d.html
open -a Safari tools/map-editor.html

# 3. Unity 2022.3.46f1 Editor workflows (inside unity/)
# Open Unity Hub -> Add/Open folder: ./unity
# Load greybox / level scene from menu:
#   KALI > Load Default Purpose-Built Map
# Sidang 3-Minute Live Demo Hotkeys (in Play Mode):
#   F9       -> Arm Presentation Stage Jump
#   F9 + 1   -> Act 1: Polluted Spawn Sightline (waterClarity = 0.12)
#   F9 + 2   -> Act 2: #10 Capitan Ular + Sampan + Kampung Bins Root-Cause Fix
#   F9 + 3   -> Act 3: Monsoon Storm + Siaga 1 Flood & Sell-Lock (~+2.09m)
#   F9 + 4   -> Clean River SDG Victory (waterClarity = 1.00)
#   Shift+X = Emergency Ocean Flush (Choice C, ends run as CompromisedOceanFlush); R = toggle monsoon (demo only, requires F9 armed)
```
