# KALI: Indonesian River Sweeper — AI-Assisted Production Playbook

Official development playbook for **KALI: Indonesian River Sweeper (*Penjaga Terakhir Sungai*)** — **IMT01303501 Computer Graphics Final Project (ALP)** at Universitas Ciputra Surabaya (Game Track, audited against `20261-CG-Penilaian ALP.pdf` for **85–100 / Grade A**).

![ALP Grade-A Production Blueprint](./alp_rubric_production_blueprint.png)

---

## 1. Complete Documentation Suite

| Document | Purpose | Target Audience |
| :--- | :--- | :--- |
| **[README.md](../README.md)** | Repository overview, narrative hook, team roster, quick start, and member plans. | All Contributors |
| **[AGENTS.md](../AGENTS.md) / [CLAUDE.md](../CLAUDE.md)** | Master AI instructions, strict `Assets/_Project/` folder isolation, C# contracts, and rubric guardrails. | AI Agents (Claude Code, Antigravity, Cursor, ChatGPT) |
| **[docs/PRD.md](./PRD.md)** | Product Requirements Document: 20 non-redundant tools, vessel progression, Medical Biohazard Waste, 3 Choices, 3 Endings, and SDG targets. | All Contributors |
| **[docs/ARCHITECTURE.md](./ARCHITECTURE.md)** | Unity URP + Blender system architecture, conflict-free directory layout, `RiverMath` (`130m × 180m`), C# hooks (`_WaterClarity`), and Excavator IK rig spec. | Ivan, JC, Wesley, Niki |
| **[docs/DESIGN.md](./DESIGN.md)** | "Kalimas Nusantara" art direction, pollution-to-clean palette, `Siaga 4 -> 1` alert colors, PBR surface specs, and UI typography. | JC, Wesley, Niki |
| **[docs/TECH_STACK.md](./TECH_STACK.md)** | Software versions (`Unity 2022.3.46f1`, `Blender 5.3.0`, `URP 14.0.11`), packages, and poly/draw-call budgets. | All Contributors |
| **[docs/TEAM_WORKFLOW.md](./TEAM_WORKFLOW.md)** | Sprint tracks, parallel build sequence, branch/folder workflow, and ready-to-paste onboarding prompts per member. | Ivan, JC, Wesley, Niki |

---

## 2. Team Directory & Isolated Scopes

| Member | Role | Student ID | Primary Track & Unity Folders |
| :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso** (`Ivan`) | **Coordinator & Core Lead** | `0706012410029` | Architecture, docs, contracts lock, C# gameplay/buoyancy/economy, `kali-river-map.json`, `MapJsonImporter`, `F9` demo stage jump (`Scripts/`, `Data/`, `tools/`) |
| **Jason Christopher** (`JC`) | **Props, Rigging & Lighting Lead** | — | Trash & Medical B3 props, 20 tool models, vessels, `SK_ExcavatorAmfibi` 3-bone IK arm + hydraulic pistons, `PF_LightingRig`, Golden Hour/Monsoon profiles (`Props/`, `Rigging/`, `Lighting/`) |
| **Wesley Goeinawan** (`Wesley`) | **Environment & Water Shader Lead** | `0706012410011` | 10 custom Blender architectural FBX meshes synced to `RiverMath` `130m × 180m` spline, `SG_KaliWater` (`_WaterClarity`), `SG_TrashTriplanar` (`Environment/`, `Shaders/`) |
| **Nicholas Gerwin Mawardji** (`Niki`) | **VFX, UI & Audio/Narrative Lead** | `0706012410015` | 4 particle emitters (`MonsoonRain`, `WaterSplashMuddy`, `MethaneSludgeBubbles`, `TrashAvalanche`), HUD/Shop/SDG UI Canvases, audio cues, Sidang demo flow (`VFX/`, `UI/`, `Audio/`) |

---

## 3. Official Game ALP Rubric Checklist (Target: 95–100 / 100)

Mapped directly against `20261-CG-Penilaian ALP.pdf` (**GAME** track):

| Rubric Criterion | Weight | 85–100 Benchmark | KALI Deliverable & Sidang Defense Proof |
| :--- | :---: | :--- | :--- |
| **Understanding of the Process** | **30%** | Detailed explanations + live project evidence | Every contributor retains raw `.blend`, UV layouts, Shader Graph nodes, VFX/UI prefabs, and modular C# scripts in Git and explains them live during Q&A. |
| **Complexity: 3D Geometry & Materials** | **30%** *(part)* | Complex, well-crafted custom models + consistent visual style | 52+ custom Blender PBR assets in [KALI_Asset_Master_Tracker.xlsx](./KALI_Asset_Master_Tracker.xlsx): 20 tools, Indonesian kampung buildings, boats, and rigged `SK_ExcavatorAmfibi`. |
| **Complexity: Game Mechanics** | **30%** *(part)* | 3+ interacting mechanics | **5 interacting systems**: (1) `RiverMath` current & sinusoidal buoyancy, (2) 20-tool physical aperture progression & Medical Biohazard hazard (`SecureMedicalWaste`), (3) Bank Sampah sorting economy, (4) Monsoon Flood Gauge (`Siaga 4 -> 1`), (5) Upstream Kampung Bins + Floating Trash Boom automation. |
| **Complexity: Design & Feedback** | **30%** *(part)* | Meaningful choices + responsive feedback | 3 systemic trade-off choices, dynamic water clarity lerp (`_WaterClarity`), lighting shift, storm rain/splashes, beacons, audio cues, and HUD feedback. |
| **Story & SDG Matchness** | **30%** *(20+10)* | Original narrative seamlessly tied to gameplay + concrete SDG targets | Rooted in Indonesian riverkeepers (*Pandawara / Pasukan Oranye*). Deep cause-effect-solution arc targeting **SDG 6.3**, **SDG 11.5**, and **SDG 14.1** across **3 Endings** + **End-Run SDG Impact Report**. |
| **Quality of Presentation** | **10%** | Engaging, seamless execution with clear sequence | Built-in `F9` Stage Jump hotkeys (`F9 + 1..4`) showcase Act 1 spawn, Act 2 choices, Monsoon `Siaga 1` storm, and Victory cleanly in 3 minutes. |

---

## 4. Core Architectural Pillars

1. **Prefab-First Parallel Pipeline**: All art, shader, VFX, and UI deliverables are packaged inside member-owned prefabs inside `unity/Assets/_Project/<Domain>/`. Nobody needs to fight over a single shared `.unity` scene file during parallel sprints.
2. **Contract-Driven C# Hooks**: `RiverGameManager`, `RiverFlowBuoyancy`, `KaliPlayerController`, and `MapJsonImporter` expose clean integration points (`_WaterClarity`, `OnStateChanged`, `OnWeatherChanged`, `"Bank Sampah"`, `"Pos Sortir"`, `"Gunung Sampah"`) so art assets light up gameplay on drop-in.
3. **Browser-First Prototyping (`tools/`)**: Anyone on the team can explore the spatial layout and 3D flood concept immediately in Safari via `tools/play-3d.html` and `tools/map-editor.html` even without opening Unity.
