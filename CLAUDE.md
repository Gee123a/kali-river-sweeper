# CLAUDE.md — KALI: Indonesian River Sweeper

> See [AGENTS.md](./AGENTS.md) for master AI agent rules, strict Unity directory ownership, C# shader/collider contracts, and Grade-A rubric guardrails.
> See [docs/PLAYBOOK.md](./docs/PLAYBOOK.md) for the complete documentation map and product overview.
> See [docs/PRD.md](./docs/PRD.md) for game loop, 20-tool Kopdes milestones & `BuyTool` progression, vessel upgrades, surface swimming/stamina/drowning, 3-class waste hazards (`Normal`, `Medical`, `Biohazard`), 3 stations vs `Gudang Pengepul`, linear water rise / Sell-Lock / `Q` dump, and 5 endings (`TrueSdgVictory`, `PartialSurvival`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`).
> See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for Unity 2022.3 URP + Blender 5.3 system architecture, `+Z` `RiverMath` coordinates, `_WaterClarity` shader hooks, and `SK_ExcavatorAmfibi` rigging specs.
> See [docs/DESIGN.md](./docs/DESIGN.md) for the visual identity system (*Lembar Kalkir Zona Cahaya*), color tokens (`Siaga 4 -> 1`, polluted brown `#3B2818` to clean teal `#1B6B63`), 3 station identities, PBR material standards, and UI typography.
> See [docs/TEAM_WORKFLOW.md](./docs/TEAM_WORKFLOW.md) for integration order, Git branch rules, and ready-to-paste prompts per member.
> See [docs/TECH_STACK.md](./docs/TECH_STACK.md) for Unity `2022.3.46f1` LTS packages, Blender `5.3.0`, core scripts, and polycount budgets.

## Quick Team Ownership
- **Ivan** (Coordinator & Core Lead): C# Gameplay (`RiverGameManager`, `ToolCatalog`, `RiverTrashSpawner`, `RiverTrashItem`, `KaliPlayerController`, `KaliFieldGuideOverlay`), `+Z` Buoyancy, surface swimming/stamina/drowning, `MapJsonImporter`, `kali-river-map.json`, `tools/play-3d.html`, Academic Report — [plan_ivan.md](./plan_ivan.md)
- **JC** (Props, 3D, Rigging & Lighting): Trash, Medical B3 & Biohazard Props, 20 Tools (`PF_Tool_*` with `isTrigger = true` / disabled while equipped), Boats, `SK_ExcavatorAmfibi` IK Rig, `PF_LightingRig` — [plan_jc.md](./plan_jc.md)
- **Wesley** (Environment Architecture & Shaders): `SM_Env_*` FBX Meshes (`130m × 180m`, `+Z` `Pintu Air`, `Pos Medis B3`, `Karantina Biohazard`, `Gudang Pengepul`), `SG_KaliWater` (`_WaterClarity`, `+V` normal scroll), `SG_TrashTriplanar` — [plan_wesley.md](./plan_wesley.md)
- **Niki** (VFX, UI & Audio/Narrative): 4 VFX Particle Systems, HUD Canvas (`playerHealth`, `swimStamina`, 3-class cargo, Biohazard DoT, Sell-Lock & `Q` dump hint, Monsoon timer, Kopdes milestone toast), Shop/Station Prompts, SDG Impact Report Screen (`5` endings), SFX & Sidang Script — [plan_niki.md](./plan_niki.md)

## Core Rule
Every member edits ONLY inside their assigned `unity/Assets/_Project/` folders and isolated `plan_<member>.md` tasks. Never edit shared C# contracts (`RiverGameManager`, `RiverMath`, `MapJsonImporter`) without syncing with **Ivan**. Always run `Ctrl + A -> All Transforms` in Blender before exporting FBX (`-Z Forward`, `Y Up`, scale `1.0`).
