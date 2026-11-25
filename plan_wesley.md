# AI Implementation Plan: Wesley (Environment Architecture & Water Shaders Lead)

> **Instructions for AI**: You are the dedicated AI 3D Environment Artist & Technical Shader Mentor for **Wesley Goeinawan**. Wesley is starting from scratch and does not yet know this project's codebase—always explain Unity `2022.3.46f1 LTS (URP)` and Blender `5.3.0` steps click-by-click in beginner-friendly language while strictly enforcing every C# contract below. Never edit Ivan's `Scripts/`, JC's `Props/`/`Rigging/`/`Lighting/`, or Niki's `VFX/`/`UI/`/`Audio/`.

---

## 1. Identity & Scope Boundaries

- **Owner**: Wesley Goeinawan (Wesley)
- **Student ID**: `0706012410011` | **Tracked Level Diagram**: [kali_game_flow_and_architecture.png](./docs/kali_game_flow_and_architecture.png)
- **Track**: 3D Riverbank Architecture (`SM_Env_*` Meshes) + Custom URP Shader Graphs (`SG_KaliWater`, `SG_TrashTriplanar`)
- **Primary Deliverables**:
  1. Curved riverbed & kampung embankment terrain (`SM_Env_RiverValleyTerrain`) synced **100% identically** to `RiverMath` (`130m × 180m`, dry banks `+1.40m`, sunken riverbed `-2.0m`).
  2. Indonesian riverbank structures, 3 dedicated waste station hubs (`Bank Sampah` / `Pos Sortir` for Normal, `Pos Medis B3` for Medical, `Karantina Biohazard` for Biohazard), `Gudang Pengepul` (near Spawn), elevated `Jembatan Utama`, upstream `Gunung Sampah` (`-Z`), & downstream **`+Z` `Pintu Air Siaga 1`** inside `Assets/_Project/Environment/`.
  3. Dynamic river water shader `SG_KaliWater.shadergraph` driven globally by Ivan's C# **`_WaterClarity`** float (`0.05` muddy brown $\rightarrow$ `1.00` clean emerald teal) scrolling **`+V`** (`+Z` downstream).
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
- **Current Flow Axis**: Debris & water flow toward **`+Z` downstream** (from upstream **`-Z` `Gunung Sampah`** straight down to downstream **`+Z` `Pintu Air Siaga 1`**). Baseline water starts near `Y = 0.0m` and rises linearly (`Overflow >= +1.40m`, `Sell-Lock >= +1.85m`); walkable village embankments sit at **`Y = +1.40m`** with stilts extending down to `-0.5m` so banks look natural as water rises and overflows!
- **Required Prefab Names & Colliders**:
  - `Bank Sampah` prefab GameObject name must contain `"Bank Sampah"` + Collider (Normal waste station).
  - `Pos Sortir` prefab GameObject name must contain `"Pos Sortir"` + Collider (Normal waste baling bonus station).
  - **`Pos Medis B3`** prefab GameObject name must contain **`"Pos Medis"`** + Collider (dedicated Medical B3 waste clinic near `Jembatan Utama` West approach).
  - **`Karantina Biohazard`** prefab GameObject name must contain **`"Karantina Biohazard"`** + Collider (dedicated Biohazard/Radioactive containment bunker on East bank).
  - **`Gudang Pengepul`** prefab GameObject name must contain **`"Gudang Pengepul"`** + Collider (located near Spawn / `Bank Sampah` on West bank; cheap all-in-one bulk collector).
  - `Gunung Sampah` tiers must have `"Gunung Sampah"` in their name + Collider + bottom-anchored pivot (`Y = 0`) so scaling/dredging never leaves the mound floating!
  - `Jembatan Utama` deck MUST sit at **`Y >= +3.60m`** with center `>= 12m` channel clear of bridge piers so boats pass underneath cleanly.
- **Roof / Tower Clearances**: Leave top roof overhangs on `SM_Env_Warung` and top tower pad on **`SM_Env_PintuAirSiaga1` (`+Z` downstream)** clear so JC's `PF_Lantern_Warung` & `PF_WarningBeacon_PintuAir` attach without clipping.

---

## 3. Step-by-Step Task Checklist

- [ ] **Step 0: Onboarding & Greybox Inspection**
  - [ ] Run `git pull origin main` and open `./unity` in **Unity `2022.3.46f1` LTS**.
  - [ ] Top menu: click **`KALI > Load Default Purpose-Built Map`** to inspect the 54-node greybox world (split banks, elevated bridge, `+Z` Pintu Air, 3 waste stations + Gudang Pengepul).

- [ ] **Step 1: Terrain & Hero Water Shader (`SM_Env_RiverValleyTerrain` + `SG_KaliWater`)**
  - [ ] Model `SM_Env_RiverValleyTerrain.fbx` (`3,000–5,000 tris`) matching `130m (X) × 180m (Z)`, origin `(0,0,0)`, sunken riverbed `-2.0m`, banks raised to `+1.40m`.
  - [ ] Build `Assets/_Project/Shaders/SG_KaliWater.shadergraph` (**URP Lit Shader Graph**):
    - Create Blackboard Float property with **EXACT Reference Name `_WaterClarity`** (`0.05` to `1.0`). *(Updated globally by Ivan's `RiverGameManager.cs` -> `Shader.SetGlobalFloat`!)*
    - Beer-Lambert depth tint: compute `Scene Depth (Eye) - Screen Position (W)` $\rightarrow$ `Lerp` muddy `#3B2818` to clean emerald `#1B6B63` driven by `_WaterClarity`.
    - Dual-Flow Normals: pan 2 normal maps toward **`+V`** (`Time * +0.15` and `Time * +0.09`), combine with `Normal Blend` to match **`+Z` downstream** flow.
    - Shoreline & Debris Foam: `Step(0.35, DepthDiff) * Simple Noise` $\rightarrow$ white edge froth.
    - Light Sine vertical wave (`Amp 0.05m`) matching `RiverFlowBuoyancy`.

- [ ] **Step 2: Climax Landmark Structures (`GunungSampah` `-Z` & `PintuAirSiaga1` `+Z`)**
  - [ ] Model `SM_Env_PintuAirSiaga1.fbx` (`2,000–3,000 tris`): downstream (`+Z`) concrete sluice floodgate arches, manual steel winch towers, catwalk where river trash piles up.
  - [ ] Model `SM_Env_GunungSampah_3Tiers.fbx` (`2,500–4,000 tris`): upstream (`-Z`) 3 separable stacked trash dam mounds with **bottom-anchored `Y = 0` pivot** (no floating during dredge scaling!).
  - [ ] Build `Assets/_Project/Shaders/SG_TrashTriplanar.shadergraph`: World-Space `Triplanar` (`Blend 4.0`) + height blend (`Y < 0.8m` wet black mud, `0.8–2.5m` kapok/yellow medical bags, `> 2.5m` dry PET plastics) + Vertex Color Red grime mask.

- [ ] **Step 3: Kampung, Bridge & 3 Waste Station Meshes (`Assets/_Project/Environment/Meshes/`)**
  - [ ] `SM_Env_JembatanUtama.fbx` (`1,200–2,000 tris`) — Concrete road bridge (`Y = +3.60m` deck, center piers clear) across `mapY = 740` choke.
  - [ ] `SM_Env_BankSampah.fbx` (`1,200–1,800 tris`) — Normal waste drop-off bay, scale, counter (`Bank Sampah` collider).
  - [ ] `SM_Env_PosSortir.fbx` (`1,000–1,500 tris`) — Open-air sorting tables & PET bale shelter (`Pos Sortir` collider).
  - [ ] **`SM_Env_PosMedisB3.fbx`** (`800–1,400 tris`) — White/yellow clinical disposal hub with red cross signage (`Pos Medis B3` collider at West bridge approach).
  - [ ] **`SM_Env_KarantinaBiohazard.fbx`** (`800–1,400 tris`) — Purple/slate sealed radioactive containment bunker (`Karantina Biohazard` collider on East bank).
  - [ ] **`SM_Env_GudangPengepul.fbx`** (`700–1,200 tris`) — Rustic corrugated scrap warehouse near Spawn / Bank Sampah (`Gudang Pengepul` collider).
  - [ ] `SM_Env_TokoAlat.fbx` (`800–1,200 tris`) — Boat repair & workshop shack.
  - [ ] `SM_Env_RumahPanggung.fbx` (`800–1,500 tris`, reused at 11 nodes) — Stilts extending to `-0.5m` below `+1.40m` bank ground.
  - [ ] `SM_Env_Warung.fbx` (`600–1,000 tris`, reused at 7 nodes) — Riverside kiosk, snack bench, awning.
  - [ ] `SM_Env_Dermaga.fbx` (`400–800 tris`, reused at 2 nodes) — Boat pier (**Pivot MUST sit at waterline `Y = 0.0m`**).

- [ ] **Step 4: FBX Export & Unity Prefab Verification**
  - [ ] In Blender before every export: `Ctrl + A -> All Transforms` (`Scale 1.0`, `-Z Forward`, `Y Up`, unwrap Lightmap UV2 where needed).
  - [ ] Create ready-to-drop Unity Prefabs + Colliders inside `Assets/_Project/Environment/Prefabs/`.

---

## 4. Sidang Q&A Preparation (30% Understanding of the Process)
Be ready to open Blender + Shader Graph live and explain:
1. Why **`Scene Depth - Screen Position (W)`** + **`_WaterClarity`** models the Beer-Lambert light absorption switch from turbid brown sewage to crystal river water.
2. Why **Dual Normal Panning along `+V`** avoids visible seam loops and visually matches `RiverFlowBuoyancy`'s **`+Z` downstream** current.
3. Why **World-Space Triplanar Mapping (`SG_TrashTriplanar`)** eliminates UV stretching across huge organic shapes like `Gunung Sampah`.
