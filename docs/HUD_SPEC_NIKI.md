# KALI: Desktop HUD Implementation Spec (`Canvas_HUD`)

> **Target Owner**: Nicholas Gerwin Mawardji (Niki) (`unity/Assets/_Project/UI/`)
> **Approved Visual Direction**: **Lembar Kalkir Zona Cahaya** (Backlit Translucent Vellum Field Sheets)
> **Target Resolutions**: `1920x1080` (Primary Desktop 16:9) & `1280x720` (Sidang Projector Minimum)
> **Language**: 100% Bahasa Indonesia
> **Interactive Reference Preview**: Open `docs/hud_reference_lembar_kalkir.html?preview=1` in Chrome/Safari to inspect spacing, typography, colors, and toggle between **Normal (Golden Pagi)**, **Dock Stasiun (B)**, and **Krisis Monsun (Siaga 1)**.

---

## 1. Visual Identity & Why We Replaced the Previous Mockup

The rejected draft used dark-navy SaaS dashboard cards (`#0F172A`, `rounded-2xl`, rainbow gradient HP bar, neon purple center pill, permanent WASD keybind strip, and a bottom-left `#05 Gayung Mandi` card that contradicted `ToolCatalog.cs` where `#02` is `Gayung Mandi` and `#05` is `Ember Cat 5L`). It also displayed `SIAGA 3 +0.84m` at the same time as `Jual dikunci (air >= 1.85m)` and omitted `Gunung Sampah`, crosshair, and river minimap.

**Lembar Kalkir Zona Cahaya** fixes every single one of those flaws with a distinctive Indonesian hydrographic field-sheet identity built around four strict rules:

1. **Backlit Vellum Neutrals (11-Step Zone Ramp)**: Translucent warm paper sheets (`#F4F2EC` at `90%` alpha) with crisp `1px` charcoal borders (`#1E1F1D`) and delicate translucent masking-tape pins. Ink on Zone X paper exceeds **12:1 contrast** across both bright Golden Morning sunbeams and dark Monsoon rain.
2. **One Dichroic Alert Accent (`#E11D8F`)**: Used exclusively for active danger filtration (`SIAGA 1`, Biohazard 10s timer, Sell-Lock conflict, wrong-station `DENDA` stamps, and the Dam choke zone on the contour map). Never used as decorative chrome.
3. **Hatch Grammar**:
   - **45-degree charcoal hatch** = active load (`GUNUNG SAMPAH %`).
   - **90-degree magenta cross-hatch** = active conflict (`DENDA` slots, `JUAL DIKUNCI >= +1.85m`, `Biohazard DoT`).
   - **Cleared light paper windows**: Hatching always halts cleanly behind a solid `#F4F2EC` text box so every Bahasa Indonesia word and numeral remains sharp at `1280x720`.
4. **Wide-Open Desktop Viewport**: Center `>68%` playfield is completely unobstructed. **Bottom-left and bottom-center remain completely empty during open navigation** (preserving 3D sampan visibility and reserving bottom space for future tools/inventory slots; the station dock sheet slides in at bottom-center only while inside a station trigger collider).

---

## 2. Color & Typography Token Table

| Token | Hex | Alpha | Usage in `Canvas_HUD` |
|---|---|---|---|
| `Zone X (Vellum Ground)` | `#F4F2EC` | `90%` (`230`) | Main translucent panel backgrounds & cleared text windows (`100%`) |
| `Zone VIII (Inset Track)` | `#DCDAD2` | `100%` | Unfilled HP cells, river channel fill on contour map |
| `Zone IV (Rule & Label)` | `#54534E` | `100%` | Secondary uppercase micro-labels (`KAS`, `AIR`, `MUATAN`, `WARGA`, 6.6:1 AA) |
| `Zone I (Primary Ink)` | `#1E1F1D` | `100%` | Borders (`1px`), primary headings, contour lines, ruler ticks |
| `Zone 0 (Solid Inverted)` | `#111211` | `100%` | Active primary station keycap (`[1] NORMAL`), player chevron, `[Q]` keycap |
| `Dichroic Alert (Text/Badge)` | `#B50E6F` | `100%` | `SIAGA 1`, Biohazard countdown, `DENDA` text & solid pill fill (5.8:1 AA) |
| `Dichroic Alert (Hatch/Line)` | `#E11D8F` | `100%` / `14%` tint | 90-deg cross-hatch lines & active conflict borders |
| `River Teal (Bar / Ink)` | `#1B8A7A` / `#0F665A` | `100%` | `#1B8A7A` fill bar, `#0F665A` WCAG AA label ink (5.7:1 AA), sightline cone (`20%`) |
| `Siaga Amber` | `#B45309` | `100%` | `SIAGA 3 / 2` indicator dot & water-gauge ruler needle |
| `Cargo Normal` | `#15803D` | `100%` | `Normal` slot top-border (`3px`) & `B` station seal |
| `Cargo Medis B3` | `#A14A06` | `100%` | `Medis B3` slot top-border (`3px`) & `M` station seal |
| `Cargo Biohazard` | `#B50E6F` | `100%` | `Bio` slot top-border (`3px`) & `K` station seal |

### TextMeshPro Font Setup
- **Display / Headers & Big Numerals**: `Barlow Condensed` (Bold `700` & SemiBold `600`, free SIL OFL Google Font). Use for `Rp 1.250.000`, `HP 72`, `SIAGA 3`, `GUNUNG SAMPAH`, `KEJERNIHAN`.
- **Tabular Telemetry & Micro-Labels**: `IBM Plex Mono` (SemiBold `600` & Bold `700`, free SIL OFL). Wrap live changing counters (`+0.84m`, `04:37`, `14 / 22`, `64%`) in `<mspace=0.62em>...</mspace>` so digits never jitter horizontally during `10 Hz` `OnStateChanged` updates.

---

## 3. Unity `Canvas_HUD` Setup & RectTransform Layout

### Root Canvas Configuration
- **Render Mode**: `Screen Space - Overlay` (`Sort Order = 10`, below `Canvas_ShopBankSampah` at `20` and `Canvas_SDGImpactReport` at `30`).
- **Canvas Scaler**: `Scale With Screen Size`
  - **Reference Resolution**: `1920 x 1080`
  - **Screen Match Mode**: `Match Width Or Height`
  - **Match**: `0.5` (guarantees balanced readability at both `1920x1080` and `1280x720`).
- **Outer Safe Margin**: `36px` horizontal, `32px` vertical (at `1920x1080` reference).

### GameObject Hierarchy & Anchor Coordinates

```text
Canvas_HUD (CanvasScaler: 1920x1080, Match 0.5)
├── TL_SurvivalFloodSheet        [Anchor: Top-Left (0,1), Pivot (0,1), Pos (36, -32), Size 342x134]
│   ├── TapePin_Top              [Image, translucent #FFFDF5 62%, Rot Z +1.5deg]
│   ├── Row_HP                   [HorizontalLayoutGroup: TMP_HPValue + 10-cell ZoneRamp Grid]
│   └── Row_SiagaWater           [TMP_SiagaLevel + Img_FiltrationDot + TMP_WaterMeters + RulerNeedle]
├── TL_ToolUnlockToast           [Anchor: Top-Left (0,1), Pos (36, -184), Size 342x58, Inactive at rest]
├── TC_EcologicalHydroRail       [Anchor: Top-Center (0.5,1), Pivot (0.5,1), Pos (0, -32), Size 780x76]
│   ├── Cell_GunungSampah        [TMP "GUNUNG SAMPAH" + TMP "64%" + 45-deg Tiled Hatch Fill]
│   ├── Cell_Kejernihan          [TMP "KEJERNIHAN" + TMP "61%" + Solid River Teal Fill]
│   └── Cell_MonsunTimer         [TMP "MONSUN" / "BADAI" + TMP "04:37" tabular mono]
├── TC_ContextualAlertRail       [Anchor: Top-Center (0.5,1), Pos (0, -118), Width 780, VerticalLayoutGroup]
│   ├── Strip_BiohazardTimer     [90-deg Magenta Cross-Hatch + Cleared #F4F2EC Text Box + Countdown]
│   └── Strip_SellLockDump       [90-deg Magenta Cross-Hatch + Cleared Box "AIR >= +1.85m · [Q] BUANG"]
├── TR_EconomyCargoLedger        [Anchor: Top-Right (1,1), Pivot (1,1), Pos (-36, -32), Size 326x202]
│   ├── Row_KasRupiah            [TMP "KAS" + TMP "Rp 1.250.000"]
│   ├── Row_MuatanHeader         [TMP "MUATAN" + TMP "14 / 22"]
│   ├── Grid_Cargo3Class         [3-Col Grid: Normal (#15803D) / Medis B3 (#B45309) / Bio (#B81776)]
│   └── Row_WargaTrust           [TMP "KEPERCAYAAN WARGA" + TMP "68"]
├── C_CrosshairReticle           [Anchor: Center (0.5,0.5), Size 24x24, 4x 7x2 ticks + 4px center dot]
├── BC_StationDockSheet          [Anchor: Bottom-Center (0.5,0), Pivot (0.5,0), Pos (0, 34), Size 660x104, HIDDEN AT REST]
│   ├── Header_StationName       [TMP "STASIUN: BANK SAMPAH BERKAH (B)" / "DERMAGA: ..." + Accepted Subtitle]
│   └── Row_ActionKeys           [4-Col Grid: [1] Normal | [2] Medis B3 | [3] Biohazard | [E] Setor Aman / Naik-Turun Sungai]
└── BR_VellumHydroMap            [Anchor: Bottom-Right (1,0), Pivot (1,0), Pos (-44, 38), Size 372x276, Rot Z +2.5deg]
    ├── TapePin_TL / TapePin_BR  [Translucent masking tape strips rotated 38deg]
    ├── Img_ContourCanalBase     [Static high-res sprite of river contour lines + "+Z" arrow]
    ├── Img_DamChokeCrossHatch   [Magenta 90-deg cross-hatch circle + TMP "DAM 64%"]
    ├── Pin_B / Pin_M / Pin_K / Pin_P / Pin_KD [4 solid discard hub seals + 1 outline Koperasi Desa (Kopdes) seal]
    └── Icon_PlayerSampan        [Live chevron + 20% teal sightline cone mapped to player world X/Z]
```

> **Bottom-Left & Bottom-Center Reservation Rule**: Keep the bottom-left completely empty at all times. Keep `BC_StationDockSheet` disabled (`CanvasGroup.alpha = 0`) unless the player is inside a station trigger zone. This guarantees clean screen space for future tool/inventory slots without rewriting the HUD layout.

---

## 4. Exact C# Event Wiring (`RiverGameManager.Instance`)

Subscribe in `OnEnable()` and unsubscribe in `OnDisable()` inside `unity/Assets/_Project/UI/Scripts/KaliHudController.cs` (do **not** poll gameplay fields inside `Update()` except smooth minimap chevron interpolation at `15 Hz`):

| HUD Module | Event Source | Exact `RiverGameManager` Properties Read | Visual Rule / State Trigger |
|---|---|---|---|
| `TL_SurvivalFloodSheet` | `OnStateChanged` | `playerHealth`, `maxPlayerHealth`, `swimStamina`, `maxSwimStamina`, `IsSwimming`, `IsDrowning`, `SiagaLevel`, `currentWaterLevelY` | Fill `Mathf.RoundToInt((playerHealth / maxPlayerHealth) * 10)` Zone Ramp cells; turn filled cells `#E11D8F` when `playerHealth <= 40` or `IsDrowning`. Show swim stamina gauge while `IsSwimming` or recovering (`#1B8A7A` -> `#B45309` <= 25% -> `#E11D8F` drowning). Move ruler needle across `[-0.25m .. 2.45m]`. Filtration dot: `#15803D` (`Siaga 4`), `#C97A0A` (`Siaga 3`), `#EA580C` (`Siaga 2`), `#E11D8F` (`Siaga 1`). |
| `TC_EcologicalHydroRail` | `OnStateChanged`, `OnWeatherChanged` | `gunungSampahHealth` (`0..1`), `waterClarity` (`0..1`), `monsoonCountdownRemaining`, `isMonsoonStorm` | `GUNUNG SAMPAH` displays `Mathf.RoundToInt(gunungSampahHealth * 100f) + "%"`. `KEJERNIHAN` displays `Mathf.RoundToInt(waterClarity * 100f) + "%"`. Format timer `MM:SS`; switch label from `MONSUN` to `BADAI` + magenta cell tint when `isMonsoonStorm == true`. |
| `TC_ContextualAlertRail` | `OnStateChanged`, `OnHazardOrAlert` | `biohazardCargo`, `IsBiohazardDotActive`, `BiohazardGraceRemaining`, `IsSellLocked` (`currentWaterLevelY >= 1.85f`), `IsDrowning` | **Never show Sell-Lock when `currentWaterLevelY < 1.85f`!** Show `Strip_BiohazardTimer` ONLY when `biohazardCargo > 0`. Show `Strip_SellLockDump` ONLY when `IsSellLocked == true`. Surface drowning / low-stamina / wrong-station fine alerts from `OnHazardOrAlert`. |
| `TR_EconomyCargoLedger` | `OnStateChanged` | `rupiah`, `cargoCount`, `cargoCapacity`, `normalCargo`, `medicalCargo`, `biohazardCargo`, `communityTrust` | Format Rupiah with Indonesian thousand separators (`"Rp " + rupiah.ToString("N0", idCulture)`). Show `"{cargoCount} / {cargoCapacity}"` and highlight magenta if `cargoCount >= cargoCapacity`. |
| `TL_ToolUnlockToast` | `OnToolUnlocked(ToolDefinition)` | `tool.Index`, `tool.DisplayName`, `tool.UnlockRupiah`, `tool.GunungDamagePerSwing` | Slide in from `scale 0.97, alpha 0` over `220ms`, hold `3.5s`, fade out. Announces Kopdes purchase availability (`"Alat Baru Tersedia di Kopdes: #XX ..."` — bought via `BuyTool(int)`, no free auto-equip). Show `"BISA KERUK"` badge when `tool.GunungDamagePerSwing > 0f` (`#13+`). |
| `BC_StationDockSheet` | Pier/Hub Trigger (`OnNearbyHubChanged`, `OnNearbyDermagaChanged`) + `OnStateChanged` | Active station (`Bank Sampah`, `Pos Medis B3`, `Karantina Biohazard`, `Gudang Pengepul`), `Koperasi Desa (Kopdes)`, or `Dermaga` | Illegal classes receive **90-deg magenta cross-hatch** + `"DENDA"` label. Legal class gets **inverted Zone-0 (`#111211`)** (`[E]` = safe `DiscardLegalAtStation`). At `Gudang Pengepul`, show `[E] JUAL SEMUA`. At `Kopdes`, show `[E] BUKA KOPDES` (`BuyTool`, upgrades). At `Dermaga` (exclusive boat port), show `[E] NAIK PERAHU` / `[E] TURUN KE DARAT`. |
| `BR_VellumHydroMap` | `LateUpdate` (throttled `15 Hz`) + `OnStateChanged` | Player `Transform.position` (`x, z`) & `eulerAngles.y`, `gunungSampahHealth` | Map river bounds (`zMin..zMax`) linearly to contour spline Y; rotate player chevron by `eulerAngles.y`; update `DAM XX%` label inside magenta cross-hatch circle. |

---

## 5. Unity Implementation Notes & Animation Standards

1. **Sprite Creation (3 Minimal Assets)**:
   - `UI_Vellum9Slice.png`: `64x64` warm `#F4F2EC` box with crisp `1px` `#1E1F1D` border (`9-slice` borders `4,4,4,4`).
   - `UI_Hatch45_Tile.png` (`32x32`, Repeat Wrap Mode): seamless 45-degree charcoal hatch lines (`RawImage` UV tiling for `GUNUNG SAMPAH` fill bar).
   - `UI_CrossHatch90_Magenta.png` (`32x32`, Repeat Wrap Mode): seamless 90-degree `#E11D8F` cross-hatch for conflict strips & `DENDA` buttons.
2. **Motion Discipline**:
   - Contextual panels (`TL_ToolUnlockToast`, `TC_ContextualAlertRail`, `BC_StationDockSheet`) enter from `scale = 0.97, alpha = 0` to `scale = 1.0, alpha = 1` over `180ms` (`EaseOutCubic`). Never pop from `scale = 0`.
   - Wrong-station fine feedback shakes the offending key slot horizontally (`0, -10, 10, -6, 6, -3, 0px` over `360ms`) and flashes magenta.
3. **1280x720 Verification Gate**:
   - Before committing `Canvas_HUD.prefab`, switch Unity Game View between `1920x1080` and `1280x720` in both Normal and Crisis (`F9 + 3`) states and confirm zero overlapping RectTransforms and crisp legible numerals.

---

## 6. Reference Visuals Included in `docs/`

- `docs/kali_hud_final_1920x1080_normal.png` (Act 2 Golden Morning Normal, `1920x1080`)
- `docs/kali_hud_final_1280x720_normal.png` (Act 2 Golden Morning Normal, `1280x720` scaling check)
- `docs/kali_hud_final_1920x1080_crisis_and_dock.png` (Act 3 Monsoon `SIAGA 1 +1.92m`, Biohazard Timer, Sell-Lock `[Q]`, `#13` Unlock Toast & `Bank Sampah Berkah` Dock)
- `docs/kali_hud_architecture_blueprint.png` (`2400x1500` Safe-Zone, Anchor, Hierarchy, Event Contract & Token Blueprint)
- `docs/hud_reference_lembar_kalkir.html` (Interactive browser reference; append `?preview=1` to switch states live)
