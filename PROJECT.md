# HUMAN PORTAL

**AI-simulated people for food & beverage decisions.**

HUMAN PORTAL is an application that uses AI to simulate real, day-to-day people. It
understands how people choose, trust, or reject products — and turns that understanding
into something a brand or retailer can act on. It helps them make a better decision,
or spots a decision they should be making but aren't.

Hackathon demo UX (the flow we build first): see **UX-FLOW.md**.

---

## The two problems we sell solutions to

1. **Understanding real people at scale.** Brands and retailers can't interview a
   thousand shoppers before every decision. Human opinion data is scattered across
   TikTok comments, Reddit threads, reviews, and shelves — noisy, unaggregated, and
   slow to read.
2. **Seeing your product's future before you commit.** Launching or stocking an F&B
   product is a bet. There's no cheap way to ask "would this persona actually buy
   this?" before the SKU, the slotting fee, and the marketing spend are already sunk.

## Who it's for

- **Brands / manufacturers** deciding what to build, launch, reformulate, or kill.
- **Retailers** deciding what to stock, shelve, promote, or delist.

Indie creators are welcome as users, but the product is designed and priced for
decision-makers at brands and retailers.

**Vertical: food & beverage only (v1).** Trends, personas, shelf intel, and the
simulation engine are all tuned to F&B. The data model should not paint us into a
corner, but F&B is the wedge.

**Launch market: UK first.** England for v1 statistics — ONS covers England &
Wales; Scottish (NRS) and Northern Irish (NISRA) agency stitching is deferred.
London-weighted data collection is acceptable for v1.

---

## Core ideas

### Human signals

The atomic unit of HUMAN PORTAL is the *human signal*: evidence of a real person's
taste, distrust, craving, habit, or rejection — pulled from public social data and
product reviews. What matters most is the human signal, not the volume metric. Every
trend and every persona we surface must trace back to real signals, and the dashboard
shows the people behind them: age, gender, job, location, habits, sentiment.

### Simulated people (persona clusters)

The simulation is populated by LLM-driven agents, each grounded in a **cluster of
real human signals** derived from the data — not a fixed cast, and not an arbitrary
number. If the data clusters into 12 distinct persona types for a market, the sim
runs 12 agents; if 30, it runs 30. Each agent is a believable person (age, job,
tastes, skepticisms) whose behavior is constrained by what real people like them
actually said and did.

### Decisions, not dashboards

Every screen ends in an action: *launch this*, *reformulate that*, *this region is
under-shelved*, *this segment will reject on price*. A beautiful trend chart that
changes nothing is a failure for this product.

---

## Main features

### 1. Research dashboard — the constant returning feature

A user researching a product area or trend gets a snapshot of data. This is the
home base users return to. It includes:

- **Trend discovery feed** — rising and falling F&B trends with velocity and
  sources, e.g. *"hojicha is becoming dominant"* backed by TikTok sounds, Reddit
  threads, and search interest — not just a count of mentions.
- **Human signal cards** — for any searched area: who the people behind the trend
  are (age, gender, job, location), what they're saying, and whether they trust
  or reject it.
- **Competitor & shelf intel** — who else plays in the space, what's shelved in
  certain regions, pricing signals — from data we scrape and aggregate in the
  backend.
- **Saved snapshots & history** — past searches and simulations, so returning
  users see how the ground has moved since last time.

**Free tier: 35 free searches.** A search = one dashboard area/trend lookup.
Simulation runs do **not** consume free searches — they are paid-only.

### 2. Market simulation — the paid showcase

The same dashboard data powers a MiroFish-style simulation: a swarm of simulated
agents (one per clustered persona) living in a simulated market, acting on the
real signals we gathered. A user introduces their product — flavor, price point,
positioning, packaging — and watches how the agents discover it, try it, adopt it,
ignore it, or reject it, and *why*.

This is not a fixed cast of 20 agents — the agent population emerges from
clustering the human signals for that market. More, richer human signals → more,
richer agents → better simulation.

> **Hackathon v1 build:** the simulation ships as a census-grounded population of
> 2,000 individual Londoners living a simulated week. See
> [Market simulation engine (v1, London)](#market-simulation-engine-v1-london)
> for the architecture, data sources, logic, and API.


### 3. Product demo mode — "see it on the shelf yourself"

A guided demo that lets a user experience the product through their own category:
we show them the competitors in their region and what's actually shelved in
certain areas (from our scraped backend shelf/competitor data), then run the
simulation against that real landscape. The demo answers: *who am I up against,
where, and would anyone actually pick me?*

---

## Data sources

### Confirmed for v1

UK-targeted. Platform access paths marked ✅ were verified live 2026-10 and are
region-agnostic (now pointed at GB); UK-specific sources are pending a UK
verification round — scheduled next.

**Social & planning signals**

| Source | Access | What it gives us |
| --- | --- | --- |
| TikTok ⚠️ | ✅ Verified: commercial API (~$50–150/mo) *or* self-hosted Playwright interceptor. Target UK via UK hashtags/sounds; no region field — infer from bio/language. TikTok-Api lib returns empty | Trends, sounds, comments, engagement — the fastest F&B signal stream |
| Reddit | ✅ Verified: official OAuth API (100 QPM) + Arctic Shift 90-day backfill. UK subreddit list (~40–60: r/CasualUK, r/AskUK, r/ukfood, r/britishproblems, r/aldi_uk, …). 48h deleted-content purge | Threads & comments: honest enthusiasm and rejection language |
| YouTube | ✅ Verified: official Data API v3 (search has its own ~100-call/day bucket; ~3k videos/day comment harvest). relevanceLanguage=en; GB channel seeds | Comments, review/trend video reactions |
| X / Twitter ⚠️ | ✅ Verified: pay-per-usage API only (~$5–35/mo for recent search). No free tier; Nitter dead; syndication endpoint hydrates known tweet IDs free | Trend chatter, launch reactions |
| Instagram ⚠️ | ✅ Verified: no clean path — best-effort logged-in instaloader (ToS risk, account may die) or approval-gated Graph API (30 hashtags/week cap) | Reels, comments, hashtag momentum |
| Pinterest | ✅ Verified: Predicts pages embed full trend JSON; en-gb pages carry UK-localized stats | Planning-intent signals |

**Commerce, reviews & shelf**

| Source | Access | What it gives us |
| --- | --- | --- |
| Ocado reviews + assortment | Direct page scraping — first UK SKU-attached corpus (grocery-pure, skews older/affluent). **Pending UK verification** | Trust/rejection language attached to actual SKUs + what's shelved |
| trolley.co.uk | Aggregated prices/promos across Big 4 + discounters in one scrape. **Pending UK verification** | Weekly pricing/promotion landscape |
| Google Trends | ✅ Verified: pytrends with `urllib3<2` pin, geo='GB' | Search-interest baselines to validate social spikes |

No official grocery API exists in the UK (the Kroger model has no equivalent) —
aggregator-first for prices, direct scrape for assortment/reviews.

**Grounding, context & events**

| Source | Access | What it gives us |
| --- | --- | --- |
| ONS Census 2021 (Nomis API) | Official, free. England & Wales; Scotland via NRS; NI deferred. **Pending UK verification** | Persona grounding: demographics by local authority |
| ONS Family Food survey / NDNS / Index of Multiple Deprivation | Official published tables — household food spend, real dietary intake, deprivation. **Pending UK verification** | Food spend, diet behavior, price-sensitivity segments |
| FSA Food Alerts | Food Standards Agency API + RSS — allergy alerts, recalls, "do not eat" warnings. **Pending UK verification** | Recall waves as trust signals; agents react |
| Seasonality | Open-Meteo (no key) + full UK cultural calendar — Christmas, Easter, Bonfire Night, Pancake Day, Ramadan/Eid, Diwali, Lunar New Year | Simulated people react to seasons and cultural moments |
| UK food media | Grocery Gazette, FoodBev Media, Talking Retail (free); The Grocer optional (paywalled) — **pending UK verification** | Structured launch/failure events the sim reacts to |
| User-uploaded surveys | CSV importer (v1: survey exports only) | First-party declared demographics & stated preferences |

### Ingestion policy (locked 2026-10, UK pivot)

- **Language:** English only at ingest. Revisit UK community languages
  (Polish, Urdu, Punjabi, Bengali, Arabic) in v2 if clustering shows a gap.
- **Geography:** every signal carries postcode + local authority where
  derivable; personas cluster at local-authority level.
- **Backfill:** 90 days of history on each adapter's first run — enough for
  trend velocity, bounded crawl cost.
- **Storage:** raw payload (JSONB) + normalized human-signal record. Raw is
  re-processable when the schema evolves. Reddit-sourced content must be
  purged within 48h when the author deletes it (Reddit terms).
- **Author identity:** public handles stored as-is. Provenance — showing the
  real person behind a signal — is core to the product; review if legal asks.
- **Shelf refresh:** weekly prices / monthly full assortment. Demo-mode shelf
  coverage: Big 4 + discounters (Tesco, Sainsbury's, Asda, Morrisons, Aldi,
  Lidl) via trolley.co.uk + Ocado.
- **Trend verification:** a trend claim earns "verified" only when corroborated
  by ≥2 independent source families (e.g. TikTok + Reddit, or social +
  search). Enforced in the trend feed, not just by convention.
- **Buy vs build:** build/scrape only. Paid listening platforms (Brandwatch,
  Spate, Tastewise, Datassential) may be consulted as validation ground truth
  but are not data feeds.

### Source verification (status)

- **Verified 2026-10, region-agnostic (now targeting GB):** Reddit (OAuth,
  100 QPM, + Arctic Shift backfill), YouTube (official API), Pinterest
  (Predicts embedded JSON), Google Trends (pytrends, `urllib3<2` pin), TikTok
  (commercial API or Playwright interception; both confirmed working), X
  (pay-per-usage only — budget decision), Instagram (no clean path —
  best-effort only).
- **Pending UK verification round:** trolley.co.uk scraping, Ocado
  review/assortment scraping, FSA Food Alerts API, ONS Nomis, ONS Family Food
  / NDNS / IMD tables, Open-Meteo, UK food-media feeds, UK subreddit list
  sanity-check.
- **US expansion:** US sources were verified working on 2026-10-03 but detail
  is stripped from this doc per decision; US launch requires re-verification
  at that time.

### Candidates for v2+

Deferred sources, roughly in priority order:

- **Menu intelligence** — Datassential/Spate/Mintel as validation ground truth.
- **Delivery & grocery apps** — Deliveroo/Just Eat/UberEats review corpora and
  availability by postcode.
- **Recipes & cooking sites** — BBC Good Food, Allrecipes UK comments; leading
  indicator for packaged F&B.
- **Google Maps reviews** — regional taste maps and complaint language.
- **Beverage verticals** — Untappd, Vivino: review-heavy beer/wine communities.
- **DTC review platforms** — Yotpo/Bazaarvoice endpoints: one integration,
  hundreds of DTC F&B brands.
- **Local chatter** — Facebook Groups, Nextdoor UK: hyperlocal taste signal.
- **Menu/LTO tracker** — chain menu-page scraping for limited-time-offer
  launches; trade-show exhibitor lists (Lunch!, Speciality & Fine Food Fair,
  Farm Shop & Deli Show).
- **Forecast reports** — Waitrose Food & Drink Report, Sainsbury's Future of
  Food, Mintel UK as sanity checks.
- **Food podcasts** — BBC The Food Programme, Off Menu transcripts (needs
  summarization pipeline).
- **Job postings** — new-store openings, dark kitchens, CPG expansion signals.

> **Note on TikTok-Api:** it is an unofficial library and breaks often as TikTok
> changes. Treat it as one signal among several, never the sole basis for a trend
> claim, and wrap it behind an adapter so it can be swapped.

---

## Market simulation engine (v1, London)

*Owner: backend/simulation. Status: hackathon demo build — implemented and
tested. Full backend documentation (file-by-file, tuning, costs, UX-FLOW
integration): [`backend/backend.md`](backend/backend.md).*

A retailer describes an F&B product and where it will be stocked. We release it
into a simulated London of **2,000 individual adults**, each with a real home
neighbourhood, a job or study place, a weekly routine, a personality, media habits,
and diet/belief constraints. Over one simulated week they walk past (or never go
near) the stores that stock it, notice it (or don't), need it at that moment (or
don't), and buy or reject it. Every agent ends with **an outcome and a reason**;
a sample of agents is interviewed by the LLM in their own voice, and the results
are summarised into a decision-ready report.

**Why London:** the UK publishes free, commercially usable census data down to
~8,000-person neighbourhoods (MSOAs). That lets us claim the population *is*
London rather than a guess, and it matches the UK launch market and the London
demo geography in UX-FLOW.md. (The ONS Census / Nomis source listed above as
"pending UK verification" is verified and in use here.)

### Design principles

1. **Real data for facts, generation for the gaps.** Demographics, geography and
   stores come from public data; personality, routines and media habits are
   generated by rules conditioned on those facts and are labelled as modelled.
2. **Python counts, the LLM explains.** The funnel (who was where, who noticed,
   who needed it, who could afford it) is deterministic, seeded Python — fast,
   reproducible, and right about numbers. The LLM is used only for ~80 first-person
   interviews and one summary report per run. A run costs cents, not dollars, and
   finishes in about a minute.
3. **Never break the demo.** No API key, a timeout, or bad JSON from the LLM falls
   back to templated quotes and a templated report. Identical products return the
   cached result instantly.

### Data sources (all verified working, all commercial-safe)

| Layer | Source | Licence | How we use it |
| --- | --- | --- | --- |
| Who lives where | **Nomis Census 2021** bulk tables at MSOA level: TS007A age, TS008 sex, TS021 ethnicity, TS030 religion, TS063 occupation, TS061 travel-to-work mode, TS066 economic activity | OGL v3 | Per-neighbourhood distributions each agent is sampled from |
| Where neighbourhoods are | **ONS MSOA 2021 population-weighted centroids** (ONS Open Geography ArcGIS service) | OGL v3 | Agent home points (centroid + jitter) and store → borough lookup |
| Where products can be sold | **OpenStreetMap** via Overpass: `shop=convenience|supermarket` (~5k in London) with brand tags | ODbL (attribute OSM) | The store universe a retailer picks stockists from |
| Where people go | **OpenStreetMap** gyms and universities + a hand-curated list of ~12 London job hubs (City, West End, Canary Wharf, King's Cross, Shoreditch, Stratford, Croydon, …) | ODbL / ours | Work, campus and gym locations |
| Everything else | **Rule-based generator** (ours) | — | Big Five personality, attention, price sensitivity, brand loyalty, media mix by age, diet flags from religion + base rates, schedule templates |

**Deliberately not used in v1** (and why): IPF synthesis / UK Data Service
microdata (research-only licences, days of work); Census origin–destination flow
matrix (large, COVID-distorted — replaced by the job-hub gravity model); ONS Time
Use Survey (replaced by archetype schedules); dunnhumby (US data); WVS/EVS
(non-commercial). These are the v2 upgrade path for accuracy.

**Known simplifications:** traits are sampled independently per neighbourhood
(joint distributions such as age × ethnicity are approximate); income is inferred
from occupation (the census has no income question); the population covers adults
16+.

### Architecture

```
 OFFLINE (run once, output committed)                ONLINE (per simulation run)
 ─────────────────────────────────────               ─────────────────────────────────────────
 Nomis census ─┐                                     ProductInput (from frontend)
 ONS centroids ├─► pipeline/build_population ─►      │
 OSM shops,    │     population/sampler   (who)      ▼
 gyms, unis  ──┘     population/geography (where)    simulation/engine.run_funnel   (Python, ~seconds)
                     population/schedules (when)       stockists → exposure → notice → need
                     population/traits    (how)        → price / belief / loyalty → purchase
                          │                            = outcome + reason + trace per agent
                          ▼                          │
             data/processed/agents.json  ───────────►│
             data/processed/stores.json              ▼
                                                     llm/interviews  (~80 agents, DeepSeek, parallel)
                                                     llm/report      (1 call → findings + actions)
                                                     │
                                                     ▼
                                                     store.py (JSON cache) ─► FastAPI ─► React map
```

```
backend/
  requirements.txt  .env.example
  app/
    main.py            FastAPI app, CORS, routers
    config.py          paths + settings (env vars)
    schemas.py         the data contract (Pydantic) — frontend types mirror this
    store.py           load population, cache simulation results (JSON files)
    api/               population.py, simulations.py
    pipeline/          fetch_census.py, fetch_centroids.py, fetch_pois.py, build_population.py
    population/        sampler.py, geography.py, schedules.py, traits.py
    simulation/        engine.py, funnel.py, categories.py, reasons.py
    llm/               client.py, prompts.py, interviews.py, report.py
  data/raw/            downloaded source files (gitignored)
  data/processed/      agents.json, stores.json (committed so nobody has to rebuild)
  tests/
```

### Simulation logic

**Building the population (offline).**

1. Allocate 2,000 agents across London's ~1,000 MSOAs in proportion to adult
   population.
2. For each agent, sample age, sex, ethnicity and religion from that MSOA's census
   counts. Economic status comes from age and local shares (students skew 16–24,
   retirees 66+). Occupation and travel mode come from local shares if working.
   Income band is derived from occupation group.
3. Assign an **archetype**: office commuter, shift worker, student, work-from-home,
   retired, or carer.
4. Place them. Home = neighbourhood centroid + ~250 m jitter. Commuters get a job
   hub weighted by size and distance (or a local job). Students get a nearby
   university.
5. Give them a **week**: weekday and weekend schedules of 7 time slots (early
   morning, morning, midday, afternoon, evening, late evening, night), each with a
   place (home, transit, work, campus, local, central, gym), an activity, and
   coordinates.
6. Give them **traits**: Big Five, attention, novelty seeking, price sensitivity,
   health consciousness, brand loyalty; media exposure per channel (TikTok,
   Instagram, YouTube, X, Facebook, TV, out-of-home, radio, podcast) by age and
   commute; diet flags (halal, kosher, vegetarian, vegan, low sugar, caffeine
   avoider) from religion and base rates.

**Running a product (online).** For each agent, for each of the 49 slots in the week:

| Step | Question | Driven by |
| --- | --- | --- |
| Stockists | Which stores carry it? | Chosen chains, store kinds, boroughs, and coverage % |
| Exposure | Is a stocking store within ~400 m of where they are right now? | Schedule coordinates |
| Need | Do they want this category *right now*? | Category × activity × time-slot curves (e.g. energy drinks peak on the morning commute, studying, gym, night shifts) and traits |
| Notice | Do they register it on the shelf? | Packaging salience (1–5), attention, novelty seeking, and ad awareness from marketing channels they actually consume |
| Price | Is it worth it? | Price vs category reference price, price sensitivity, income band |
| Belief | Does it fit who they are? | Diet flags vs product claims (halal, vegan, sugar-free, caffeine…) |
| Loyalty | Would they switch from their usual? | Brand loyalty vs novelty seeking |

Each agent ends with one **outcome** and one **reason**:

| Outcome | Reason codes |
| --- | --- |
| `never_exposed` | `NO_STORE_NEARBY` — never within reach of a stocking store |
| `not_noticed` | `DIDNT_NOTICE` — walked past it, didn't register it (packaging/awareness problem) |
| `no_need` | `NOT_THERE_WHEN_NEEDED` — near it only when they didn't want it, wanted it elsewhere · `NO_NEED` — never wanted the category |
| `rejected` | `TOO_EXPENSIVE` · `BELIEF_CONFLICT` · `LOYAL_TO_EXISTING` |
| `bought` | `BOUGHT` |

Results are aggregated into a funnel (total → exposed → noticed → needed → bought),
reason shares, and **segment breakdowns** (age band, sex, ethnicity, borough,
archetype, income band) showing who was interested and why the rest said no.
The LLM then interviews a stratified sample (every outcome represented, buyers and
rejecters oversampled) with the agent's persona and simulated week as context,
prompted to be honest rather than agreeable (LLM agents are known to skew towards
buying). A final report call turns the numbers and quotes into **headline, key
findings, rejection reasons, interested segments, and prioritised action items**.

### API (for the frontend)

Base URL: `http://localhost:8000`. Interactive docs at `/docs`. All types are
defined in `backend/app/schemas.py`.

| Method | Path | Returns | Use |
| --- | --- | --- | --- |
| GET | `/api/health` | `{status, agents, stores, llm}` | Is the backend up, is the LLM configured |
| GET | `/api/agents` | `AgentPoint[]` (id, lat, lon, borough, age_band, sex, ethnicity, archetype, income_band) | Draw the population on the map |
| GET | `/api/agents/{id}` | `Agent` (full profile + weekly schedule) | Agent detail panel |
| GET | `/api/population/summary` | counts by borough / age_band / sex / ethnicity / archetype / income_band | "Who lives in our London" panel |
| GET | `/api/stores?kind=&borough=` | `Store[]` | Store layer + stockist picker |
| POST | `/api/simulations` | `202 {id, status}` | Start a run with a `ProductInput` body |
| GET | `/api/simulations` | `SimulationSummary[]` | History |
| GET | `/api/simulations/{id}` | `SimulationResult` (add `?include_outcomes=false` to skip the per-agent list) | Poll every ~1.5 s until `status == "done"` |
| GET | `/api/simulations/{id}/agents/{agent_id}` | `AgentTrace` (agent + outcome + week trace + interview) | Click an agent on the map |

**`ProductInput`** (POST body):

```json
{
  "name": "Volt Rush",
  "category": "energy_drink",
  "description": "Sugar-free citrus energy drink, 160mg caffeine",
  "price_gbp": 1.89,
  "packaging_salience": 2,
  "packaging_description": "Matte grey can, small logo",
  "image_url": null,
  "claims": ["sugar_free", "caffeinated", "vegan"],
  "stockists": {
    "chains": ["Tesco", "Co-op"],
    "store_kinds": ["convenience"],
    "boroughs": ["Hackney", "Tower Hamlets"],
    "coverage": 0.4
  },
  "marketing_channels": ["tiktok", "ooh"],
  "marketing_intensity": 0.3,
  "target_audience": "students and young professionals",
  "seed": 42
}
```

`category`: `energy_drink | soft_drink | coffee_rtd | snack | healthy_snack |
confectionery | ready_meal | alcohol | other`.
`claims`: `vegan | vegetarian | halal | kosher | sugar_free | low_calorie |
high_protein | organic | caffeinated | alcoholic | plant_based`.
`marketing_channels`: `tiktok | instagram | youtube | x | facebook | tv | ooh |
radio | podcast`. Empty `chains`/`boroughs` = everywhere. The LLM is text-only,
so packaging is described by `packaging_salience` (1 = bland, 5 = loud) plus an
optional text description; `image_url` is stored for display.

**`SimulationResult`** (GET, abridged):

```json
{
  "id": "3f9c1a2b7d4e",
  "status": "running | done | failed | queued",
  "progress": "Interviewing agents",
  "stores_stocking": 212,
  "funnel": { "total": 2000, "exposed": 640, "noticed": 210, "needed": 95, "bought": 41 },
  "reasons": [ { "code": "NO_STORE_NEARBY", "label": "...", "count": 1360, "pct": 68.0 } ],
  "segments": [ { "dimension": "age_band", "value": "16-24", "total": 260, "interested": 30,
                  "bought": 14, "conversion": 0.054, "top_reason": "NOT_THERE_WHEN_NEEDED" } ],
  "outcomes": [ { "agent_id": "a00042", "lat": 51.54, "lon": -0.06, "outcome": "no_need",
                  "reason": "NOT_THERE_WHEN_NEEDED", "exposures": 6, "noticed": true, "purchases": 0 } ],
  "interviews": [ { "agent_id": "a00042", "name": "...", "persona": "24, female, student in Hackney…",
                    "outcome": "no_need", "reason": "NOT_THERE_WHEN_NEEDED",
                    "quote": "I'd grab one before a lecture, but…", "source": "llm" } ],
  "report": { "headline": "...", "key_findings": ["..."],
              "rejection_reasons": [ { "title": "...", "detail": "..." } ],
              "interested_segments": [ { "title": "...", "detail": "..." } ],
              "action_items": [ { "action": "...", "rationale": "...", "priority": "high" } ],
              "source": "llm | template" }
}
```

`reasons[].pct` is a percentage of all agents (0–100); `segments[].conversion` is a
0–1 fraction.

Outcomes are filled as soon as the funnel finishes (a few seconds), so the map can
colour agents while interviews and the report are still generating.

### Running it

```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # macOS/Linux: .venv/bin/pip
cp .env.example .env            # add DEEPSEEK_API_KEY (optional — templates without it)
python -m app.pipeline.build_population   # only if data/processed/ is missing
python -m uvicorn app.main:app --reload --port 8000
```

### v2 upgrade path

IPF joint-distribution synthesis; Census origin–destination flows for commutes;
ONS Time Use Survey for schedules; Family Food / NDNS for category baselines;
grounding agent attitudes in scraped human signals (the research dashboard data),
which merges this population with the persona-cluster model above; social spread
between agents; multi-week runs with memory.

---

## Monetization

- **Free:** 35 dashboard searches. Simulations are not free — they're the reason
  to pay.
- **Paid:** subscription unlocks simulation runs (and expanded/continued
  searches).
- **Demo scope honesty:** v1 includes the paywall logic (sim runs gated for paid
  users) but **no real payments** — it's a demo.

## How we measure success

**North star: decisions influenced.** v1 works when a user runs a simulation and
changes a real product or market decision because of it. Secondary signals:
return rate to saved snapshots, free→paid conversion after the 35 searches.

---

## Tech stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Backend | **Python** | Natural fit for scraping pipelines + data science (clustering, signal processing) |
| Frontend | **Next.js 16 (App Router) + shadcn/ui** | SSR/SSG shell for the dashboard, sim UI, and demo mode |
| Map | **Leaflet + react-leaflet** | OSM base tiles; signal / shelf / persona overlays |
| LLM | **DeepSeek** (single provider v1) | Persona reasoning + signal summarization |
| Database | **PostgreSQL** | See below |

### Running Postgres locally (the demo story)

Yes — Postgres runs locally, and the demo setup is deliberately boring:

- **Default: Postgres in Docker Compose.** One `docker compose up` gives every
  developer (and any demo laptop with Docker) the same database. This is the
  recommended path.
- **Zero-setup fallback: SQLite** via the same ORM layer for anyone who can't run
  Docker — fine for demos, not for production parity.
- **Later: a free cloud branch** (Neon/Supabase) when we need shared/staging
  demos or production. Same Postgres, no code change.

## Proposed architecture

```
 scrapers/adapters (TikTok, Reddit, YT, X, reviews, shelf, …)
        │
        ▼
 signal store ──► clustering ──► persona clusters ──► simulation engine
 (Postgres)         │                  │                    │
        │           ▼                  ▼                    ▼
        └────► trend feed ◄──── human signal cards ◄── sim results
                        │
                   FastAPI backend ──► Next.js 16 + shadcn/ui frontend
```

- **Ingestion service** — per-source adapters normalizing everything into
  human-signal records (who, what, sentiment, source, timestamp, region).
- **Clustering** — group signals into persona clusters per market; the cluster
  count *is* the agent count.
- **Simulation engine** — LLM (DeepSeek) agents, one per cluster, behaving per
  their grounded signals; runs the market sim against a user's product.
- **API** — FastAPI serving searches, snapshots, sim runs, paywall state.
- **Frontend** — dashboard, signal cards, sim visualization, demo mode.

---

## Roadmap

1. **Phase 0 — Foundations.** Repo scaffolding (`backend/`, `frontend/`), Docker
   Compose Postgres, ingestion adapter for 2 sources (TikTok + Reddit), signal
   schema.
2. **Phase 1 — Dashboard MVP.** Search → trend feed + human signal cards for a
   few F&B categories; saved snapshots; the 35-search counter.
3. **Phase 2 — Clustering & personas.** Signal clustering → persona clusters
   rendered as people (age, job, habits) on the dashboard.
4. **Phase 3 — Simulation.** Paid-gated sim runs: agents-per-cluster reacting to
   a user's product; "why they rejected it" output.
5. **Phase 4 — Demo mode.** Competitor/shelf intel + guided demo flow for a
   user's own category.
6. **Phase 5 — Remaining sources & monetization plumbing.** YouTube/X/reviews/
   Instagram/Google Trends; subscription integration.

## Open questions

- Exact subscription pricing/tiers — deliberately undecided until sim value is
  proven on real users.
- Multi-region expansion timing after UK launch (Scotland/Wales/NI statistical
  coverage first, then US — US sources require re-verification).
- When to promote v2 candidate sources into the pipeline (delivery-app corpora
  and Google Maps reviews are the leading candidates).
