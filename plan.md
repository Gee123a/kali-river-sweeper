# KALI Master Plan: The Million-Piece River

Status: **planned, nothing built**. Per-member tasks live in [plan_ivan.md](./plan_ivan.md), [plan_jc.md](./plan_jc.md), [plan_wesley.md](./plan_wesley.md), [plan_niki.md](./plan_niki.md) under "New River Loop". Task IDs are `R<phase>-<member><n>` (I Ivan, J JC, W Wesley, N Niki).

Where this plan conflicts with `docs/PRD.md`, `docs/MECHANICS_SPEC.md` or `docs/PROGRESSION_REDESIGN.md`, **this plan wins**. Those docs are updated in Phase 6.

Markers: **[agreed]** said by Ivan. **[default]** proposed, change if wrong. **[open]** needs a decision. All numbers are untested starting values until the simulator confirms them.

## 1. Core loop

- **[agreed]** Gunung Sampah has **1,000,000 HP**. One floating bundle is **50 HP**, so the run holds **20,000 bundles**.
- **[agreed]** The mountain pours trash into the river. Pouring does **not** lower HP. HP drops **only when trash is picked up**.
- **[agreed]** Trash never disappears. What is not picked up stays, jams at Pintu Air and fills the river back upstream.
- **[agreed]** The river must look **very full**. A river that is too full overflows. Flooding is forgiving.
- **[agreed]** Every tool, including hooks and the excavator, takes trash **from the river**. Nothing touches the mountain. Gunung dredging is removed.
- **[default]** `mountain stock = HP / 50 - bundles in river` (picked-up bundles have already left HP). Pouring stops when the stock is 0.
- **[default]** **Win:** HP reaches 0. **Lose:** flood, health, or emergency flush.
- **[default]** Dumping cargo (`Q`) returns the bundles to the river and restores their HP.

## 2. River fill and water

| Setting | Starting value | Marker |
|---|---|---|
| River capacity (overflow) | 8,000 bundles | default |
| River at the start | 3,000 bundles | default |
| Base pour rate | 17 bundles/s, slowing as HP drops | default |
| Top-up floor (keeps the river looking full) | 3,000 bundles while stock lasts | default |
| Idle player floods at | about 5:00 | default |
| Target winning run | about 15 minutes | default |

- Water level follows fill: `waterY = base + fill / capacity * (fatal - base) + storm rise`.
- Monsoon storms stay as built (3:00, 45 s, every 180 s). The temporary rain rise eats into the headroom.
- **Biggest balance risk:** the player must reach a removal rate close to the pour rate (storage level 2) before the river fills. The simulator has to prove this first (R0-I1).

## 3. Tools: lift per click and source

**[agreed]** Lift matches the object (a bucket lifts far more than tongs). Tools come from the Kopdes shop, mystery quests, or easter eggs near the mountain. Numbers and sources are **[default]**.

| # | Tool | Role | Lift | Source |
|---|---|---|---|---|
| 1 | Sendok bengkok | Serok (trash) | 1 | start |
| 2 | Gayung | Serok | 3 | Kopdes |
| 5 | Ember 5L | Serok | 8 | easter egg |
| 6 | Gayung saringan bambu | Serok | 12 | Kopdes |
| 7 | Serokan waring 3m | Serok | 20 | Kopdes |
| 9 | Ember 20L | Serok | 30 | Kopdes |
| 12 | Serokan jumbo 4.5m | Serok | 60 | quest |
| 14 | Jala lempar | Serok | 150 | Kopdes |
| 3 | Centong nasi | Capit (medical) | 1 | Kopdes |
| 4 | Garpu taman | Capit | 2 | Kopdes |
| 10 | Capitan ular | Capit | 4 | quest |
| 8 | Ganco 1 mata | Ganco (biohazard) | 1 | Kopdes |
| 13 | Ganco ganda winch | Ganco | 5 | quest |
| 16 | Blok magnet 50kg | Ganco | 12 | easter egg |
| 17 | Senapan panah tali | Ganco | 16 | Kopdes |
| 11 | Arit panjang | Garuk (jam) | 8 | Kopdes |
| 15 | Pompa siphon | Garuk | 25 | Kopdes |
| 18 | Pompa mesin 49cc | Garuk | 60 | quest |
| 19 | Gergaji ganda | Garuk | 80 | easter egg |
| 20 | Skimmer hidrolik | Garuk | 200 | Kopdes |

- One slot per role and 50% trade-in stay.
- **[open]** Medical is about 14% of bundles (about 2,800) but Capit lifts at most 4, which is about 700 clicks. Raise Capit lift, or let the excavator sweep all classes?

## 4. Storage

**[agreed]** The tool sets how much one click grabs. Storage sets how much you hold before delivering.

`grab = min(tool lift, free storage, bundles in reach)`; then `carried += grab`, `HP -= grab * 50`. What does not fit stays in the river.

| Level | Storage | Capacity | Source [default] |
|---|---|---|---|
| 0 | hands | 40 | start |
| 1 | sack or cart (new) | 150 | Kopdes |
| 2 | sampan | 600 | Kopdes or quest |
| 3 | excavator | 2,000 (scoop 300) | Kopdes |

- On foot you carry in hands or the sack (the sack replaces hands; they do not add up). Boat and excavator each have their own hold.
- All waste classes share capacity.
- The shop warns when a tool lifts more than you can carry.
- **[agreed]** Boat and excavator storage work **only while aboard**; the load stays in the vehicle.

## 5. Vehicles and delivery

- **[agreed]** The excavator does **not** move. It is boarded where it is parked, and must reach the river from there.
- **[default]** Unload by hand: `[E]` on a vehicle moves a load into your own storage.
- **[default]** The boat stays on water: dock, then carry.
- **[agreed, idea stage]** A pickup truck takes the excavator's load. `[E]` calls it; it drives up, loads, leaves; payment about 40 s later at about 70% of station price. Never crosses the bridge. One truck at a time.
- **[default]** Stations accept only their own class. During high water Gudang Pengepul stays open, so a full load can never trap the player.

## 6. Money and hazards

- **[default]** Pay per bundle drops sharply: Normal Rp 200, Medical Rp 450, Biohazard Rp 700. Tool and upgrade prices are set by the simulator.
- **[default]** Mix stays 80 / 14 / 6. Medical prick chance applies **once per click**, not per bundle.
- **[open]** Trash Boom: counts as picking up (lowers HP)? Default yes.
- **[open]** Kampung bins: default lowers the pour rate by 20%.

## 7. Phases

Each phase ends with: compile clean, `KALI QA` pass, independent check, commit. Push only with Ivan's OK. Play Mode testing by Ivan.

| Phase | Goal | Tasks | Done when |
|---|---|---|---|
| 0 | Prove it works | R0-I1 simulator of the new loop; R0-I2 frame-rate spike with 8,000 floating bundles | targets reachable; at least 60 FPS on the demo laptop, else lower the drawn count |
| 1 | Core river | R1-I1 mountain HP and pouring; R1-I2 bundle field, jam, water from fill; R1-I3 remove dredging; R1-J1; R1-W1 | river full from the start; HP drops only on pickup; overflow works |
| 2 | Tools and storage | R2-I1 lift table; R2-I2 storage levels, pay, delivery; R2-J1; R2-N1; R2-N2 | table and storage rules pass QA |
| 3 | Vehicles and truck | R3-I1 boarding storage, hand unload; R3-I2 truck service (placeholder); R3-J1 (= JC Task 7C); R3-W1; R3-N1 | excavator load reaches money both ways |
| 4 | Quests and easter eggs | R4-I1 quest system giving tools (extends 6C); R4-I2 easter egg pickups; R4-J1; R4-W1; R4-N1 | every tool obtainable |
| 5 | Look and feel | R5-N1 audio; R5-W1 water and jam readability | dense river reads clearly |
| 6 | Balance, docs, QA | R6-I1 tune with simulator; R6-I2 update PRD, MECHANICS_SPEC, PROGRESSION_REDESIGN | targets met, docs match the game |

Art never blocks code: Ivan ships placeholder shapes first.

## 8. What this replaces

- Replaced: Gunung dredging, timed spawn of a few bundles, hidden numeric barrier pile, cargo 8 / 22 / 60, tool unlock only by cumulative money.
- Ivan's 6B (trust tiers) is **paused**: tool sources are now shop, quest and easter egg. 6C feeds R4-I1. 6E folds into R6-I1.
- Kept: monsoon rework, tool roles, waypoints, boat model, NPC talk, Es Teh.

## 9. Before building

- Wesley's pushed work is not merged yet (kiosk, hills, jetties, trash readability, floor marks). Merge it before Phase 1.
- Decide the **[open]** items in sections 3 and 6.
