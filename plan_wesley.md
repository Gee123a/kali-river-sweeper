# AI Implementation Plan: Wesley (Environment Architecture & Water Shaders Lead)

> **Instructions for AI**: You are the dedicated AI 3D Environment Artist & Technical Shader Mentor for **Wesley Goeinawan**. Wesley is starting from scratch and does not yet know this project's codebase—always explain Unity `2022.3.46f1 LTS (URP)` and Blender `5.3.0` steps click-by-click in beginner-friendly language while strictly enforcing every C# contract below. Never edit Ivan's `Scripts/`, JC's `Props/`/`Rigging/`/`Lighting/`, or Niki's `VFX/`/`UI/`/`Audio/`.

---

## 1. Identity & Scope Boundaries

- **Owner**: Wesley Goeinawan (Wesley)
- **Student ID**: `0706012410011` | **Tracked Level Diagram**: [kali_game_flow_and_architecture.png](./docs/kali_game_flow_and_architecture.png)
- **Track**: 3D Riverbank Architecture (`10` `SM_Env_*` Meshes) + Custom URP Shader Graphs (`SG_KaliWater`, `SG_TrashTriplanar`)
- **Primary Deliverables**:
  1. Curved riverbed & kampung embankment terrain (`SM_Env_RiverValleyTerrain`) synced **100% identically** to `RiverMath` (`130m × 180m`).
  2. 9 authentic Indonesian riverbank structures & dam assets (`SM_Env_*` FBX + prefabs inside `Assets/_Project/Environment/`).
  3. Dynamic river water shader `SG_KaliWater.shadergraph` driven globally by Ivan's C# **`_WaterClarity`** float (`0.12` muddy brown $\rightarrow$ `1.00` clean emerald teal).
  4. Height-blended world triplanar shader `SG_TrashTriplanar.shadergraph` for `SM_Env_GunungSampah_3Tiers`.

### Allowed Files & Directories (READ & WRITE)
- `unity/Assets/_Project/Environment/**` (`Meshes/`, `Materials/`, `Textures/`, `Prefabs/`)
- `unity/Assets/_Project/Shaders/**` (`SG_KaliWater.shadergraph`, `SG_TrashTriplanar.shadergraph`, subgraphs/materials)

### Strictly Forbidden (DO NOT MODIFY OTHER FOLDERS)
- `unity/Assets/_Project/Scripts/**`, `Data/**` *(Owned by Ivan — C# contracts are locked)*
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/VFX/**`, `UI/**`, `Audio/**` *(Owned by Niki)*

### Context Files to Read
1. `AGENTS.md` (Scale, `RiverMath` `130m × 180m` curve, `_WaterClarity`, Collider name hooks)
2. `docs/ARCHITECTURE.md` (Section 2 & Section 3A–3C C# integration points)
3. `docs/DESIGN.md` (Exact color hexes: `#3B2818`, `#1B6B63`, `#06B6D4`, PBR bamboo/zinc/silt rules)
4. `docs/PRD.md` (Zone 1 Kampung Hulu, Zone 2 Jembatan, Zone 3 Pintu Air & Gunung Sampah)

---

## 2. Hard Technical Constraints (Locked in Ivan's C# Scripts)

- **Exact Terrain World Size**: `130m wide (X) × 180m long (Z)`, centered at `(0, 0, 0)` (`WorldW=1040`, `WorldH=1440`, `MapScale=0.125`).
- **River Channel S-Curve**: Centerline follows `CenterX(mapY) = 520 + sin((mapY / 1440) * PI * 1.6) * 58`; base river width is `22.5m` (narrows at `mapY = 740` bridge choke, widens at south bay `mapY = 1220` & northern basin `mapY < 320`).
- **Current Flow Axis**: Debris & water flow toward **`-Z`** (north) straight into `Pintu Air` & `Gunung Sampah`. Keep water surface at `Y = 0.0m` and walkable village embankments at `Y = +0.8m` to `+2.0m`.
- **Required Prefab Names & Colliders**:
  - `Bank Sampah` prefab GameObject name must contain `"Bank Sampah"` + Collider (triggers `KaliPlayerController` `E` key sale).
  - `Pos Sortir` prefab GameObject name must contain `"Pos Sortir"` + Collider (triggers `3×` sorted PET sale).
  - `Gunung Sampah` tiers must have `"Gunung Sampah"` in their name + Collider (enables Excavator dredging).
- **Roof / Tower Clearances**: Leave top roof overhangs on `SM_Env_Warung` and top tower pad on `SM_Env_PintuAirSiaga1` clear so JC's `PF_Lantern_Warung` & `PF_WarningBeacon_PintuAir` attach without clipping.

---

## 3. Step-by-Step Task Checklist

- [ ] **Step 0: Onboarding & Greybox Inspection**
  - [ ] Run `git pull origin main` and open `./unity` in **Unity `2022.3.46f1` LTS**.
  - [ ] Top menu: click **`KALI > Load Default Purpose-Built Map`** to inspect the 51-node greybox world and see where all 10 buildings sit.

- [ ] **Step 1: Terrain & Hero Water Shader (`SM_Env_RiverValleyTerrain` + `SG_KaliWater`)**
  - [ ] Model `SM_Env_RiverValleyTerrain.fbx` (`3,000–5,000 tris`) matching `130m (X) × 180m (Z)`, origin `(0,0,0)`, sunken riverbed below `Y = -1.5m`, banks raised to `+0.8m`–`+2.0m`.
  - [ ] Build `Assets/_Project/Shaders/SG_KaliWater.shadergraph` (**URP Lit Shader Graph**):
    - Create Blackboard Float property with **EXACT Reference Name `_WaterClarity`** (`0.12` to `1.0`). *(Updated globally every frame/scoop via `RiverGameManager.cs` -> `Shader.SetGlobalFloat`!)*
    - Beer-Lambert depth tint: compute `Scene Depth (Eye) - Screen Position (W)` $\rightarrow$ `Lerp` muddy `#3B2818` to clean emerald `#1B6B63` driven by `_WaterClarity`.
    - Dual-Flow Normals: pan 2 normal maps toward **`-V`** (`Time * -0.15` and `Time * -0.09`), combine with `Normal Blend`.
    - Shoreline & Debris Foam: `Step(0.35, DepthDiff) * Simple Noise` $\rightarrow$ white edge froth.
    - Light Sine vertical wave (`Amp 0.05m`) matching `RiverFlowBuoyancy`.

- [ ] **Step 2: Climax Landmark Structures (`GunungSampah` & `PintuAirSiaga1`)**
  - [ ] Model `SM_Env_PintuAirSiaga1.fbx` (`2,000–3,000 tris`): concrete sluice floodgate arches, manual steel winch towers, catwalk.
  - [ ] Model `SM_Env_GunungSampah_3Tiers.fbx` (`2,500–4,000 tris`): 3 separable stacked trash dam mounds (Bedrock Silt tier, Mid Entangled tier, Top Plastic Floater tier).
  - [ ] Build `Assets/_Project/Shaders/SG_TrashTriplanar.shadergraph`: World-Space `Triplanar` (`Blend 4.0`) + height blend (`Y < 0.8m` wet black mud, `0.8–2.5m` kapok/yellow medical bags, `> 2.5m` dry PET plastics) + Vertex Color Red grime mask.

- [ ] **Step 3: Remaining 7 Kampung & Bridge Meshes (`Assets/_Project/Environment/Meshes/`)**
  - [ ] `SM_Env_JembatanUtama.fbx` (`1,200–2,000 tris`) — Concrete road bridge across `mapY = 740` choke.
  - [ ] `SM_Env_BankSampah.fbx` (`1,200–1,800 tris`) — Drop-off bay, scale, counter (`Bank Sampah` collider).
  - [ ] `SM_Env_PosSortir.fbx` (`1,000–1,500 tris`) — Open-air sorting tables & PET bale shelter (`Pos Sortir` collider).
  - [ ] `SM_Env_TokoAlat.fbx` (`800–1,200 tris`) — Boat repair & bamboo/pump workshop shack.
  - [ ] `SM_Env_RumahPanggung.fbx` (`800–1,500 tris`, reused at 11 nodes) — Stilts extending to `-0.5m`, weathered planks, rusted zinc roof.
  - [ ] `SM_Env_Warung.fbx` (`600–1,000 tris`, reused at 7 nodes) — Riverside kiosk, snack bench, awning.
  - [ ] `SM_Env_Dermaga.fbx` (`400–800 tris`, reused at 2 nodes) — Boat pier (**Pivot MUST sit at waterline `Y = 0.0m`**).

- [ ] **Step 4: FBX Export & Unity Prefab Verification**
  - [ ] In Blender before every export: `Ctrl + A -> All Transforms` (`Scale 1.0`, `-Z Forward`, `Y Up`, unwrap Lightmap UV2 where needed).
  - [ ] Create ready-to-drop Unity Prefabs + Colliders inside `Assets/_Project/Environment/Prefabs/`.

---

## 4. Sidang Q&A Preparation (30% Understanding of the Process)
Be ready to open Blender + Shader Graph live and explain:
1. Why **`Scene Depth - Screen Position (W)`** + **`_WaterClarity`** models the Beer-Lambert light absorption switch from turbid brown sewage to crystal river water.
2. Why **Dual Normal Panning along `-V`** avoids visible seam loops and visually matches `RiverFlowBuoyancy`'s `-Z` current.
3. Why **World-Space Triplanar Mapping (`SG_TrashTriplanar`)** eliminates UV stretching across huge organic shapes like `Gunung Sampah`.
