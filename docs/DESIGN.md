# DESIGN.md — "Kalimas Nusantara" Visual Identity & Art Bible

> **Purpose**: Ensures consistent Indonesian riverbank aesthetics, unified color psychology across lighting, water shaders, props, and UI, and strict adherence to Grade-A **Complexity & Quality of Result** criteria.
> **Applies To**: **JC** (Props, Tools, Lighting), **Wesley** (Environment Architecture & Shaders), **Niki** (UI Canvas & VFX).

---

## 1. Visual Pillar: Polluted Industrial Grime $\rightarrow$ Restored Living River

The entire visual experience visualizes the game's core ecological promise through color and surface transition rather than walls of text:

1. **Act 1 — Choked Polluted Village (`waterClarity = 0.05..0.25`, `Siaga 4–3`)**:
   - Warm low tropical haze (`3400K` Golden Hour), damp muddy embankments (`+1.40m`), weathered faded plastics, rusted corrugated *seng* roofs, opaque brown-sludge water dragging `Normal`, `Medical`, and `Biohazard` waste **`+Z` downstream** toward `Pintu Air`.
2. **Act 3 — Monsoon Overflow & Sell-Lock (`isMonsoonStorm = true`, `Siaga 2–1`)**:
   - Cool storm overcast (`#334155`), wind-driven rain streaks, flashing orange `PF_WarningBeacon_PintuAir` beacons at downstream `+Z` `Pintu Air`, water overflowing `+1.40m` riverbanks and flooding stations past `+1.85m` (`Sell-Lock`), triggering urgent **`[Q] High-Ground Dump`** & `Biohazard DoT` banners.
3. **Endgame Victory — Restored Nusantara Sanctuary (`waterClarity = 1.00`, `Siaga 4`)**:
   - Clear shimmering emerald-teal river (`#1B6B63` to `#06B6D4`), dismantled `Gunung Sampah` (`-Z`), sunny kampung docks with hanging lanterns (`PF_Lantern_Warung`), and organized recycling across `Bank Sampah`, `Pos Medis B3`, and `Karantina Biohazard`.

---

## 2. Official Color Palette & Environmental Tokens

### 2.1 Water & Sludge Transition (`SG_KaliWater` & `SG_TrashTriplanar`)

| Surface State | Hex Token | RGB (0–1) | PBR Smoothness | Where Used |
| :--- | :---: | :--- | :---: | :--- |
| **Toxic Muddy River** (`_WaterClarity = 0.12`) | `#3B2818` | `(0.23, 0.16, 0.09)` | `0.65` (oily) | Shallow polluted edges & initial river state |
| **Mid-Transition Olive** (`_WaterClarity = 0.50`) | `#365314` | `(0.21, 0.33, 0.08)` | `0.75` | Half-cleared Kalimas channel |
| **Restored Emerald Teal** (`_WaterClarity = 1.00`) | `#1B6B63` | `(0.11, 0.42, 0.39)` | `0.90` | Clean shallow-to-deep Beer-Lambert absorption |
| **Crystal Caustic Highlight** | `#06B6D4` | `(0.02, 0.71, 0.83)` | — | Final victory clarity tint & foam edge sheen |
| **Anaerobic Bed Silt** | `#1C1917` | `(0.11, 0.10, 0.09)` | `0.80` (wet) | Bottom layer `< 0.8m` of `Gunung Sampah` |

### 2.2 `Siaga 4 -> 1` Flood Gauge & UI Alert Tokens (`Canvas_HUD` — Niki)

Every flood alert badge pairs color with an explicit uppercase label (`SIAGA 4 - AMAN`, etc.) — never rely on color alone:

| Flood State | Threshold (`floodPressure`) | Primary Accent Hex | HUD Canvas Surface | Visual Feedback |
| :--- | :--- | :---: | :---: | :--- |
| **SIAGA 4 (Normal / Aman)** | `< 0.35` | `#22C55E` (Emerald) | `#0F172A` (`85%` alpha) | Steady calm green indicator |
| **SIAGA 3 (Waspada)** | `0.35 – 0.59` | `#FACC15` (Amber Yellow) | `#0F172A` (`85%` alpha) | Debris density notice at middle choke |
| **SIAGA 2 (Kritis)** | `0.60 – 0.84` | `#F97316` (Orange) | `#1E1B18` (`90%` alpha) | Rotating Pintu Air warning beacon starts |
| **SIAGA 1 (Bencana Banjir)** | `>= 0.85` | `#F43F5E` (Crimson Red) | `#2A1215` (`92%` alpha) | Pulsing vignette + flood alarm audio |

### 2.3 Authentic Scavenger Material Tokens (`JC` & `Wesley`)

| Material Archetype | Specular / Metallic | Roughness | Surface Details |
| :--- | :--- | :---: | :--- |
| **Sun-Faded Indonesian Plastic** (*Gayung Pink, Ember 20L, Botol Aqua*) | Non-metal (`0.0`) | `0.35 – 0.55` | Scuff marks, slight drill/tape repairs, glossy black electrical vinyl tape (`Roughness 0.25`) |
| **Split River Bamboo & Weathered Teak** | Non-metal (`0.0`) | `0.75 – 0.88` | Splintered warm bamboo grain, damp dark base near waterline (`Y = 0`) |
| **Corrugated Seng & Forged Iron** (*Atap Seng, Ganco, Winch*) | Metal (`0.75 – 0.90`) | `0.50 – 0.80` | Heavy orange-brown oxidation patina along edges, wet specular reflections |
| **Hydraulic Steel Rams & Excavator** (`SK_ExcavatorAmfibi`) | Industrial Yellow `#EAB308` (`M: 0.15`) / Chrome `#E2E8F0` (`M: 0.95`) | `0.45` (body) / `0.10` (rams) | Oily grease near seals, dried mud buildup along pontoon tracks |
| **Medical Waste (`WasteClass.Medical`)** (*Yellow Biohazard Bags, Syringe Boxes*) | Non-metal / Foil (`0.0 – 0.4`) | `0.30 – 0.45` | Hazard yellow `#EAB308` + red B3 stripes; causes needle-prick HP injury unless handled with `#10 Capitan Ular`; sorted at **`Pos Medis B3`** |
| **Biohazard / Radioactive (`WasteClass.Biohazard`)** (*Containment Drums / Barrels*) | Coated Drum (`0.2 – 0.6`) | `0.25 – 0.45` | High-contrast purple `#A855F7` + radioactive lime `#84CC16` glow; deals Cargo DoT after 10s; sorted at **`Karantina Biohazard`** |

### 2.4 Dedicated Station Identity Tokens (`Wesley` & `Niki`)

| Station | Waste Accepted | Sign / Accent Color | Wrong-Class Penalty |
| :--- | :--- | :---: | :--- |
| **`Bank Sampah Berkah` / `Pos Sortir`** | `Normal` plastics & organic | `#22C55E` / `#14B8A6` | Fines `Medical` (`Rp 5,000`) & `Biohazard` (`Rp 8,000`) |
| **`Pos Medis B3`** | `Medical` (`MedicalBag`, `SyringeBox`) | `#EAB308` + Red Cross `#DC2626` | Fines `Normal` (`Rp 2,500`) & `Biohazard` (`Rp 8,000`) |
| **`Karantina Biohazard`** | `Biohazard` / Radioactive | `#A855F7` + `#84CC16` | Fines `Normal` (`Rp 2,500`) & `Medical` (`Rp 5,000`) |
| **`Gudang Pengepul`** *(Near Spawn)* | All 3 classes in 1 go | `#A87018` (Amber Rust) | Cheap payout (`2k/3k/4.5k`), **0 fine**, **Trust penalty** for `Medical`/`Biohazard` |

---

## 3. PBR & Pivot Standards (Zero Primitive Rule)

1. **Zero Untagged Default Primitives**: Replace every Unity primitive placeholder spawned by fallback `MapJsonImporter` with custom Blender meshes carrying proper UV maps and tangent-space normal maps.
2. **Uniform Pivot Rules**:
   - **20 Scavenging Tools (`JC`)**: Pivot `(0, 0, 0)` placed directly at the player hand grip, shaft extending cleanly along `+Z` / `+Y`.
   - **Kampung Buildings (`Wesley`)**: Pivot `(0, 0, 0)` at bottom-center ground plane; stilts extend slightly below `Y = 0` (`-0.5m`) so slope margins never float.
   - **Boat Pier `SM_Env_Dermaga` (`Wesley`)**: Pivot `(0, 0, 0)` at exact waterline height (`Y = 0.0m`).
3. **Typography & HUD Layout (`Niki`)**:
   - Clean sans-serif for Rupiah / capacity numbers (`TextMeshPro` bold tabular digits) + dark translucent glass cards (`#0F172A` at 85% opacity, `2px` accent border) pinned cleanly to corners (`18px` safe margins) leaving the central `70%` viewport completely unobstructed for river sweeping.
