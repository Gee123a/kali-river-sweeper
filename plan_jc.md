# AI Implementation Plan: JC (Props, 3D Rigging & Lighting Lead)

> **Instructions for AI**: You are the dedicated AI 3D Technical Artist assistant for **Jason Christopher (JC)** on **KALI: Indonesian River Sweeper** (`Unity 2022.3.46f1 LTS URP` + `Blender 5.3.0`). Stay strictly inside JC's owned paths below. Never modify Ivan's `Scripts/`, Wesley's `Environment/` or `Shaders/`, or Niki's `VFX/`, `UI/`, `Audio/`.

---

## 1. Identity & Scope Boundaries

- **Owner**: Jason Christopher (JC)
- **Track**: 3D Props, 20 Scavenging Tools, Medical B3 & Biohazard Props, Hero IK Rigging & Lighting
- **Unity Version Alignment**: Current workspace operates on Unity `2022.3.46f1 LTS`. To address `CVE-2025-59489` security vulnerabilities, team will coordinate either upgrading to patched Unity `2022.3.67f2` or migrating to patched Unity 6 (`6000.0.58f2+` / `6000.3.29f1 LTS`) prior to final build packaging.
- **Git Contributor Hygiene**: Local personal git author commits only. Zero AI bot author attribution, zero `Co-Authored-By` trailers.
- **Primary Deliverables**:
  1. Authentic Indonesian floating trash prefabs + **Medical B3 (`MedicalBag`, `SyringeBox`)** & **Biohazard/Radioactive** prefabs (`Assets/_Project/Props/Trash/`).
  2. 20 non-redundant tool models (from `Sendok Makan` and `Gayung` to `Capitan Ular` and `Garuk Skimmer Hidrolik`, with `PF_Tool_*` `BoxCollider` `isTrigger = true` or disabled while equipped), vessels (`Rakit Gabus`, `Perahu Sampan`), `Kampung Bins`, and `PF_Prop_TrashBoomSegment` (`Assets/_Project/Props/Equipment/`).
  3. Hero rigged `SK_ExcavatorAmfibi.fbx` with 3-bone IK arm, 4 vertical spud legs, and dual `Damped Track` hydraulic pistons (`Assets/_Project/Rigging/`).
  4. Scene lighting & Post-FX prefabs (`KaliLightingBuilder.cs`, `PF_LightingRig`, `VolumeProfile_GoldenHour` *(superseded by `VP_KaliSky`)*, `VolumeProfile_MonsoonStorm` *(superseded by `VP_KaliSky`)*, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`) (`Assets/_Project/Lighting/`).

### Allowed Files & Directories (READ & WRITE)
- `blender/**` *(Reproducible Blender 5.3 Python generators - `blender -b -P blender/build_all.py`)*
- `unity/Assets/_Project/Props/**` (`Trash/`, `Tools/`, `Equipment/`)
- `unity/Assets/_Project/Rigging/**` (`SK_ExcavatorAmfibi.*`, Animators)
- `unity/Assets/_Project/Lighting/**` (`KaliLightingBuilder.cs`, `Prefabs/`, `VolumeProfiles/`)

### Strictly Forbidden (DO NOT READ OR MODIFY)
- `unity/Assets/_Project/Scripts/**`, `Data/**` *(Owned by Ivan)*
- `unity/Assets/_Project/Environment/**`, `Shaders/**` *(Owned by Wesley)*
- `unity/Assets/_Project/VFX/**`, `UI/**`, `Audio/**` *(Owned by Niki)*

### Context Files to Read
1. `AGENTS.md` (Scale, Blender export rules, exact `MapJsonImporter.cs` prefab paths)
2. `docs/ARCHITECTURE.md` (Section 3C auto-spawned paths & Section 4 Excavator Rig Spec)
3. `docs/PRD.md` (Section 3 20 Tools list + Section 4 Trash & Medical Waste classes)
4. `docs/DESIGN.md` (PBR plastic/bamboo/rusted steel/biohazard color tokens)

---

## 2. Roadmap & Milestone Tasks (Prioritized)

- **Timeline Overview**: **Completed in `main`** (`SM_Tool_*` x20 FBX, `SK_ExcavatorAmfibi.fbx`, `SM_Trash_MedicalBag.fbx`, `SM_Trash_SyringeBox.fbx`, `KaliPropPrefabBuilder.cs`) vs **Generated Locally on Ivan's Machine** (`PF_Tool_*`, `PF_Trash_*`, `PF_ExcavatorAmfibi.prefab` pending commit).

### Completed in main
- [x] **Task 1: Hero Rigged Asset - `SK_ExcavatorAmfibi` (`Assets/_Project/Rigging/`)** *(Implemented in `blender/build_all.py` - 4,298 tris)*
  - [x] Model pontoon catamaran hull, 4 vertical spud anchors (`0 to -3.5m` Z), rotating cab turret (`360° Z`), `4.2m` Boom, `2.8m` Stick, `1.4m` 5-tooth Bucket (`-Y` forward, `+X` left in Blender).
  - [x] Build Armature hierarchy: `B_Root_Hull` $\to$ `B_Turret_Slew` $\to$ `B_Arm_Boom` $\to$ `B_Arm_Stick` $\to$ `B_Tool_Bucket`, `B_Piston_Bucket_Base` parented to `B_Arm_Stick`, plus `B_Spud_Leg_FL/FR/BL/BR`.
  - [x] Add Non-Deform controller bones (`CTRL_IK_Bucket` placed at wrist joint + `Copy Rotation` for bucket curl, `POLE_Elbow_Target`).
  - [x] Pose Mode on `B_Arm_Stick`: `Inverse Kinematics` constraint $\to$ Target `CTRL_IK_Bucket`, Pole `POLE_Elbow_Target`, **`Chain Length = 2`** *(keep poses within ergonomic Boom `-15°..75°` & Stick `-110°..+10°` bounds during animation since Pole-Target IK bypasses Limit Rotation)*.
  - [x] Setup Dual Mutual **`Damped Track` (`+Y`)** Hydraulic Piston Pairs for Boom L/R, Stick, and Bucket hydraulics.
  - [x] Assign 3 PBR material slots (`M_Excavator_Body`, `M_Hydraulic_Steel`, `M_Pontoon_Rubber`).
  - [x] Export FBX: `Ctrl + A -> All Transforms`, `-Z Forward`, `Y Up`, Face smoothing, **UNCHECK `Add Leaf Bones`** (zero `_end` bones); verify Unity Prefab hull faces `+Z` (blue forward arrow).
- [x] **Task 1b: 20 Scavenging Tools & Medical B3 Assets**
  - [x] Model all **20 Scavenging Tools** per `docs/PRD.md` Section 3 (`#01 Sendok Makan` .. `#20 Garuk Skimmer Hidrolik`, 364–1,120 tris, grip pivot `(0,0,0)` along Z, `2048×2048` `T_Tools_Atlas` Albedo/Normal/Mask) $\to$ `Props/Tools/Meshes/SM_Tool_*.fbx`.
  - [x] **CRITICAL `PF_Tool_*` Collider Rule**: `BoxCollider.isTrigger = true` implemented in `KaliPropPrefabBuilder.cs` and disabled while equipped in `KaliPlayerController.cs`.
  - [x] Model **Medical Waste B3 (`WasteClass.Medical`)** props (`SM_Trash_MedicalBag` 372 tris, `SM_Trash_SyringeBox` 288 tris) in hazard yellow (`#EAB308`) with red accents $\to$ `Props/Trash/Meshes/`, `T_Trash_Atlas` 2048 (`0%` needle prick when using `#10 Capitan Ular`, sorted at **`Pos Medis B3`**).
- [x] **Task 2A (Parody Trash & Biohazard Drum) & Task 2B/2C Core Props**: `PF_Trash_BiohazardDrum`, `PF_Trash_AquaBottle_600ml`, `PF_Trash_AquaGalon_19L`, 9 parody-brand trash prefabs + 9 `PF_Product_*` prefabs, `PF_Prop_TrashBoomSegment`, `PF_Prop_RakitGabus`, `PF_Prop_PerahuSampan`, and `PF_Prop_TongSampahKampung` shipped on `main`.
- [x] **Task 3: Lighting & Base Rigging FBXs (`Assets/_Project/Lighting/`, `Rigging/`)**: procedural skybox & 12-min day/night rig (`KaliSky.shader`, `M_KaliSky.mat`, `VP_KaliSky.asset`, `KaliLightingBuilder.cs`, `PF_LightingRig.prefab`) built by Ivan (`Scripts/Core/KaliDayNightCycle.cs`); `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`, `SK_VillagerNPC.fbx` (`Idle` / `ThrowTrash` / `CarryBin`), `SM_Villager_Bin`, `SM_Villager_TrashBag`, and `Anim_PlayerToolSwing.fbx` (`SerokanScoop` / `GancoHookSwing`) landed on `main`.

### Priority 1: Ambient NPC Animations & Props (Feeds Ivan's NPC System)
- [ ] **Task 4A: Villager NPC Animations (`SK_VillagerNPC.fbx` in `Assets/_Project/Rigging/`)**: add Humanoid 30 fps clips matching `Rigging/README.md` (`Idle`/`CarryBin` convention, Root Motion off):
  - [ ] Fishing cast & seated/standing idle loop (`Bapak-bapak` fishers).
  - [ ] Washing-clothes crouched scrub loop (`Ibu-ibu` washers).
  - [ ] Kids splash / wade / jetty-jump loops (`Bocah-bocah`).
  - [ ] Chatting idle loop (`Warung` / house porch villagers).
  - *Dependency*: Ivan's ambient NPC system (`plan_ivan.md`, `KaliAmbientNpc.cs`) starts with existing `Idle`/`ThrowTrash`/`CarryBin` + procedural fallback, then swaps in these clips once merged.
- [ ] **Task 4B: Villager Activity Props (`Assets/_Project/Props/Equipment/` or `Rigging/`)**: model/export `PF_Prop_FishingRod` (matching `Socket_RightHand` / `Socket_LeftHand`), `PF_Prop_LaundryBasket` (woven basket for washers/chatters), and `PF_Prop_WaterBucket` (`T_Villager_Palette` or `T_Equipment`).
  - *Dependency*: Mounted by Ivan's `KaliAmbientNpc.cs` to replace generated cylinder/line rod stand-ins.

### Priority 2: Missing World Prop, Branch Sync & First-Person Tool Swing Wiring
- [ ] **Task 5A: `PF_Prop_SolarInterceptor` (`Assets/_Project/Props/Equipment/`)**: model/export `SM_Prop_SolarInterceptor.fbx` + `PF_Prop_SolarInterceptor.prefab` (`Waterline Y = 0` pivot + collider) to replace the teal primitive placeholder currently mapped to `"interceptor"` in `MapJsonImporter.cs` / `Main.unity`.
  - *Dependency*: Once pushed, Ivan re-runs `KALI > Load Default Purpose-Built Map` to bake the real prefab into `Main.unity`.
- [ ] **Task 5B: Rebase `jc-products` onto `main`**: resolve merge conflicts against `main` (`KaliPropPrefabBuilder.cs`, `blender/SM_Trash_Pack.blend`, `blender/build_all.py`, and texture atlases — note `PF_Product_*`, `AquaBottle_600ml`, `AquaGalon_19L` are already on `main`), keep only clean non-duplicate Blender/product generator changes, and verify `Build Product Prefabs` compiles cleanly before closing the branch.
- [ ] **Task 5C: Wire `Anim_PlayerToolSwing` (`Assets/_Project/Rigging/`)**: create the `Generic` Animator Controller + `ToolHolder` rig prefab per `Rigging/README.md` (`SerokanScoop` 0.8s for nets/scoops, `GancoHookSwing` 0.7s for hooks/sickles/rakes, resting at `ToolHolder` `Euler(65, -8, 0)`).
  - *Dependency*: Notify Ivan as soon as `Anim_PlayerToolSwing` is wired on the player tool rig so Ivan disables `KaliPlayerController.cs`'s own procedural `32°` `ToolSocket.localRotation` sway (otherwise both swings add up).

### Priority 3: Guardrails & Optional Stretch
- [ ] **Unity 6 Guardrail**: if using Unity 6 locally, export/commit `.fbx`/`.prefab`/`.cs`/`.meta` only inside `Props/`, `Rigging/`, `Lighting/`. NEVER commit/push `ProjectSettings/ProjectVersion.txt` or `Library` unless the whole team upgrades together (`plan_ivan.md` Task 4C).
- [ ] **Optional Stretch (Only After Priorities 1–2)**: `SpillBarrierFloat`, `PumpGenerator`, and extra organic trash variants (`EcengGondok`, `BatangPisang`, `SandalSwallow`, `BanBekas`, `KasurKapuk`) if extra prop variety is requested before freeze.

---

## 3. Blender Export Checklist & Sidang Q&A Proof
- Keep raw `.blend` files and UV sheets ready to open live during Sidang Q&A (**30% Understanding of the Process**).
- Be ready to toggle `CTRL_IK_Bucket` in Blender Pose Mode live to prove zero-clipping mutual `Damped Track` hydraulic telescoping and `Chain Length = 2` IK isolation.
