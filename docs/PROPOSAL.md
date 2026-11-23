# KALI: Indonesian River Sweeper (*Pembersih Sungai Nusantara*)
**A Sisyphean River Cleanup & Industrial Automation Simulator**  
*Curriculum Mapping: IMT01303501 Computer Graphics A (Modules 3 & 4) • Targeting Grade A (85–100%)*

![KALI: Indonesian River Sweeper Concept Architecture](/Users/mynamegee/.gemini/antigravity-cli/brain/1493f298-fcf1-4dd5-b19d-26b52db61e03/kali_river_sweeper_concept.png)

---

## 1. Executive Summary & Why This Guarantees an A+

This proposal takes the viral, absurdly addictive progression loop of ***Moon Sweepers*** and ***Find The Needle*** and grounds it directly in an urgent, deeply relatable Indonesian cultural reality: **cleaning up Indonesia's heavily choked urban rivers (Citarum, Ciliwung, and Kalimas Surabaya)**.

### The Rubric Scorecard (Universitas Ciputra RPS)
* **P3.1 Understanding of Graphics Process (30% Weight)**:
  - Custom Shader Graph **Dynamic River Water Shader**: Computes directional flow UV vectors ($v = (v_x, v_z) \cdot t$), depth-based light absorption (Beer-Lambert law), and a real-time **Water Cleansing Lerp** that dynamically shifts river color from thick, opaque brown sludge $\rightarrow$ translucent green $\rightarrow$ crystal blue based on a runtime Trash Density RenderTexture.
  - Multi-point raycast buoyancy simulation math calculating surface normals and wave height to realistically float and drift garbage carpets.
* **KK1.2 Complexity and Quality Exceeding Minimum (30% Weight)**:
  - Custom Blender 3D models of authentic Indonesian riverbank architecture: stilt houses (*rumah panggung bantaran*), corrugated zinc roofs (*atap seng*), wooden *sampan* canoes, warung kelontong, and heavy industrial machinery like the amphibious pontoon excavator (*ekskavator amfibi*).
  - Rich PBR materials: wet plastic specular reflections, rotting organic algae normals, rust-pitted corrugated metals.
* **KU4.2 Story & UN SDG Alignment (30% Weight)**:
  - Inspired by modern Indonesian grassroots movements (**Pandawara Group**, **Sungai Watch**, and the municipal **Pasukan Oranye**).
  - Direct measurable impact on **SDG 6 (Clean Water and Sanitation)**, **SDG 14 (Life Below Water / Marine Plastic Prevention)**, and **SDG 11 (Sustainable Cities / Flood Mitigation)**.
* **KU2.2 Presentation in English (10% Weight)**:
  - Culturally authentic, emotionally resonant, and mathematically rigorous.

---

## 2. Core Game Loop: The 4-Stage "Absurdity to Industry" Progression

The core emotional hook mirrors *Moon Sweepers*: **You start with a comically inadequate tool against an overwhelmingly vast, filthy river, and gradually build an automated industrial cleanup empire.**

```
Stage 1: Tanggul & Serokan (Manual Bank Scooping)
  │  [Broken Fishnet, Leaky Styrofoam Raft, Sandal Swallow, Mie Cups]
  ▼
Stage 2: Perahu Sampan & Galah Bambu (Mid-River Navigation)
  │  [Wooden Sampan, Long Hook Pole, Hand Winch, Floating Mattresses]
  ▼
Stage 3: Pontoon Trash Boom (Semi-Automated River Trapping)
  │  [Floating River Booms, Waterwheel Paddle Belt, Sorting Chutes]
  ▼
Stage 4: Industrial Solar Interceptor (Autonomous River Cleansing)
  │  [Pindad Amphibious Backhoe, Solar Catamaran, Automated Shredders]
  ▼
ENDGAME: Pristine River Ecosystem Restored (Fish & River Otters Return!)
```

### Stage 1: Tanggul & Serokan (Manual Bank Dragging)
* **Starting Tool**: A cracked plastic fishnet (*serokan ikan bolong*) and a sharpened bamboo skewer (*tusukan bambu*).
* **Starting Vessel**: A single slab of tied-together white styrofoam blocks (*rakit gabus*) that slowly leaks water.
* **Targets**: Low-tier municipal floatables: *sandal swallow* (rubber flip-flops), empty *Pop Mie* cups, plastic grocery bags (*kresek*), plastic straw bundles, and *Teh Gelas* cups.
* **Gameplay**: Stand on the muddy embankment or balance on the styrofoam raft. Drag the net through thick sludge. Drop collected trash into a cracked paint bucket.
* **Economy**: Carry filled buckets to the local roadside scrap collector (*pengepul rongsokan / bank sampah*) to earn Rupiah (IDR).

### Stage 2: Perahu Sampan & Galah Bambu (Mid-River Reach)
* **Upgraded Gear**: A 4-meter bamboo pole equipped with a forged iron claw hook (*galah kait*), heavy rubber wading boots (*sepatu boots oranye*), and a hand-cranked line winch.
* **Vessel**: A classic Indonesian wooden *sampan* canoe propelled by a single wooden oar.
* **Targets**: Medium-density obstacles: soggy kapok mattresses (*kasur kapuk*), discarded bicycle tires, rotting banana tree trunks (*gedebog pisang*), and water hyacinth weed mats (*eceng gondok*).
* **Gameplay**: Navigate tricky mid-river current vectors. Anchor the sampan near bridge pillars where swirling eddy currents trap massive trash islands. Winch heavy soaked mattresses out of the river before they sink and clog the sluice gates.

### Stage 3: Pontoon Trash Boom (Semi-Automated Trapping)
* **Upgraded Gear**: Floating barrier booms made of linked HDPE barrels chained diagonally across the river channel to divert floating debris into collection funnels.
* **Vessel / Platform**: Anchored twin-pontoon sorting platform.
* **Mechanism**: A waterwheel-driven continuous paddle-lift conveyor belt (*sabuk konveyor bertenaga arus air*) that scoops floating trash up from the water surface and dumps it onto an inclined vibratory sorting table.
* **Gameplay**: The player transitions from manual scooper to logistics manager: clearing conveyor jams, sorting plastics into color-coded recycling bins (PET, HDPE, organics), and operating baling presses to compress plastic bottles into high-value export cubes.

### Stage 4: Industrial Solar Interceptor & Amphibious Excavator (Autonomous Scale)
* **The Mega-Machines**:
  1. **Solar-Powered River Interceptor Catamaran**: Autonomous barge with conveyor intake mouth and automated dumpster shuttle bays (inspired by *The Ocean Cleanup Interceptor 001* operating in Jakarta / Cengkareng Drain).
  2. **Amphibious Pontoon Excavator**: Heavy tracked diesel backhoe floating on welded steel pontoons, equipped with a wide clamshell rake to dredge cubic meters of compacted anaerobic riverbed sludge.
* **Endgame Transformation**: The river reaches 100% cleanliness. The murky black/brown water clears up to a translucent shimmering turquoise. Native river fish (Ikan Mujair, Gabus, Tawes) spawn back into the clean waters, and local children jump off the bridge into a clean swimming river.

---

## 3. Computer Graphics Module 3: 3D Modeling, PBR & Lighting

### A. 3D Asset Modeling (Blender Pipeline)
* **Architecture & Environment**:
  - Modular riverbank embankments (cracked concrete retaining walls, stone rip-rap, bamboo stilt footpaths).
  - Dense informal settlement details (*kampung bantaran kali*): corrugated rusted zinc roofs, wooden warung kelontong with hanging snack sachets, banana trees, and weeping willows.
  - Sluice gates (*pintu air sungai*) with warning level gauges (Siaga 1, 2, 3, 4).
* **The Authentic Indonesian Trash Asset Library**:
  - Highly detailed low-poly meshes with LOD (LOD0, LOD1, LOD2):
    1. Discarded *Sandal Swallow* (classic blue/white rubber flip-flops).
    2. Crushed *Aqua* 600ml and 19-liter plastic jugs (*galon*).
    3. Crumpled *Indomie* and *Pop Mie* instant noodle packaging.
    4. Soggy, unraveling *kasur kapuk* (quilted kapok mattress with bursting cotton fibers).
    5. Tangled plastic bags (*kresek hitam & merah*) with translucent plastic folds.
    6. Floating water hyacinth plants (*eceng gondok*) with bulbous spongy stems and purple flowers.
* **Vehicles & Machinery**:
  - Leaky styrofoam raft $\rightarrow$ Wooden painted *sampan* $\rightarrow$ Pontoon sorting platform $\rightarrow$ Amphibious backhoe excavator.

### B. PBR Textures & Custom Shader Graph Shaders
* **1. Dynamic River Water & Cleansing Shader**:
  - **Directional Flow UV Panning**: Computes river current movement using flow vectors:
    $$\vec{UV}_{\text{flow}} = \vec{UV} + \vec{V}_{\text{flow}} \cdot t$$
    Blends two normal maps at fractional phases to eliminate looping seam artifacts.
  - **Dynamic Water Quality Lerp**:
    The water shader samples a runtime **Trash Density Mask** (a low-res RenderTexture updated as players collect garbage):
    - *High Pollution (Trash $> 70\%$)*: Opaque, turbid black/brown color ($\text{Hex } \#2c2317$), high subsurface absorption, greasy scum sheen.
    - *Moderate Pollution (Trash $30\% - 70\%$)*: Murky olive green with suspended silt particles.
    - *Pristine Clean (Trash $< 10\%$)*: Translucent emerald cyan ($\text{Hex } \#06b6d4$) with caustic light patterns dancing across sandy riverbed pebbles.
  - **Foam Edge Detection**: Screen-space depth difference generates thick white scum and foam edges around trash clusters and concrete bridge pilings.
* **2. Wetness & Slime Material Shader**:
  - Trash items floating in water dynamically blend between dry PBR textures (rough, faded) and submerged PBR textures (maximum smoothness $1.0$, darkened albedo, and glistening normal map highlights).
* **3. Subsurface Scattering (SSS) Shader**:
  - Used on floating water hyacinth leaves (*eceng gondok*) and surrounding tropical banana foliage along the riverbank.

### C. Lighting Architecture
* **Tropical Golden Hour**: Low-angle warm directional sunlight ($3200\text{K}$) casting elongated shadows of stilt houses across the shimmering river surface.
* **Torrential Monsoon Downpour Mode**: Dark overcast ambient lighting, high atmospheric fog, real-time lightning flash triggers with instant shadow updates, and sodium-vapor yellow streetlights reflecting over wet concrete.

---

## 4. Computer Graphics Module 4: Animation, VFX & Simulation

### A. Rigging & Inverse Kinematics (IK)
* **Amphibious Excavator Arm Rig**:
  - 3-joint hydraulic arm hierarchy (Boom $\rightarrow$ Arm $\rightarrow$ Bucket Rake).
  - Programmed with a **Two-Bone / FABRIK Inverse Kinematics (IK) Solver** allowing the player to control the excavator scoop via mouse target coordinates.
  - Animated hydraulic piston shafts that smoothly extend and retract based on joint angles.
* **Character Cleanup State Machine**:
  - Mecanim Animator controller with multi-directional blend trees:
    - *Idle* on rocking raft $\leftrightarrow$ *Balancing* $\leftrightarrow$ *Scooping* net down $\leftrightarrow$ *Lifting* heavy trash $\leftrightarrow$ *Dumping* into bucket.

### B. Dynamic River Physics & Buoyancy Simulation
* **Multi-Point Raycast Buoyancy**:
  - Each floating trash object (or raft/sampan) calculates 4 raycast points to sample the procedural river wave height:
    $$y_{\text{wave}} = \sum A_i \cdot \sin(\vec{k}_i \cdot \vec{x} - \omega_i t)$$
  - Calculates upward buoyant force ($F_b = \rho V g$) and dampening drag to naturally pitch, roll, and bob with passing boat wakes.
* **River Flow Vector Splines**:
  - Trash items automatically drift downriver along Bezier spline paths, swirling realistically into whirlpool eddies behind bridge pillars.

### C. Particle VFX (VFX Graph)
* **Muddy Splash VFX**: Brown turbid water droplets and splashing foam whenever heavy trash is hauled from the water.
* **Methane Gas Bubble Emitters**: Anaerobic swamp gas bubbles rising from deep riverbed sludge, popping at the water surface with tiny murky splatter particles.
* **Swarming Insect Boids**: Flocks of buzzing river gnats and flies orbiting smelly organic waste piles.
* **Tropical Monsoon Rain System**: High-density vertical raindrop streaks colliding with the river surface mesh to spawn circular expansion ripple rings.

---

## 5. Team Division of Labor (3-Person Work Breakdown)

| Team Member | Core Role | Specific Responsibilities |
| :--- | :--- | :--- |
| **Stevanus Ivan Santoso** | **Lead Graphics & Technical Director** | Dynamic River Water Shader (Shader Graph), Water Cleansing Lerp, Buoyancy & Current Spline Physics, Post-Processing & Lighting Architecture. |
| **Wesley Goeinawan** | **3D Asset & Environment Artist** | Custom Blender 3D modeling (Rumah bantaran, wooden sampan, authentic Indonesian trash props), UV unwrapping, and PBR multi-texturing. |
| **Nicholas Gerwin Mawardji** | **Mechanics & Animation Engineer** | Excavator Arm Rigging & Inverse Kinematics (IK), Character Mecanim blend trees, conveyor belt sorting logic, and Bank Sampah economy loop. |

---

## 6. Academic Defense & Presentation Strategy (Why This Gets an A+)

When presenting in English to **Citra Lestari, S.Kom., M.Kom.** and **Rudi Limantara**:
1. **The Theoretical Proof**: Show the mathematical formulation of the **Beer-Lambert Light Absorption Law** and **Directional Flow UV Vector Mathematics** inside the custom water shader.
2. **The Cultural & Social Proof**: Explain how the game gamifies real-world Indonesian environmental volunteerism (Pandawara Group, Pasukan Oranye) to solve urban flooding and marine plastic emissions (**SDGs 6, 14, 11**).
3. **The Gameplay Proof**: Demonstrate the live progression—starting with a cracked fishnet on a leaky styrofoam block, scooping *sandal swallow*, and escalating into a twin-pontoon conveyor factory and an amphibious excavator dredging 100-ton trash islands.
