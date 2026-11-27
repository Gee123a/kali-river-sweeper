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

* **English Summary**: In this world, mountains of trash (*Gunung Sampah* upstream at `-Z`) shed waste downstream (`+Z`) toward the floodgate (*Pintu Air Siaga 1*). Walk, sprint, swim on the river surface (managing swim stamina against drowning), or steer boats along `+Z` currents to scoop `Normal`, `Medical`, and `Biohazard` waste, routing each to its dedicated sorting station (or risking fines / cheap bulk sales at `Gudang Pengepul`). Your 20 official JC scavenging tools unlock purchase eligibility at **Koperasi Desa (Kopdes)** as cumulative Rupiah rises (`BuyTool`). Win by completely dismantling `Gunung Sampah` (`0%` -> `TrueSdgVictory`) before fatal flood or `0 HP` death (surviving the 5-minute Monsoon Countdown with Gunung intact yields `PartialSurvival`).
* **SDG Targets Integrated Into Mechanics**:
  * **SDG 6.3 (Clean Water & Sanitation)**: Driving `_WaterClarity` from polluted toxic brown (`0.05`) to healthy river turquoise (`1.00`) while safely isolating Medical (`Pos Medis B3`) and Radioactive Biohazard (`Karantina Biohazard`) waste.
  * **SDG 11.5 (Sustainable Cities / Flood Mitigation)**: Controlling linear river rise (`waterLevelY = -0.25 + 0.020 * trashInRiver`) before banks overflow (`+1.40m`), stations hit `Sell-Lock` (`+1.85m`), or fatal flood (`+2.45m`) submerges Kampung Hulu.
  * **SDG 14.1 (Life Below Water)**: Choosing to clear river debris, dump on high ground (`Q`) during Sell-Lock, and dismantle `Gunung Sampah` rather than triggering `CompromisedOceanFlush`.

---

## 2. Core Game Loop & Interacting Mechanics

```text
  [1. SCOOP N/M/B (+Z) + SWIM STAMINA] ──> [2. SORT AT 3 STATIONS / PENGEPUL] ──> [3. KOPDES 20-TOOL & BOAT SHOP]
          ▲                                                                                    │
          └────────────── [5. PREVENT & AUTOMATE (Bins & Trash Boom)] ◄────────────────────────┘
                                              │
                                 [4. LINEAR WATER RISE -> SELL-LOCK -> MONSOON]
```

1. **Dynamic `+Z` Current & Linear Water Level (`RiverFlowBuoyancy.cs`, `RiverGameManager.cs`)**: Floating waste sheds from upstream `Gunung Sampah` (`-Z`) and drifts **`+Z` downstream** toward `Pintu Air` (`2.2x` faster in monsoon). `waterLevelY = -0.25f + TotalTrashInRiver * 0.020f` reacts immediately to every item scooped (`Overflow >= 1.40m`, `Sell-Lock >= 1.85m`, `Fatal Flood >= 2.45m`).
2. **20 Milestone-Unlocked Tools Purchased at Kopdes + 3-Class Waste Hazards (`ToolCatalog.cs`, `RiverGameManager.cs`)**: Any tool can scoop all 3 classes (`Normal`, `Medical`, `Biohazard`). Tools `#01..#20` unlock purchase eligibility as cumulative Rupiah crosses milestones (`CheckToolMilestones()` / `OnToolUnlocked`), and are bought using Rupiah at Kopdes via `BuyTool(int)` (`#01` starts owned; buying equips it without auto-equipping free milestones). `Medical` waste risks needle-prick HP damage (`-18 HP`) mitigated to `0%` once **`#10 Capitan Ular`** is unlocked. `Biohazard`/Radioactive waste inflicts Cargo DoT after a 10s grace period (`0 HP` triggers `HealthFail`).
3. **3 Dedicated Stations (+ Fines) vs `Gudang Pengepul` (`1 / 2 / 3 / E`)**: Sort `Normal` at `Bank Sampah` (`4,000` IDR), `Medical` at `Pos Medis B3` (`9,000` + `+10 HP`), and `Biohazard` at `Karantina Biohazard` (`14,000`). Safe `[E]` (`DiscardLegalAtStation`) deposits only the station's matching class; `[1]/[2]/[3]` allow explicit class discard (wrong station incurs Rupiah fine + Trust loss!). Alternatively, `Gudang Pengepul` (near Spawn) buys all classes in one go cheaply (`2k/3k/4.5k`) with SDG/Trust penalties for hazardous waste.
4. **Sell-Lock, High-Ground Dump (`Q`), Surface Swimming & `Dermaga` Boat Port**: Past `+1.85m`, stations flood (`Sell-Lock`) and reject sales (`Pos Medis B3` keeps emergency `+10 HP` triage accessible). Players hold **`Q`** (`0.5s`) to dump cargo safely onto high ground or hold **`Shift+X`** (`1.5s`) for Emergency Ocean Flush. On foot, players walk (`6.5 m/s`), sprint (`10.5 m/s`), or enter `RiverMath.IsInRiver` to **swim on the water surface** (`swimSpeed = 4.2`, `swimSprintSpeed = 6.2`, `swimStamina` `100` draining `8/16/4 s⁻¹` and recovering `18 s⁻¹` on dry land/`Jembatan`/`Dermaga`/boat; exhausting `swimStamina` to `0` triggers **drowning** at `14 HP/s` -> `HealthFail`). Boarding/disembarking boats (`[E]`) remains exclusive to **`Dermaga Awal`** and **`Dermaga Tengah`**.
5. **Root-Cause Prevention & River Automation (`Koperasi Desa / Kopdes`)**: Buying **Kampung Trash Bins** (`30,000 IDR`) cuts upstream shedding by **60%**, while **Trash Boom Timur** (`75,000 IDR`) slows downstream drift and earns passive income.
6. **12-Minute Procedural Sky, Day/Night Cycle & Water Sun Glint (`KaliSky.shader`, `KaliDayNightCycle.cs`, `SG_KaliWater.shadergraph`)**: An independent 720-second day/night clock (shown as `HH:MM` on `Canvas_HUD`, not reset by `RestartRun()`) starts at evening Golden Hour (`17:30`) with the sun rising over `Pintu Air` (`+Z`) and setting behind `Gunung Sampah` (`-Z`). Atmosphere, trilight ambient, exponential fog, `SG_KaliWater` sun glint/sky tint, and URP Bloom/Tonemapping/ColorAdjustments respond dynamically to time of day (`T` cycles Golden Hour → Dusk → Night → Dawn → Noon), Monsoon overcast (`~6s` blend), and pollution smog (`waterClarity < 0.60`).

---

## 3. Itemized 20-Tool Kopdes Milestones (`SM_Tool_*` Exact Contracts)

Cumulative **Rupiah (`cumulativeEarnings`)** unlocks purchase availability (`IsToolUnlocked(int)` / `OnToolUnlocked`), and players buy tools with **Rupiah** via `BuyTool(int)` at **Kopdes** (`#01` starts owned; `Scroll` / `[ ]` cycles owned tools; `PF_Tool_*` `BoxCollider`s stay `isTrigger = true` / disabled while equipped):

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

**Vessel Upgrades (`Koperasi Desa / Kopdes`)**: *Rakit Gabus* (8 cap) $\to$ *Perahu Sampan Kayu* (22 cap, `40k`) $\to$ *Trash Boom Timur* (`75k`) $\to$ **Amphibious Excavator (`SK_ExcavatorAmfibi`)** (60 cap + fast `DamageGunungSampah()`, `120k`). Boat embark/disembark is strictly gated through `Dermaga Awal` and `Dermaga Tengah` (foot swimmers can also enter/exit the river and climb back onto banks/`Dermaga`).

---

## 4. River Waste Taxonomy (3 Scoopable Classes)

| Class | Assets | Hazard & Station Contract |
| :--- | :--- | :--- |
| **`Normal`** | Shipped: `PF_Trash_BotolLifeman`, `BotolSprit`, `BungkusIndomy`, `BungkusRisol`, `BungkusSariBoti`, `KotakRokok`, `SachetKecapBingo`, `SachetMoli`, `StyrofoamMakanan`, `AquaBottle_600ml`, `AquaGalon_19L` *(plus `SandalSwallow`, `PopMieCup`, `KresekBag`, `KasurKapuk`, `BanBekas`, `EcengGondok`, `BatangPisang`)* | Safe to scoop; sort at **`Bank Sampah Berkah`** (`4,000 IDR`). |
| **`Medical`** | `PF_Trash_MedicalBag`, `PF_Trash_SyringeBox` (yellow + red B3 markings) | **Pickup Prick Hazard**: Any tool can scoop, but lower tools risk `-18 HP` needle pricks (`0%` once **`#10 Capitan Ular`** milestone is unlocked). Sort at **`Pos Medis B3`** (`9,000 IDR` + `+10 HP`). |
| **`Biohazard`** | `PF_Trash_BiohazardDrum` / `RadioactiveBarrel` (runtime fallback; purple/lime glow) | **Cargo DoT Hazard**: Deals escalating Damage Over Time if held past `10s` grace period. Sort at **`Karantina Biohazard`** (`14,000 IDR`). |

---

## 5. Three Meaningful Player Choices & Five Endings

1. **Choice A — 3 Dedicated Stations vs. `Gudang Pengepul` Shortcut**:
   - Routing `Normal` $\to$ `Bank Sampah`, `Medical` $\to$ `Pos Medis B3`, and `Biohazard` $\to$ `Karantina Biohazard` (`1/2/3/E`) pays full Rupiah and builds Trust (wrong-station discards incur Rupiah fines!).
   - Dumping everything in one go at **`Gudang Pengepul`** (near Spawn) pays cheaper rates (`2k/3k/4.5k`) with **no fine**, but inflicts severe Community Trust / SDG penalties if hazardous cargo is mixed in.
2. **Choice B — Personal Vessel vs. Upstream `Kampung Bins` (`30,000 IDR`)**:
   - Skipping prevention keeps upstream shedding relentless; buying `Kampung Bins` cuts upstream shedding ~60% (spawn interval x2.5) and the `Trash Boom` slows downstream drift along `Trash Boom Timur` and pays passive Rp 2.500 / 4 s.
3. **Choice C — Monsoon `Sell-Lock` Crisis & 5 Endings**:
   - **`TrueSdgVictory`**: Reach **`0% Gunung Sampah`** (`CompleteCleanBreach()` or survive countdown with `gunungSampahHealth <= 0.01f`) without fatal flood or `0 HP` death.
   - **`PartialSurvival`**: Survive the 5-minute Monsoon Countdown with `Gunung Sampah` still intact (`> 0.01f`).
   - **`CompromisedOceanFlush`**: Panic-open the floodgate (`TriggerEmergencyFlush(confirmed: true)` during Sell-Lock). Saves Kampung from flooding, but flags **SDG 14.1 Failed**.
   - **`FloodFail`**: `waterLevelY >= 2.45m` (`+1.05m` over bank top) floods Kampung Hulu fatally.
   - **`HealthFail`**: `playerHealth <= 0` from repeated `Medical` needle pricks, untreated `Biohazard` Cargo DoT, or **drowning** after exhausting `swimStamina`.
