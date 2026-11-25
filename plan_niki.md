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
3. `docs/PRD.md` (3 Choices, 3-class waste hazards, 3 stations vs Pengepul, Sell-Lock/`Q` dump, 4 Endings, SDG targets 6.3 / 11.5 / 14.1)

---

## 2. Public C# Event Contracts (`RiverGameManager.Instance`)

Your UI & VFX components subscribe cleanly to these public members in `RiverGameManager`:
- `OnStateChanged` (`Action`, throttled ~10 Hz on continuous ticks): Refresh HUD metrics whenever player scoops trash, trades/gets fined at stations, suffers Medical prick or Biohazard DoT, unlocks tools, or flood level changes.
  - **Health & Hazards**: `playerHealth` / `maxPlayerHealth` (`0..100`), `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `infectionIncidents`.
  - **3-Class Cargo & Economy**: `rupiah`, `cumulativeEarnings`, `cargoCount` / `cargoCapacity`, `normalCargo`, `medicalCargo`, `biohazardCargo`, `wrongDiscardCount`, `totalFinesPaid`, `pengepulHazardDumped`.
  - **Linear Water Rise & Monsoon**: `currentWaterLevelY` (`-0.25m` to `2.45m+`), `IsBankOverflowing` (`>= 1.40m`), `IsSellLocked` (`>= 1.85m`), `floodPressure`, `SiagaLevel` (`4..1`), `waterClarity`, `gunungSampahHealth`, `monsoonCountdownRemaining` (`MM:SS` timer), `communityTrust`, `medicalWasteSecured`, `biohazardWasteSecured`.
  - **Tools & Unlocks**: `equippedToolIndex` (`1..20`), `highestUnlockedToolIndex` (`1..20`), `EquippedTool`, `galahUnlocked`, `sampanUnlocked`, `trashBoomActive`, `excavatorUnlocked`, `kampungBinsInstalled`.
- `OnToolUnlocked` (`Action<ToolDefinition>`) & `OnEquippedToolChanged` (`Action<ToolDefinition>`): Drive auto-unlock celebration toasts (`#01..#20`) and bottom tool badge updates.
- `OnHazardOrAlert` (`Action<string msg, bool isDanger>`): Show immediate red/purple warning banner on Medical needle prick, Biohazard DoT, wrong-station fine, or Sell-Lock block.
- `OnWeatherChanged` (`Action<bool isMonsoonStorm>`): Enables/disables `VFX_MonsoonRain` and storm ambient sound.
- `OnEndingTriggered` (`Action<GameEnding ending>`): Displays `Canvas_SDGImpactReport` tailored to **`TrueSdgVictory`**, **`CompromisedOceanFlush`**, **`FloodFail`**, or **`HealthFail`** using `recycledKg`, `flushedKg`, `medicalWasteSecured`, `biohazardWasteSecured`, `totalFinesPaid`, `pengepulHazardDumped`, and `communityTrust`.

---

## 3. Step-by-Step Task Checklist

- [ ] **Task 1: 4 URP VFX Systems (`Assets/_Project/VFX/`)**
  - [ ] `VFX_MonsoonRain`: Camera-follow heavy raindrop streaks + surface ripple spawn; toggles via `OnWeatherChanged`.
  - [ ] `VFX_WaterSplashMuddy`: One-shot dirty water droplet burst triggered when player scoops trash or paddles boat.
  - [ ] `VFX_MethaneSludgeBubbles`: Looping green-brown gas bubbles rising & popping at `Trash Piles` and `Gunung Sampah`.
  - [ ] `VFX_TrashAvalanche`: Heavy debris dust/splash cascade triggered when `DamageGunungSampah()` breaks a dam tier.

- [ ] **Task 2: HUD, Station Prompts, Shop & SDG Impact Report (`Assets/_Project/UI/`)**
  - [ ] `Canvas_HUD`: Corner-anchored translucent dark panels (`#0F172A` 85% alpha) leaving center 70% clear:
    - Top-Left: **`playerHealth` (`HP`) bar**, Flood Meter **`SIAGA 4 -> 1`** + linear water height (`+X.XXm`), `waterClarity` %, and **Monsoon Countdown timer** (`MM:SS`).
    - Top-Right: `Rupiah (IDR)`, **3-class Cargo readout** (`Normal / Medical / Biohazard`), `Community Trust`, & `Medical / Biohazard` hazard counters.
    - Center Top Alert Banners: **Biohazard DoT Countdown / Active Alert** (`Karantina before DoT!`), **Overflow Banner**, and **Sell-Lock Banner** (`isSellLocked`) with explicit **`[Q] Dump Cargo on High Ground`** hint & Emergency Flush option.
    - Center Bottom Context Prompt: **Station Quick-Discard Prompt** (`[1] Normal [2] Medis [3] Biohazard [E] Discard All` with fine warnings, vs `[E] Gudang Pengepul`).
    - Bottom: Compact **Active Tool Slot** (`#01..#20` + **auto-unlock toast** on `OnToolUnlocked`), Vessel badge, and quick controls (`WASD`, `LMB`, `1/2/3/E`, `Q`, `Scroll/[ ]`, `R`, `F`).
  - [ ] `Canvas_ShopBankSampah`: Station quick-discard buttons (`DiscardWasteAtStation` / `DiscardAllAtStation`), `Gudang Pengepul` bulk dump (`SellAllAtPengepul`), Choice B upgrades (**`BuyKampungBins()`**, `BuyUpgrade(UpgradeTier)`), 20-tool unlock milestone viewer (`SelectTool`), and Choice C emergency floodgate (`TriggerEmergencyFlush()`).
  - [ ] `Canvas_SDGImpactReport`: Victory/Ending modal handling all **4 endings** (`TrueSdgVictory`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`), summarizing recycled vs flushed kg, Medical/Biohazard secured, wrong-station fines, Pengepul hazard dumps, and **SDG 6.3 / 11.5 / 14.1** educational verdict.

- [ ] **Task 3: Audio & 3-Minute Sidang Presentation Flow (`Assets/_Project/Audio/`)**
  - [ ] Add looping calm river vs heavy monsoon storm SFX, wet scoop splashes, needle-prick/Biohazard Geiger warning chime, wrong-station fine buzzer, tool unlock chime, and `Siaga 2/1` siren.
  - [ ] Coordinate the 3-minute Sidang demo script synchronized to `F9 + 1`, `F9 + 2`, `F9 + 3` (Monsoon Overflow + Sell-Lock), `F9 + 4`.

---

## 4. Verification & Live Sidang Talking Points
- Test every UI panel at `1920×1080` and `1280×720` with zero overlapping text.
- Be ready to explain VFX particle emission/collision parameters, how C# events drive the `Siaga` warning feedback without polling every frame, and how `Canvas_SDGImpactReport` proves SDG consequences (**10% Problem & Message + 10% Presentation**).
