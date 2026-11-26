# KALI: Indonesian River Sweeper — Niki Quickstart Guide
> **Role**: VFX, UI & Audio / Narrative Lead (Student ID: `0706012410015`)  
> **Target Unity Version**: `2022.3.46f1 LTS URP`  
> **Workspace Scopes**: `unity/Assets/_Project/VFX/`, `unity/Assets/_Project/UI/`, `unity/Assets/_Project/Audio/`

---

## 1. Git Sync First (Avoid Merge Conflicts)
Before touching any Unity assets or scripts, run these commands in your terminal to grab Ivan's finalized C# manager scripts and JC's FBX assets:

```bash
git checkout main
git pull origin main
git checkout -b feature/niki-vfx-ui-audio
```
> *Note*: This leaves your stale local branch behind and syncs you with the latest clean `main` branch.

---

## 2. First-Open Unity GUID Lock Rule
1. Open the `./unity` project folder in **Unity 2022.3.46f1**.
2. Let the initial asset import complete fully.
3. Immediately commit and push `unity/ProjectSettings/*.asset` and all generated `*.meta` files so everyone shares the exact same GUIDs before building prefabs or scenes:
```bash
git add unity/ProjectSettings unity/Assets
git commit -m "chore(unity): commit initial ProjectSettings and .meta GUIDs"
git push
```

---

## 3. Exact Unity Menu Order
When the editor loads, you must execute the custom Kali bootstrap menus in exact sequence:

* **Step 1**: Click **`KALI > JC > Build All JC Prefabs`** in the top Unity menu. *(Builds atlas materials, `PF_Tool_*`, `PF_Trash_MedicalBag/SyringeBox`, and `PF_ExcavatorAmfibi` — **Must run FIRST!**)*
* **Step 2**: Click **`KALI > Load Default Purpose-Built Map`**. *(Spawns the `_KALI_World` 54-node scene with `Player_Rig`, `RiverGameManager`, `RiverTrashSpawner`, and tools pre-wired).*
* **Step 3**: Save your scene under `unity/Assets/_Project/Scenes/`, or press **Play** and hit **`F9`** followed by **`1..4`** to preview all 4 game stages/scenarios instantly.

---

## 4. Scope Boundaries & C# Event Contracts
Restrict all your work strictly to:
- `unity/Assets/_Project/VFX/**`
- `unity/Assets/_Project/UI/**` (including UI glue scripts inside `UI/Scripts/`)
- `unity/Assets/_Project/Audio/**`

### `RiverGameManager.Instance` Event Subscriptions
Do not modify Ivan's core systems (`Scripts/Core/RiverGameManager.cs`). Instead, subscribe to these public events and properties from your UI/VFX scripts:

- **`OnStateChanged`** (`Action`): Throttled ~10Hz ticker. Drive HUD meters (`playerHealth`, `rupiah`, cargo counts, water height `currentWaterLevelY`, `SiagaLevel` 4..1, `monsoonCountdownRemaining`).
- **`OnToolUnlocked`** (`Action<ToolDefinition>`): Trigger auto-unlock celebration toasts for tools `#01..#20`.
- **`OnEquippedToolChanged`** (`Action<ToolDefinition>`): Update bottom tool bar active slot badges.
- **`OnHazardOrAlert`** (`Action<string msg, bool isDanger>`): Display immediate warning banners for Medical needle pricks, Biohazard DoT ticks, or Sell-Lock blocks (`[Q] Dump Cargo on High Ground`).
- **`OnWeatherChanged`** (`Action<bool isMonsoonStorm>`): Toggle `VFX_MonsoonRain` and storm audio ambient loops.
- **`OnEndingTriggered`** (`Action<GameEnding ending>`): Display `Canvas_SDGImpactReport` (`TrueSdgVictory`, `CompromisedOceanFlush`, `FloodFail`, `HealthFail`) summarizing recycled vs flushed kg and SDG metrics.

---
*End of Quickstart Guide. Follow this procedure strictly to maintain zero-conflict collaboration.*
