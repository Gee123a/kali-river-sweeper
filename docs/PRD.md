# Product Requirements Document (PRD) — KALI: Indonesian River Sweeper

| Field | Detail |
| :--- | :--- |
| **Project Title** | **KALI: Indonesian River Sweeper** (*Penjaga Terakhir Sungai Nusantara*) |
| **Course & Rubric** | IMT01303501 Computer Graphics (Universitas Ciputra Surabaya) — `20261-CG-Penilaian ALP.pdf` (**GAME** track, target **85–100% Grade A**) |
| **Engine / Art Pipeline** | Unity `2022.3.46f1` LTS (URP `14.0.11`) + Blender `5.3.0` |
| **Coordinator / Lead** | **Stevanus Ivan Santoso** (`0706012410029`) — Core C# Logic, Physics, Map Spawner, Contracts |
| **Team Authors** | **Jason Christopher (JC)** (Props, Rigging & Lighting), **Wesley Goeinawan** (Environment & Water Shaders), **Nicholas Gerwin Mawardji (Niki)** (VFX, UI & Audio/Narrative) |

![Game Flow & River Topology](./kali_game_flow_and_architecture.png)

---

## 1. Story Premise & UN SDG Vision

> *"Di dunia ini, gunung sampah telah menumpuk sangat tinggi hingga mencekik satu-satunya sungai di desa, dan kamu adalah generasi terakhir penjaga sungai yang tersisa."*

* **English Summary**: In this world, mountains of trash (*Gunung Sampah* upstream at `-Z`) shed waste downstream (`+Z`) toward the floodgate (*Pintu Air Siaga 1*). Navigate `+Z` river currents to scoop `Normal`, `Medical`, and `Biohazard` waste, routing each to its dedicated sorting station (or risking fines / cheap bulk sales at `Gudang Pengepul`). Your 20 official JC scavenging tools auto-unlock automatically as cumulative Rupiah rises. Win by completely dismantling `Gunung Sampah` (`0%`) OR surviving the 5-minute Monsoon Countdown without fatal flood or `0 HP` death.
* **SDG Targets Integrated Into Mechanics**:
  * **SDG 6.3 (Clean Water & Sanitation)**: Driving `_WaterClarity` from polluted toxic brown (`0.05`) to healthy river turquoise (`1.00`) while safely isolating Medical (`Pos Medis B3`) and Radioactive Biohazard (`Karantina Biohazard`) waste.
  * **SDG 11.5 (Sustainable Cities / Flood Mitigation)**: Controlling linear river rise (`waterLevelY = -0.25 + 0.020 * trashInRiver`) before banks overflow (`+1.40m`), stations hit `Sell-Lock` (`+1.85m`), or fatal drowning (`+2.45m`) floods Kampung Hulu.
  * **SDG 14.1 (Life Below Water)**: Choosing to clear river debris, dump on high ground (`Q`) during Sell-Lock, and dismantle `Gunung Sampah` rather than triggering `CompromisedOceanFlush`.

---

## 2. Core Game Loop & 5 Interacting Mechanics

```text
  [1. SCOOP N/M/B (+Z)] ──> [2. SORT AT 3 STATIONS / PENGEPUL] ──> [3. 20 TOOLS AUTO-UNLOCK]
         ▲                                                                     │
         └────── [5. PREVENT & AUTOMATE (Bins & Trash Boom)] ◄─────────────────┘
                                    │
                       [4. LINEAR WATER RISE -> SELL-LOCK -> MONSOON]
```

1. **Dynamic `+Z` Current & Linear Water Level (`RiverFlowBuoyancy.cs`, `RiverGameManager.cs`)**: Floating waste sheds from upstream `Gunung Sampah` (`-Z`) and drifts **`+Z` downstream** toward `Pintu Air` (`2.2x` faster in monsoon). `waterLevelY = -0.25f + TotalTrashInRiver * 0.020f` reacts immediately to every item scooped (`Overflow >= 1.40m`, `Sell-Lock >= 1.85m`, `Fatal Flood >= 2.45m`).
2. **20 Auto-Unlocking Scavenging Tools + 3-Class Waste Hazards (`ToolCatalog.cs`)**: Any tool can scoop all 3 classes (`Normal`, `Medical`, `Biohazard`). Tools `#01..#20` unlock automatically by cumulative Rupiah milestones. `Medical` waste risks needle-prick HP damage (`-18 HP`) mitigated to `0%` by **`#10 Capitan Ular`**. `Biohazard`/Radioactive waste inflicts Cargo DoT after a 10s grace period (`0 HP` triggers `HealthFail`).
3. **3 Dedicated Stations (+ Fines) vs `Gudang Pengepul` (`1 / 2 / 3 / E`)**: Sort `Normal` at `Bank Sampah` (`4,000` / `7,500` at `Pos Sortir`), `Medical` at `Pos Medis B3` (`9,000` + `+10 HP`), and `Biohazard` at `Karantina Biohazard` (`14,000`). Discarding at the wrong station incurs a Rupiah fine + Trust loss! Alternatively, `Gudang Pengepul` (near Spawn) buys all classes in one go cheaply (`2k/3k/4.5k`) with SDG/Trust penalties for hazardous waste.
4. **Sell-Lock & High-Ground Dump Anti-Deadlock (`Q` key)**: Past `+1.85m`, stations flood (`Sell-Lock`) and reject sales. Players press **`Q`** to dump cargo safely onto high ground (preventing cargo deadlock) or trigger Emergency Ocean Flush.
5. **Root-Cause Prevention & River Automation (`Toko Alat`)**: Buying **Kampung Trash Bins** (`30,000 IDR`) cuts upstream shedding by **60%**, while **Trash Boom** slows downstream pileup & passively harvests.

---

## 3. Itemized 20-Tool Auto-Unlock Milestones (`SM_Tool_*` Exact Contracts)

Tools unlock automatically as **Cumulative Rupiah (`cumulativeEarnings`)** crosses each milestone (`Scroll` / `[ ]` cycles unlocked tools; `PF_Tool_*` `BoxCollider`s stay `isTrigger = true` / disabled while equipped):

| # | Official Mesh (`SM_Tool_*`) | Indonesian Name | Milestone (IDR) | Reach / Batch | Medical Prick Risk & Role |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **01** | `SM_Tool_SendokMakanBengkok` | *Sendok Makan Bengkok* | `0` | `4.2m / 1` | `60%` prick — Starter dining spoon |
| **02** | `SM_Tool_GayungMandi` | *Gayung Mandi* | `4,000` | `4.5m / 1` | `55%` prick — Bath dipper |
| **03** | `SM_Tool_CentongNasi` | *Centong Nasi* | `8,000` | `4.8m / 1` | `50%` prick — Flat rice paddle |
| **04** | `SM_Tool_GarpuTaman` | *Garpu Taman* | `14,000` | `5.0m / 2` | `45%` prick — Garden hand fork |
| **05** | `SM_Tool_EmberCat5L` | *Ember Cat 5L* | `20,000` | `5.2m / 2` | `42%` prick — 5L paint pail |
| **06** | `SM_Tool_GayungSaringanBambu` | *Gayung Saringan Bambu* | `28,000` | `6.2m / 2` | `35%` prick — Perforated bamboo dipper |
| **07** | `SM_Tool_SerokanWaring3m` | *Serokan Waring 3m* | `38,000` | `6.8m / 3` | `30%` prick — 3m bamboo hand net |
| **08** | `SM_Tool_GancoBesi1Mata` | *Ganco Besi 1-Mata* | `50,000` | `7.0m / 2` | `25%` prick — Single spike iron hook |
| **09** | `SM_Tool_EmberCat20L` | *Ember Cat 20L* | `64,000` | `7.4m / 3` | `22%` prick — Weighted 20L rope bucket |
| **10** | `SM_Tool_CapitanUlar` | *Capitan Ular* | `80,000` | `7.8m / 2` | **`0%` prick** — Dedicated B3 snake grabber |
| **11** | `SM_Tool_AritSabitPanjang` | *Arit Sabit Panjang* | `98,000` | `8.2m / 3` | `14%` prick — Long grass sickle |
| **12** | `SM_Tool_SerokanJumbo4_5m` | *Serokan Jumbo 4.5m* | `118,000` | `8.8m / 4` | `12%` prick — 4.5m jumbo waring net |
| **13** | `SM_Tool_GancoGandaWinch` | *Ganco Ganda Winch* | `140,000` | `9.0m / 3` | `8%` prick — Double winch (chips Gunung!) |
| **14** | `SM_Tool_JalaCincinLempar` | *Jala Cincin Lempar* | `165,000` | `9.6m / 4` | `10%` prick — Float ring cast net |
| **15** | `SM_Tool_PompaSiphonManual` | *Pompa Siphon Manual* | `192,000` | `9.8m / 4` | `6%` prick — Manual bilge siphon |
| **16** | `SM_Tool_BlokMagnet50kg` | *Blok Magnet 50kg* | `222,000` | `10.4m / 4` | `6%` prick — 50kg salvage magnet |
| **17** | `SM_Tool_SenapanPanahTali` | *Senapan Panah Tali* | `254,000` | `11.2m / 3` | `4%` prick — Pneumatic harpoon |
| **18** | `SM_Tool_PompaMesinRumput49cc` | *Pompa Mesin Rumput 49cc* | `288,000` | `11.6m / 5` | `5%` prick — 49cc vacuum impeller |
| **19** | `SM_Tool_PenebasGergajiGanda` | *Penebas Gergaji Ganda* | `324,000` | `12.2m / 5` | `5%` prick — Twin-saw weed slasher |
| **20** | `SM_Tool_GarukSkimmerHidrolik` | *Garuk Skimmer Hidrolik* | `360,000` | `13.0m / 6` | `3%` prick — Hydraulic bow skimmer |

**Vessel Upgrades (`Toko Alat`)**: *Rakit Gabus* (8 cap) $\to$ *Perahu Sampan Kayu* (22 cap, `40k`) $\to$ *Trash Boom & Pos Sortir* (`75k`) $\to$ **Amphibious Excavator (`SK_ExcavatorAmfibi`)** (60 cap + fast `DamageGunungSampah()`, `120k`).

---

## 4. River Waste Taxonomy (3 Scoopable Classes)

| Class | Assets | Hazard & Station Contract |
| :--- | :--- | :--- |
| **`Normal`** | `PF_Trash_SandalSwallow`, `AquaBottle_600ml`, `AquaGalon_19L`, `PopMieCup`, `KresekBag`, `KasurKapuk`, `BanBekas`, `EcengGondok`, `BatangPisang` | Safe to scoop; sort at **`Bank Sampah Berkah`** (`4,000 IDR`) or **`Pos Sortir`** (`7,500 IDR` w/ Boom). |
| **`Medical`** | `PF_Trash_MedicalBag`, `PF_Trash_SyringeBox` (yellow + red B3 markings) | **Pickup Prick Hazard**: Any tool can scoop, but lower tools risk `-18 HP` needle pricks (`0%` with **`#10 Capitan Ular`**). Sort at **`Pos Medis B3`** (`9,000 IDR` + `+10 HP`). |
| **`Biohazard`** | `PF_Trash_BiohazardDrum` / Radioactive containment barrels (purple/lime glow) | **Cargo DoT Hazard**: Deals escalating Damage Over Time if held past `10s` grace period. Sort at **`Karantina Biohazard`** (`14,000 IDR`). |

---

## 5. Three Meaningful Player Choices & Four Endings

1. **Choice A — 3 Dedicated Stations vs. `Gudang Pengepul` Shortcut**:
   - Routing `Normal` $\to$ `Bank Sampah`, `Medical` $\to$ `Pos Medis B3`, and `Biohazard` $\to$ `Karantina Biohazard` (`1/2/3/E`) pays full Rupiah and builds Trust (wrong-station discards incur Rupiah fines!).
   - Dumping everything in one go at **`Gudang Pengepul`** (near Spawn) pays cheaper rates (`2k/3k/4.5k`) with **no fine**, but inflicts severe Community Trust / SDG penalties if hazardous cargo is mixed in.
2. **Choice B — Personal Vessel vs. Upstream `Kampung Bins` (`30,000 IDR`)**:
   - Skipping prevention keeps upstream shedding relentless; buying `Kampung Bins` + `Trash Boom` cuts shedding by **60%** and slows downstream barrier pileup.
3. **Choice C — Monsoon `Sell-Lock` Crisis & 4 Endings**:
   - **`TrueSdgVictory`**: Reach **`0% Gunung Sampah`** (`CompleteCleanBreach()`) OR **survive the 5-minute Monsoon Countdown** without fatal flood or `0 HP` death.
   - **`CompromisedOceanFlush`**: Panic-open the floodgate (`TriggerEmergencyFlush()`). Saves Kampung from flooding, but flags **SDG 14.1 Failed**.
   - **`FloodFail`**: `waterLevelY >= 2.45m` (`+1.05m` over bank top) drowns the player and floods Kampung Hulu.
   - **`HealthFail`**: `playerHealth <= 0` from repeated `Medical` needle pricks or untreated `Biohazard` Cargo DoT.
