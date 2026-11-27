# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- Primary players: Indonesian university students, indie desktop gamers, and academic Computer Graphics (IMT01303501 ALP) jurors evaluating gameplay and visual craft during a 3-minute live desktop demo.
- Internal builders: 4-person student team (Ivan on Core C#, JC on Blender low-poly props/rigging/lighting, Wesley on environment & URP shaders, Niki on Unity uGUI/TextMeshPro HUD, VFX, and audio).

## Product Purpose

KALI: Indonesian River Sweeper is a first-person desktop river-cleanup simulation and crisis management game set along a tropical Indonesian urban river (Kalimas Nusantara). Players scoop three distinct waste classes drifting downstream (+Z), sort them at dedicated waste stations (or dump cheaply at Gudang Pengepul at the cost of community trust), manage linear flood water rise across Siaga 4 to Siaga 1 thresholds, auto-unlock 20 authentic Indonesian scavenging tools, and dismantle an upstream Gunung Sampah before monsoon flooding submerges the village.

## Positioning

Unlike generic casual cleaning simulators or sci-fi HUDs, KALI grounds every mechanic in recognizable Indonesian municipal flood control (Pintu Air Siaga 4 to Siaga 1, Bank Sampah, Pos Medis B3, Karantina Biohazard, Gudang Pengepul, and authentic local tools from Sendok Makan Bengkok and Gayung Mandi up to Capitan Ular and an Amphibious Excavator) tied directly to SDG 6.3, 11.5, and 14.1 outcomes.

## Operating Context

- Primary runtime: Unity 2022.3.46f1 LTS (URP) desktop game rendered at 1920x1080 and 1280x720 (16:9), plus standalone Three.js browser prototype (`tools/play-3d.html`).
- Live game art style: Flat-faceted stylized low-poly 3D assets built in Blender 5.3.0 (verified `SK_ExcavatorAmfibi`, 20 `SM_Tool_*` meshes, `SM_Trash_MedicalBag`, `SM_Trash_SyringeBox`) under warm tropical Golden Hour (`3400K`) transitioning to dark Monsoon Storm overcast (`#334155`).
- Live HUD events come exclusively from `RiverGameManager.Instance` (`OnStateChanged` ~10 Hz, `OnToolUnlocked`, `OnEquippedToolChanged`, `OnHazardOrAlert`, `OnWeatherChanged`, `OnEndingTriggered`).

## Capabilities and Constraints

- Language: Full Bahasa Indonesia UI copy across the HUD.
- Mandatory live HUD elements confirmed by owner:
  - Top-center Gunung Sampah progress bar with percentage (`0%` to `100%`).
  - Center crosshair / reticle for first-person scooping and dredging.
  - Compact tactical river minimap (`+Z` downstream flow, stations, player orientation).
  - Live vital & flood telemetry: `playerHealth` (`HP`), `SiagaLevel` (`SIAGA 4` to `SIAGA 1`), linear `currentWaterLevelY` (`-0.25m` baseline, `+1.40m` overflow, `+1.85m` sell-lock, `+2.45m` fatal), `waterClarity` (`%`), and `monsoonCountdownRemaining` (`MM:SS`).
  - Economy & 3-class cargo: `rupiah` (`Rp`), `cargoCount / cargoCapacity` broken down by `Normal`, `Medis`, and `Biohazard`, `communityTrust` (`0-100`), active vessel (`Rakit Gabus`, `Sampan Kayu`, `Excavator Amfibi`), and active tool (`#01` to `#20` from `ToolCatalog.cs` with real `MedicalPrickChance`).
  - Contextual-only prompts & alerts: station discard prompt (`[1]` Normal, `[2]` Medis, `[3]` Biohazard, `[E]` Semua + real fine warning) visible only near a station; emergency banners (`Biohazard DoT` 10s grace timer, `Jual Dikunci` >= `+1.85m` with `[Q] Buang di Daratan Tinggi`, tool unlock toast) appearing only when active and never in contradictory states.
- Center ~70% of the 16:9 viewport must remain clear for first-person aiming and river visibility.
- Must translate cleanly to Unity uGUI + TextMeshPro (`Canvas Scaler` Scale With Screen Size `1920x1080`, `match = 0.5`) for Niki to implement without custom shaders required on UI elements.

## Brand Commitments

- Authentic Indonesian river cleanup identity ("Kalimas Nusantara"), rejecting generic dark-navy SaaS dashboard card aesthetics.
- Status colors must never rely on color alone: every `SIAGA 4` to `SIAGA 1` state and waste class (`Normal`, `Medis B3`, `Biohazard`) pairs distinct color with explicit Bahasa Indonesia labels and unmistakable shapes/icons.
- Exact data truth from `ToolCatalog.cs` and `RiverGameManager.cs` (for example `#02 Gayung Mandi`, `#05 Ember Cat 5L`, `#10 Capitan Ular`).

## Evidence on Hand

- Live C# core state machine & contracts: `unity/Assets/_Project/Scripts/Core/RiverGameManager.cs`, `ToolCatalog.cs`, `RiverFlowBuoyancy.cs`, `Player/KaliPlayerController.cs`.
- 53-node river layout: `unity/Assets/_Project/Data/kali-river-map.json`.
- Verified Blender 5.3.0 low-poly renders (`docs/jc_excavator_lowpoly_render.png`, `docs/jc_20_tools_lowpoly_render.png`, `docs/jc_tier0_tools_closeup.png`, `docs/jc_trash_b3_lowpoly_render.png`).
- Existing art tokens: `docs/DESIGN.md`.
- Anti-reference: Claude's SaaS-card HUD mockup (`uploaded_media_1795677964354.jpg`) exhibiting dark rounded-card dashboard slop, contradictory alerts, wrong tool index `#05 Gayung Mandi`, and cluttered permanent keycap chips.

## Product Principles

1. Peripheral clarity first: keep the river sightline and crosshair unobstructed; move telemetry to disciplined screen edges.
2. Crisis escalation is physical, not noisy: water level, Siaga severity, and Biohazard timers escalate visually through real flood-gauge cues rather than stacked neon banners.
3. Every indicator earns its pixels: permanent chrome holds only continuous survival and routing metrics; station choices, fines, and unlock celebrations appear strictly on trigger.
4. Zero fake or contradictory telemetry: every displayed value in mockups and runtime must obey `RiverGameManager.cs` and `ToolCatalog.cs` math.

## Accessibility & Inclusion

- Minimum WCAG AA text contrast across bright tropical Golden Hour skies and dark Monsoon storm frames.
- Colorblind-safe encoding: `SIAGA` levels and all 3 waste classes pair distinct hues with clear labels and distinct geometric/pictorial silhouettes.
- Readable at both `1920x1080` and `1280x720` desktop resolutions with crisp tabular numerals (`font-variant-numeric: tabular-nums` / TMP monospace digits).
