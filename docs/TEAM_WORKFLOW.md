# TEAM_WORKFLOW.md — Parallel Production Playbook (Ivan, JC, Wesley, Niki)

> **How to use this file**: Each member of KALI owns an isolated directory tree inside `unity/Assets/_Project/`, an isolated implementation file (`plan_<member>.md`), and a ready-to-paste AI prompt below. Paste your prompt into Claude Code, Antigravity, Cursor, or ChatGPT so your AI automatically reads `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/DESIGN.md` before doing anything.

---

## 1. Team Tracks & Parallel Workstreams

| Track | Member | Owned Unity Folders | Primary Deliverables |
| :--- | :--- | :--- | :--- |
| **Core & Integration** | **Ivan** | `Scripts/`, `Data/`, `tools/` | C# game loop (`RiverGameManager`), `RiverMath` buoyancy, FP/boat controls, `MapJsonImporter`, Medical Waste B3 hook, `kali-river-map.json`, `F9` Sidang demo hotkeys, prefab wire-up, Academic Report |
| **Props, Rig & Lighting** | **JC** | `Props/`, `Rigging/`, `Lighting/` | Trash & Medical B3 prefabs (`PF_Trash_*`), 20 scavenging tool models, vessels (`Rakit`, `Sampan`), `PF_Prop_TrashBoomSegment`, `SK_ExcavatorAmfibi` 3-bone IK + `Damped Track` hydraulic rig, `KaliLightingBuilder` + `PF_LightingRig` |
| **Environment & Shaders** | **Wesley** | `Environment/`, `Shaders/` | 10 `SM_Env_*` FBX meshes synced to `130m × 180m` `RiverMath` curve, `SG_KaliWater` (`_WaterClarity` global hook), `SG_TrashTriplanar` |
| **VFX, UI & Audio** | **Niki** | `VFX/`, `UI/`, `Audio/` | 4 particle VFX prefabs (`MonsoonRain`, `WaterSplashMuddy`, `MethaneSludgeBubbles`, `TrashAvalanche`), 3 UI Canvases (`HUD`, `ShopBankSampah`, `SDGImpactReport`), SFX triggers & Sidang script |

---

## 2. Step-by-Step Integration Order (Zero Blockers)

1. **Phase 0 — Contract Lock (Ivan — Complete)**:
   - C# core architecture, `RiverMath` (`130m × 180m`), `_WaterClarity` global shader push, `MapJsonImporter` menu (`KALI > Load Default Purpose-Built Map`), and 51-node `kali-river-map.json` pushed to `main`.
2. **Phase 1 — Parallel Build (JC, Wesley, Niki work simultaneously with zero merge clashes)**:
   - **JC**: Builds `SK_ExcavatorAmfibi.fbx`, trash/medical props, 20 tools, and generates lighting prefabs inside `Props/`, `Rigging/`, `Lighting/`.
   - **Wesley**: Models terrain + 9 landmark buildings inside `Environment/` and wires `SG_KaliWater` + `SG_TrashTriplanar` inside `Shaders/`.
   - **Niki**: Creates 4 VFX systems inside `VFX/`, builds HUD/Shop/Impact Report UI bound to `RiverGameManager` events inside `UI/`, and imports river/alarm audio inside `Audio/`.
3. **Phase 2 — Prefab Wire-Up (Ivan)**:
   - Maps Wesley's 10 `SM_Env_*` prefabs, JC's `SK_ExcavatorAmfibi`, and Niki's UI/VFX into `MapJsonImporter.cs` / main scene; attaches Colliders (`"Bank Sampah"`, `"Pos Sortir"`, `"Gunung Sampah"`).
4. **Phase 3 — Sidang `F9` Rehearsal & Polish (All)**:
   - Test full `F9 + 1..4` presentation sequence at 60+ FPS, capture screenshots for Academic Report, rehearse each member's Q&A live explanation (30% Process grade).

---

## 3. Ready-to-Paste Onboarding AI Prompts per Member

### For Ivan — Core Code, Prefab Wire-Up & Technical Coordinator (`plan_ivan.md`)
```text
Read AGENTS.md, plan_ivan.md, docs/PRD.md and docs/ARCHITECTURE.md first. Follow all ownership rules.
I am Ivan (Coordinator & Core Lead). Stay inside my assigned paths:
- unity/Assets/_Project/Scripts/ (Core/, Player/, Editor/)
- unity/Assets/_Project/Data/kali-river-map.json
- tools/ (play-3d.html, map-editor.html) and docs/

Help me finish my remaining milestones cleanly:
1. Keep RiverGameManager.cs, KaliPlayerController.cs, and RiverFlowBuoyancy.cs synced with JC's 20 tools (especially Capitan Ular -> SecureMedicalWaste(true)), Wesley's env colliders ("Bank Sampah", "Pos Sortir", "Gunung Sampah"), and Niki's UI events.
2. Extend MapJsonImporter.cs so Wesley's SM_Env_* prefabs and SG_KaliWater material attach cleanly alongside JC's PF_LightingRig and PF_Trash_* prefabs.
3. Verify F9 Stage Jump (1..4) and standalone browser preview (tools/play-3d.html) match every game requirement for 85-100 rubric score.
```

### For JC — Props, Tools, Excavator IK Rig & Lighting (`plan_jc.md`)
```text
Read AGENTS.md, plan_jc.md, docs/PRD.md, docs/ARCHITECTURE.md, and docs/DESIGN.md first.
I am JC (3D Props, Rigging & Lighting Lead). Work strictly inside:
- unity/Assets/_Project/Props/
- unity/Assets/_Project/Rigging/
- unity/Assets/_Project/Lighting/

My deliverables (guide me step-by-step in Blender 5.3.0 & Unity 2022.3.46f1 URP):
1. Hero Rigged Excavator (SK_ExcavatorAmfibi.fbx): Build hull + 360 turret + Boom (4.2m) -> Stick (2.8m) -> Bucket (1.4m) + 4 Spud Legs. Setup Pose-mode IK on B_Arm_Stick targeting CTRL_IK_Bucket (Chain Length = 2) and mutual Damped Track (+Y) constraints on hydraulic cylinder/ram bone pairs. Uncheck "Add Leaf Bones" on FBX export (-Z Forward, Y Up, Ctrl+A All Transforms).
2. Trash & Medical Biohazard Props (PF_Trash_* matching MapJsonImporter paths) + 20 non-redundant tools with grip pivot at (0,0,0) + Floating Trash Boom segment (PF_Prop_TrashBoomSegment).
3. Lighting Prefabs via KaliLightingBuilder.cs: PF_LightingRig, VolumeProfile_GoldenHour, VolumeProfile_MonsoonStorm, PF_Lantern_Warung, PF_WarningBeacon_PintuAir.
Explain every step simply and prep me to defend the IK & hydraulic rig live during Sidang Q&A.
```

### For Wesley — 10 Environment Meshes & URP Water Shaders (`plan_wesley.md`)
```text
Read AGENTS.md, plan_wesley.md, docs/PRD.md, docs/ARCHITECTURE.md, and docs/DESIGN.md first.
I am Wesley (3D Environment & Shaders Lead). I am starting from scratch and don't know the codebase yet — walk me step-by-step from cloning GitHub (Gee123a/kali-river-sweeper), opening Unity 2022.3.46f1 URP, running menu "KALI > Load Default Purpose-Built Map" to inspect the 51-node greybox, to completing all my deliverables inside ONLY:
- unity/Assets/_Project/Environment/
- unity/Assets/_Project/Shaders/

My deliverables:
1. SM_Env_RiverValleyTerrain (130m X x 180m Z exact footprint matching RiverMath S-curve, water plane Y=0, dry banks >= +0.8m) + 9 Indonesian river structures (SM_Env_GunungSampah_3Tiers, SM_Env_PintuAirSiaga1, SM_Env_JembatanUtama, SM_Env_BankSampah, SM_Env_PosSortir, SM_Env_TokoAlat, SM_Env_RumahPanggung, SM_Env_Warung, SM_Env_Dermaga with waterline Y=0 pivot).
2. SG_KaliWater.shadergraph: CRITICAL — declare Blackboard Float property with exact Reference Name "_WaterClarity" (driven globally by Ivan's RiverGameManager.cs via Shader.SetGlobalFloat). Implement Beer-Lambert depth lerp (#3B2818 muddy -> #1B6B63 teal), dual panning normals along -V (-Z downstream), and Step depth shoreline foam.
3. SG_TrashTriplanar.shadergraph: World-space Triplanar height blend (wet silt -> kapok/medical bags -> dry PET) with zero UV stretching.
Guide me click-by-click in Blender 5.3.0 and Unity URP, and teach me how to explain Beer-Lambert absorption & triplanar mapping for our 30% Process Q&A grade.
```

### For Niki — VFX, UI Canvases & Audio/Narrative (`plan_niki.md`)
```text
Read AGENTS.md, plan_niki.md, docs/PRD.md, docs/ARCHITECTURE.md, and docs/DESIGN.md first.
I am Niki (VFX, UI & Audio/Narrative Lead). Work strictly inside:
- unity/Assets/_Project/VFX/
- unity/Assets/_Project/UI/
- unity/Assets/_Project/Audio/

My deliverables (guide me click-by-click in Unity 2022.3.46f1 URP):
1. 4 VFX Systems: VFX_MonsoonRain (reacts to RiverGameManager.OnWeatherChanged), VFX_WaterSplashMuddy (scoop/boat wake), VFX_MethaneSludgeBubbles (anaerobic sludge gas), VFX_TrashAvalanche (Gunung Sampah breach).
2. 3 UI Canvases (following docs/DESIGN.md Siaga 4->1 alert tokens & OnStateChanged/OnEndingTriggered C# events):
   - Canvas_HUD (Cargo counter, Rupiah, Siaga 4->1 Flood Meter, Water Clarity %, Medical Waste & Infection indicator, active tool badge).
   - Canvas_ShopBankSampah (Choice A: Burn Pit vs Bank Sampah/Pos Sortir; Choice B: Boats, 20 Tools & Kampung Bins; Choice C: Emergency Flush vs Hold & Dredge).
   - Canvas_SDGImpactReport (Triggered by OnEndingTriggered: shows TrueSdgVictory vs CompromisedOceanFlush vs FloodFail metrics for SDGs 6.3, 11.5, 14.1).
3. Ambient river audio, scoop splash, monsoon thunder, Pintu Air siren + 3-minute Sidang presentation flow synced to F9 + 1..4 hotkeys.
```

---

## 4. Git & Asset Contribution Rules

1. **Pull First**: Run `git pull origin main` before every Blender/Unity work session.
2. **Strict Folder Isolation**: Never save or commit scenes/assets inside another member's folder; Unity `.meta` files must always be committed together with their paired assets.
3. **Blender Transforms & Leaf Bones**: Always verify `Scale = (1, 1, 1)`, `-Z Forward`, `Y Up`, and no garbage leaf bones before committing `.fbx` files.
4. **Keep Concept Renders Local**: Do not force-add ignored `docs/*.jpg` / `docs/*.png` local concept renders into Git.
5. **Test `F9` Flow Before Final Freeze**: Verify no missing pink shaders, missing script references, or overlapping UI elements at `1920×1080` and `1280×720`.
