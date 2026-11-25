# AI Implementation Plan: Niki (VFX, UI & Audio/Narrative Lead)

> **Instructions for AI**: You are the dedicated AI Unity VFX, UI & Audio assistant for **Nicholas Gerwin Mawardji (Niki)** on **KALI: Indonesian River Sweeper** (`Unity 2022.3.46f1 LTS URP`). Work strictly inside `VFX/`, `UI/`, and `Audio/`. Read Ivan's C# event signatures in `RiverGameManager.cs` before wiring any Canvas or Particle script so UI and VFX subscribe cleanly with zero merge conflicts.

---

## 1. Identity & Scope Boundaries

- **Owner**: Nicholas Gerwin Mawardji (Niki)
- **Student ID**: `0706012410015`
- **Track**: URP VFX Systems, uGUI / TextMeshPro Interfaces, Audio Design & Sidang Demo Flow
- **Primary Deliverables**:
  1. 4 VFX prefabs inside `Assets/_Project/VFX/`: `VFX_MonsoonRain`, `VFX_WaterSplashMuddy`, `VFX_MethaneSludgeBubbles`, `VFX_TrashAvalanche`.
  2. 3 Responsive UI Canvases inside `Assets/_Project/UI/`: `Canvas_HUD`, `Canvas_ShopBankSampah`, `Canvas_SDGImpactReport`.
  3. River/storm/siren/scoop audio clips & mixer triggers (`Assets/_Project/Audio/`).
  4. Polished 3-minute Sidang live presentation script aligned to `F9 + 1..4` demo jumps.

### Allowed Files & Directories (READ & WRITE)
- `unity/Assets/_Project/VFX/**`
- `unity/Assets/_Project/UI/**` (including UI glue scripts inside `UI/Scripts/` subscribing to `RiverGameManager.Instance`)
- `unity/Assets/_Project/Audio/**`

### Strictly Forbidden (DO NOT MODIFY OTHER FOLDERS)
- `unity/Assets/_Project/Scripts/**`, `Data/**` *(Owned by Ivan — subscribe via public events only)*
- `unity/Assets/_Project/Props/**`, `Rigging/**`, `Lighting/**` *(Owned by JC)*
- `unity/Assets/_Project/Environment/**`, `Shaders/**` *(Owned by Wesley)*

### Context Files to Read
1. `AGENTS.md` (Public C# event signatures in `RiverGameManager.cs`)
2. `docs/DESIGN.md` (Exact `Siaga 4 -> 1` alert colors `#22C55E`, `#FACC15`, `#F97316`, `#F43F5E`, glass HUD surface `#0F172A`)
3. `docs/PRD.md` (3 Choices, Medical Biohazard feedback, 3 Endings, SDG targets 6.3 / 11.5 / 14.1)

---

## 2. Public C# Event Contracts (`RiverGameManager.Instance`)

Your UI & VFX components subscribe cleanly to these public members in `RiverGameManager`:
- `OnStateChanged` (`Action`): Refresh HUD metrics whenever player scoops trash, trades at Bank Sampah, secures/drops Medical Waste, upgrades tiers, or flood pressure ticks.
  - Readable fields: `rupiah`, `cargoCount`, `cargoCapacity`, `waterClarity`, `floodPressure`, `SiagaLevel` (`4..1`), `gunungSampahHealth`, `communityTrust`, `medicalWasteSecured`, `infectionIncidents`, `galahUnlocked`, `sampanUnlocked`, `trashBoomActive`, `excavatorUnlocked`, `kampungBinsInstalled`.
- `OnWeatherChanged` (`Action<bool isMonsoonStorm>`): Enables/disables `VFX_MonsoonRain` and storm ambient sound.
- `OnEndingTriggered` (`Action<GameEnding ending>`): Displays `Canvas_SDGImpactReport` tailored to `TrueSdgVictory`, `CompromisedOceanFlush`, or `FloodFail` using `recycledKg`, `flushedKg`, `medicalWasteSecured`, and `communityTrust`.

---

## 3. Step-by-Step Task Checklist

- [ ] **Task 1: 4 URP VFX Systems (`Assets/_Project/VFX/`)**
  - [ ] `VFX_MonsoonRain`: Camera-follow heavy raindrop streaks + surface ripple spawn; toggles via `OnWeatherChanged`.
  - [ ] `VFX_WaterSplashMuddy`: One-shot dirty water droplet burst triggered when player scoops trash or paddles boat.
  - [ ] `VFX_MethaneSludgeBubbles`: Looping green-brown gas bubbles rising & popping at `Trash Piles` and `Gunung Sampah`.
  - [ ] `VFX_TrashAvalanche`: Heavy debris dust/splash cascade triggered when `DamageGunungSampah()` breaks a dam tier.

- [ ] **Task 2: HUD, Bank Sampah Shop & SDG Impact Report (`Assets/_Project/UI/`)**
  - [ ] `Canvas_HUD`: Corner-anchored translucent dark panels (`#0F172A` 85% alpha) leaving center 70% clear:
    - Top-Left: Flood Meter **`SIAGA 4 -> 1`** using `docs/DESIGN.md` hexes (`#22C55E` -> `#FACC15` -> `#F97316` -> `#F43F5E`) + `waterClarity` %.
    - Top-Right: `Rupiah (IDR)`, `Cargo count/max`, `Community Trust`, & `Medical Hazard / Infection` indicator.
    - Bottom: Compact active Tool Slot & Vessel badge + quick controls hint (`WASD`, `E` Interact/Boat, `LMB` Scoop, `R` Weather, `F` FreeCam).
  - [ ] `Canvas_ShopBankSampah`: Choice A buttons (**Burn Pit** `DumpAtBurnPit()` vs **Bank Sampah Sort** `SellAtBankSampah(true)`), Choice B upgrades (**`BuyKampungBins()`**, `BuyUpgrade(UpgradeTier)`), Choice C emergency floodgate warning (**`TriggerEmergencyFlush()`**).
  - [ ] `Canvas_SDGImpactReport`: Victory/Ending modal summarizing recycled vs flushed kg, Medical Waste B3 secured, Flood prevented status, and **SDG 6.3 / 11.5 / 14.1** educational verdict.

- [ ] **Task 3: Audio & 3-Minute Sidang Presentation Flow (`Assets/_Project/Audio/`)**
  - [ ] Add looping calm river vs heavy monsoon storm SFX, wet scoop splashes, metallic winch clanks, warning siren on `Siaga 2/1`, and Biohazard alert chime.
  - [ ] Coordinate the 3-minute Sidang demo script synchronized to `F9 + 1`, `F9 + 2`, `F9 + 3`, `F9 + 4`.

---

## 4. Verification & Live Sidang Talking Points
- Test every UI panel at `1920×1080` and `1280×720` with zero overlapping text.
- Be ready to explain VFX particle emission/collision parameters, how C# events drive the `Siaga` warning feedback without polling every frame, and how `Canvas_SDGImpactReport` proves SDG consequences (**10% Problem & Message + 10% Presentation**).
