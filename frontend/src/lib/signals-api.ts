// Client for the live human-signal search API (backend /api/signals/search).
// Returns real pulled signals mapped onto the UI Signal shape; throws on
// failure so callers can fall back to fixtures.

import type { Signal } from "@/lib/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export interface LiveSignalResponse {
  signals: Signal[]
  live: boolean
  sources: Record<string, string>
}

interface ApiSignal {
  id: string
  platform: string
  topic: string
  quote: string
  author: string
  authorMeta: string
  observedAt: string
  sentiment: Signal["sentiment"]
  confidence: Signal["confidence"]
  url: string | null
}

function relativeDate(iso: string): string {
  const days = Math.floor(
    (Date.now() - new Date(iso).getTime()) / 86_400_000
  )
  if (Number.isNaN(days) || days <= 0) return "today"
  if (days === 1) return "1d ago"
  if (days < 30) return `${days}d ago`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months}mo ago`
  return `${Math.floor(months / 12)}y ago`
}

function toUiSignal(s: ApiSignal): Signal {
  const platform: Signal["platform"] = s.platform.startsWith(
    "StackExchange"
  )
    ? "StackExchange"
    : s.platform === "Reddit"
      ? "Reddit"
      : "Reviews"
  return {
    id: s.id,
    platform,
    topic: s.topic,
    quote: s.quote,
    author: s.author,
    authorMeta: s.authorMeta,
    date: relativeDate(s.observedAt),
    sentiment: s.sentiment,
    confidence: s.confidence,
  }
}

export async function fetchLiveSignals(
  query: string,
  area?: string
): Promise<LiveSignalResponse> {
  const params = new URLSearchParams({ query, limit: "12" })
  if (area) params.set("area", area)
  const res = await fetch(`${API_URL}/api/signals/search?${params}`, {
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) throw new Error(`signals API ${res.status}`)
  const data = await res.json()
  return {
    signals: (data.signals as ApiSignal[]).map(toUiSignal),
    live: Boolean(data.live),
    sources: data.sources ?? {},
  }
}
