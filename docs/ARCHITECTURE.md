# ARCHITECTURE.md — Unity URP + Blender System Design & Contracts

> **Purpose**: Defines the conflict-free folder hierarchy, `RiverMath` coordinate mapping (`130m × 180m`), C#-to-Shader/Collider contracts, and the `SK_ExcavatorAmfibi` IK + hydraulic piston rigging spec shared across **Ivan**, **JC**, **Wesley**, and **Niki**.

![Game Flow & River Topology](./kali_game_flow_and_architecture.png)

---

## 1. Repository Directory Structure (Conflict-Free Ownership)

```text
kali-river-sweeper/
├── AGENTS.md                                # [Ivan] Master AI rules, directory boundaries & guardrails
├── CLAUDE.md                                # [Ivan] Quick AI entry pointer
├── README.md                                # [Shared] Overview, team split & quick start
├── plan_ivan.md                             # [Ivan] Isolated implementation plan (Core C#, Map, Report)
├── plan_jc.md                               # [JC] Isolated implementation plan (Props, Tools, IK Rig, Lighting)
├── plan_wesley.md                           # [Wesley] Isolated implementation plan (13 Env Meshes, Shaders)
├── plan_niki.md                             # [Niki] Isolated implementation plan (VFX, UI Canvases, Audio)
├── docs/
│   ├── PLAYBOOK.md                          # Master AI-assisted production playbook & rubric scorecard
│   ├── PRD.md                               # Product Requirements, 20 auto-unlock tools, 3-class waste, 3 stations & 4 endings
│   ├── ARCHITECTURE.md                      # System design, C# contracts & rigging architecture (this file)
│   ├── DESIGN.md                            # Visual identity, color palette, PBR rules & HUD typography
│   ├── TECH_STACK.md                        # Unity 2022.3.46f1 URP, Blender 5.3.0 & poly budgets
│   ├── TEAM_WORKFLOW.md                     # Integration sequence, Git rules & ready-to-paste prompts
│   └── KALI_Asset_Master_Tracker.xlsx/.tsv  # Complete asset deliverable tracker
├── tools/
│   ├── play-3d.html                         # [Ivan] Standalone Three.js browser prototype (zero Unity needed)
│   └── map-editor.html                      # [Ivan] Interactive river level layout editor
└── unity/
    ├── ProjectSettings/ProjectVersion.txt   # Unity 2022.3.46f1
    ├── Packages/manifest.json               # URP 14.0.11, ShaderGraph, VFX Graph, AnimationRigging
    └── Assets/_Project/
        ├── Scripts/                         # [Ivan ONLY] Core/ (incl. ToolCatalog, RiverTrashItem, RiverTrashSpawner), Player/, Editor/
        ├── Data/kali-river-map.json         # [Ivan ONLY] 54 spatial river nodes, +Z flow & 3 stations + Pengepul
        ├── Props/                           # [JC ONLY] Trash/ (Normal, Medical, Biohazard), Tools/ (20 PF_Tool_*), Equipment/
        ├── Rigging/                         # [JC ONLY] SK_ExcavatorAmfibi.fbx & Animator controllers
        ├── Lighting/                        # [JC ONLY] KaliLightingBuilder.cs, PF_LightingRig, Profiles
        ├── Environment/                     # [Wesley ONLY] Meshes/, Materials/, Textures/, Prefabs/ (SM_Env_*)
        ├── Shaders/                         # [Wesley ONLY] SG_KaliWater.shadergraph, SG_TrashTriplanar
        ├── VFX/                             # [Niki ONLY] 4 URP VFX / Shuriken particle prefabs
        ├── UI/                              # [Niki ONLY] Canvas_HUD, Canvas_ShopBankSampah, Canvas_SDGImpactReport
        ├── Audio/                           # [Niki ONLY] Ambience, splash, siren & UI SFX
        └── Scenes/                          # [Ivan Integration] Generated via KALI > Load Default Purpose-Built Map
```

---

## 2. Single Source of Truth Constants & Coordinate Contract (`RiverMath`)

Defined in `unity/Assets/_Project/Scripts/Core/RiverFlowBuoyancy.cs` and mirrored in `tools/play-3d.html`:

| Constant / Method | Exact Value / Formula | Impact Across Team |
| :--- | :--- | :--- |
| `WorldW` / `WorldH` / `MapScale` | `1040f` / `1440f` / `0.125f` | **Wesley's Terrain Footprint** MUST equal **`130m (X) × 180m (Z)`**, centered at `(0, 0, 0)`. |
| `ToWorld3D(mapX, mapY, elev)` | `((mapX - 520) * 0.125, elev, (mapY - 720) * 0.125)` | Converts `kali-river-map.json` nodes into Unity meters. |
| `RiverCenterMapX(mapY)` | `520 + sin((mapY / 1440) * PI * 1.6) * 58` | Exact S-curve centerline Wesley's `SM_Env_RiverValleyTerrain` riverbed must follow. |
| `RiverHalfWidthMap(mapY)` | Base width `22.5m`, narrows at `mapY = 740` (Bridge), widens at `mapY < 320` & `mapY = 1220` | Houses/warungs (`+0.8m` elev) must stay clear of channel banks (`IsInRiver()`). |
| Current Vector & Linear Water Y | `waterLevelY = -0.25f + TotalTrashInRiver * 0.020f` (`Overflow 1.40m`, `Sell-Lock 1.85m`, `Fatal 2.45m`), drift toward **`+Z` downstream** (`Gunung Sampah` `-Z` upstream $\to$ `Pintu Air` `+Z` downstream barrier) | Floating trash (`JC`), water flow UV pan (`Wesley`, **`+V`**), and foam (`Wesley`/`Niki`) align on **`+Z`**. |

---

## 3. C# Runtime Hooks & Integration Contracts

All subsystems integrate via these verified symbols in `Scripts/`:

### A. Shader Global Contract (`RiverGameManager.cs` $\leftrightarrow$ `Wesley`)
- `RiverGameManager.NotifyState()` (throttled ~10 Hz on continuous ticks) executes **`Shader.SetGlobalFloat("_WaterClarity", waterClarity)`** (`0.05f` polluted muddy brown $\rightarrow$ `1.0f` crystal turquoise).
- `SG_KaliWater.shadergraph` MUST define a Blackboard Float property with exact Reference Name **`_WaterClarity`**.
- Water surface panning: dual normal maps scrolled in **`+V`** (`+Z` downstream world flow); depth absorption via `Scene Depth - Screen Position (W)`; shoreline/trash foam via `Step(0.35, DepthDiff)`.

### B. Collider & Name Hooks (`KaliPlayerController.cs` $\leftrightarrow$ `Wesley` & `JC`)
- `TryFindNearestHub()` scans `Physics.OverlapSphere(pos, 7.5f)` for **`1 / 2 / 3 / E`** station interactions:
  - GameObject containing **`"Bank Sampah"`** with Collider $\rightarrow$ `Normal` waste station.
  - GameObject containing **`"Pos Sortir"`** with Collider $\rightarrow$ `Normal` waste baling bonus station.
  - GameObject containing **`"Pos Medis"`** with Collider $\rightarrow$ `Medical` B3 waste clinic.
  - GameObject containing **`"Karantina Biohazard"`** with Collider $\rightarrow$ `Biohazard` quarantine bunker.
  - GameObject containing **`"Gudang Pengepul"`** with Collider (near Spawn) $\rightarrow$ cheap all-in-one bulk dump (`SellAllAtPengepul()`).
  - Wrong-station discards trigger Rupiah fines; during `IsSellLocked` (`waterLevelY >= 1.85m`), hubs lock and player presses **`Q`** to dump cargo on high ground.
- `TryScoopOrDredge()` uses camera-aimed nearest-target selection on **`Left Click`**:
  - GameObject with **`RiverFlowBuoyancy`** + **`RiverTrashItem`** + Collider $\rightarrow$ scoops `Normal`, `Medical` (prick risk mitigated to `0%` by `#10 Capitan Ular`), or `Biohazard` (DoT in cargo past 10s).
  - GameObject containing **`"PintuAirPile"`** with Collider $\rightarrow$ scoops piled downstream barrier debris (`TryScoopPiledBarrierTrash`).
  - GameObject containing **`"Gunung Sampah"`** + `GunungNodeController` + Collider $\rightarrow$ bottom-anchored dredge scaling (`excavatorUnlocked` or tool `#13+`).
  - **Equipped Tool Colliders**: `PF_Tool_*` `BoxCollider` must be **`isTrigger = true` or disabled while equipped** (`KaliPlayerController` forces this on equip).

### C. Prefab Auto-Spawner Hooks (`MapJsonImporter.cs` $\leftrightarrow$ `JC` & `Wesley`)
Menu item **`KALI > Load Default Purpose-Built Map`** splits West/East `Ground_Daratan` banks (open water channel down to `-2.0m`), elevates `Jembatan Utama` (`Y = +3.6m`), attaches `RiverTrashSpawner` to `Managers`, parses all **54 nodes** in `kali-river-map.json` (`11` rumah, `7` warung, `11` pohon, `8` trash_pile, `3` gunung_node, `2` dermaga, `1` sluice_gate at `+Z`, `1` jembatan, `1` bank_sampah, `1` pos_medis, `1` karantina_biohazard, `1` pengepul near Spawn, `1` toko_alat, `1` sorting_yard, `1` trash_boom, `1` excavator, `1` interceptor, `1` spawn), and auto-loads:
- `Assets/_Project/Lighting/Prefabs/PF_LightingRig.prefab`
- `Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab` (attached above `warung` nodes)
- `Assets/_Project/Lighting/Prefabs/PF_WarningBeacon_PintuAir.prefab` (attached atop `+Z` downstream `sluice_gate`)
- `Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TrashBoomSegment.prefab`
- `Assets/_Project/Props/Trash/Prefabs/PF_Trash_{SandalSwallow,AquaBottle_600ml,AquaGalon_19L,PopMieCup,KresekBag,KasurKapuk,BanBekas,EcengGondok,BatangPisang,MedicalBag,SyringeBox}.prefab` (plus `PF_Trash_BiohazardDrum` / `PF_Trash_RadioactiveBarrel` with runtime fallback)
- `Assets/_Project/Props/Tools/Prefabs/PF_Tool_<Name>.prefab` (`#01 SendokMakanBengkok` .. `#20 GarukSkimmerHidrolik`)

### D. Event Subscriptions for UI & VFX (`RiverGameManager.cs` $\leftrightarrow$ `Niki`)
- `RiverGameManager.Instance.OnStateChanged` (throttled ~10 Hz on continuous ticks) $\rightarrow$ Refresh `Canvas_HUD` (`rupiah`, `cumulativeEarnings`, `playerHealth`, `cargoCount/cargoCapacity`, `normalCargo/medicalCargo/biohazardCargo`, `currentWaterLevelY`, `IsBankOverflowing`, `IsSellLocked`, `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `SiagaLevel`, `floodPressure`, `monsoonCountdownRemaining`, `equippedToolIndex/highestUnlockedToolIndex`, `waterClarity`, `gunungSampahHealth`, `communityTrust`, `medicalWasteSecured`, `biohazardWasteSecured`, `infectionIncidents`, `wrongDiscardCount`, `totalFinesPaid`, `pengepulHazardDumped`).
- `RiverGameManager.Instance.OnToolUnlocked(ToolDefinition)` & `OnEquippedToolChanged(ToolDefinition)` $\rightarrow$ Show tool milestone toast & update tool HUD slot.
- `RiverGameManager.Instance.OnHazardOrAlert(string msg, bool isDanger)` $\rightarrow$ Display prick, Biohazard DoT, wrong-station fine, and Sell-Lock alert banners.
- `RiverGameManager.Instance.OnWeatherChanged(bool isMonsoonStorm)` $\rightarrow$ Toggle `VFX_MonsoonRain` and storm lighting/audio.
- `RiverGameManager.Instance.OnEndingTriggered(GameEnding ending)` $\rightarrow$ Display `Canvas_SDGImpactReport` for **`TrueSdgVictory`**, **`CompromisedOceanFlush`**, **`FloodFail`**, or **`HealthFail`**.

---

## 4. Hero IK & Hydraulic Rigging Spec (`SK_ExcavatorAmfibi` — `JC`)

1. **Bone Hierarchy & Coordinate Alignment**:
   - Blender orientation: Excavator faces **`-Y`** (Front), Left = **`+X`**, Up = **`+Z`**. Ensure the Unity Prefab forward aligns with **`+Z` (blue arrow)** on the root hull.
   - `B_Root_Hull` (Pontoon hull + `B_Spud_Leg_FL/FR/BL/BR` lowering `0 to -3.5m` in Z)
   - $\rightarrow$ `B_Turret_Slew` (360° Z rotation) $\rightarrow$ `B_Arm_Boom` (`4.2m`) $\rightarrow$ `B_Arm_Stick` (`2.8m`) $\rightarrow$ `B_Tool_Bucket` (`1.4m` dredge scoop + clamp)
   - Hydraulic cylinder parents: `B_Piston_Boom_Base_L/R` under `B_Turret_Slew`; `B_Piston_Stick_Base` under `B_Arm_Boom`; **`B_Piston_Bucket_Base` under `B_Arm_Stick`** (matching physical stick-mounted actuator geometry).
   - Controllers (Deform UNCHECKED): **`CTRL_IK_Bucket` anchored at wrist hinge** (`B_Tool_Bucket` head / `B_Arm_Stick` tail) + `POLE_Elbow_Target`.
2. **IK Solver & Rotation Control**:
   - Pose Mode on `B_Arm_Stick` $\rightarrow$ `Inverse Kinematics` constraint $\rightarrow$ Target `CTRL_IK_Bucket`, Pole `POLE_Elbow_Target`, **`Chain Length = 2`** (Boom + Stick only).
   - Add `Copy Rotation` on `B_Tool_Bucket` targeting `CTRL_IK_Bucket` so one wrist controller handles reach + scoop curl.
   - Note: Blender's IK solver with a Pole Target overrides `Limit Rotation` constraints; keep `CTRL_IK_Bucket` keyframes within ergonomic reach (Boom `-15°..75°`, Stick `-110°..+10°`) when animating.
3. **Zero-Clipping Hydraulic Pistons**: Mutual **`Damped Track` (`+Y`)** pairs (`Base` $\leftrightarrow$ `Rod`) for Boom L/R, Stick, and Bucket so chrome shafts telescope smoothly with zero gaps or clipping.
4. **FBX Export Protocol (Blender 5.3 $\to$ Unity 2022.3)**:
   - `Ctrl + A -> All Transforms` (`Scale: 1.0`, `Rot: 0,0,0`), reproducible build via `blender -b -P blender/build_all.py`.
   - Forward: `-Z Forward`, Up: `Y Up`, Smoothing: `Face`.
   - Armature tab: **UNCHECK `Add Leaf Bones`** (verified zero `_end` bones).
   - Unity Inspector Rig tab: Animation Type **`Generic`**, Root Node **`B_Root_Hull`**.
   - Material slots (`4,298 tris`): `M_Excavator_Body`, `M_Hydraulic_Steel`, `M_Pontoon_Rubber`.
