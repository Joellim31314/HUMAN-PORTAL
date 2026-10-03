# UX FLOW — Hackathon Demo

The entire product answers **one question**: *"Where should I sell this item?"*

Not "is my product good" — **where** it wins. One universal flow; no founder/buyer
branch, no role picker. Geography is **London** for the demo.

---

## Act 0 — Landing (the map, immediately)

First-time visitors land on the Research map — no interview wall. With no
saved product, the map runs the hojicha example dataset (badged "Demo
dataset") so the engine is visibly working: circles, ranked areas, evidence.
The interview is one click away via **"Test your product"**; a **"Demo data"**
button pre-fills it with the hojicha RTD example. Once a product is
submitted, `/` shows that product's map instead.

## Act 1 — Upfront interview (~6–8 questions, 60–90s)

One screen, grouped into two blocks. Answers become **bets** the product settles
in Act 2 — this framing is the Human Truth angle.

**Product facts**
1. What's the product? (name + one-liner; example product pre-fills this)
2. Category (select: beverages / snacks & confectionery / sauces & condiments /
   dairy & alternatives / bakery / ready meals)
3. Price point + pack size
4. Sold anywhere today, or pre-launch? (channels)

**Bets (the interesting half)**
5. Who do you *think* buys it?
6. Why do they choose it over the alternative?
7. Why would someone *distrust or reject* it?
8. **Where do you think it would sell best?** — the placement guess. The map in
   Act 2 exists to confirm or wreck it.

No "what decision are you making?" question — placement IS the decision.

## Act 2 — Research (costs 1 of 35 free searches; counter shows, never blocks)

The map is home. After the interview runs:

- **Opportunity circles** on a London map: ranked areas where this product should
  sell. Each circle's score composes four signals:
  trend heat (social velocity in-category) · competitor gap (demand minus
  players) · shelf whitespace (under-served physical retail) · demographic fit
  (local persona clusters vs. the product's likely buyers).
- **Ranked area list** beside the map; clicking a list row or circle flies the
  map there and opens the **area detail panel**.
- **Bets settled, inline**: where the evidence contradicts an interview answer,
  it's highlighted on the card that carries the evidence, plus an
  **"Your assumptions" summary strip** up top ("You guessed Shoreditch; signals
  say Walthamstow"). Every key claim has an expandable **"Why we believe this"**
  with cited signals and confidence.

## Act 3 — MISO Simulation (one click)

Area detail panel has one big button: **"Simulate my product here."** Product
profile comes from the interview — no further choices.

Result screen:
- **Agent narratives first**: "Maya, 22, student — rejected at £3.80: she buys
  whatever her gym friends post, and she's never seen your brand."
- **Cluster verdict table below**: per persona cluster — adopt / reject / ignore,
  with driver tags (habit, trust, social proof, price anchor).

## Act 4 — Decision brief

The artifact judges screenshot:
- **Recommendation**: where to sell (the top area), who to win first, the one
  thing blocking trust.
- **Evidence**: top signals behind each claim, expandable citations.
- **Watch list**: 2–3 signals to monitor — the reason to return to the dashboard.

---

## Demo mechanics

| Mechanic | Decision |
| --- | --- |
| Geography | London (map centers on London) |
| Free searches | First research costs 1 of 35; counter visible but **never blocks** |
| Example product | One-click hojicha RTD pre-fill |
| Assistant FAB | **Removed** from the map |
| Back-test evidence | One canned historical launch: simulated with pre-launch data only, shown vs. its known fate |
| Payments | None — Pro/paywall surfaces are stubs |

## Deliberately cut from the demo

- Founder/buyer role branching (one flow serves both)
- Saved snapshots & history (the brief is the artifact; snapshots come post-demo)
- Freeform sim scenarios (one-click only)
- Chat assistant
- Decision-type picker (launch/stock/price/promote)

## Judge journey (~5 minutes)

1. Land → map with example dataset proves the engine (30s)
2. One-click example product → interview is pre-filled, bets visible (30s)
3. Research → circles appear; the placement bet gets settled inline (90s)
4. Click top area → "Simulate here" → MISO verdict with narratives (90s)
5. Brief → recommendation + citations + the canned back-test slide (60s)
