# Product Requirements Document (PRD) & Game Flow Architecture
# KALI: Indonesian River Sweeper (*Pembersih Sungai Nusantara*)
**A Sisyphean River Cleanup & Industrial Automation Simulator**  
*Curriculum Mapping: IMT01303501 Computer Graphics A (Modules 3 & 4) • Targeting Grade A (85–100%)*

![KALI: Game Flow & River Topology Architecture](/Users/mynamegee/.gemini/antigravity-cli/brain/1493f298-fcf1-4dd5-b19d-26b52db61e03/kali_game_flow_and_architecture.png)

---

## 1. Document Control & Product Vision

| Field | Detail |
| :--- | :--- |
| **Project Title** | **KALI: Indonesian River Sweeper** (*Pembersih Sungai Nusantara*) |
| **Target Course** | IMT01303501 Computer Graphics A, Universitas Ciputra Surabaya |
| **Target Grade** | **Grade A (85–100%)** — P3.1 (30%), KK1.2 (30%), KU4.2 (30%), KU2.2 (10%) |
| **Engine / Pipeline** | Unity 6 / Universal Render Pipeline (URP) |
| **Target Platform** | PC (Steam / Windows & macOS), Mouse & Keyboard |
| **Team Authors** | Stevanus Ivan Santoso (Lead Graphics), Wesley Goeinawan (3D Art), Nicholas Gerwin Mawardji (Mechanics) |

### 1.1 The High Concept
Inspired by the viral progression loop of ***Moon Sweepers*** (cleaning the moon with a toothbrush) and ***Find The Needle*** (digging a mountain of hay with a trowel), **KALI** places players in the boots of an Indonesian river volunteer (*Pasukan Oranye / Pandawara style*). 

You start with a comically inadequate tool—a **broken plastic fishnet (*serokan ikan bolong*)** balancing on a **leaky styrofoam block raft (*rakit gabus*)**—facing an impossibly clogged urban river. Far downriver stands the colossal final obstacle: **The Great Trash Mountain (*Gunung Sampah Pintu Air*)**, an ancient 3-story dam of compacted plastics and urban runoff threatening to burst the municipal sluice gates during monsoon season. Through manual grit, sorting, economic scaling, deployable floating booms, and heavy industrial amphibious machinery, players dismantle the mountain and restore the river to a pristine, crystal-clear sanctuary.

---

## 2. The Core Mechanic: "The Great Trash Mountain" (*Gunung Sampah Pintu Air*)

The downriver terminus of the map features a monumental environmental barrier: **Gunung Sampah Pintu Air**, an enormous dam formed where decades of uncollected municipal trash have wedged against the primary floodgate (*Pintu Air Bendungan*).

```
                     [ GUNUNG SAMPAH ANATOMY ]
   ▲
3m │  [TOP LAYER] Fresh Floaters: Sandal Swallow, Pop Mie, Kresek, Aqua Bottles
   │  ─────────────────────────────────────────────────────────────────────────
2m │  [MID LAYER] Tangled Entanglement: Mattresses, Ropes, Bicycle Tires, Branches
   │  ─────────────────────────────────────────────────────────────────────────
1m │  [DEEP BED]  Anaerobic Sludge: Compacted Black Silt, Decomposed Organics, Scrap Iron
   ▼
══════════════════════ [ CONCRETE SLUICE GATES ] ═══════════════════════════════
```

### 2.1 Physical Layer Structure
1. **Top Layer (Surface Floaters - 0 to 1m depth)**:
   - Freshly accumulated buoyant debris: discarded *Sandal Swallow*, plastic beverage cups, instant noodle packaging, single-use bags (*kresek*).
   - Easily collected with hand nets and bamboo claw poles.
2. **Middle Layer (Tangled Structural Dam - 1m to 2.5m depth)**:
   - Intertwined, high-drag obstacles: waterlogged kapok mattresses (*kasur kapuk*), nylon fishing ropes, discarded motor tires, and dense water hyacinth root mats (*eceng gondok*).
   - Requires winch hooks, floating boom funnels, and motorized cutters to untangle.
3. **Bedrock Layer (Anaerobic Sludge & Compacted Trash - 2.5m to 4m depth)**:
   - Heavy, compacted black sludge, rusted scrap iron, and anaerobic mud emitting methane gas bubbles.
   - Completely blocks the sluice gate drainage culverts. Can only be dredged using the **Amphibious Backhoe Excavator** and **Solar Catamaran Interceptor**.

### 2.2 Dynamic Environmental Threat: Sluice Gate Pressure & Flood Timer
* **The Sluice Gauge (*Indikator Siaga Pintu Air*)**:
  - The floodgate displays a real-time water level marker: **Siaga 4 (Normal, Green)** $\rightarrow$ **Siaga 3 (Alert, Yellow)** $\rightarrow$ **Siaga 2 (Danger, Orange)** $\rightarrow$ **Siaga 1 (Critical Emergency, Red)**.
* **Monsoon Rain Influx**:
  - Periodic tropical downpours dramatically increase river flow velocity ($0.5\text{ m/s} \rightarrow 2.5\text{ m/s}$) and push additional floating debris downriver against the Trash Mountain.
  - As debris accumulates, the dam height rises, choking the sluice gates and causing upstream water levels to rise.
* **Failure Condition (The Spillover)**:
  - If the water level hits **Siaga 1 Critical**, water overflows the concrete embankments and floods the upstream stilt kampung (*Kampung Hulu*), destroying player sorting bins and incurring severe municipal penalty fines!
* **Victory Condition (The Great Dam Breach)**:
  - When the player dredges out the final structural core of the Trash Mountain using the amphibious excavator, the dam collapses in a dynamic physics avalanche.
  - The sluice gates open, trapped stagnant water flushes out, and the entire river turns from murky black sludge into sparkling, clear emerald blue!

---

## 3. Game Flow & Level Topology

The game world is laid out as a continuous 1.5-kilometer urban river corridor divided into 3 distinct operational zones:

```
[ ZONE 1: KAMPUNG HULU ]       [ ZONE 2: JEMBATAN KOTA ]      [ ZONE 3: BENDUNGAN SIAGA 1 ]
   (Shallow Banks)                (Mid-River Eddies)             (The Trash Mountain)
         │                               │                                │
  • Leaky Raft & Net              • Wooden Sampan & Winch         • Amphibious Excavator
  • Sandal & Cups                 • Mattresses & Tires            • 100-Ton Plastic Dam
  • Bank Sampah Berkah            • Floating Boom Traps           • Sluice Gate Breach
         │                               │                                │
         └───────────── River Current Vector (0.5 to 2.5 m/s) ────────────┘
```

### 3.1 Zone 1: Kampung Hulu (Upstream Shallows & Starting Hub)
* **Visual Atmosphere**: Dense riverside informal settlement (*kampung bantaran kali*). Bamboo stilt houses, laundry lines, weeping willows, banana palms, wooden docks.
* **Flow Velocity**: Gentle current ($0.5\text{ m/s}$), shallow muddy riverbanks ($0.5\text{m} - 1.2\text{m}$ depth).
* **Base Hub ("Bank Sampah Berkah")**:
  - Located on a wooden dock by the embankment.
  - Equipped with a hanging mechanical hook scale (*timbangan gantung*), color-coded scrap bins, and a vendor NPC (*Pak RT / Pengepul*).
* **Player Phase**:
  - Learning manual collection controls using the broken fishnet and bamboo skewer.
  - Dragging shallow banks, carrying buckets up to Bank Sampah, and earning initial seed capital (50,000 IDR) to purchase the wooden *sampan*.

### 3.2 Zone 2: Jembatan Kota & Arus Tengah (Mid-River Navigation)
* **Visual Atmosphere**: Concrete urban highway bridges, storm drain outlets, swirling whirlpool eddies formed behind bridge pillars.
* **Flow Velocity**: Moderate-to-fast current ($1.5\text{ m/s}$), deeper navigation channel ($2.0\text{m} - 3.5\text{m}$ depth).
* **Key Hazards**: Current drag pushing player vessels downriver; swirling eddies trapping large trash carpets; passing debris logs that can tip light boats.
* **Player Phase**:
  - Piloting the wooden *sampan* canoe against the current.
  - Using the 4-meter bamboo claw pole and hand winch to haul heavy mattresses and tires.
  - Anchoring the first **Deployable Floating Trash Booms** across the river channel to divert floating garbage automatically toward an anchored pontoon sorting barge.

### 3.3 Zone 3: Bendungan Siaga 1 & Gunung Sampah (The Final Frontier)
* **Visual Atmosphere**: Massive concrete floodgate retaining walls, warning sirens, flashing orange beacons, towering 3-story Trash Mountain choking the river terminus.
* **Flow Velocity**: Stagnant, suffocating current backed up behind the blockage ($0.1\text{ m/s}$), but extreme hydraulic head pressure built up against the sluice gates.
* **Player Phase**:
  - Deploying the **Solar-Powered Interceptor Catamaran** to maintain automated perimeter vacuuming.
  - Operating the heavy **Pindad Amphibious Excavator**: using the 3-joint hydraulic arm to dig into the Trash Mountain, loading dump barges, and triggering structural dam collapse sequences.
  - Final cinematic breach: opening the sluice gates, flushing the basin, and restoring the river ecosystem.

---

## 4. Core Gameplay Loop & Progression Economy

The gameplay loop operates on a satisfying 4-step incremental expansion cycle:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE 4-STEP EXPANSION CYCLE                      │
│                                                                        │
│   [ 1. SCOOP & DREDGE ] ──► [ 2. SORT & COMPACT ]                     │
│         ▲                               │                              │
│         │                               ▼                              │
│   [ 4. AUTOMATE & UPGRADE ] ◄── [ 3. BANK SAMPAH (IDR) ]               │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Step 1: Scoop & Dredge
* **Inventory Capacity**: Every vessel has a strict **Weight Capacity (kg)** and **Volume Capacity (Litres)**.
  - Leaky Styrofoam Raft: $25\text{ kg}$ max (exceeding causes raft to submerge and lose balance!).
  - Wooden Sampan: $150\text{ kg}$ max.
  - Pontoon Sorting Barge: $1,200\text{ kg}$ max.
  - Interceptor Dumpster Hopper: $5,000\text{ kg}$ max.
* **Tactile Interactions**:
  - Dragging the net creates drag force against the boat.
  - Hooking waterlogged mattresses requires rhythmic reeling inputs to avoid snapping the rope.

### 4.2 Step 2: Sort & Classify (Value Multiplication)
Collected waste can be dumped raw for low base payout, or sorted at a sorting table to multiply profit:

| Waste Category | Item Examples | Raw Price (IDR/kg) | Sorted / Baled Price |
| :--- | :--- | :---: | :---: |
| **High-Grade Plastic (PET)** | Clean Aqua bottles, clear drink cups | 3,500 IDR | **10,500 IDR** ($3\times$ after Baling Press) |
| **Low-Grade Plastic (HDPE/PP)** | Pop Mie cups, bottle caps, buckets | 2,000 IDR | 5,000 IDR |
| **Scrap Metals & Cans** | Soda cans, discarded zinc, wire coils | 6,000 IDR | **14,000 IDR** |
| **Rubber & Foam** | Sandal Swallow, mattresses, tires | 1,000 IDR | 3,000 IDR (Fuel Pellets) |
| **Organic Sludge / Biomass** | Water hyacinth, rotting tree branches | 200 IDR | 1,200 IDR (Compost) |

* **The Hydraulic Baling Press (*Mesin Press Botol*)**:
  - Compresses 50 loose plastic bottles into a neat, dense rectangular export bale.
  - Dramatically reduces cargo volume while tripling market value at the Bank Sampah!

### 4.3 Step 3: Bank Sampah & Eco-Reputation
* **Monetary Currency (Rupiah - IDR)**: Used to buy tools, hire local workers, purchase fuel, and unlock machinery.
* **Eco-Reputation Points (Bintang Lingkungan)**:
  - Earned by keeping river turbidity low and preventing sluice gate flood warnings.
  - Unlocks municipal funding grants and permits for heavy equipment (e.g., getting permission from the City Public Works Department to operate an amphibious excavator).

### 4.4 Step 4: Upgrades & Equipment Tree

```
[ TIER 1: PERALATAN TANGAN ]
  ├── Broken Net (0 IDR) ──► Reinforced Steel Net (45k IDR) ──► 4m Telescopic Claw Galah (120k IDR)
  └── Leaky Styrofoam Raft (0 IDR) ──► Plywood Sampan (250k IDR) ──► Motorized Sampan (750k IDR)

[ TIER 2: AUTOMATION BOOMS & CONVEYORS ]
  ├── HDPE Floating Boom Barrier (400k IDR / 10m section)
  ├── Anchored Sorting Pontoon (1.5M IDR)
  └── Waterwheel Paddle-Lift Conveyor Belt (3.2M IDR)

[ TIER 3: INDUSTRIAL HEAVY MACHINERY ]
  ├── Hydraulic Baling Press (2.8M IDR)
  ├── Solar-Powered Autonomous Interceptor Catamaran (12M IDR)
  └── Pindad Amphibious Backhoe Excavator (25M IDR)
```

---

## 5. Computer Graphics Architecture (Modules 3 & 4 Implementation)

To guarantee the **Grade A (85–100%)** score, every technical feature is mathematically grounded in the syllabus requirements:

### 5.1 Module 3: 3D Modeling, PBR Materials & Custom Shaders

#### A. Dynamic River Water Cleansing Shader (Shader Graph / HLSL)
* **Directional Current UV Panning**:
  - Animates water normals using a velocity vector field $\vec{V}_{\text{flow}}(x, z)$:
    $$\vec{UV}_1 = \vec{UV} + \vec{V}_{\text{flow}} \cdot t, \quad \vec{UV}_2 = \vec{UV} + \vec{V}_{\text{flow}} \cdot (t + 0.5)$$
  - Blends two normal maps with fractional phase interpolation to prevent visible looping repetition.
* **Runtime Water Quality Lerp**:
  - The shader samples a runtime **Trash Density Texture** (a $256\times 256$ grayscale RenderTexture updated by a CPU rasterizer tracking uncollected garbage positions).
  - Uses the **Beer-Lambert Law** for light extinction through turbid water:
    $$I(d) = I_0 \cdot e^{-\sigma_{\text{ext}} \cdot d}$$
  - Dynamically interpolates water material parameters:
    - *Full Pollution ($\text{Density} > 0.8$)*: Base color is thick opaque brown sludge ($\text{Hex } \#2c2317$), high extinction coefficient $\sigma_{\text{ext}} = 4.5$, metallic oily scum film, zero bottom visibility.
    - *Intermediate ($\text{Density} \approx 0.4$)*: Murky river green ($\text{Hex } \#365314$), $\sigma_{\text{ext}} = 1.8$.
    - *Clean State ($\text{Density} < 0.1$)*: Transparent shimmering cyan ($\text{Hex } \#06b6d4$), $\sigma_{\text{ext}} = 0.3$, dynamic caustic sunlight projection onto riverbed pebbles.
* **Screen-Space Foam Edge Intersection**:
  - Computes depth difference between river water surface and submerged geometry (trash, bridge pilings, banks) to render thick white organic scum and bubble froth edges.

#### B. The Trash Mountain Layered Heightfield Shader
* **Multi-Layer Vertex Displacement & Carving**:
  - The Trash Mountain uses a custom Triplanar Shader Graph that blends three PBR material sets across world height $Y$:
    - $Y \in [0.0\text{m}, 1.2\text{m}]$: Anaerobic Mud & Crushed Rusted Iron (high normal roughness, dark albedo).
    - $Y \in [1.2\text{m}, 2.5\text{m}]$: Entangled Mattress Fibers, Kapok & Nylon Ropes.
    - $Y \in [2.5\text{m}, 4.0\text{m}]$: Multi-colored Specular Plastics (Sandal Swallow blue, Aqua bottle cyan, Indomie red highlights).
  - When the player dredges with the excavator scoop, a spherical brush subtracts height values from a displacement render texture, visually and physically carving caves and trenches into the mountain.
* **Structural Collapse Physics**:
  - If the player scoops out the bottom layer without stabilizing the upper tier, the top mesh triggers a structural stability check. If breached, the upper mesh instantiates rigid-body debris prefabs that tumble into the water in a dramatic garbage avalanche!

#### C. Authentic Indonesian PBR Asset Pipeline (Blender Workflow)
* **Modular Riverbank Kit**:
  - Bamboo stilt foundations (*tiang bambu petung*), weathered teak planks (*kayu jati bekas*), corrugated rusted zinc roofs (*seng gelombang berkarat*), warung snack sachets, and concrete rip-rap retaining blocks.
* **Authentic Trash Library (Low-Poly with LODs)**:
  - Discarded *Sandal Swallow* (blue/white rubber flip-flops with dirt stains).
  - Crushed *Aqua* bottles ($600\text{ml}$ and $19\text{L}$ galon).
  - *Pop Mie* and *Indomie* wrappers with foil-lined interior PBR materials.
  - Wet kapok mattress (*kasur kapuk*) with exposed rusted wire springs.
* **Lighting Architecture**:
  - Low-angle tropical golden hour sunlight ($3400\text{K}$) with volumetric sun shafts penetrating between stilt houses.
  - Real-time soft shadow mapping cast by bridges and palm trees across the water surface.

---

### 5.2 Module 4: Rigging, VFX, Physics & SDG Simulation

#### A. Amphibious Excavator Inverse Kinematics (IK) Rigging
* **3-Joint Hydraulic Kinematic Chain**:
  - Bone hierarchy: `BaseTurret` $\rightarrow$ `BoomJoint` $\rightarrow$ `ArmJoint` $\rightarrow$ `BucketJoint`.
  - Implemented using Unity's **Two-Bone IK / FABRIK Solver**.
  - The player moves a target reticle in 3D space with the mouse; the IK solver computes joint rotation angles in real time.
* **Hydraulic Piston Dynamic Rig**:
  - 4 hydraulic piston pairs rigged with `LookAt` constraints so cylinders and piston rods dynamically slide into each other as the arm bends.
* **Character Cleanup Animation State Machine**:
  - Mecanim Animator controller with 2D blend trees:
    - *Raft Idle (rocking balance)* $\leftrightarrow$ *Net Dragging (straining forward)* $\leftrightarrow$ *Hauling Heavy Load* $\leftrightarrow$ *Dumping into Bucket*.

#### B. Dynamic Buoyancy Physics & River Current Vector Simulation
* **Multi-Point Raycast Buoyancy**:
  - Every floating object (trash clusters, sampan, pontoon barges) casts 4 down-facing raycasts to sample local water mesh surface normals and height:
    $$F_{\text{buoyant}} = \rho_{\text{water}} \cdot V_{\text{submerged}} \cdot g - c_{\text{drag}} \cdot \vec{v}_{\text{rel}}$$
  - Computes authentic angular torque: sampans pitch and roll when loaded unevenly, and styrofoam rafts submerge when overloaded!
* **Bezier Spline River Current Flow**:
  - Debris follows a vector spline network representing main channel currents and bridge eddy whirlpools.

#### C. Particle VFX (VFX Graph Systems)
1. **Muddy Dredging Splashes**: High-velocity brown fluid drops, foam spray, and spreading surface ripple rings spawned whenever the excavator scoop breaks the surface.
2. **Methane Sludge Bubble Emitters**: Intermittent gas bubbles rising from deep sludge, expanding, and popping into tiny brown mist splatters.
3. **Swarming River Gnats (Boids System)**: Procedural swarms of insects orbiting high-density organic waste piles.
4. **Monsoon Torrential Downpour**: Dense screen-space raindrop streaks colliding with the river mesh to generate thousands of animated circular splash rings.

---

## 6. UN SDG Alignment & Academic Rubric Mapping

| Rubric Criteria | Weight | How "KALI" Demonstrates Mastery |
| :--- | :---: | :--- |
| **P3.1 Understanding Graphics Process** | **30%** | Mathematical proof of **Beer-Lambert Light Absorption** for water turbidity, **Directional Flow UV Vector Mathematics**, and **Multi-Point Buoyancy Equations**. |
| **KK1.2 Complexity & Result Quality** | **30%** | Exceeds the "1 simple model" baseline by delivering a complete authentic Indonesian 3D asset library, multi-layered PBR materials, custom Shader Graph water/mountain shaders, and an animated IK excavator rig. |
| **KU4.2 UN SDG Alignment & Story** | **30%** | **SDG 6 (Clean Water & Sanitation)**: Transforming toxic river water into safe community waterways.<br>**SDG 14 (Life Below Water)**: Preventing land-based plastic from entering the ocean.<br>**SDG 11 (Sustainable Cities)**: Eliminating sluice gate clogs to prevent annual monsoon urban flooding (*banjir bandang*). |
| **KU2.2 English Presentation Quality** | **10%** | Polished, professional English slide deck and live gameplay demonstration defending the mathematical and technical graphics architecture. |

---

## 7. Production Roadmap & 3-Person Work Breakdown

```
WEEKS 9-10 (Module 3 Sprint): 3D Modeling & Shader Engine
  ├── Wesley: Model Indonesian stilt houses, sampan, and authentic trash library in Blender.
  ├── Ivan: Build Dynamic River Water Shader (Flow UVs, Beer-Lambert Lerp, Foam) in Shader Graph.
  └── Nicholas: Setup Bank Sampah economic logic, grid triggers, and inventory weight system.

WEEKS 11-12 (Module 3 Polish): The Trash Mountain & Lighting
  ├── Wesley: Model Trash Mountain multi-tier mesh and Pindad amphibious excavator.
  ├── Ivan: Build Trash Mountain Triplanar Carver Shader and Tropical Golden Hour lighting.
  └── Nicholas: Program Baling Press machine and floating boom barrier mechanics.

WEEKS 13-14 (Module 4 Sprint): Rigging, IK & Buoyancy Physics
  ├── Wesley: UV unwrapping, LOD generation, and environmental prop detailing.
  ├── Ivan: Multi-point raycast buoyancy simulation and river current vector splines.
  └── Nicholas: Excavator 3-joint Inverse Kinematics (IK) rig and character Mecanim blend trees.

WEEKS 15-16 (Module 4 Polish): VFX Graph, Monsoon Weather & Sidang Prep
  ├── Wesley: Refine texture budgets, collision meshes, and environment props.
  ├── Ivan: Build VFX Graph particles (Mud splashes, methane bubbles, rain ripples) & Post-Processing.
  └── Nicholas & Team: Sluice gate flood warning state machine, English presentation slides & video trailer.
```
