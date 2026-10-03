export type Platform = "TikTok" | "Reddit" | "YouTube" | "X" | "Reviews"

export type Sentiment = "positive" | "negative" | "mixed"

export type Confidence = "high" | "medium" | "low"

export interface ProductProfile {
  slug: string
  name: string
  tagline: string
  category: string
  price: string
  packSize: string
  status: "selling" | "prelaunch"
  channels: string[]
}

export interface ProductBets {
  buyerGuess: string
  choiceReason: string
  rejectReason: string
  placementGuess: string
}

export type ProductAnswers = ProductProfile & ProductBets

export interface Signal {
  id: string
  platform: Platform
  topic: string
  quote: string
  author: string
  authorMeta: string
  date: string
  sentiment: Sentiment
  confidence: Confidence
}

export interface AreaScore {
  trend: number
  gap: number
  shelf: number
  demo: number
  total: number
}

export interface Area {
  slug: string
  name: string
  borough: string
  center: [number, number]
  radiusM: number
  rank: number
  score: AreaScore
  summary: string
  signals: Signal[]
  competitors: { name: string; note: string }[]
  shelf: { outlets: number; whitespace: string }
  demoFit: { matchPct: number; note: string }
}

export type SettlementStatus = "confirmed" | "contradicted" | "partial"

export interface BetSettlement {
  key: "placement" | "buyer" | "choice"
  label: string
  userSaid: string
  signalsSay: string
  status: SettlementStatus
  areaSlug?: string
}

export interface ResearchResult {
  product: ProductAnswers
  areas: Area[]
  settlements: BetSettlement[]
}

export type Verdict = "adopt" | "reject" | "ignore"

export interface AgentNarrative {
  name: string
  age: number
  job: string
  cluster: string
  verdict: Verdict
  text: string
}

export interface PersonaCluster {
  name: string
  share: number
  ages: string
  occupations: string
  verdict: Verdict
  drivers: string[]
  adoptPct: number
  rejectPct: number
  ignorePct: number
}

export interface SimResult {
  areaSlug: string
  heroNarratives: AgentNarrative[]
  allNarratives: AgentNarrative[]
  clusters: PersonaCluster[]
  overall: { adopt: number; reject: number; ignore: number }
  takeaway: string
}
