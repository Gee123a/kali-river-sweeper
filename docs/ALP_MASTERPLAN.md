# KALI: Indonesian River Sweeper — ALP Grade-A (85–100) Production Masterplan
**Audited Against Official Rubric: `20261-CG-Penilaian ALP.pdf` (Game Track)**  
*Engine: Unity `2022.3.46f1` LTS (URP) + Blender `5.3.0`*  
*Team: Stevanus Ivan Santoso (Ivan), Jason Christopher (JC), Wesley Goeinawan (Wesley), Nicholas Gerwin Mawardji (Niki)*

![ALP Grade-A Production Blueprint](file:///Users/mynamegee/kali-river-sweeper/docs/alp_rubric_production_blueprint.png)

---

## 1. Official Game ALP Rubric Checklist (Target: 95–100 / 100)

Every row of the **GAME** table in `20261-CG-Penilaian ALP.pdf` mapped to concrete deliverables:

| Rubric Criterion | Weight | 85–100 Requirement | KALI Implementation & Proof |
| :--- | :---: | :--- | :--- |
| **Understanding of the Process** | **30%** | Correct answer in detail and able to demonstrate/show live evidence | Keep all raw `.blend` files, UV layouts, rigs, Shader Graphs, and C# scripts in Git. Each member opens and explains their own files live during Sidang Q&A. |
| **Complexity: 3D Geometry & Materials** | **30%** *(part)* | Complex, well-crafted models with high-quality materials, textures, and consistent visual style | 100% custom stylized PBR assets modeled in Blender 5.3.0 (zero raw primitives or store asset flips), clean UVs, Albedo/Normal/Roughness maps, consistent Indonesian riverbank look. |
| **Complexity: Game Mechanics** | **30%** *(part)* | Three or more interacting mechanics | **5 interacting mechanics**: (1) River current splines & multi-point buoyancy, (2) Scoop/dredge & boat weight limit, (3) Sort/Bale/Bank Sampah economy, (4) Monsoon Flood Gauge (`Siaga 4 -> 1`), (5) Villager litter spawner vs. prevention bins. |
| **Complexity: Gameplay Design & Feedback** | **30%** *(part)* | Engaging gameplay with challenges and meaningful player choices; responsive controls with clear feedback | Clear Spawn-to-Gunung-Sampah horizon sightline, **3 trade-off choices**, boat tilt/water splashes, web-style audio SFX, hit-stop/particles on scoop & dredge. |
| **Story & SDG Matchness** | **30%** *(20+10)* | Original story idea; story & gameplay seamlessly integrated with player actions meaningfully influencing narrative; strong SDG target & consequences of decisions | Targets **SDG 6.3 (Water Quality)**, **SDG 14.1 (Marine Plastic)**, **SDG 11.5 (Flood Mitigation)**. Root cause (upstream littering) -> Impact (clogged Pintu Air / flood risk) -> Solutions (Bank Sampah, Kampung Bins, Trash Boom, Excavator) -> **3 Endings** + **End-Run Impact Report**. |
| **Quality of Presentation** | **10%** | Highly engaging, seamlessly executed, well-planned sequence | Built-in **`F9` Presentation Stage Jump** hotkeys (`1`–`4`) to demo Act 1, Act 2 Choices, Monsoon `Siaga 1` Climax, and Clean River Victory smoothly in 3 minutes. |

---

## 2. The 3 Meaningful Player Choices & Consequences

1. **Choice A — Quick Burn Pit vs. Bank Sampah Sorting**:
   - *Burn Pit (Fast Cash)*: Dump unsorted trash for instant Rupiah → dark smog rises over Kampung Hulu, *Pak RT* warns about toxic smoke, villagers keep littering.
   - *Bank Sampah / Pos Sortir (SDG Path)*: Sort PET/Metal/Organic → unlocks **$3\times$ baled PET value**, clears air, builds Community Trust.
2. **Choice B — Bigger Boat Upgrades vs. Upstream Root-Cause Prevention**:
   - *Symptom Only*: Upgrading only personal net/sampan feels Sisyphean because upstream stilt houses keep throwing *kresek* into the river.
   - *Root-Cause Fix*: Buying **Kampung Trash Bins** + **Floating Trash Boom** reduces villager river littering by **60%** and auto-funnels remaining debris to Pos Sortir.
3. **Choice C — Monsoon `Siaga 1` Floodgate Climax**:
   - *Emergency Flush (Panic)*: Open **Pintu Air** early to save Kampung Hulu fast → dumps plastic out to sea (**Compromised Ending: Flood Averted, Ocean Polluted — fails SDG 14.1**).
   - *Hold Gate & Dredge (Hero)*: Keep gate shut in the storm, dredge **Gunung Sampah** with the Excavator → clean breach, river turns turquoise, fish return (**True SDG Victory**).
   - *Ignore Warning*: Water overtops embankment and floods Kampung Hulu (**Flood Fail State** with instant retry).

---

## 3. Confirmed 4-Person Role Split & Unity Folder Ownership

To eliminate Git merge conflicts and ensure every member owns verifiable evidence for the **30% Process** grade, each person owns dedicated folders inside `Assets/_Project/`:

| Member | Role | Unity Folder Ownership | Exact Responsibilities | Live Sidang Q&A Proof |
| :--- | :--- | :--- | :--- | :--- |
| **Stevanus Ivan Santoso (Ivan)** | **Game Logic & Core Lead** | `Assets/_Project/Scripts/` | FP Walk/Boat controller, multi-point buoyancy & current splines, Scoop/Dredge logic, 3-Choice State Machine & Bank Sampah economy, Flood Gauge (`Siaga 4 -> 1`), `F9` Demo Stage Jump, `kali-river-map.json` Level Loader, Git integration | Walks through C# state machine, buoyancy math, and JSON level spawner |
| **Jason Christopher (JC)** | **Props, 3D & Lighting Lead** | `Assets/_Project/Props/`<br>`Assets/_Project/Lighting/` | **Blender Props**: *Sandal Swallow*, *Aqua* bottles/galon, *Pop Mie* cups, *Kresek*, *Kasur Kapuk*, *Eceng Gondok*, *Pohon Pisang*, Kampung Trash Bins, Rakit/Sampan props.<br>**Unity Lighting**: Golden Hour sun & shadows, Monsoon storm sky/fog, glowing Warung lanterns, flashing Pintu Air beacons, Post-Processing | Opens trash `.blend` files + Unity Lighting/Post-FX profile |
| **Wesley Goeinawan (Wesley)** | **3D Environment & Water Lead** | `Assets/_Project/Environment/`<br>`Assets/_Project/Shaders/` | **Blender Environment**: *Rumah Panggung*, *Warung*, *Bank Sampah*, *Toko Alat*, *Pos Sortir*, *Jembatan Utama*, *Pintu Air Siaga 1*, *Dermaga*, 3-tier destructible *Gunung Sampah*, curved river valley mesh, PBR UVs.<br>**Unity Shader**: `SG_KaliWater` (dual-flow normal panning, Beer-Lambert `_WaterClarity` lerp, depth foam) | Opens architecture `.blend` topology/UVs + `SG_KaliWater` Shader Graph |
| **Nicholas Gerwin Mawardji (Niki)** | **Rigging, VFX & UI Lead** | `Assets/_Project/Rigging/`<br>`Assets/_Project/VFX/`<br>`Assets/_Project/UI/` | **Rigging**: `SK_ExcavatorAmfibi` 3-joint IK arm + sliding hydraulic pistons, FP tool swing animations, Villager NPC litter/bin animations.<br>**VFX**: Monsoon rain, muddy water splashes, methane sludge bubbles.<br>**UI & Narrative**: HUD, Upgrade Shop, NPC reaction dialogue, End-Run SDG Impact Screen, SFX | Opens Excavator rig + IK setup, VFX Graph emitters, and UI Canvas/Impact Screen |

---

## 4. Blender `5.3.0` → Unity `2022.3.46f1` Standards

* **Scale & Transforms**: `1 Blender Unit = 1 Meter` (`Z` up exported cleanly to Unity `Y` up; always run `Ctrl + A` → **Apply Rotation & Scale** before `.fbx` export!).
* **Naming**: `SM_` (Static Mesh), `SK_` (Skeletal Rigged Mesh), `M_` (Material), `T_` (Texture `_Albedo`, `_Normal`, `_Roughness`), `SG_` (Shader Graph).
* **Poly Budgets**: Trash props `150–400 tris`, Buildings `800–2,500 tris`, `SK_ExcavatorAmfibi` `4,000–6,000 tris` (keeps demo steady at 60+ FPS).

---

## 5. 4-Week Production Sprint & `F9` Demo Hotkeys

* **Week 1 — Greybox & Core Core Loop**: Ivan creates Unity `2022.3.46f1` URP project + auto-spawns `kali-river-map.json` greybox; locks FP Walk/Boat/Scoop/Sell loop. JC & Wesley model hero props and buildings; Niki sets up HUD & Excavator IK prototype.
* **Week 2 — Custom Art Drop & Water Shader**: Wesley & JC import UV-mapped PBR `.fbx` assets; Wesley wires `SG_KaliWater`; JC sets Golden Hour & Monsoon lighting presets.
* **Week 3 — 3 Choices, Monsoon Climax & VFX**: Ivan wires Choices A/B/C + Flood Gauge; Niki adds rain/splash/methane VFX, NPC animations, Upgrade Shop, and Impact Report UI.
* **Week 4 — `F9` Demo Mode & Sidang Rehearsal**:
  - `F9 + 1`: Act 1 Spawn Sightline + Litter Cause
  - `F9 + 2`: Act 2 Choice Trade-Off (Kampung Bins + Trash Boom + Pos Sortir)
  - `F9 + 3`: Act 3 Monsoon `Siaga 1` Climax + Excavator Dredge
  - `F9 + 4`: Clean River Victory + SDG Impact Report Screen
