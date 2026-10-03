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

| Source | What it gives us |
| --- | --- |
| TikTok (via [TikTok-Api](https://github.com/davidteather/TikTok-Api)) | Trends, sounds, comments, engagement — the fastest F&B signal stream |
| Reddit | Threads & comments: honest enthusiasm and rejection language |
| YouTube | Comments, review/trend video reactions |
| X / Twitter | Trend chatter, launch reactions |
| Product reviews | Trust/rejection language attached to actual SKUs |
| Google Trends | Search-interest baselines to validate social spikes |
| Instagram | Reels, comments, hashtag momentum |
| User-uploaded data | First-party: surveys, owned reviews, sales data |
| Scraped shelf & competitor data | Backend-scraped: regional competitors, what's shelved where |

### Candidate F&B-specific signals to evaluate

The F&B world emits far more structured signal than general social data. To
evaluate for v1/v2:

- **Menu intelligence** — flavor/menu penetration trackers (the Datassential,
  Spate, Mintel category of data) as validation ground truth.
- **Delivery & grocery apps** — Instacart/DoorDash/UberEats trend reports and
  review corpora.
- **Recipes & cooking sites** — what people actually cook (Allrecipes, Tasty
  comments) — leading indicator for packaged F&B.
- **Pinterest trends** — "mini desserts up 529%" style planning signals.
- **Regulatory & recall feeds** — FDA/USDA data; a recall wave is a trust signal.
- **Store circulars & grocery price data** — pricing/promotion landscape.
- **Google Maps / Yelp reviews** — regional taste maps and complaint language.
- **Published forecast reports** — McCormick Flavor Forecast, Whole Foods Trends
  Council, National Restaurant Association "What's Hot" — as sanity checks.

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
| Frontend | **React + Vite** | SPA |
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
                   FastAPI backend ──► React + Vite frontend
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
- Which candidate F&B signal sources make the v1 cut (menu intelligence,
  delivery-app data, circulars are the leading candidates).
- How often shelf/competitor scraping must refresh to stay trustworthy.
- Multi-region expansion timing after US launch.
