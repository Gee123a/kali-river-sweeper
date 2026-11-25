# AI Implementation Plan: JC (Props, 3D Rigging & Lighting Lead)

> **Instructions for AI**: You are the dedicated AI 3D Technical Artist assistant for **Jason Christopher (JC)** on **KALI: Indonesian River Sweeper** (`Unity 2022.3.46f1 LTS URP` + `Blender 5.3.0`). Stay strictly inside JC's owned paths below. Never modify Ivan's `Scripts/`, Wesley's `Environment/` or `Shaders/`, or Niki's `VFX/`, `UI/`, `Audio/`.

---

## 1. Identity & Scope Boundaries

- **Owner**: Jason Christopher (JC)
- **Track**: 3D Props, 20 Scavenging Tools, Medical Biohazard Props, Hero IK Rigging & Lighting
- **Primary Deliverables**:
  1. Authentic Indonesian floating trash prefabs + **Medical Biohazard Waste B3** prefabs (`Assets/_Project/Props/Trash/`).
  2. 20 non-redundant tool models (from `Sendok Makan` and `Gayung` to `Capitan Ular` and `Pompa Mesin 49cc`), vessels (`Rakit Gabus`, `Perahu Sampan`), `Kampung Bins`, and `PF_Prop_TrashBoomSegment` (`Assets/_Project/Props/Equipment/`).
  3. Hero rigged `SK_ExcavatorAmfibi.fbx` with 3-bone IK arm, 4 vertical spud legs, and dual `Damped Track` hydraulic pistons (`Assets/_Project/Rigging/`).
  4. Scene lighting & Post-FX prefabs (`KaliLightingBuilder.cs`, `PF_LightingRig`, `VolumeProfile_GoldenHour`, `VolumeProfile_MonsoonStorm`, `PF_Lantern_Warung`, `PF_WarningBeacon_PintuAir`) (`Assets/_Project/Lighting/`).

### Allowed Files & Directories (READ & WRITE)
- `unity/Assets/_Project/Props/**` (`Trash/`, `Equipment/`)
- `unity/Assets/_Project/Rigging/**` (`SK_ExcavatorAmfibi.*`, Animators, `.blend` sources if tracked)
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

## 2. Step-by-Step Task Checklist

- [ ] **Task 1: Hero Rigged Asset — `SK_ExcavatorAmfibi` (`Assets/_Project/Rigging/`)**
  - [ ] Model pontoon catamaran hull (`7.2m × 4.8m × 1.4m`), 4 corner spud anchors, rotating cab turret (`360° Z`), `4.2m` Boom, `2.8m` Stick, `1.4m` 5-tooth dredge Bucket + thumb clamp (`4,000–6,000 tris` total).
  - [ ] Build Armature hierarchy: `B_Root_Hull` $\to$ `B_Turret_Slew` $\to$ `B_Arm_Boom` $\to$ `B_Arm_Stick` $\to$ `B_Tool_Bucket`, plus `B_Spud_Leg_FL/FR/BL/BR`.
  - [ ] Add Non-Deform controller bones (`CTRL_IK_Bucket`, `POLE_Elbow_Target`, UNCHECK `Deform`).
  - [ ] Pose Mode on `B_Arm_Stick`: add `Inverse Kinematics` constraint $\to$ Target `CTRL_IK_Bucket`, Pole `POLE_Elbow_Target`, **`Chain Length = 2`**.
  - [ ] Setup Dual Mutual **`Damped Track` (`+Y`)** Hydraulic Piston Pairs (`Cylinder` parented to base tracking `Ram`; `Ram` parented to moving arm tracking `Cylinder`) for Boom, Stick, and Bucket hydraulics.
  - [ ] Assign 3 PBR material slots: `M_Excavator_Body` (`#EAB308`), `M_Hydraulic_Steel` (`Metallic 0.95`, `Smoothness 0.90`), `M_Pontoon_Rubber` (`#1E293B`).
  - [ ] Export FBX: `Ctrl + A -> All Transforms` (`Scale 1.0`, `Rot 0,0,0`), `-Z Forward`, `Y Up`, **UNCHECK `Add Leaf Bones`**; set Unity Rig to **`Generic`**, Root Node `B_Root_Hull`.

- [ ] **Task 2: Trash, Medical Biohazard & 20 Scavenging Tools (`Assets/_Project/Props/`)**
  - [ ] Ensure exact prefab paths expected by `MapJsonImporter.cs` exist inside `Assets/_Project/Props/Trash/Prefabs/`:
    - `PF_Trash_SandalSwallow.prefab`, `PF_Trash_AquaBottle_600ml.prefab`, `PF_Trash_AquaGalon_19L.prefab`, `PF_Trash_PopMieCup.prefab`, `PF_Trash_KresekBag.prefab`, `PF_Trash_KasurKapuk.prefab`, `PF_Trash_BanBekas.prefab`, `PF_Trash_EcengGondok.prefab`, `PF_Trash_BatangPisang.prefab`.
  - [ ] Attach `Collider` + `RiverFlowBuoyancy` on every floating trash prefab.
  - [ ] Model **Medical Biohazard Waste B3** props (`PF_Trash_MedicalBag`, `PF_Trash_SyringeBox`) in hazard yellow (`#EAB308`) with red accents so players spot them for `Capitan Ular` extraction.
  - [ ] Model all **20 Non-Redundant Tools** (`300–1,200 tris` each, shared `2048×2048` atlas) with **grip pivot exact at `(0, 0, 0)`**, shaft pointing `+Z`/`+Y`.
  - [ ] Package `Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab` (with `Waterline` `Y = 0` pivot), `RakitGabus`, `PerahuSampan`, and `TongSampahKampung`.

- [ ] **Task 3: Lighting & Post-Processing Rigs (`Assets/_Project/Lighting/`)**
  - [ ] Build/verify `Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab` (Sun + `VolumeProfile_GoldenHour` `3400K` + `VolumeProfile_MonsoonStorm`).
  - [ ] Build `Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab` (warm `2100K` point light with subtle flicker) and `PF_WarningBeacon_PintuAir.prefab` (rotating orange/red flood siren spot light).

---

## 3. Blender Export Checklist & Sidang Q&A Proof
- Keep raw `.blend` files and UV sheets ready to open live during Sidang Q&A (**30% Understanding of the Process**).
- Be ready to toggle `CTRL_IK_Bucket` in Blender Pose Mode live to prove zero-clipping mutual `Damped Track` hydraulic telescoping and `Chain Length = 2` IK isolation.
