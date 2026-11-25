# KALI: Indonesian River Sweeper (`kali-river-sweeper`)

Official repository for **KALI: Indonesian River Sweeper (*Penjaga Terakhir Sungai Nusantara*)** — **IMT01303501 Computer Graphics Final Project (ALP)**, Universitas Ciputra Surabaya (Game Track, targeting Grade A **85–100%**).

> *"Di dunia ini, gunung sampah telah menumpuk sangat tinggi hingga mencekik satu-satunya sungai di desa, dan kamu adalah generasi terakhir penjaga sungai yang tersisa."*

The game transforms real Indonesian river revitalization (*Citarum, Ciliwung, Kalimas Surabaya*) into a 3D first-person & vessel cleanup simulator built in **Unity `2022.3.46f1` LTS (URP)** and **Blender `5.3.0`**:
1. **Start Improvised, End Industrial (20 Non-Redundant Tools + 5 Craft Tiers)**:
   - Begin wading/paddling on a leaky styrofoam raft (*rakit gabus*) with makeshift tools (*Sendok Makan Bengkok, Gayung Mandi Bolong, Centong Nasi, Garpu Taman*) and scale up through bamboo nets, forged hooks (*Ganco*), reachers for **Medical Biohazard Waste** (*Capitan Ular*), 49cc motorized slurry pumps, autonomous solar interceptors, and a rigged amphibious excavator (*SK_ExcavatorAmfibi*).
2. **Dynamic Flood Gauge (`Siaga 4 -> 1`) & Monsoon Climax**:
   - Debris drifts along curved river splines (`RiverMath`) toward the clogged sluice gate mountain (*Gunung Sampah Pintu Air*). As monsoon storms arrive, players manage flood pressure and choose across **3 ethical/systemic trade-offs** leading to **3 distinct endings** (`TrueSdgVictory`, `CompromisedOceanFlush`, or `FloodFail`).
3. **Real-Time Graphics & Simulation**:
   - C#-driven `SG_KaliWater` turbidity/clarity transition (`_WaterClarity`: `0.12` muddy brown $\rightarrow$ `1.00` clean emerald teal), Beer-Lambert depth absorption, world-space triplanar carving on `Gunung Sampah`, 3-bone IK excavator arm with dual `Damped Track` hydraulic pistons, URP volumetric/storm lighting, and VFX Graph monsoon/splash systems.

---

## 1. Team & Role Ownership

| Member | Role | Student ID | Primary Track & Unity Folders |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso** (`Ivan`) | **Coordinator & Core Lead** | `0706012410029` | Game loop, `RiverMath` buoyancy/drift, 3-Choice state machine, Flood Gauge (`Siaga 4 -> 1`), `F9` Demo hotkeys, `MapJsonImporter`, Git integration (`Assets/_Project/Scripts/`, `Data/`, `tools/`) |
| **Jason Christopher** (`JC`) | **Props, 3D, Rigging & Lighting Lead** | — | Indonesian trash props + Medical Waste B3, 20 tool models, vessels, `SK_ExcavatorAmfibi` 3-bone IK + hydraulic rig, Golden Hour / Monsoon `PF_LightingRig` (`Assets/_Project/Props/`, `Rigging/`, `Lighting/`) |
| **Wesley Goeinawan** (`Wesley`) | **Environment & Shader Lead** | `0706012410011` | 10 `SM_Env_*` riverbank & dam FBX meshes synced to `130m × 180m` river curve, `SG_KaliWater` (`_WaterClarity` global hook) & `SG_TrashTriplanar` (`Assets/_Project/Environment/`, `Shaders/`) |
| **Nicholas Gerwin Mawardji** (`Niki`) | **VFX, UI & Audio/Narrative Lead** | `0706012410015` | 4 particle VFX (`MonsoonRain`, `WaterSplashMuddy`, `MethaneSludgeBubbles`, `TrashAvalanche`), HUD Canvas, Bank Sampah Shop, SDG Impact Report Screen, SFX & Sidang deck (`Assets/_Project/VFX/`, `UI/`, `Audio/`) |

---

## 2. Documentation Suite for Agent-Driven Development

Before modeling, shading, wiring prefabs, or prompting an AI coding/3D assistant (Claude Code, Antigravity, Cursor, ChatGPT), read these core documents:

1. **[AGENTS.md](./AGENTS.md) / [CLAUDE.md](./CLAUDE.md)** — Master AI rules, conflict-free Unity directory boundaries, C# shader/collider contracts, and rubric guardrails.
2. **[docs/PLAYBOOK.md](./docs/PLAYBOOK.md)** — High-level production playbook, documentation map, and Grade-A rubric matrix.
3. **[docs/PRD.md](./docs/PRD.md)** — Full Product Requirements Document: story, 20-tool & vessel progression, Medical Waste B3 mechanic, 3 Dilemmas, 3 Endings, and SDG targets (**6.3**, **11.5**, **14.1**).
4. **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — Unity URP + Blender system design, conflict-free folder tree, `RiverMath` (`130m × 180m`) coordinate math, C# event/shader hooks (`_WaterClarity`), and `SK_ExcavatorAmfibi` IK rigging blueprint.
5. **[docs/DESIGN.md](./docs/DESIGN.md)** — "Kalimas Nusantara" visual identity, PBR surface rules, lighting moods (`Golden Hour` vs `Monsoon`), and UI HUD color tokens.
6. **[docs/TECH_STACK.md](./docs/TECH_STACK.md)** — Software versions (`Unity 2022.3.46f1`, `URP 14.0.11`, `Blender 5.3.0`), installed packages, and polygon/texture budgets.
7. **[docs/TEAM_WORKFLOW.md](./docs/TEAM_WORKFLOW.md)** — Parallel sprint sequence, integration order, Git conventions, and ready-to-paste onboarding AI prompts for each teammate.

### Dedicated Member AI Plans (Isolated Scope, Zero Token Waste)
Each teammate has an isolated implementation checklist built for direct AI execution:
- **Ivan (Core Code)**: **[plan_ivan.md](./plan_ivan.md)** — C# state machine, medical waste handling, prefab wire-up in `MapJsonImporter`, WebGL prototype, Academic ALP Report & release.
- **JC (Props, Rigging & Lighting)**: **[plan_jc.md](./plan_jc.md)** — Trash & Medical B3 library, 20 scavenging tools, vessels, `SK_ExcavatorAmfibi` IK + dual `Damped Track` pistons, `KaliLightingBuilder` rigs.
- **Wesley (Environment & Shaders)**: **[plan_wesley.md](./plan_wesley.md)** — Beginner-proof Unity/Blender setup, 10 `SM_Env_*` architectural meshes (`130m × 180m`), `SG_KaliWater` (`_WaterClarity`), `SG_TrashTriplanar`.
- **Niki (VFX, UI & Audio)**: **[plan_niki.md](./plan_niki.md)** — Monsoon & splash VFX, `Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`, SFX triggers, Sidang rehearsal.

*Asset Master Tracking Matrix*: [docs/KALI_Asset_Master_Tracker.xlsx](./docs/KALI_Asset_Master_Tracker.xlsx) / [docs/KALI_Asset_Master_Tracker.tsv](./docs/KALI_Asset_Master_Tracker.tsv)

---

## 3. Quick Start & Browser / Unity Preview

```bash
# 1. Clone repository & pull latest specs
git clone https://github.com/Gee123a/kali-river-sweeper.git
cd kali-river-sweeper

# 2. Instant browser playtest (Zero Unity install required)
open -a Safari tools/play-3d.html
open -a Safari tools/map-editor.html

# 3. Unity 2022.3.46f1 LTS Workflow
# - Open ./unity in Unity Hub (2022.3.46f1)
# - Menu bar: KALI -> Load Default Purpose-Built Map
# - Press Play; press F9 then keys 1 / 2 / 3 / 4 for live stage showcase
```
