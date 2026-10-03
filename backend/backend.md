# HUMAN PORTAL — Simulation Backend

*Owner: backend/simulation · Status: hackathon demo build, implemented and tested
(25 tests passing, live DeepSeek run verified) · Python 3.11+ · FastAPI*

This document covers everything in `backend/`: what it does, why it is built this
way, where the data comes from, how the simulation logic works, the API the
frontend uses, and how to run, test, and tune it. PROJECT.md carries a shorter
version of this under "Market simulation engine (v1, London)".

---

## 1. What it does

A retailer or brand describes an F&B product and where it will be stocked. We
release it into a simulated London of **2,000 individual adults**. Each one has a
real home neighbourhood, a job or study place, a weekly routine, a personality,
media habits, and diet/belief constraints.

Over one simulated week (7 days × 7 time slots) every agent either walks past a
stocking store or never goes near one. They notice the product or don't, need it
at that moment or don't, and then buy it or reject it. **Every agent ends with
exactly one outcome and one reason.** The LLM then interviews a sample of agents
in their own voice, and a final call turns the numbers and quotes into a
decision-ready report.

It answers the questions the retailer cares about:

- **Why didn't people buy it?** Not stocked on their routes; not there when they
  needed it; walked past without noticing; too expensive; conflicts with their
  diet or beliefs; loyal to their usual brand.
- **Who was interested?** Conversion and interest by age band, sex, ethnicity,
  borough, archetype (commuter, student, …), and income band.
- **What should we do?** Prioritised action items, plus first-person quotes that
  explain the numbers.

---

## 2. Design reasoning

| Decision | Why |
| --- | --- |
| **Individual agents, not persona clusters** | The key insights are about *place and time* (e.g. energy drinks stocked near homes when people need them on the commute). A cluster has no home, route, or schedule; an individual does. Clustering on scraped signals remains the v2 path (see §11). |
| **London only** | The UK publishes free, commercially usable census data down to ~8,000-person neighbourhoods (MSOAs), so the population *is* London rather than a guess. This matches the UK launch market and UX-FLOW.md. |
| **Real data for facts, rules for the gaps** | Demographics, geography, and stores come from public data. Personality, routines, and media habits come from rules conditioned on those facts, and are documented as modelled. |
| **Python counts, the LLM explains** | The funnel is deterministic, seeded Python: fast (~1 s per run), reproducible across video takes, and correct about numbers. LLMs are poor at arithmetic and are known to lean towards "yes, I'd buy it". The LLM only writes ~80 interviews and one report per run. |
| **Never break the demo** | No API key, a timeout, or bad JSON from the LLM falls back to templated quotes and a templated report. Identical product inputs return the cached result instantly at zero cost. |
| **JSON files, not Postgres (for now)** | Zero setup for the hackathon. `store.py` is the only persistence module, so swapping in Postgres later touches one file. |
| **Population built once and committed** | `data/processed/agents.json` (4.6 MB) and `stores.json` (1 MB) are in git, so nobody needs to run the data pipeline to start the API. |

---

## 3. Data sources

All verified working in October 2026. All licences permit commercial use.

| Layer | Source | Access | Licence | How we use it |
| --- | --- | --- | --- | --- |
| Who lives where | **Nomis Census 2021 bulk tables**, MSOA level: `ts007a` age, `ts008` sex, `ts021` ethnicity, `ts030` religion, `ts063` occupation, `ts061` travel to work, `ts066` economic activity. URL pattern `https://www.nomisweb.co.uk/output/census/2021/census2021-<table>.zip` | Free, no key | OGL v3 | Per-neighbourhood distributions each agent is sampled from |
| Where neighbourhoods are | **ONS MSOA Dec 2021 population-weighted centroids** (ArcGIS FeatureServer `MSOA_December_2021_EW_PWC_V2`) | Free, no key | OGL v3 | Agent home points; store → borough lookup |
| Where products can be sold | **OpenStreetMap** via the Overpass API: `shop=convenience` and `shop=supermarket` nodes and ways in the London bounding box, with brand tags | Free, User-Agent header required | ODbL (attribute "© OpenStreetMap contributors") | 7,001 stores: 5,693 convenience, 1,308 supermarkets, 2,563 branded (Tesco Express 458, Sainsbury's Local 312, Londis 233, Co-op 201, …) |
| Where people go | **OpenStreetMap** `leisure=fitness_centre` (1,103 gyms) and `amenity=university` (145 sites), plus a hand-curated list of 12 London job hubs (City, West End, Canary Wharf, King's Cross, Shoreditch, London Bridge, Stratford, Croydon, Hammersmith, Paddington, Heathrow, …) | Free | ODbL / ours | Work, campus, and gym locations |
| Everything else | **Rule-based generator** (ours) | — | — | Big Five, shopping traits, media mix, diet flags, schedules |

**Population fidelity** (sample vs. census, adults 16+):

| Age band | 16–24 | 25–34 | 35–44 | 45–54 | 55–64 | 65+ |
| --- | --- | --- | --- | --- | --- | --- |
| Sample % | 14.2 | 23.4 | 19.7 | 18.2 | 11.8 | 12.8 |
| Census % | 13.8 | 22.4 | 19.7 | 16.4 | 12.9 | 14.7 |

| Ethnicity | White | Asian | Black | Mixed | Other |
| --- | --- | --- | --- | --- | --- |
| Sample % | 53.5 | 21.5 | 13.7 | 6.0 | 5.3 |
| Census % | 54.0 | 20.5 | 13.4 | 5.8 | 6.3 |

### Deliberately not used (v1)

| Source | Why not | Replaced by |
| --- | --- | --- |
| IPF synthesis (humanleague) + UK Data Service microdata | Research-only licences; days of work | Independent sampling from MSOA marginals plus consistency rules |
| Census origin–destination flows (ODWP01EW) | Large files; 2021 figures distorted by COVID work-from-home | Job-hub gravity model (hub size × distance decay, plus a 35% "local job" weight) |
| ONS Time Use Survey | Time | Six archetype schedule templates with per-agent variation |
| Big Five open dataset | Not needed for a demo | Clipped normal distributions |
| dunnhumby Complete Journey | US data | — |
| WVS / EVS values surveys | Non-commercial licences | Religion from the census plus diet-flag rules |
| Geolytix retail points | Tesco only | OSM, which covers every chain |

### Known simplifications

- Traits are sampled independently within each neighbourhood, so joint
  distributions (e.g. age × ethnicity) are approximate.
- Income is inferred from occupation group; the census has no income question.
- About 26% of agents are work-from-home. Census 2021 was taken during the
  pandemic; lower the WFH weight in `population/sampler.py` if wanted.
- Unemployed agents use the `retired` (70%) or `carer` (30%) schedule archetype.
- Census 15–19 counts are scaled by 0.8 to approximate 16–19.
- Adults 16+ only.

---

## 4. Architecture

```
 OFFLINE (run once, output committed)                 ONLINE (per simulation run)
 ──────────────────────────────────────               ───────────────────────────────────────────
 Nomis census ─┐                                      ProductInput  (POST /api/simulations)
 ONS centroids ├─► pipeline/build_population ─►       │
 OSM shops,    │     population/sampler    (who)      ▼
 gyms, unis  ──┘     population/geography  (where)    simulation/engine.run_funnel   (~1 s, seeded)
                     population/schedules  (when)       stockists → exposure → need → notice
                     population/traits     (how)        → price / belief / loyalty → purchase
                           │                            = outcome + reason + trace per agent
                           ▼                          │   (outcomes saved → map can colour agents)
              data/processed/agents.json ────────────►│
              data/processed/stores.json              ▼
                                                      llm/interviews   (~80 agents, DeepSeek, 16 parallel)
                                                      llm/report       (1 call → findings + actions)
                                                      │
                                                      ▼
                                                      store.py (JSON cache, keyed by product hash)
                                                      │
                                                      ▼
                                                      FastAPI  ──►  Next.js map frontend
```

### File map

```
backend/
  backend.md               this document
  requirements.txt         fastapi, uvicorn, pydantic, numpy, pandas, httpx, openai, python-dotenv, pytest
  .env.example             copy to .env; DEEPSEEK_API_KEY etc. (.env is gitignored)
  app/
    main.py                FastAPI app, CORS, routers, startup data load
    config.py              all paths and settings (env-overridable)
    schemas.py             THE data contract (Pydantic). Frontend types mirror this.
    store.py               load population/stores; save and load simulation results and traces
    api/
      population.py        /api/health, /api/agents, /api/agents/{id}, /api/stores, /api/population/summary
      simulations.py       POST/GET /api/simulations, per-agent trace; background run + cache
    pipeline/
      fetch_census.py      download and parse Nomis tables (cached in data/raw/)
      fetch_centroids.py   ONS MSOA centroids (ArcGIS, paginated)
      fetch_pois.py        OSM shops, gyms, universities (Overpass, mirror fallbacks)
      build_population.py  end to end: fetch → sample → place → schedule → validate → write
    population/
      sampler.py           MSOA allocation; age/sex/ethnicity/religion/status/occupation/travel/income/archetype
      geography.py         home jitter, job hubs, universities, gyms
      schedules.py         6 archetype templates × weekday/weekend, 7 slots each
      traits.py            Big Five, shopping traits, media weights, diet flags
      names.py             deterministic names per ethnic group and sex
    simulation/
      engine.py            run_funnel() and FunnelRun: the per-agent, per-slot loop
      funnel.py            stockist filter, spatial grid index, aggregation (funnel/reasons/segments)
      categories.py        need curves, reference prices, belief/price/loyalty rules
      reasons.py           REASON_LABELS (plain-English reason text)
    llm/
      client.py            DeepSeek via OpenAI SDK; JSON mode; semaphore; returns None on any failure
      prompts.py           persona card/line renderers; interview and report system prompts
      interviews.py        stratified sampling + concurrent interviews + template fallback
      report.py            report call + validated template fallback
  data/
    raw/                   downloaded sources (gitignored, ~15 MB)
    processed/             agents.json, stores.json (committed)
    simulations/           cached run results + traces (gitignored)
  tests/
    conftest.py            make_agent / make_store / make_population / make_stores factories
    test_sampler.py        population builder (offline)
    test_funnel.py         engine scenarios, invariants, performance
    test_api.py            API end to end with fake engine, LLM disabled
```

---

## 5. Population logic (offline)

`python -m app.pipeline.build_population` (about 10 s once the raw files are cached).

1. **Allocate** 2,000 agents across London's 1,002 MSOAs in proportion to adult
   population (largest-remainder method). London = the 33 boroughs, matched on
   MSOA name prefix.
2. **Sample demographics** from that MSOA's census counts: age (5-year band, then
   uniform within it), sex, ethnicity (5 groups plus a detailed sub-group), and
   religion ("Not answered" dropped and the rest renormalised).
3. **Economic status** from age multipliers × local shares: 16–24 skews student,
   66+ skews retired, otherwise employed, self-employed, unemployed, or carer.
   **Occupation** (SOC major group) and **travel mode** (underground, train, bus,
   car, bicycle, on foot, WFH) come from local shares if working.
4. **Income band** from occupation group: managers and professionals → high;
   associate professional, admin, and skilled trades → mid; caring, sales,
   process, and elementary → low. Students, retirees, and unemployed agents skew
   low. Noise is added throughout.
5. **Archetype**: `office_commuter`, `shift_worker` (probability by occupation,
   e.g. 50% for caring roles), `student`, `wfh`, `retired`, or `carer`.
6. **Geography**: home = MSOA centroid + ~250 m Gaussian jitter. Commuters pick a
   job hub weighted by hub size × distance decay, or a local job (weight 0.35).
   Students get a weighted nearby university. Others have no workplace.
7. **Schedule**: weekday and weekend, 7 slots each (`early_morning`, `morning`,
   `midday`, `afternoon`, `evening`, `late_evening`, `night`). Each slot has a place
   (`home`, `transit`, `work`, `campus`, `local`, `central`, `gym`), an activity,
   and resolved coordinates: transit = home–work midpoint, central = West End +
   jitter, gym = the nearest gym for active agents. Shift workers can work late or
   at night. About 20% of evenings vary per agent.
8. **Traits** (all 0–1): Big Five, attention, novelty seeking (higher when young),
   price sensitivity (higher on low income), health consciousness, brand loyalty
   (higher with age). **Media weights** for TikTok, Instagram, YouTube, X,
   Facebook, TV, out-of-home, radio, and podcast are age-anchored, with out-of-home
   boosted for commuters. **Diet flags**: halal (~85% of Muslims), kosher (~30% of
   Jewish agents), vegetarian (~40% of Hindus, plus base rates), vegan (~3%,
   higher when young; vegans are also flagged vegetarian), health-conscious,
   low-sugar (~10%), caffeine avoider (~8%).
9. **Validate** every agent against `schemas.Agent`, then write compact JSON.

---

## 6. Simulation logic (online)

`simulation/engine.run_funnel(product, agents, stores) -> FunnelRun`. It is
deterministic for a given `product.seed`; 2,000 agents × 49 slots × ~7,000 stores
runs in about 1 s.

**1. Stockists.** Filter stores by `store_kinds`, `chains` (case-insensitive
substring match on brand or name), and `boroughs`, then keep a seeded `coverage`
share. Stocking stores go into a ~500 m grid index.

**2. Ad awareness.** The sum over the product's `marketing_channels` of the
agent's media weight × `marketing_intensity`, capped at 1. It boosts noticing.

**3. Weekly loop.** For each day (Mon–Fri use the weekday schedule, Sat–Sun the
weekend one) and each awake slot:

| Step | Question | Driven by |
| --- | --- | --- |
| Exposure | Is a stocking store within 400 m (`WALK_RADIUS_M`) right now? | Slot coordinates + grid lookup |
| Need | Do they want this category *now*? Computed for every slot, so we know when they needed it somewhere without a stockist | Category × activity × slot curves in `categories.py`, adjusted by traits, archetype, and age (e.g. energy drinks peak on the morning commute, studying, gym, and night shifts; alcohol is 18+ on social evenings) |
| Notice | Do they register it on the shelf? | `SALIENCE_BASE[packaging_salience]` (1 → 0.12 … 5 → 0.60) × attention × `NOTICE_SCALE`, boosted by ad awareness and novelty seeking; once noticed, they stay aware |
| Price | Is it worth it? | `price_gbp` ÷ category reference price × price sensitivity, worse on low income |
| Belief | Does it fit who they are? | Diet flags vs. claims: halal vs. alcohol; caffeine avoider vs. caffeinated; health-conscious or low-sugar vs. sugary categories without `sugar_free`/`low_calorie`; vegan/vegetarian vs. animal-risk categories without a plant claim; halal vs. ready meals/snacks without a `halal` claim (modest) |
| Loyalty | Would they switch from their usual? | High brand loyalty and low novelty seeking → stays with the usual brand |
| Purchase | All checks passed | First purchase; repeat purchases at `REPEAT_BUY_P` = 0.25 |

Category reference prices (`categories.REF_PRICE`): energy drink £1.60, soft
drink £1.40, coffee RTD £2.20, snack £1.20, healthy snack £1.80, confectionery
£1.00, ready meal £4.00, alcohol £2.50, other £2.00.

**4. One outcome and one reason per agent:**

| Outcome | Reason | Meaning | Typical fix |
| --- | --- | --- | --- |
| `never_exposed` | `NO_STORE_NEARBY` | No stocking store anywhere along their week | Expand distribution along routes |
| `not_noticed` | `DIDNT_NOTICE` | Walked past it, didn't register it | Bolder packaging, eye-level placement, marketing |
| `no_need` | `NOT_THERE_WHEN_NEEDED` | Near it only when they didn't want it; wanted it elsewhere | Stock near stations, workplaces, campuses |
| `no_need` | `NO_NEED` | Noticed it, never wanted the category | Reposition around a clear use occasion |
| `rejected` | `TOO_EXPENSIVE` | Considered it; price said no | Price point, promotion, smaller pack |
| `rejected` | `BELIEF_CONFLICT` | Considered it; diet or beliefs said no | Reformulate, add claims (halal, vegan, sugar-free) |
| `rejected` | `LOYAL_TO_EXISTING` | Considered it; stuck with their usual | Sampling, trial promotions |
| `bought` | `BOUGHT` | Bought at least once | — |

For rejected agents, the reason is their most frequent failing check.

**5. Aggregates.** Funnel counts (total → exposed → noticed → needed → bought);
reason stats (`pct` = % of all agents, 0–100); segment stats per dimension
(`age_band`, `sex`, `ethnicity`, `borough`, `archetype`, `income_band`) with
total, interested (rejected + bought), bought, conversion (0–1 fraction), and
top non-buy reason.

**6. Traces.** Up to 25 human-readable events per agent, e.g. "Within 214 m of
Tesco Express while working at work; the product is stocked there" or "Wanted an
energy drink while commuting at transit, but no store stocking it was within
walking distance". These are what the LLM reads to role-play the agent, and what
the map's agent panel shows.

### Example run (Volt Rush, cached demo product)

An invented sugar-free energy drink at £1.89 in a bland grey can (salience 2),
stocked in 40% of Tesco and Co-op convenience stores across London, with light
TikTok marketing.

```
stocking 240 stores · exposed 1,303 · noticed 323 · needed 52 · bought 34 (1.7%)
DIDNT_NOTICE 49.0% · NO_STORE_NEARBY 34.9% · NO_NEED 7.2% · NOT_THERE_WHEN_NEEDED 6.4%
TOO_EXPENSIVE 0.5% · BELIEF_CONFLICT 0.2% · LOYAL_TO_EXISTING 0.2%
```

> *"I actually spotted it in Tesco Express on my commute and thought about grabbing
> one while out with mates on Saturday — but I avoid caffeine, so a 160mg can is a
> no from me."* — 19, male, Bangladeshi, student in Tower Hamlets

---

## 7. LLM layer

- **Provider**: DeepSeek (`deepseek-chat`) via the OpenAI-compatible SDK, JSON mode.
- **Interviews** (`llm/interviews.py`): a stratified, seeded sample of
  `INTERVIEW_COUNT` (default 80) agents. Every outcome/reason stratum is covered
  first, then buyers and rejecters are oversampled 3×, balancing age bands and
  ethnicities. Each agent gets a persona card (demographics, borough, job,
  traits in words, top media, diet flags, weekday routine), the product, their
  outcome, and their trace. The system prompt tells the model to stay consistent
  with the simulated facts and to be honest rather than agreeable, with a
  negative few-shot example to counter LLM buy-bias. Output: `{quote, bio}`.
- **Report** (`llm/report.py`): the product, funnel, reasons, top and bottom
  segments (min size 20), and all quotes go into one call. The output is validated
  into `Report`: headline, 3–5 key findings, rejection reasons, interested
  segments, and prioritised action items. The prompt includes a field glossary
  (salience is 1–5, coverage is a share, pct is 0–100).
- **Concurrency and timeouts**: 16 parallel calls (`LLM_CONCURRENCY`). A 45 s
  timeout applies per call, counted after acquiring a slot.
- **Fallbacks**: `chat_json` never raises; any failure returns `None`, which
  triggers template quotes (reason text + a natural "Think Tuesday morning, when
  I was on my way in" detail) and a template report. `source: "llm" | "template"`
  on every interview and report shows which path ran.

### Cost (measured)

| | Input tokens | Output tokens |
| --- | --- | --- |
| Per interview | ~1,160 | ~150 |
| Per run (80 interviews + report) | ~108k | ~13k |

About **$0.03–0.05 per run at most**. A full 80-interview run takes ~28 s. Real
spend during testing (1 tiny call, one 10-interview run, one 80-interview run)
didn't move the $7.79 balance by a visible cent. Repeat runs of the same product
cost nothing (cache). Set `INTERVIEW_COUNT=40` to halve per-run cost. The test
suite always runs with the LLM disabled.

---

## 8. API

Base URL `http://localhost:8000`; interactive docs at `/docs`. All types are in
`app/schemas.py`. CORS is open by default (`CORS_ORIGINS`).

| Method | Path | Returns | Use |
| --- | --- | --- | --- |
| GET | `/api/health` | `{status, agents, stores, llm}` | Backend up? LLM configured? |
| GET | `/api/agents` | `AgentPoint[]`: id, lat, lon, borough, age_band, sex, ethnicity, archetype, income_band | Draw the population on the map |
| GET | `/api/agents/{id}` | `Agent`: full profile + weekly schedule | Agent detail panel |
| GET | `/api/population/summary` | Counts by borough / age_band / sex / ethnicity / archetype / income_band + total | "Who lives in our London" panel |
| GET | `/api/stores?kind=&borough=` | `Store[]` | Store layer, stockist picker |
| POST | `/api/simulations` | `202 {id, status}` | Start a run (body: `ProductInput`). An identical product returns the cached id with `status: "done"` |
| GET | `/api/simulations` | `SimulationSummary[]` | History |
| GET | `/api/simulations/{id}` | `SimulationResult`; `?include_outcomes=false` drops the per-agent list | Poll every ~1.5 s until `done` / `failed` |
| GET | `/api/simulations/{id}/agents/{agent_id}` | `AgentTrace`: agent + outcome + week trace + interview | Click an agent on the map |

**Run lifecycle**: `queued` → `running` (progress: "Simulating 2,000 Londoners'
week") → outcomes, funnel, reasons, and segments are filled within ~1–2 s →
"Interviewing agents" → "Writing report" → `done`. On error: `failed` + `error`.

### `ProductInput`

```json
{
  "name": "Volt Rush",
  "category": "energy_drink",
  "description": "Sugar-free citrus energy drink, 160mg caffeine, 500ml can",
  "price_gbp": 1.89,
  "packaging_salience": 2,
  "packaging_description": "Matte grey can, small logo",
  "image_url": null,
  "claims": ["sugar_free", "caffeinated", "vegan"],
  "stockists": {
    "chains": ["Tesco", "Co-op"],
    "store_kinds": ["convenience"],
    "boroughs": [],
    "coverage": 0.4
  },
  "marketing_channels": ["tiktok"],
  "marketing_intensity": 0.3,
  "target_audience": "students and young professionals",
  "seed": 42
}
```

| Field | Values |
| --- | --- |
| `category` | `energy_drink`, `soft_drink`, `coffee_rtd`, `snack`, `healthy_snack`, `confectionery`, `ready_meal`, `alcohol`, `other` |
| `claims` | `vegan`, `vegetarian`, `halal`, `kosher`, `sugar_free`, `low_calorie`, `high_protein`, `organic`, `caffeinated`, `alcoholic`, `plant_based` |
| `marketing_channels` | `tiktok`, `instagram`, `youtube`, `x`, `facebook`, `tv`, `ooh`, `radio`, `podcast` |
| `packaging_salience` | 1 (bland) to 5 (loud). The LLM is text-only, so this plus `packaging_description` stands in for the image; `image_url` is stored for display |
| `stockists` | Empty `chains`/`boroughs` = everywhere; `coverage` 0–1 = share of matching stores that stock it |
| `seed` | Same seed + same product = identical result (and cache hit) |

### `SimulationResult` (abridged)

```json
{
  "id": "d499bb2f9b05",
  "status": "done",
  "progress": "Complete",
  "stores_stocking": 240,
  "funnel": { "total": 2000, "exposed": 1303, "noticed": 323, "needed": 52, "bought": 34 },
  "reasons": [ { "code": "DIDNT_NOTICE", "label": "Walked past the product but never noticed it", "count": 980, "pct": 49.0 } ],
  "segments": [ { "dimension": "archetype", "value": "shift_worker", "total": 112, "interested": 6,
                  "bought": 5, "conversion": 0.0446, "top_reason": "NO_STORE_NEARBY" } ],
  "outcomes": [ { "agent_id": "a00042", "lat": 51.54, "lon": -0.06, "outcome": "no_need",
                  "reason": "NOT_THERE_WHEN_NEEDED", "exposures": 6, "noticed": true, "purchases": 0 } ],
  "interviews": [ { "agent_id": "a01344", "name": "…", "persona": "19, male, Bangladeshi, student in Tower Hamlets…",
                    "outcome": "rejected", "reason": "BELIEF_CONFLICT", "quote": "…", "source": "llm" } ],
  "report": { "headline": "…", "key_findings": ["…"],
              "rejection_reasons": [ { "title": "…", "detail": "…" } ],
              "interested_segments": [ { "title": "…", "detail": "…" } ],
              "action_items": [ { "action": "…", "rationale": "…", "priority": "high" } ],
              "source": "llm" }
}
```

---

## 9. Integration with UX-FLOW.md

How the demo acts map onto this API:

| UX-FLOW | Backend |
| --- | --- |
| Map centred on London | `GET /api/agents` (2,000 points) and `GET /api/stores` |
| Act 1 interview → product profile | Build a `ProductInput` (mapping below) |
| Act 3 "Simulate my product here" on an area | `POST /api/simulations` with `stockists.boroughs = [that area's borough]` |
| Agent narratives first | `result.interviews[]` (`persona` + `quote`); click-through via `/api/simulations/{id}/agents/{agent_id}` |
| Cluster verdict table (adopt / reject / ignore + drivers) | `result.segments` filtered to `dimension == "archetype"` (or `age_band`): bought → adopt, rejected → reject, not_noticed / no_need / never_exposed → ignore; `top_reason` → driver tag |
| Act 4 decision brief | `result.report` (headline, findings, action items) |

**Interview → `ProductInput` mapping:**

| Interview question | Field |
| --- | --- |
| Product name + one-liner | `name`, `description` |
| Category | `category` (map below) |
| Price point + pack size | `price_gbp` (put pack size in `description`) |
| Who do you think buys it? | `target_audience` |
| Why would someone reject it? | Append to `description`; set matching `claims` |
| Where would it sell best? | `stockists.boroughs` (to test the bet), or leave empty and compare boroughs in `segments` |

**Category mapping** (UX-FLOW categories are broader than the engine's need
curves): beverages → `soft_drink`, `energy_drink`, `coffee_rtd` (use this for
the **hojicha RTD** example), or `alcohol`; snacks & confectionery → `snack`,
`healthy_snack`, or `confectionery`; ready meals → `ready_meal`; sauces &
condiments, dairy & alternatives, bakery → `other` (generic need curve, until
dedicated curves are added in `categories.py`).

**Open gaps vs. UX-FLOW** (not built yet):

- Opportunity-circle scoring (trend heat, competitor gap, shelf whitespace,
  demographic fit) is a research-dashboard feature, not part of this backend. The
  simulation can supply the *demographic fit* and *shelf whitespace* inputs via
  per-borough `segments` and `/api/stores`.
- Bets settled inline, citations, and the back-test slide are not implemented.
- Pre-run the hojicha RTD example before the demo so it is served from cache.

---

## 10. Running, testing, tuning

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # macOS/Linux: .venv/bin/pip
cp .env.example .env                                  # set DEEPSEEK_API_KEY (optional)
python -m app.pipeline.build_population               # only if data/processed/ is missing
python -m uvicorn app.main:app --reload --port 8000   # docs at http://localhost:8000/docs
python -m pytest -q                                   # 25 tests, LLM disabled, ~13 s
```

**Environment variables** (`app/config.py`): `DEEPSEEK_API_KEY`,
`DEEPSEEK_MODEL` (deepseek-chat), `DEEPSEEK_BASE_URL`, `INTERVIEW_COUNT` (80),
`LLM_CONCURRENCY` (16), `LLM_TIMEOUT_S` (45), `POPULATION_SIZE` (2000),
`POPULATION_SEED` (7), `WALK_RADIUS_M` (400; the grid supports up to ~550),
`CORS_ORIGINS` (*).

**Tuning knobs:**

| Knob | File | Effect |
| --- | --- | --- |
| `NOTICE_SCALE`, `SALIENCE_BASE` | `simulation/engine.py` | How often exposed agents notice the product |
| `REPEAT_BUY_P` | `simulation/engine.py` | Repeat purchases within the week |
| `PROFILES` (need curves), `REF_PRICE` | `simulation/categories.py` | When each category is wanted; price anchors |
| `HUBS`, `LOCAL_WEIGHT` | `population/geography.py` | Where commuters work |
| WFH / shift probabilities, income mapping | `population/sampler.py` | Archetype mix |

After changing population code, rebuild with `python -m app.pipeline.build_population`
and commit the new `data/processed/` files. Cached simulation results in
`data/simulations/` should be deleted after changing engine or prompt logic.

**Before a demo:** start the server, run each demo product once (results are
cached; repeat clicks are instant and free), and check `report.source == "llm"`.

---

## 11. v2 upgrade path

- IPF joint-distribution synthesis for realistic age × ethnicity × occupation combinations.
- Census origin–destination flows (blended with pre-COVID data) for commutes.
- ONS Time Use Survey for schedules; Family Food / NDNS for category baselines.
- Ground agent attitudes in scraped human signals from the research dashboard,
  merging this population with the persona-cluster model in PROJECT.md.
- Social spread between agents (word of mouth, TikTok virality).
- Multi-week runs with memory and repeat-purchase habits.
- Postgres behind `store.py`; dedicated need curves for sauces, dairy, and bakery.
