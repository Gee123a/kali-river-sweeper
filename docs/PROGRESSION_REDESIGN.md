# KALI — Progression, NPC Interaction & Mini-Quest Redesign (2026-11-28)

Source: [PLAYTEST_PROGRESSION.md](./PLAYTEST_PROGRESSION.md).
Problem: rewards are **handed out**. Tools unlock automatically from cumulative Rp, there are 6 toasts in the first minute, and nothing asks for skill or choices. Meanwhile the start is empty, the storm doesn't threaten, and the SDG win sits at ~7%. The villagers are scenery only.
Goal: every unlock is **earned** through how well you clean, sort and help the kampung. The villagers are the people you are cleaning *for*, and they react, ask and reward.

## 1. Design pillars
1. **Earned, not given.** No unlock without a reason the player can name: "I unlocked the Capitan Ular because I kept Bu Siti's washing steps safe from needles."
2. **Two currencies.**
   - **Rupiah** buys things.
   - **Kepercayaan Warga** (community trust, already in code as `communityTrust` 0–100) opens tiers.
   - Money alone never opens a tier.
3. **Always a next goal within 30 s.** Every moment shows one clear target: a quest marker, a tool goal, or the water level.
4. **The village reacts to you.** Cleaner water brings the kids back to swim and the washers back to the steps; dirty water and storms send them away. That is the visible SDG reward.
5. **Short and readable.** A run lasts 300 s, so quests take 30–60 s, use 1–2 lines of dialogue, and need no menus.

## 2. Earned progression (replaces cumulative-Rp auto unlocks)
| Tier | Tools | How it opens (all must be true) | Feel |
|---|---|---|---|
| 0 Starter | #1 Sendok | Start | "I'm improvising." |
| 1 Kampung | #2–#6 | Trust ≥ 30 **and** first correct delivery at each of the 3 stations ("Belajar Memilah") | Learning to sort pays off. |
| 2 Pengrajin | #7–#12 | Trust ≥ 50 **and** 1 villager quest done. #10 Capitan Ular needs **Bu Siti's quest** specifically. | The villagers trust me with real gear. |
| 3 Ahli Sungai | #13–#16 | Trust ≥ 70 **and** Pak Darto's quest. #13 Ganco Winch is his gift-recommendation. | Ready for Gunung Sampah. |
| 4 Pahlawan | #17–#20 | Trust ≥ 85 **and** Gotong Royong quest (Pak RT) | Endgame and replay mastery. |

Rules:
- **The tier opens the Kopdes shelf; Rupiah still pays.** The ladder trade-in (Task 4L) stays.
- **Cumulative Rp no longer unlocks anything** on its own. It stays as a score.
- **Trust moves only through actions:**
  - correct sort: +2 per item
  - wrong station: -8 / -12
  - Pengepul hazard dump: -8 / -12
  - quest done: +10 to +20
  - kids evacuated in the storm: +10
  - prick or infection: -5
- **Combo ("Setoran Bersih"):** a delivery trip with zero wrong items and zero hazards left in cargo adds +1 to the streak; each streak step pays +5% (cap +25%). A mistake resets it. This rewards skill, not time spent.
- **Upgrades are earned too:**
  - Sampan becomes **Pak Darto's** reward (he lends his boat once his quest is done).
  - Trash Boom becomes **Pak RT's** Gotong Royong reward: the village installs it with you, so it isn't bought.
  - Excavator stays a large Rp purchase gated by Tier 3.
- **Re-scale:** Tier 3 should be reachable by ~150–170 s for a good sorter, so the SDG win becomes realistic (target 30–50% for a good Sorter). Check with `docs/playtest/progression_sim.py`.

## 3. Natural feel fixes
- **Diegetic tutorial:** Pak RT stands at spawn and says "Nak, sampah di Tangga Cuci itu dulu ya", pointing at the live tutorial pile 10 m away. The first sale lands in under 30 s.
- **Live trash at start:** bake the `trash_pile` clusters as real `RiverTrashItem`s (P0, from the playtest).
- **Biohazard fairness:** grace 10 s → 25 s, or the timer starts only once you are on land. The Geiger ticks get faster as time runs out.
- **Reward cadence:** quest markers sit along the river, so there is always something within ~40 m.
- **Storm as climax:**
  - surge stronger (5 s → 1.5 s)
  - kids caught in the water become an **evacuation** moment
  - Siaga 2 should be reachable for active players
- **Fewer, bigger toasts:** one "Tier Baru Terbuka!" banner per tier instead of 20 tool toasts.

## 4. NPC interaction (talk + reactions + NPC↔NPC)
- **[E] Bicara** within 2.5 m of any villager shows 1–2 lines in a speech bubble. Lines depend on game state:
  - **calm / clean:** "Airnya mulai jernih, Nak!"
  - **dirty:** "Bau sekali sungainya…"
  - **storm:** "Cepat naik! Banjir!"
  - **high trust:** "Ini dia pahlawan kali kita."
  - **low trust:** "Jangan buang limbah ke Pengepul lagi ya."
- **Reactive behaviour** (already partly in `KaliAmbientNpc`):
  - **Washers** step back from the water when `waterClarity` < 0.25, and return to scrub when it is ≥ 0.45.
  - **Kids** swim only when clarity ≥ 0.4; otherwise they sit on the jetty and point at the trash.
  - **Fishers** pull a "sampah nyangkut" bag up on the line every ~20 s while the river is dirty. It drops as a pickable item, so they feed trash to the player.
  - **Everyone** looks at the player (head turn) within 4 m, and cheers once (clap clip) when the player delivers a clean combo nearby.
- **NPC↔NPC:**
  - **Chatters:** pairs at the warungs swap 1-line gossip that matches the state ("Katanya Gunung Sampah makin tinggi").
  - **Kids:** a kid runs to the nearest fisher, the fisher points and the kids follow (a scripted 6 s chain every ~45 s).
  - **Washers:** a washer calls her kids out of the water during a storm. This is the evacuation quest hook.

## 5. Mini quests (one per NPC type, 30–60 s each)
| Quest | Giver (npc_group) | Ask | Reward (earned) |
|---|---|---|---|
| **Q1 Belajar Memilah** | Pak RT (spawn / `npc_chatter_east_warung`) | One correct delivery to each of the 3 stations | Tier 1 opens, +10 trust |
| **Q2 Jarum di Tangga Cuci** | Bu Siti (`npc_washer_west_mid`) | Secure 3 medical items near the washing steps, taken to Pos Medis with no prick | Unlocks **#10 Capitan Ular** on the shelf, +15 trust |
| **Q3 Kail Nyangkut** | Pak Darto (`npc_fisher_jetty2`) | Clear the 6-item snag around jetty 2 within 60 s | **Sampan** lent for free, #13 recommended (Tier 3 condition), +15 trust |
| **Q4 Bola Hanyut** | Raka & kids (`npc_kids_west_jetty3`) | Catch the drifting ball before it reaches the barrier (timed chase) | Kids act as "pengintai": biohazard pinged on the minimap for 60 s, +10 trust |
| **Q5 Gotong Royong** | Pak RT | 15 correctly sorted items before the storm | **Trash Boom** installed by the village, +20 trust, Tier 4 condition |
| **Q6 Evakuasi** (storm only) | Bu Siti's kids (`npc_kids_east_shallow`) | Reach the kids in the water within 20 s of the storm starting | +10 trust; a fail costs -10 trust |
| **Side: Es Teh Mbok Nah** | Warung (`npc_chatter_west_warung`) | Talk while trust ≥ 50 (once per run) | +30 HP. A rest stop that rewards being liked. |

Quest rules:
- At most 1 active quest plus 1 storm quest.
- Givers show a "!" marker.
- Quests are tracked in the HUD.
- The SDG report lists the quests done (a teaching moment for the sidang).

## 6. Tech shape (minimal, Ivan-owned C#)
- `Scripts/Core/KaliQuestCatalog.cs`: a static table of quest definitions (id, giver id, goal type, count, time limit, reward). No ScriptableObjects; the table is simple and fast to tune.
- `Scripts/Core/KaliQuestManager.cs`:
  - listens to the existing `RiverGameManager` events (`OnStationAuditReceipt`, pickup and secure calls, `OnWeatherChanged`)
  - tracks progress and pays rewards
  - exposes `ActiveQuest`, `OnQuestStarted/Progress/Completed/Failed`
- `Scripts/Core/KaliNpcInteractable.cs`: on each NPC group root. It handles the proximity prompt, state-based line picking via `KaliNpcDialogue` (a static line table, Bahasa) and the "!" marker.
- `RiverGameManager`:
  - `GetToolTier(int)`
  - `IsTierOpen(int)` (trust plus quest flags)
  - tier gating in `BuyTool`
  - trust deltas and the combo streak
- Niki's HUD only subscribes to events; nothing polls per frame.
- QA: extend `KaliCoreQaTests` to cover tier gating, quest completion paths and combo reset. Re-run the simulator for the target win rate.

## 7. Who does what
See the "Progression & Village Life" section in each `plan_*.md`.
- **Ivan:** core systems.
- **Niki:** dialogue UI, quest HUD, Bahasa script and audio.
- **JC:** talk and cheer animations, quest props.
- **Wesley:** quest landmarks.
