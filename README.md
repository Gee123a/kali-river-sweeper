# KALI: Indonesian River Sweeper (*Pembersih Sungai Nusantara*)
**A Sisyphean River Cleanup & Industrial Automation Simulator**  
*Course: IMT01303501 Computer Graphics A (Universitas Ciputra Surabaya) • Grade A Mastery Proposal*

---

## 📌 Project Overview
**KALI** applies the viral "absurd micro-manual to macro-industrial automation" progression recipe of ***Moon Sweepers*** and ***Find The Needle*** to Indonesian river revitalization (Citarum, Ciliwung, and Kalimas Surabaya).

* **The Starting Tool**: A broken plastic fishnet (*serokan ikan bolong*) and bamboo skewer on a leaky styrofoam block raft (*rakit gabus*).
* **The Granular Grind**: Sifting through authentic Indonesian trash (Sandal Swallow, Pop Mie cups, kresek, soggy kapok mattresses).
* **The Final Frontier**: **Gunung Sampah Pintu Air**—a 3-story monumental trash dam wedged against the downriver floodgate, threatening to burst and cause municipal monsoon flooding (*Siaga 1*).
* **The Endgame**: Operating heavy Pindad amphibious backhoe excavators and autonomous solar interceptors to dismantle the mountain, open the sluice gates, and restore the river to crystal-clear water.

---

## 📂 Project Directory Structure

```
kali-river-sweeper/
├── README.md                           # This document
├── docs/                               # Formal specifications & graphics
│   ├── PRD.md                          # Full Product Requirements Document
│   ├── PROPOSAL.md                     # Academic Computer Graphics proposal
│   ├── kali_game_flow_and_architecture.png # Game flow & river topology map
│   └── kali_river_sweeper_concept.png      # Progression & shader architecture
├── assets/                             # 3D models & PBR materials
│   ├── models/                         # Blender .blend & .fbx meshes
│   ├── textures/                       # PBR albedo, normal, roughness maps
│   └── references/                     # Real-world Indonesian river references
├── src/                                # Unity source files
│   ├── Shaders/                        # Shader Graph & HLSL water/mountain shaders
│   └── Scripts/                        # Buoyancy, IK & game economy controllers
└── tools/                              # Asset processing & math verification tools
```

---

## 👥 Team & Responsibilities
* **Stevanus Ivan Santoso (0706012410029)** — **Game Logic & Core Lead**: FP Walk/Boat controller, buoyancy & current splines, scoop/dredge mechanics, 3-Choice state machine, Bank Sampah economy, Flood Gauge (`Siaga 4 -> 1`), Map JSON loader, and Git integration.
* **Jason Christopher (JC)** — **Props, 3D, Rigging & Lighting Lead**: Custom Blender Indonesian trash props (*Sandal Swallow*, *Aqua*, *Pop Mie*, *Kresek*, *Kasur Kapuk*, *Eceng Gondok*, *Pohon Pisang*, Kampung Bins), `SK_ExcavatorAmfibi` 3-joint IK rig, Golden Hour & Monsoon lighting, Warung lanterns, and Post-Processing.
* **Wesley Goeinawan (0706012410011)** — **3D Environment & Water Lead**: Custom Blender architecture (*Rumah Panggung*, *Warung*, *Bank Sampah*, *Toko Alat*, *Pos Sortir*, *Jembatan Utama*, *Pintu Air*, 3-tier *Gunung Sampah*), curved river valley mesh, PBR UVs, and `SG_KaliWater` Shader Graph.
* **Nicholas Gerwin Mawardji (Niki) (0706012410015)** — **VFX, UI & Audio/Narrative Lead**: Rain/splash/methane VFX, trash avalanche particles, HUD Canvas, Bank Sampah Upgrade Shop, NPC dialogue, SFX, and End-Run SDG Impact Screen.

---

## 🔗 Key Documentation Links
* [ALP Grade-A Production Masterplan](file:///Users/mynamegee/kali-river-sweeper/docs/ALP_MASTERPLAN.md)
* [ALP Rubric Production Blueprint](file:///Users/mynamegee/kali-river-sweeper/docs/alp_rubric_production_blueprint.png)
* [Product Requirements Document (PRD)](file:///Users/mynamegee/kali-river-sweeper/docs/PRD.md)
* [Academic Proposal](file:///Users/mynamegee/kali-river-sweeper/docs/PROPOSAL.md)
* [Game Flow Diagram](file:///Users/mynamegee/kali-river-sweeper/docs/kali_game_flow_and_architecture.png)
* [Concept Architecture Diagram](file:///Users/mynamegee/kali-river-sweeper/docs/kali_river_sweeper_concept.png)
