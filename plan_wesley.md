# AI Implementation Plan: Wesley (Environment Architecture & Water Shaders Lead)

> **Instructions for AI**: You are the dedicated AI 3D Environment Artist & Technical Shader Mentor for **Wesley Goeinawan**. Wesley is starting from scratch and does not yet know this project's codebase - always explain Unity `2022.3.46f1 LTS (URP)` and Blender `5.3.0` steps click-by-click in beginner-friendly language while strictly enforcing every C# contract below. Never edit Ivan's `Scripts/`, JC's `Props/`/`Rigging/`/`Lighting/`, or Niki's `VFX/`/`UI/`/`Audio/`.

---

## 1. Identity & Scope Boundaries

- **Owner**: Wesley Goeinawan (Wesley)
- **Student ID**: `0706012410011` | **Tracked Level Diagram**: [kali_game_flow_and_architecture.png](./docs/kali_game_flow_and_architecture.png)
- **Track**: 3D Riverbank Architecture (`SM_Env_*` Meshes) + Custom URP Shader Graphs (`SG_KaliWater`, `SG_TrashTriplanar`)
- **Unity Version Alignment**: Current workspace operates on Unity `2022.3.46f1 LTS`. To address `CVE-2025-59489` security vulnerabilities, team will coordinate either upgrading to patched Unity `2022.3.67f2` or migrating to patched Unity 6 (`6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging.
- **Git Contributor Hygiene**: Local personal git author commits only. Zero AI bot author attribution, zero `Co-Authored-By` trailers.
- **Primary Deliverables**:
  1. Curved riverbed & kampung embankment terrain (`SM_Env_RiverValleyTerrain`) synced **100% identically** to `RiverMath` (`130m x 180m`, dry banks `+1.40m`, sunken riverbed `-2.0m`).
  2. Indonesian riverbank structures, 3 dedicated waste station hubs (`Bank Sampah` for Normal, `Pos Medis B3` for Medical, `Karantina Biohazard` for Biohazard), `Gudang Pengepul` (near Spawn), `Koperasi Desa (Kopdes)`, `Warung Madura` (x7), `Dermaga` (exclusive embark/disembark river ports x2), elevated `Jembatan Utama`, upstream `Gunung Sampah` (`-Z`), & downstream **`+Z` `Pintu Air Siaga 1`** inside `Assets/_Project/Environment/`.
  3. Dynamic river water shader `SG_KaliWater.shadergraph` driven globally by Ivan's C# **`_WaterClarity`** float (`0.05` muddy brown -> `1.00` clean emerald teal) scrolling **`+V`** (`+Z` downstream).
  4. Height-blended world triplanar shader `SG_TrashTriplanar.shadergraph` for `SM_Env_GunungSampah_3Tiers`.

### Allowed Files & Directories (READ & WRITE)
- `unity/Assets/_Project/Environment/**` (`Meshes/`, `Materials/`, `Textures/`, `Prefabs/`)
- `unity/Assets/_Project/Shaders/**` (`SG_KaliWater.shadergraph`, `SG_TrashTriplanar.shadergraph`, subgraphs/materials)

### Strictly Forbidden (DO NOT MODIFY OTHER FOLDERS)
- `unity/Assets/_Project/Scripts/**`, `Data/**` *(Owned by Ivan - C# contracts are locked)*
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/VFX/**`, `UI/**`, `Audio/**` *(Owned by Niki)*

### Context Files to Read
1. `AGENTS.md` (Scale, `RiverMath` `130m x 180m` curve, `_WaterClarity`, Collider name hooks)
2. `docs/ARCHITECTURE.md` (Section 2 & Section 3A-3C C# integration points)
3. `docs/DESIGN.md` (Exact color hexes: `#3B2818`, `#1B6B63`, `#06B6D4`, PBR bamboo/zinc/silt rules)
4. `docs/PRD.md` (Zone 1 Kampung Hulu, Zone 2 Jembatan, Zone 3 Pintu Air & Gunung Sampah)

---

## 2. Hard Technical Constraints (Locked in Ivan's C# Scripts)

- **Exact Terrain World Size**: `130m wide (X) x 180m long (Z)`, centered at `(0, 0, 0)` (`WorldW=1040`, `WorldH=1440`, `MapScale=0.125`).
- **River Channel S-Curve**: Centerline follows `CenterX(mapY) = 520 + sin((mapY / 1440) * PI * 1.6) * 58`; base river width is `22.5m` (narrows at `mapY = 740` bridge choke, widens at south bay `mapY = 1220` & northern basin `mapY < 320`).
- **Current Flow Axis**: Debris & water flow toward **`+Z` downstream** (from upstream **`-Z` `Gunung Sampah`** straight down to downstream **`+Z` `Pintu Air Siaga 1`**). Baseline water starts near `Y = 0.0m` and rises linearly (`Overflow >= +1.40m`, `Sell-Lock >= +1.85m`); walkable village embankments sit at **`Y = +1.40m`** with stilts extending down to `-0.5m` so banks look natural as water rises and overflows!
- **Required Prefab Names & Colliders**:
  - `Bank Sampah` prefab GameObject name must contain `"Bank Sampah"` + Collider (Normal waste station).
  - **`Koperasi Desa (Kopdes)`** prefab GameObject name must contain **`"Koperasi Desa"`** or **`"Kopdes"`** + Collider (upgrade/gear shop).
  - **`Dermaga`** (`SM_Env_Dermaga`) prefab GameObject name must contain **`"Dermaga"`** + solid Collider (exclusive river port for boarding/disembarking boats and dry-dock swim stamina recovery).
  - **`Pos Medis B3`** prefab GameObject name must contain **`"Pos Medis"`** + Collider (dedicated Medical B3 waste clinic near `Jembatan Utama` West approach).
  - **`Karantina Biohazard`** prefab GameObject name must contain **`"Karantina Biohazard"`** + Collider (dedicated Biohazard/Radioactive containment bunker on East bank).
  - **`Gudang Pengepul`** prefab GameObject name must contain **`"Gudang Pengepul"`** + Collider (located near Spawn / `Bank Sampah` on West bank; cheap all-in-one bulk collector).
  - `Gunung Sampah` tiers must have `"Gunung Sampah"` in their name + Collider + bottom-anchored pivot (`Y = 0`) so scaling/dredging never leaves the mound floating!
  - `Jembatan Utama` deck MUST sit at **`Y >= +3.60m`** with center `>= 12m` channel clear of bridge piers so boats pass underneath cleanly.
- **Roof / Tower Clearances**: Leave top roof overhangs on `SM_Env_WarungMadura` and top tower pad on **`SM_Env_PintuAirSiaga1` (`+Z` downstream)** clear so JC's `PF_Lantern_Warung` & `PF_WarningBeacon_PintuAir` attach without clipping.

---

## 3. Milestone Tasks (Prioritized)

### Current Status & Unity Guardrail Note
Previous commit `7509ca6` (`SM_Env_RiverValleyTerrain` & `KaliWaterClarityPreview.cs`) was reverted in `a04d46c`. Environment assets are now on main via the `wesley-env-shaders` merge (`d4b1266`, `Main.unity` bake `e50ff50`). **Unity 6 Guardrail**: If working locally in Unity 6, only commit/push assets inside `Environment/` & `Shaders/` (plus their `.meta`s) - NEVER push `ProjectSettings/ProjectVersion.txt` alone without team-wide migration.

### Completed Onboarding
- [x] **Step 0: Onboarding & Greybox Inspection** (`git pull origin main`, inspect 53-node greybox via `KALI > Load Default Purpose-Built Map`).

### Priority 1: MVP Blockers (Kerjakan Sekarang)
- [x] **Step 1A: Terrain & Hero Water Shader (`SM_Env_RiverValleyTerrain` + `SG_KaliWater`)**: model/export `SM_Env_RiverValleyTerrain.fbx` (`130m x 180m`, riverbed `-2.0m`, banks `+1.40m`) + prefab, and build `SG_KaliWater.shadergraph` (`_WaterClarity`, Beer-Lambert depth tint `#3B2818` -> `#1B6B63`, `+V` dual-flow normals, shoreline foam, `0.05m` sine wave).
- [x] **Step 1B: Core Interactive Station Hubs + Pengepul (`Environment/Prefabs/`)**: build & push collider-ready prefabs matching C# string hooks for `Bank Sampah` (`SM_Env_BankSampah`), `Pos Medis` (`SM_Env_PosMedisB3`), `Karantina Biohazard` (`SM_Env_KarantinaBiohazard`), and `Gudang Pengepul` (`SM_Env_GudangPengepul`).

### Priority 2: Climax Landmarks, Triplanar Shader & Bridge (Setelah Terrain & Stations)
- [x] **Step 2: Landmarks & Bridge**: `SM_Env_PintuAirSiaga1.fbx` (`+Z` sluice gate, clear tower pad for JC beacon), `SM_Env_GunungSampah_3Tiers.fbx` (`-Z` upstream, bottom-anchored `Y = 0` pivot), `SG_TrashTriplanar.shadergraph`, and `SM_Env_JembatanUtama.fbx` (`Y >= +3.60m` deck, `>= 12m` center channel clear).

### Priority 3: Kampung Dressing, Natural Environment Replacements & Verification
- [x] **Step 3: Kampung Structures**: `SM_Env_KoperasiDesa` (`Koperasi Desa / Kopdes`), `SM_Env_RumahPanggung` (stilts to `-0.5m`, x11 nodes), `SM_Env_WarungMadura` (24-jam Warung Madura kiosk w/ clear roof overhang for lantern, x7 nodes), `SM_Env_Dermaga` (`Y = 0.0m` waterline pivot, exclusive boat port, x2 nodes).
- [ ] **Step 4A: Tropical Tree Models (`kelapa` & `pisang` in `Environment/`)**: model/export `SM_Env_PohonKelapa.fbx` + `SM_Env_PohonPisang.fbx` and build prefabs (`PF_Env_PohonKelapa.prefab`, `PF_Env_PohonPisang.prefab`) using shared paletted/weathered materials (`Environment/Materials/`) to replace the 86 generated slim low-poly tree stand-ins in `KaliMapBackdropBuilder.CreateLowPolyTree()` (`11` `pohon` + `75` rear groves).
  - *Dependency*: Wait for Ivan's kampung rows re-layout commit (`plan_ivan.md`), then Ivan wires the prefab paths in `KaliKampungBuilder.cs` / `KaliMapBackdropBuilder.cs`.
- [ ] **Step 4B: Backdrop Hills Horizon Mesh (`Environment/`)**: model/export `SM_Env_BackdropHills.fbx` + `PF_Env_BackdropHills.prefab` (`420m` outer rolling horizon ring matching the `130m × 180m` bank lip `Y = +1.40m` and `M_Env_TanahBantaran` / `SG_EnvWeathered`) to replace the procedural ring generated by `KaliMapBackdropBuilder.BuildBackdropHillsMesh()`. Keep `-Z` upstream profile low enough not to occlude `KaliSky`'s golden-hour sunset behind `Gunung Sampah`.
  - *Dependency*: Wait for Ivan's kampung rows re-layout commit; Ivan swaps the procedural hill mesh in `KaliMapBackdropBuilder.cs`.
- [ ] **Step 4C: River Washing Steps (`tangga cuci`) & Additional Jetties (`Environment/`)**: model/export `SM_Env_TanggaCuci.fbx` + `PF_Env_TanggaCuci.prefab` (stepped stone/concrete bank access descending to `Y = 0.0m` waterline, visually distinct from `Dermaga` boat ports) and additional rustic wooden jetties (`SM_Env_JettyKayu.fbx` + `PF_Env_JettyKayu.prefab`) to upgrade the procedural `KaliKampungBuilder` plank jetties.
  - *Dependency*: Wait for Ivan's kampung rows re-layout commit; used directly by Ivan's Ambient NPC system (`plan_ivan.md` / `KALI_NPC_BRIEF.md` — `Ibu-ibu` washing at `tangga cuci`, `Bapak-bapak` fishing & `Bocah-bocah` jumping from jetties).
- [ ] **Step 4D (Optional): Kampung Fences & Footpath Meshes (`Environment/`)**: modular low-poly bamboo/wood fences (`PF_Env_PagarKampung`) and stepped bank footpath tiles (`PF_Env_JalanSetapak`) for dense bank dressing between `RumahPanggung` rows.
  - *Dependency*: Optional polish after Steps 4A–4C; Ivan places along cleared bank corridors in `KaliKampungBuilder.cs`.
- [ ] **Step 4E: Blender `Ctrl + A -> All Transforms` (`-Z Forward`, `Y Up`, Lightmap UV2), `Environment/Prefabs/` Verification & Unity 6 Guardrail**: verify every new FBX/Prefab pivot, collider, and `Environment/` `.meta`, and NEVER push `ProjectSettings/ProjectVersion.txt` alone without team agreement (`plan_ivan.md` Task 4C).

---

## 4. Sidang Q&A Preparation (30% Understanding of the Process)
Be ready to open Blender + Shader Graph live and explain:
1. Why **`Scene Depth - Screen Position (W)`** + **`_WaterClarity`** models the Beer-Lambert light absorption switch from turbid brown sewage to crystal river water.
2. Why **Dual Normal Panning along `+V`** avoids visible seam loops and visually matches `RiverFlowBuoyancy`'s **`+Z` downstream** current.
3. Why **World-Space Triplanar Mapping (`SG_TrashTriplanar`)** eliminates UV stretching across huge organic shapes like `Gunung Sampah`.
