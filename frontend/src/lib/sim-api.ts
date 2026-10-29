// Client for the Python simulation backend (backend/backend.md §8) and an
// adapter from its SimulationResult into the SimResult shape the UI renders.

import type {
  AgentNarrative,
  PersonaCluster,
  ProductAnswers,
  SimResult,
  Verdict,
} from "@/lib/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

// Hosted demo (Vercel): replay the example product's pre-run simulations from
// public/demo (exported by backend/app/pipeline/export_demo.py) instead of
// calling the Python backend. Chat goes through the /api/chat route handler.
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "1"
const DEMO_PRODUCT_SLUG = "well-and-truly-thins"

function demoJson<T>(path: string): Promise<T> {
  return fetch(`/demo/${path}`).then((res) => {
    if (!res.ok) throw new Error(`/demo/${path} -> ${res.status}`)
    return res.json() as Promise<T>
  })
}

// Research areas -> census borough names used by the backend.
const AREA_BOROUGH: Record<string, string> = {
  walthamstow: "Waltham Forest",
  peckham: "Southwark",
  camden: "Camden",
  stratford: "Newham",
  shoreditch: "Hackney",
  clapham: "Lambeth",
  kingston: "Kingston upon Thames",
}

const ARCHETYPE_LABEL: Record<string, string> = {
  office_commuter: "Office commuters",
  shift_worker: "Shift workers",
  student: "Students",
  wfh: "Work-from-home locals",
  retired: "Retirees",
  carer: "Carers & home-makers",
}

const REASON_DRIVER: Record<string, string> = {
  NO_STORE_NEARBY: "no stockist on route",
  NOT_THERE_WHEN_NEEDED: "wrong place, wrong time",
  DIDNT_NOTICE: "didn't notice it",
  NO_NEED: "no need",
  TOO_EXPENSIVE: "price",
  BELIEF_CONFLICT: "diet / beliefs",
  LOYAL_TO_EXISTING: "habit",
  BOUGHT: "bought",
}

export type Outcome = "never_exposed" | "not_noticed" | "no_need" | "rejected" | "bought"

interface ApiOutcome {
  agent_id: string
  outcome: Outcome
  reason: string
}

interface ApiInterview {
  agent_id: string
  name: string
  persona: string
  outcome: Outcome
  reason: string
  quote: string
}

export interface ApiReport {
  headline: string
  key_findings: string[]
  action_items: { action: string; rationale: string; priority: string }[]
  source: "llm" | "template"
}

interface ApiResult {
  id: string
  status: "queued" | "running" | "done" | "failed"
  progress: string
  error: string | null
  stores_stocking: number
  funnel: { total: number; exposed: number; noticed: number; needed: number; bought: number } | null
  outcomes: ApiOutcome[]
  interviews: ApiInterview[]
  report: ApiReport | null
}

interface AgentPoint {
  id: string
  age_band: string
  archetype: string
}

export interface LiveExtras {
  simId: string
  borough: string
  storesStocking: number
  funnel: NonNullable<ApiResult["funnel"]>
  passersBy: number
  report: ApiReport | null
}

export interface LiveAreaScore {
  rank: number
  score: number
  bought: number
}

const BOROUGH_AREA: Record<string, string> = {
  "Waltham Forest": "walthamstow",
  Southwark: "peckham",
  Camden: "camden",
  Newham: "stratford",
  Hackney: "shoreditch",
  Lambeth: "clapham",
  "Kingston upon Thames": "kingston",
}

/** Rank all 7 areas with the real funnel engine for this product. */
export async function scoreAreas(
  product: ProductAnswers
): Promise<Record<string, LiveAreaScore> | null> {
  try {
    if (DEMO_MODE) {
      if (product.slug !== DEMO_PRODUCT_SLUG) return null
      return rankBySlug(await demoJson<AreaScoreResponse>("areas.json"))
    }
    const res = await fetch(`${API_URL}/api/areas/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toProductInput(product, "")),
      signal: AbortSignal.timeout(120_000),
    })
    if (!res.ok) return null
    return rankBySlug(await res.json())
  } catch {
    return null
  }
}

interface AreaScoreResponse {
  areas: { borough: string; rank: number; score: number; bought: number }[]
}

function rankBySlug(data: AreaScoreResponse) {
  const out: Record<string, LiveAreaScore> = {}
  for (const a of data.areas) {
    const slug = BOROUGH_AREA[a.borough]
    if (slug) out[slug] = { rank: a.rank, score: a.score, bought: a.bought }
  }
  return out
}

function textOf(p: ProductAnswers) {
  return `${p.name} ${p.tagline} ${p.packSize}`.toLowerCase()
}

function mapCategory(p: ProductAnswers): string {
  const t = textOf(p)
  switch (p.category) {
    case "Beverages":
      if (/beer|lager|wine|cider|spirit|gin/.test(t)) return "alcohol"
      if (/energy/.test(t) && !/calm/.test(t)) return "energy_drink"
      if (/coffee|tea|matcha|hojicha|latte|caffeine/.test(t)) return "coffee_rtd"
      return "soft_drink"
    case "Snacks & confectionery":
      if (/chocolate|sweet|candy|gummy|confection/.test(t)) return "confectionery"
      if (/protein|healthy|bar|nut|seed|wholegrain/.test(t)) return "healthy_snack"
      return "snack"
    case "Ready meals":
      return "ready_meal"
    default:
      return "other"
  }
}

function claimsOf(p: ProductAnswers): string[] {
  const t = textOf(p)
  const claims: string[] = []
  if (/caffeine|coffee|tea|matcha|hojicha|energy/.test(t)) claims.push("caffeinated")
  if (/sugar[- ]free|no sugar|zero sugar|unsweetened/.test(t)) claims.push("sugar_free")
  if (/vegan/.test(t)) claims.push("vegan")
  if (/plant[- ]based/.test(t)) claims.push("plant_based")
  if (/halal/.test(t)) claims.push("halal")
  if (/protein/.test(t)) claims.push("high_protein")
  if (/organic/.test(t)) claims.push("organic")
  return claims
}

export function toProductInput(p: ProductAnswers, areaSlug: string) {
  const borough = AREA_BOROUGH[areaSlug]
  return {
    name: p.name,
    category: mapCategory(p),
    description: `${p.tagline} (${p.packSize})`,
    price_gbp: Number.parseFloat(String(p.price).replace(/[^0-9.]/g, "")) || 2,
    packaging_salience: p.packagingSalience ?? 3,
    packaging_description: p.packagingSalience
      ? `Packaging photo scored ${p.packagingSalience}/5 for shelf standout`
      : null,
    claims: claimsOf(p),
    stockists: {
      chains: [],
      store_kinds: ["convenience", "supermarket"],
      boroughs: borough ? [borough] : [],
      coverage: 0.6,
    },
    marketing_channels: ["instagram", "tiktok"],
    marketing_intensity: 0.3,
    target_audience: p.buyerGuess || null,
    seed: 42,
  }
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init)
  if (!res.ok) throw new Error(`${path} -> ${res.status}`)
  return res.json() as Promise<T>
}

let agentCache: Promise<Map<string, AgentPoint>> | null = null
function agentIndex() {
  agentCache ??= (
    DEMO_MODE ? demoJson<AgentPoint[]>("agents.json") : getJson<AgentPoint[]>("/api/agents")
  ).then(
    (rows) => new Map(rows.map((a) => [a.id, a]))
  )
  return agentCache
}

const verdictOf = (o: Outcome): Verdict =>
  o === "bought" ? "adopt" : o === "rejected" ? "reject" : "ignore"

function pct(n: number, d: number) {
  return d ? Math.round((n / d) * 100) : 0
}

function topKeys(counts: Map<string, number>, k: number) {
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, k).map(([key]) => key)
}

export async function runLiveSimulation(
  product: ProductAnswers,
  areaSlug: string,
  onProgress?: (msg: string) => void
): Promise<{ result: SimResult; extras: LiveExtras }> {
  const body = toProductInput(product, areaSlug)
  if (DEMO_MODE && product.slug !== DEMO_PRODUCT_SLUG) {
    throw new Error("The hosted demo only replays the example product")
  }
  const [agents, started] = await Promise.all([
    agentIndex(),
    DEMO_MODE
      ? { id: areaSlug } // demo runs are stored per area
      : getJson<{ id: string }>("/api/simulations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }),
  ])

  let data: ApiResult
  const deadline = Date.now() + 120_000
  for (;;) {
    if (DEMO_MODE) {
      data = await demoJson<ApiResult>(`sims/${areaSlug}.json`)
      break
    }
    data = await getJson<ApiResult>(`/api/simulations/${started.id}`)
    if (data.status === "done") break
    if (data.status === "failed") throw new Error(data.error ?? "simulation failed")
    if (Date.now() > deadline) throw new Error("simulation timed out")
    onProgress?.(data.progress)
    await new Promise((r) => setTimeout(r, 1500))
  }

  // Everyone who walked past a stockist in this area is the relevant audience.
  const exposed = data.outcomes.filter((o) => o.outcome !== "never_exposed")
  const tally = (rows: ApiOutcome[]) => {
    const adopt = rows.filter((o) => o.outcome === "bought").length
    const reject = rows.filter((o) => o.outcome === "rejected").length
    return { adopt, reject, ignore: rows.length - adopt - reject }
  }

  const t = tally(exposed)
  const overallAdopt = pct(t.adopt, exposed.length)
  const overallReject = pct(t.reject, exposed.length)
  const overall = {
    adopt: overallAdopt,
    reject: overallReject,
    ignore: Math.max(0, 100 - overallAdopt - overallReject),
  }

  const groups = new Map<string, ApiOutcome[]>()
  for (const o of exposed) {
    const arch = agents.get(o.agent_id)?.archetype ?? "other"
    groups.set(arch, [...(groups.get(arch) ?? []), o])
  }
  const clusters: PersonaCluster[] = [...groups.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([arch, rows]) => {
      const g = tally(rows)
      const adoptPct = pct(g.adopt, rows.length)
      const rejectPct = pct(g.reject, rows.length)
      const reasons = new Map<string, number>()
      const ages = new Map<string, number>()
      for (const o of rows) {
        if (o.reason !== "BOUGHT") reasons.set(o.reason, (reasons.get(o.reason) ?? 0) + 1)
        const band = agents.get(o.agent_id)?.age_band
        if (band) ages.set(band, (ages.get(band) ?? 0) + 1)
      }
      const verdict: Verdict =
        adoptPct >= 8 && adoptPct >= rejectPct ? "adopt" : rejectPct >= 8 ? "reject" : "ignore"
      return {
        name: ARCHETYPE_LABEL[arch] ?? arch,
        share: pct(rows.length, exposed.length),
        ages: topKeys(ages, 2).join(", "),
        occupations: `${rows.length} passed a stockist`,
        verdict,
        drivers: topKeys(reasons, 2).map((r) => REASON_DRIVER[r] ?? r),
        adoptPct,
        rejectPct,
        ignorePct: Math.max(0, 100 - adoptPct - rejectPct),
      }
    })

  const order: Outcome[] = ["bought", "rejected", "no_need", "not_noticed", "never_exposed"]
  const narratives: AgentNarrative[] = [...data.interviews]
    .sort((a, b) => order.indexOf(a.outcome) - order.indexOf(b.outcome))
    .filter((i) => i.outcome !== "never_exposed")
    .map((i) => {
      const parts = i.persona.split(",").map((s) => s.trim())
      return {
        name: i.name.split(" ")[0],
        age: Number.parseInt(parts[0], 10) || 0,
        job: parts[3] ?? "",
        cluster: ARCHETYPE_LABEL[agents.get(i.agent_id)?.archetype ?? ""] ?? "Londoner",
        verdict: verdictOf(i.outcome),
        text: i.quote,
      }
    })
  // Lead with one of each verdict so the hero cards tell the whole story.
  const hero: AgentNarrative[] = []
  for (const v of ["adopt", "reject", "ignore"] as Verdict[]) {
    const n = narratives.find((x) => x.verdict === v && !hero.includes(x))
    if (n) hero.push(n)
  }
  for (const n of narratives) {
    if (hero.length >= 4) break
    if (!hero.includes(n)) hero.push(n)
  }
  const allNarratives = [...hero, ...narratives.filter((n) => !hero.includes(n))]

  const report = data.report
  const takeaway = report
    ? [report.headline, report.action_items[0]?.action].filter(Boolean).join(" ")
    : "Simulation complete."

  return {
    result: {
      areaSlug,
      heroNarratives: hero,
      allNarratives,
      clusters,
      overall,
      takeaway,
    },
    extras: {
      simId: started.id,
      borough: body.stockists.boroughs[0] ?? "London",
      storesStocking: data.stores_stocking,
      funnel: data.funnel!,
      passersBy: exposed.length,
      report,
    },
  }
}

// --- Week playback (GET /api/simulations/{id}/playback) ---------------------

export type PlaybackKind = "seen" | "noticed" | "missed" | "rejected" | "bought"

export interface Playback {
  days: string[]
  slots: string[]
  agents: {
    id: string
    name: string
    archetype: string
    outcome: Outcome
    weekday: [number, number][]
    weekend: [number, number][]
  }[]
  stores: { id: string; name: string; lat: number; lon: number }[]
  /** [agent index, tick, kind]; tick = day * slots.length + slot, sorted by tick */
  events: [number, number, PlaybackKind][]
}

export interface AgentTrace {
  agent: {
    id: string
    name: string
    age: number
    borough: string
    archetype: string
    occupation: string | null
    work_label: string | null
  }
  outcome: { outcome: Outcome; reason: string }
  trace: { day: string; slot: string; step: string; passed: boolean; detail: string }[]
  interview: { quote: string } | null
}

export function getPlayback(simId: string) {
  return DEMO_MODE
    ? demoJson<Playback>(`sims/${simId}.playback.json`)
    : getJson<Playback>(`/api/simulations/${simId}/playback`)
}

const demoAgents = new Map<string, Promise<Record<string, AgentTrace>>>()

export async function getAgentTrace(simId: string, agentId: string) {
  if (!DEMO_MODE) return getJson<AgentTrace>(`/api/simulations/${simId}/agents/${agentId}`)
  if (!demoAgents.has(simId)) demoAgents.set(simId, demoJson(`sims/${simId}.agents.json`))
  const trace = (await demoAgents.get(simId)!)[agentId]
  if (!trace) throw new Error(`No demo trace for ${agentId}`)
  return trace
}

export interface ChatTurn {
  role: "retailer" | "agent"
  content: string
}

export interface ChatReply {
  reply: string
  source: "llm" | "unavailable"
}

export function chatWithAgent(simId: string, agentId: string, messages: ChatTurn[]) {
  const init = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(DEMO_MODE ? { simId, agentId, messages } : { messages }),
  }
  if (!DEMO_MODE) {
    return getJson<ChatReply>(`/api/simulations/${simId}/agents/${agentId}/chat`, init)
  }
  return fetch("/api/chat", init).then(async (res) => {
    if (!res.ok && res.status !== 429) throw new Error(`/api/chat -> ${res.status}`)
    return res.json() as Promise<ChatReply>
  })
}
