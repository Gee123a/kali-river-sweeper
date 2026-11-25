# AGENTS.md — Master AI Agent Rules (KALI: Indonesian River Sweeper)

> **AI Agent Instructions**: Read this file before modifying any script, prefab, 3D model, shader, UI, or scene in this repository. This project is the **IMT01303501 Computer Graphics** Final Project (ALP, Universitas Ciputra Surabaya — **GAME Track**, targeting Grade A **85–100%** against `20261-CG-Penilaian ALP.pdf`).

---

## 1. Team & Ownership Architecture

To eliminate Unity/Blender merge conflicts (especially `.unity`, `.prefab`, `.meta`, `.fbx`) and ensure every member owns verifiable proof for the **30% Understanding of the Process** defense criterion, every agent and contributor must work strictly inside their assigned directories inside `unity/Assets/_Project/`:

| Member | Role | Student ID | Primary Scope & Owned Directories |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso (Ivan)** | **Coordinator & Core Lead** | `0706012410029` | Scope, schedule, docs, shared C# contracts lock, Git integration, gameplay physics & level spawner:<br>• `unity/Assets/_Project/Scripts/` (`Core/`, `Player/`, `Editor/`)<br>• `unity/Assets/_Project/Data/` (`kali-river-map.json`)<br>• `tools/` (`play-3d.html`, `map-editor.html`) |
| **Jason Christopher (JC)** | **Props, 3D, Rigging & Lighting Lead** | — | Authentic Indonesian trash props (incl. Medical Waste B3), 20 scavenging tools, vessels, hydraulic IK rig, Unity lighting & Post-FX:<br>• `blender/**` (`blender -b -P blender/build_all.py`)<br>• `unity/Assets/_Project/Props/` (`Trash/`, `Tools/`, `Equipment/`)<br>• `unity/Assets/_Project/Rigging/` (`SK_ExcavatorAmfibi.fbx`, IK arm, pistons)<br>• `unity/Assets/_Project/Lighting/` (`KaliLightingBuilder.cs`, `PF_LightingRig`, `VolumeProfile_*`, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`) |
| **Wesley Goeinawan (Wesley)** | **Environment Architecture & Shaders Lead** | `0706012410011` | Custom 3D Indonesian riverbank architecture (10 `SM_Env_*` FBX meshes) + URP Shader Graphs:<br>• `unity/Assets/_Project/Environment/` (`Meshes/`, `Materials/`, `Textures/`, `Prefabs/`)<br>• `unity/Assets/_Project/Shaders/` (`SG_KaliWater.shadergraph`, `SG_TrashTriplanar.shadergraph`) |
| **Nicholas Gerwin Mawardji (Niki)** | **VFX, UI & Audio/Narrative Lead** | `0706012410015` | URP particle systems, Canvas HUD/shops/end-run SDG report, sound effects, Sidang presentation flow:<br>• `unity/Assets/_Project/VFX/` (`VFX_MonsoonRain`, `VFX_WaterSplashMuddy`, `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche`)<br>• `unity/Assets/_Project/UI/` (`Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`)<br>• `unity/Assets/_Project/Audio/` |

**Zero-Touch Scene Rule**: Only **Ivan** edits shared main scene hierarchy or `MapJsonImporter.cs` integration hooks directly unless explicitly coordinated. Other members build self-contained **Prefabs**, **Materials**, **Shaders**, and **FBX** assets inside their own owned folders so `MapJsonImporter.cs` or Ivan's integration branch wires them cleanly with zero `.unity` YAML merge conflicts.

---

## 2. Shared Contracts & Single Source of Truth

All scripts, shaders, 3D meshes, colliders, and UI panels must obey these hard-coded contracts already live in `unity/Assets/_Project/Scripts/`:

1. **World Scale & River Channel Math (`RiverMath` in `Scripts/Core/RiverFlowBuoyancy.cs`)**:
   - `MapScale = 0.125f`, `WorldW = 1040f`, `WorldH = 1440f` $\rightarrow$ **Exact Unity terrain size: `130m (X) × 180m (Z)`**, centered at origin `(0, 0, 0)`.
   - Mapping formula: `ToWorld3D(mapX, mapY, elev) = ((mapX - 520) * 0.125, elev, (mapY - 720) * 0.125)`.
   - River centerline curve: `CenterX(mapY) = 520 + sin((mapY / 1440) * PI * 1.6) * 58`, base width `22.5m` (`180 * 0.125`), narrowing at central bridge choke (`mapY = 740`), widening at `southBay` (`mapY = 1220`) and northern retention basin (`mapY < 320`).
   - Current direction: Debris floats toward **`-Z`** (`pos.z > -44f`) toward `Gunung Sampah` & `Pintu Air`. Water surface plane rests at **`Y = 0.0f`**; dry riverbank land starts at `Y >= +0.8m`.
2. **Global Water Shader Contract (`RiverGameManager.cs`)**:
   - `RiverGameManager` broadcasts `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` on startup and every `NotifyState()` change (`0.12f` polluted muddy brown $\rightarrow$ `1.0f` pristine turquoise).
   - **Wesley's `SG_KaliWater`** Shader Graph Blackboard MUST declare a Float property with exact Reference Name **`_WaterClarity`**.
3. **Collider & Prefab Path Contracts (`KaliPlayerController.cs` & `MapJsonImporter.cs`)**:
   - **Sorting Interaction (`E` key)**: Requires a `Collider` on a GameObject whose name contains `"Bank Sampah"` (raw sale) or `"Pos Sortir"` (baled $3\times$ sale).
   - **Dredging Interaction (`Left Click`)**:
     - Floating waste prefabs must have a `Collider` + `RiverFlowBuoyancy` component (`TryAddCargo(1)`).
     - Dismantlable `Gunung Sampah` nodes must have a `Collider` on a GameObject whose name contains `"Gunung Sampah"`.
   - **Auto-Spawned Prefab Paths in `MapJsonImporter.cs`**:
     - `Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab`
     - `Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab`
     - `Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab`
     - `Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab`
     - `Assets/_Project/Props/Trash/Prefabs/PF_Trash_<Variant>.prefab`
4. **C# UI / VFX Events (`RiverGameManager.cs`)**:
   - `OnStateChanged` (`Action`): Subscribe UI gauges (`rupiah`, `cargoCount/cargoCapacity`, `SiagaLevel` `4..1`, `waterClarity`, `floodPressure`, `gunungSampahHealth`, `communityTrust`, `medicalWasteSecured`, `infectionIncidents`).
   - `OnWeatherChanged` (`Action<bool>`): Fires when `isMonsoonStorm` toggles (`VFX_MonsoonRain`, `VolumeProfile_MonsoonStorm`).
   - `OnEndingTriggered` (`Action<GameEnding>`): Fires on `FloodFail`, `CompromisedOceanFlush`, or `TrueSdgVictory`.
   - Trade-off & Upgrade APIs: `DumpAtBurnPit()`, `SellAtBankSampah(bool sortedAtPosSortir)`, `SecureMedicalWaste(bool usingSnakeGrabber)`, `BuyKampungBins()`, `BuyUpgrade(UpgradeTier)`, `DamageGunungSampah(float)`, `TriggerEmergencyFlush()`, `CompleteCleanBreach()`.

---

## 3. Non-Negotiable Guardrails (Rubric & Technical)

1. **Zero Raw Primitives / Asset-Store Flips**: Every visible hero prop, tool, building, and terrain mesh must be custom modeled in **Blender 5.3.0** with unwrapped UVs and PBR materials matching Indonesian cultural style (no default Unity cubes/spheres in final scenes).
2. **Blender 5.3.0 $\rightarrow$ Unity 2022.3 LTS Scale Rule**: Always use metric `1 Blender Unit = 1 Meter`, run `Ctrl + A -> All Transforms` (`Scale = 1,1,1`, `Rotation = 0,0,0`), export FBX as `-Z Forward`, `Y Up`, and **uncheck `Add Leaf Bones`** on rigged meshes (`SK_ExcavatorAmfibi`).
3. **Zero-Redundancy 20-Tool & Medical Waste Logic**: Tools are physically differentiated across 4 tiers (`Sendok Makan`, `Gayung`, `Centong Nasi`, `Garpu Taman`, `Serokan Waring`, `Ganco`, `Ember Cat`, `Capitan Ular`, `Pompa Vakum 49cc`, `Garuk Skimmer`, etc.). Medical Biohazard Waste (*Limbah B3 Medis*: syringes, IV bags, yellow biohazard sacks) requires `Capitan Ular` (`SecureMedicalWaste(true)`); unsafe scooping triggers `infectionIncidents` and trust loss.
4. **Three Interacting Systems & Meaningful Choices**:
   - Physics buoyancy + 20-tool progression + Bank Sampah economy + Monsoon `Siaga 4 -> 1` flood pressure + Upstream automation.
   - All **3 Dilemmas** (Burn Pit vs. Bank Sampah / Medical Waste Hazard; Boat Upgrades vs. Kampung Bins Root-Cause; Monsoon Emergency Flush vs. Hold & Dredge) must visibly shift world state, fog/water clarity, and the End-Run SDG Impact Report (SDGs **6.3**, **11.5**, **14.1**).
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
#   F9 + 2   -> Act 2: Unlocked Tiers + Kampung Bins Root-Cause Fix
#   F9 + 3   -> Act 3: Monsoon Storm + Siaga 1 Flood Pressure (0.78)
#   F9 + 4   -> Clean River SDG Victory (waterClarity = 1.00)
```
