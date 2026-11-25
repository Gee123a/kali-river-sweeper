# KALI: Indonesian River Sweeper (`kali-river-sweeper`)

Official repository for **KALI: Indonesian River Sweeper (*Penjaga Terakhir Sungai Nusantara*)** — **IMT01303501 Computer Graphics Final Project (ALP)**, Universitas Ciputra Surabaya (Game Track, targeting Grade A **85–100%**).

> *"Di dunia ini, gunung sampah telah menumpuk sangat tinggi hingga mencekik satu-satunya sungai di desa, dan kamu adalah generasi terakhir penjaga sungai yang tersisa."*

The game transforms real Indonesian river revitalization (*Citarum, Ciliwung, Kalimas Surabaya*) into a 3D first-person & vessel cleanup simulator built in **Unity `2022.3.46f1` LTS (URP)** and **Blender `5.3.0`**:
1. **Start Improvised, End Industrial (20 Auto-Unlocking Tools + Vessel Tiers)**:
   - Begin on a leaky styrofoam raft (*rakit gabus*) with `#01 Sendok Makan Bengkok` and automatically unlock all **20 official JC tools** (`#01 SendokMakanBengkok` .. `#20 GarukSkimmerHidrolik`) as cumulative Rupiah crosses milestones — scaling up to `#10 Capitan Ular` (mitigating Medical B3 prick risk to `0%`), motorized pumps, hydraulic skimmers, and the rigged amphibious excavator (`SK_ExcavatorAmfibi`).
2. **3 Waste Classes, 3 Dedicated Stations + Linear Flood & Sell-Lock (`+Z` Flow)**:
   - Debris sheds from upstream `Gunung Sampah` (`-Z`) and drifts **`+Z` downstream** toward `Pintu Air Siaga 1` (`+Z`). All 3 classes (**`Normal`**, **`Medical`**, **`Biohazard`**) can be scooped with any tool, but `Medical` can prick player HP (mitigated by `#10 Capitan Ular`) and `Biohazard` inflicts Cargo DoT if held too long. Sort cleanly at **`Bank Sampah`**, **`Pos Medis B3`**, and **`Karantina Biohazard`** (`1/2/3/E` keys — wrong station = fine!) or dump cheaply in one go at **`Gudang Pengepul`** (near Spawn) with Trust penalties.
   - River height rises linearly with `TotalTrashInRiver` (`waterLevelY = -0.25 + 0.020 * trash`): overflowing banks (`1.40m`), triggering **Sell-Lock** (`1.85m`, solvable via **`Q`** high-ground cargo dump or Emergency Flush), and drowning (`2.45m` -> `FloodFail`) or `0 HP` (`HealthFail`). Win by clearing `Gunung Sampah` to `0%` OR surviving the 5-minute Monsoon Countdown (`TrueSdgVictory`).
3. **Real-Time Graphics & Simulation**:
   - C#-driven `SG_KaliWater` turbidity/clarity transition (`_WaterClarity`: `0.05` muddy brown $\rightarrow$ `1.00` clean emerald teal) with `+V` downstream normal scrolling, Beer-Lambert depth absorption, world-space triplanar carving on `Gunung Sampah`, 3-bone IK excavator arm with dual `Damped Track` hydraulic pistons, URP volumetric/storm lighting, and VFX Graph monsoon/splash systems.

---

## 1. Team & Role Ownership

| Member | Role | Student ID | Primary Track & Unity Folders |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso** (`Ivan`) | **Coordinator & Core Lead** | `0706012410029` | Game loop, `+Z` `RiverMath` buoyancy/drift, linear water rise & Sell-Lock, 3-class waste/stations, 20-tool milestones, `F9` Demo, `MapJsonImporter`, `tools/play-3d.html` (`Assets/_Project/Scripts/`, `Data/`, `tools/`) |
| **Jason Christopher** (`JC`) | **Props, 3D, Rigging & Lighting Lead** | — | Indonesian trash props + Medical (`MedicalBag`, `SyringeBox`) & Biohazard props, 20 tool models (`PF_Tool_*` trigger/disabled collider rule), vessels, `SK_ExcavatorAmfibi` 3-bone IK + hydraulic rig, Golden Hour / Monsoon `PF_LightingRig` (`Assets/_Project/Props/`, `Rigging/`, `Lighting/`) |
| **Wesley Goeinawan** (`Wesley`) | **Environment & Shader Lead** | `0706012410011` | `SM_Env_*` riverbank, `+Z` `Pintu Air`, `Pos Medis B3`, `Karantina Biohazard`, `Gudang Pengepul` FBX meshes synced to `130m × 180m` river curve, `SG_KaliWater` (`_WaterClarity`, `+V` flow) & `SG_TrashTriplanar` (`Assets/_Project/Environment/`, `Shaders/`) |
| **Nicholas Gerwin Mawardji** (`Niki`) | **VFX, UI & Audio/Narrative Lead** | `0706012410015` | 4 particle VFX (`MonsoonRain`, `WaterSplashMuddy`, `MethaneSludgeBubbles`, `TrashAvalanche`), HUD Canvas (`playerHealth`, 3-class cargo, DoT/Sell-Lock/`Q` dump/Monsoon timer/auto-unlock toast), Shop/Station prompts, SDG Report (`4` endings), SFX & Sidang deck (`Assets/_Project/VFX/`, `UI/`, `Audio/`) |

---

## 2. Documentation Suite for Agent-Driven Development

Before modeling, shading, wiring prefabs, or prompting an AI coding/3D assistant (Claude Code, Antigravity, Cursor, ChatGPT), read these core documents:

1. **[AGENTS.md](./AGENTS.md) / [CLAUDE.md](./CLAUDE.md)** — Master AI rules, conflict-free Unity directory boundaries, C# shader/collider contracts, and rubric guardrails.
2. **[docs/PLAYBOOK.md](./docs/PLAYBOOK.md)** — High-level production playbook, documentation map, and Grade-A rubric matrix.
3. **[docs/PRD.md](./docs/PRD.md)** — Full Product Requirements Document: story, 20 auto-unlocking tools & vessel progression, 3-class waste hazards (`Normal`, `Medical`, `Biohazard`), 3 stations vs `Gudang Pengepul`, linear flood/Sell-Lock/`Q` dump, 4 Endings, and SDG targets (**6.3**, **11.5**, **14.1**).
4. **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — Unity URP + Blender system design, conflict-free folder tree, `RiverMath` (`130m × 180m`) coordinate math, C# event/shader hooks (`_WaterClarity`), and `SK_ExcavatorAmfibi` IK rigging blueprint.
5. **[docs/DESIGN.md](./docs/DESIGN.md)** — "Kalimas Nusantara" visual identity, PBR surface rules, lighting moods (`Golden Hour` vs `Monsoon`), and UI HUD color tokens.
6. **[docs/TECH_STACK.md](./docs/TECH_STACK.md)** — Software versions (`Unity 2022.3.46f1`, `URP 14.0.11`, `Blender 5.3.0`), installed packages, and polygon/texture budgets.
7. **[docs/TEAM_WORKFLOW.md](./docs/TEAM_WORKFLOW.md)** — Parallel sprint sequence, integration order, Git conventions, and ready-to-paste onboarding AI prompts for each teammate.

### Dedicated Member AI Plans (Isolated Scope, Zero Token Waste)
Each teammate has an isolated implementation checklist built for direct AI execution:
- **Ivan (Core Code)**: **[plan_ivan.md](./plan_ivan.md)** — C# state machine, medical waste handling, prefab wire-up in `MapJsonImporter`, WebGL prototype, Academic ALP Report & release.
- **JC (Props, Rigging & Lighting)**: **[plan_jc.md](./plan_jc.md)** — Trash, Medical B3 & Biohazard library, 20 scavenging tools (`PF_Tool_*` trigger/disabled collider rule), vessels, `SK_ExcavatorAmfibi` IK + dual `Damped Track` pistons, `KaliLightingBuilder` rigs.
- **Wesley (Environment & Shaders)**: **[plan_wesley.md](./plan_wesley.md)** — Beginner-proof Unity/Blender setup, 13 `SM_Env_*` terrain & architectural meshes (`130m × 180m`), `SG_KaliWater` (`_WaterClarity`, `+V` flow), `SG_TrashTriplanar`.
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
