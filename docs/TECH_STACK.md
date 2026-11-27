# TECH_STACK.md — KALI: Indonesian River Sweeper

| Layer | Technology | Version / Specification | Primary Owners |
| :--- | :--- | :--- | :--- |
| **Game Engine** | **Unity LTS** | `2022.3.46f1` (`unity/ProjectSettings/ProjectVersion.txt`) | **All** (Integration: **Ivan**) |
| **Render Pipeline** | **Universal Render Pipeline (URP)** | `14.0.11` (`com.unity.render-pipelines.universal`) | **Wesley** (Shaders) & **JC** (Lighting/Post-FX) |
| **3D Modeling & Rigging** | **Blender** | `5.3.0+` (FBX export `-Z Forward`, `Y Up`, scale `1.0`) | **JC** (Props/Rig) & **Wesley** (Environment) |
| **Custom Shaders** | **Unity Shader Graph (URP)** | `SG_KaliWater` (Beer-Lambert + panning normals), `SG_TrashTriplanar` | **Wesley** |
| **Rigging & IK** | **Blender Constraints + Unity Animation Rigging** | Blender IK + Dual `Damped Track` pistons; `com.unity.animation.rigging` `1.2.1` | **JC** |
| **VFX Pipeline** | **Unity VFX Graph & Shuriken** | `com.unity.visualeffectgraph` `14.0.11` | **Niki** |
| **UI & Typography** | **uGUI + TextMeshPro** | `com.unity.ugui` `1.0.0`, `com.unity.textmeshpro` `3.0.6` | **Niki** |
| **Camera & Splines** | **Cinemachine & Unity Splines** | `2.10.1` / `2.6.1` | **Ivan** & **Niki** |
| **Level Data & Tools** | **JSON + Three.js Browser Preview** | `kali-river-map.json` (53 nodes, `+Z` flow), `tools/play-3d.html`, `tools/map-editor.html` | **Ivan** |
| **Asset Coordination** | **MCP For Unity + Git LFS / `.gitattributes`** | `com.coplaydev.unity-mcp` | **Ivan** |

---

## 1. Team Directory

| Member | Role | Student ID | Owned Repository Paths |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso** (`Ivan`) | Coordinator & Core Lead | `0706012410029` | `unity/Assets/_Project/Scripts/`, `unity/Assets/_Project/Data/`, `tools/`, `docs/` |
| **Jason Christopher** (`JC`) | Props, 3D, Rigging & Lighting Lead | — | `unity/Assets/_Project/Props/`, `unity/Assets/_Project/Rigging/`, `unity/Assets/_Project/Lighting/` |
| **Wesley Goeinawan** (`Wesley`) | Environment Architecture & Shaders Lead | `0706012410011` | `unity/Assets/_Project/Environment/`, `unity/Assets/_Project/Shaders/` |
| **Nicholas Gerwin Mawardji** (`Niki`) | VFX, UI & Audio/Narrative Lead | `0706012410015` | `unity/Assets/_Project/VFX/`, `unity/Assets/_Project/UI/`, `unity/Assets/_Project/Audio/` |

---

## 2. Performance & Polycount Budgets (60+ FPS Target)

| Asset Category | Triangle Budget | Texture / Atlas Spec | Owner |
| :--- | :---: | :--- | :--- |
| **Small Trash Props** (`Sandal`, `Aqua`, `Syringe`, `Kresek`) | `150 – 400 tris` | Shared `T_Trash_Atlas` `2048×2048` PBR | **JC** |
| **20 Scavenging Tools** (`Sendok` to `Garuk Skimmer Hidrolik`) | `300 – 1,200 tris` | Shared `T_Tools_Atlas` `2048×2048` PBR | **JC** |
| **Vessels & Automation Props** (`Rakit`, `Sampan`, `TrashBoom`) | `500 – 2,500 tris` | `1024×1024` PBR | **JC** |
| **Hero Rigged Excavator** (`SK_ExcavatorAmfibi`) | `4,000 – 6,000 tris` | 3 Material Slots (`Body`, `Hydraulic_Steel`, `Pontoon_Rubber`) | **JC** |
| **Modular Kampung Buildings** (`Rumah`, `Warung Madura`, `Bank`, `Kopdes`) | `600 – 1,800 tris` | `1024×1024`–`2048×2048` PBR + Lightmap UV2 | **Wesley** |
| **Major River Structures** (`JembatanUtama`, `PintuAir`, `GunungSampah`) | `1,200 – 4,000 tris` | `2048×2048` PBR (`SG_TrashTriplanar` for mound) | **Wesley** |
| **River Valley Terrain** (`SM_Env_RiverValleyTerrain`) | `3,000 – 5,000 tris` | Vertex color + tiled mud/grass PBR | **Wesley** |

---

## 3. Core C# Scripts Inventory (`unity/Assets/_Project/Scripts/`)

- `Core/RiverGameManager.cs` — Central state machine, linear water level (`waterLevelY = -0.25 + 0.020 * trash`), Overflow & Sell-Lock (`Q` dump), Rupiah & 3-station sorting (`DiscardLegalAtStation`) vs `Gudang Pengepul`, Medical prick, Biohazard DoT, swim stamina & drowning (`playerHealth`, `swimStamina`), Monsoon countdown, 20-tool milestone unlocks & Kopdes `BuyTool(int)` ownership, `_WaterClarity` global shader push (throttled ~10 Hz).
- `Core/ToolCatalog.cs` — Authoritative 20 official JC tools (`#01 SM_Tool_SendokMakanBengkok` .. `#20 SM_Tool_GarukSkimmerHidrolik`), cumulative Rupiah milestone costs (`UnlockRupiah`), reach/batch/cooldown/prick-mitigation stats, `WasteClass` & `DiscardStationType` enums.
- `Core/RiverTrashItem.cs` & `Core/RiverTrashSpawner.cs` — Live active/piled trash registration (`TotalTrashInRiver`), `Normal`/`Medical`/`Biohazard` classification, and upstream `-Z` spawning slowed by `Kampung Bins`.
- `Core/RiverFlowBuoyancy.cs` — `RiverMath` (`130m × 180m` spline projection & width profile) + `RiverFlowBuoyancy` (`+Z` downstream drift toward `Pintu Air`, dynamic water Y sync) + `RiverWaterSurfaceFollower` + `GunungNodeController` (bottom-anchored scaling).
- `Player/KaliPlayerController.cs` — Dual Input System + Legacy fallback, FP walk/sprint, surface-only swimming + bank/dock climb-out + swim stamina/drowning feed, `Dermaga`-gated boat embark/disembark & Y-tracking, FreeCam (`F`), Weather toggle (`R`), camera-aimed nearest-target scoop (`LMB`, `SafeClosestPoint`), station quick-discard (`1/2/3/E`), high-ground cargo dump (`Q` hold), tool switching (`Scroll` / `[ ]`, auto-disabling equipped `PF_Tool_*` `BoxCollider`s).
- `Player/KaliFieldGuideOverlay.cs` — Lightweight live alert/fine toast, `[H]`/`[F1]` toggleable controls & sorting guide, and contextual swim stamina indicator.
- `Editor/MapJsonImporter.cs` — Editor menu (`KALI > Load Default Purpose-Built Map`) generating split West/East banks (fallback) or `SM_Env_RiverValleyTerrain` concave colliders, elevated `Jembatan Utama`, `+Z` `Pintu Air`, `Pos Medis B3`, `Karantina Biohazard`, `Gudang Pengepul` near Spawn, `RiverTrashSpawner`, `EventSystem`, and loading JC/Wesley/Niki prefabs (`PF_LightingRig`, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`, `PF_Prop_TrashBoomSegment`, `PF_Trash_*`, `PF_Tool_*`).
- `Editor/KaliCoreQaTests.cs` — 11-suite Unity Editor QA harness (`KALI > QA > Run Core Verification`).
