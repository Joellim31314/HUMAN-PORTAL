# HUMAN PORTAL

**AI-simulated people for food & beverage decisions.**

HUMAN PORTAL is an application that uses AI to simulate real, day-to-day people. It
understands how people choose, trust, or reject products — and turns that understanding
into something a brand or retailer can act on. It helps them make a better decision,
or spots a decision they should be making but aren't.

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

**Launch market: US first.**

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

### 3. Product demo mode — "see it on the shelf yourself"

A guided demo that lets a user experience the product through their own category:
we show them the competitors in their region and what's actually shelved in
certain areas (from our scraped backend shelf/competitor data), then run the
simulation against that real landscape. The demo answers: *who am I up against,
where, and would anyone actually pick me?*

---

## Data sources

### Confirmed for v1

Sourcing decisions locked 2026-10 (see *Ingestion policy* below).

**Social & planning signals**

| Source | Access | What it gives us |
| --- | --- | --- |
| TikTok | [TikTok-Api](https://github.com/davidteather/TikTok-Api), adapter-wrapped | Trends, sounds, comments, engagement — the fastest F&B signal stream |
| Reddit | Official API, curated subreddit list (~40–60 food subs) | Threads & comments: honest enthusiasm and rejection language |
| YouTube | Official API | Comments, review/trend video reactions |
| X / Twitter | API/scrape | Trend chatter, launch reactions |
| Instagram | Scrape | Reels, comments, hashtag momentum |
| Pinterest | Trends page + Pinterest Predicts report | Planning-intent signals ("mini desserts up 529%") |

**Commerce, reviews & shelf**

| Source | Access | What it gives us |
| --- | --- | --- |
| Walmart reviews | Direct page scraping (first SKU-attached corpus) | Trust/rejection language attached to actual SKUs |
| Kroger product & price API | Official developer API | Shelf/pricing ground truth, price by ZIP |
| Flipp | Aggregated circulars | Pricing/promotion landscape across US chains |
| Google Trends | pytrends | Search-interest baselines to validate social spikes |

**Grounding, context & events**

| Source | Access | What it gives us |
| --- | --- | --- |
| Census ACS / BLS / USDA ERS / CDC NHANES | Official APIs & CSVs | Persona grounding: demographics, food spend, food access, real dietary intake by region |
| FDA + USDA FSIS recall feeds | RSS/API | Recall waves as trust signals; agents react |
| Seasonality | NOAA weather + holiday/event calendar | Simulated people react to seasons (grilling, pumpkin spice, January diets) |
| Food-media event feeds | Scrape: Food Dive, Food Navigator-USA, BevNET | Structured launch/failure events the sim reacts to |
| User-uploaded surveys | CSV importer (v1: survey exports only) | First-party declared demographics & stated preferences |

### Ingestion policy (locked 2026-10)

- **Languages:** English + Spanish at ingest. US is the second-largest
  Spanish-speaking country; ignoring it is a known blind spot we're choosing
  to close early.
- **Geography:** every signal carries ZIP + county where derivable; personas
  cluster at county level.
- **Backfill:** 90 days of history on each adapter's first run — enough for
  trend velocity, bounded crawl cost.
- **Storage:** raw payload (JSONB) + normalized human-signal record. Raw is
  re-processable when the schema evolves.
- **Author identity:** public handles stored as-is. Provenance — showing the
  real person behind a signal — is core to the product; review if legal asks.
- **Shelf refresh:** weekly prices / monthly full assortment. Demo-mode shelf
  coverage: Walmart, Kroger, Target (top 3).
- **Trend verification:** a trend claim earns "verified" only when corroborated
  by ≥2 independent source families (e.g. TikTok + Reddit, or social +
  search). Enforced in the trend feed, not just by convention.
- **Buy vs build:** build/scrape only. Paid listening platforms (Brandwatch,
  Spate, Tastewise, Datassential) may be consulted as validation ground truth
  but are not data feeds.

### Candidates for v2+

Deferred sources, roughly in priority order:

- **Menu intelligence** — Datassential/Spate/Mintel as validation ground truth.
- **Delivery & grocery apps** — Instacart/DoorDash/UberEats review corpora and
  availability by ZIP.
- **Recipes & cooking sites** — Allrecipes, Tasty comments; leading indicator
  for packaged F&B.
- **Google Maps / Yelp reviews** — regional taste maps and complaint language.
- **Beverage verticals** — Untappd, Vivino: review-heavy beer/wine communities.
- **DTC review platforms** — Yotpo/Bazaarvoice endpoints: one integration,
  hundreds of DTC F&B brands.
- **Local chatter** — Facebook Groups, Nextdoor: hyperlocal taste signal.
- **Menu/LTO tracker** — chain menu-page scraping for limited-time-offer
  launches; trade-show exhibitor lists (Expo West, Sweets & Snacks).
- **Forecast reports** — McCormick Flavor Forecast, Whole Foods Trends Council,
  NRA "What's Hot" as sanity checks.
- **Food podcasts** — Sporkful, Taste Radio transcripts (needs summarization
  pipeline).
- **Job postings** — new-store openings, ghost kitchens, CPG expansion signals.

> **Note on TikTok-Api:** it is an unofficial library and breaks often as TikTok
> changes. Treat it as one signal among several, never the sole basis for a trend
> claim, and wrap it behind an adapter so it can be swapped.

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
- Multi-region expansion timing after US launch.
- When to promote v2 candidate sources into the pipeline (delivery-app corpora
  and Google Maps/Yelp are the leading candidates).
