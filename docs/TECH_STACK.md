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
| **Level Data & Tools** | **JSON + Three.js Browser Preview** | `kali-river-map.json` (51 nodes), `tools/play-3d.html`, `tools/map-editor.html` | **Ivan** |
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
| **20 Scavenging Tools** (`Sendok` to `Vakum 49cc`) | `300 – 1,200 tris` | Shared `T_Tools_Atlas` `2048×2048` PBR | **JC** |
| **Vessels & Automation Props** (`Rakit`, `Sampan`, `TrashBoom`) | `500 – 2,500 tris` | `1024×1024` PBR | **JC** |
| **Hero Rigged Excavator** (`SK_ExcavatorAmfibi`) | `4,000 – 6,000 tris` | 3 Material Slots (`Body`, `Hydraulic_Steel`, `Pontoon_Rubber`) | **JC** |
| **Modular Kampung Buildings** (`Rumah`, `Warung`, `Bank`, `Toko`, `Pos`) | `600 – 1,800 tris` | `1024×1024`–`2048×2048` PBR + Lightmap UV2 | **Wesley** |
| **Major River Structures** (`JembatanUtama`, `PintuAir`, `GunungSampah`) | `1,200 – 4,000 tris` | `2048×2048` PBR (`SG_TrashTriplanar` for mound) | **Wesley** |
| **River Valley Terrain** (`SM_Env_RiverValleyTerrain`) | `3,000 – 5,000 tris` | Vertex color + tiled mud/grass PBR | **Wesley** |

---

## 3. Core C# Scripts Inventory (`unity/Assets/_Project/Scripts/`)

- `Core/RiverGameManager.cs` — Central state machine, Rupiah & Bank Sampah payouts, Medical Biohazard risk (`SecureMedicalWaste`), Kampung Bins, Upgrade Tiers, Monsoon `Siaga 4 -> 1` flood gauge, `_WaterClarity` global shader push, `F9` Presentation hotkeys.
- `Core/RiverFlowBuoyancy.cs` — `RiverMath` (`130m × 180m` spline projection & width profile) + `RiverFlowBuoyancy` component for sinusoidal bobbing and `-Z` current drift.
- `Player/KaliPlayerController.cs` — First-person walking/sprinting, boat toggle (`E`), FreeCam (`F`), Weather test toggle (`R`), Bank Sampah / Pos Sortir interaction, and Scoop/Dredge (`Left Click`).
- `Editor/MapJsonImporter.cs` — Editor menu (`KALI > Load Default Purpose-Built Map`) spawning all 51 nodes from `kali-river-map.json` plus JC's prefabs (`PF_LightingRig`, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`, `PF_Prop_TrashBoomSegment`, `PF_Trash_*`).
