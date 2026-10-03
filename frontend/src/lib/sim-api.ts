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

type Outcome = "never_exposed" | "not_noticed" | "no_need" | "rejected" | "bought"

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
  borough: string
  storesStocking: number
  funnel: NonNullable<ApiResult["funnel"]>
  passersBy: number
  report: ApiReport | null
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
    packaging_salience: 3,
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
  agentCache ??= getJson<AgentPoint[]>("/api/agents").then(
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
  const [agents, started] = await Promise.all([
    agentIndex(),
    getJson<{ id: string }>("/api/simulations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  ])

  let data: ApiResult
  const deadline = Date.now() + 120_000
  for (;;) {
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
      borough: body.stockists.boroughs[0] ?? "London",
      storesStocking: data.stores_stocking,
      funnel: data.funnel!,
      passersBy: exposed.length,
      report,
    },
  }
}
