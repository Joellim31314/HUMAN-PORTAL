"use client"

import { useEffect, useState } from "react"
import { ArrowRight, Building2, Users } from "lucide-react"
import { useRouter } from "next/navigation"

import { ScoreBreakdown } from "@/components/research/score-bars"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { fetchLiveSignals } from "@/lib/signals-api"
import type { Area, Platform, ProductAnswers, Signal } from "@/lib/types"
import { cn } from "@/lib/utils"

const PLATFORM_STYLES: Record<Platform, string> = {
  TikTok: "bg-slate-900 text-white",
  Reddit: "bg-orange-500 text-white",
  YouTube: "bg-red-600 text-white",
  X: "bg-sky-600 text-white",
  Reviews: "bg-emerald-600 text-white",
  StackExchange: "bg-[#1e5397] text-white",
}

const SENTIMENT_DOT: Record<Signal["sentiment"], string> = {
  positive: "bg-emerald-500",
  negative: "bg-rose-500",
  mixed: "bg-amber-400",
}

function SignalRow({ signal }: { signal: Signal }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "rounded px-1.5 py-0.5 text-[10px] font-semibold",
            PLATFORM_STYLES[signal.platform]
          )}
        >
          {signal.platform}
        </span>
        <span className="truncate text-xs font-medium text-muted-foreground">
          {signal.topic}
        </span>
        <span
          className={cn(
            "ml-auto size-2 shrink-0 rounded-full",
            SENTIMENT_DOT[signal.sentiment]
          )}
        />
      </div>
      <p className="mt-1.5 text-sm leading-snug">&ldquo;{signal.quote}&rdquo;</p>
      <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
        <span>{signal.author}</span>
        <span>·</span>
        <span>{signal.authorMeta}</span>
        <span>·</span>
        <span>{signal.date}</span>
        <Badge
          variant="outline"
          className="ml-auto text-[10px] capitalize text-muted-foreground"
        >
          {signal.confidence} confidence
        </Badge>
      </div>
    </div>
  )
}

export function EvidenceSidebar({
  area,
  product,
}: {
  area: Area
  product: ProductAnswers
}) {
  const router = useRouter()
  const [liveSignals, setLiveSignals] = useState<Signal[] | null>(null)
  const [liveStatus, setLiveStatus] = useState<"loading" | "live" | "cached">(
    "loading"
  )

  useEffect(() => {
    let cancelled = false
    setLiveStatus("loading")
    setLiveSignals(null)
    fetchLiveSignals(product.name, area.name)
      .then((result) => {
        if (cancelled) return
        if (result.signals.length > 0) {
          setLiveSignals(result.signals)
          setLiveStatus("live")
        } else {
          setLiveStatus("cached")
        }
      })
      .catch(() => {
        if (!cancelled) setLiveStatus("cached")
      })
    return () => {
      cancelled = true
    }
  }, [area.slug, area.name, product.name])

  const displaySignals = liveSignals ?? area.signals

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="grid size-6 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
            {area.rank}
          </span>
          <h2 className="text-sm font-semibold">{area.name}</h2>
          <span className="text-xs text-muted-foreground">
            {area.borough}
          </span>
          <span className="ml-auto text-lg font-bold tabular-nums">
            {area.score.total}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{area.summary}</p>
      </div>

      <div className="flex flex-col gap-4 overflow-y-auto p-4">
        <section>
          <h3 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Opportunity score
          </h3>
          <ScoreBreakdown score={area.score} />
        </section>

        <section>
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Human signals ({displaySignals.length})
            </h3>
            {liveStatus === "live" && (
              <Badge className="bg-emerald-100 text-[10px] text-emerald-800 hover:bg-emerald-100">
                Live · pulled now
              </Badge>
            )}
            {liveStatus === "loading" && (
              <Badge variant="outline" className="text-[10px] text-muted-foreground">
                Pulling…
              </Badge>
            )}
            {liveStatus === "cached" && (
              <Badge variant="outline" className="text-[10px] text-muted-foreground">
                Cached demo data
              </Badge>
            )}
          </div>
          <div className="flex flex-col gap-2">
            {displaySignals.map((signal) => (
              <SignalRow key={signal.id} signal={signal} />
            ))}
          </div>
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Competitors here
          </h3>
          <div className="flex flex-col gap-2">
            {area.competitors.map((c) => (
              <div key={c.name} className="rounded-lg border bg-background p-3">
                <p className="text-sm font-medium">{c.name}</p>
                <p className="text-xs text-muted-foreground">{c.note}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Shelf intel
          </h3>
          <div className="rounded-lg border bg-background p-3 text-sm">
            <div className="flex items-center gap-2">
              <Building2 className="size-4 text-muted-foreground" />
              <span>{area.shelf.outlets} outlets scanned nearby</span>
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {area.shelf.whitespace}
            </p>
          </div>
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Who lives here
          </h3>
          <div className="rounded-lg border bg-background p-3 text-sm">
            <div className="flex items-center gap-2">
              <Users className="size-4 text-muted-foreground" />
              <span className="font-medium">
                {area.demoFit.matchPct}% persona match
              </span>
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {area.demoFit.note}
            </p>
          </div>
        </section>

        <Separator />
        <p className="text-xs text-muted-foreground">
          {liveStatus === "live"
            ? "Signals pulled live from open APIs · sentiment & topics via DeepSeek"
            : "Data updated 03/10/2026 · Fixture dataset for demo"}
        </p>
      </div>

      <div className="border-t p-4">
        <Button
          className="w-full gap-2"
          onClick={() =>
            router.push(
              `/simulate?product=${product.slug}&area=${area.slug}`
            )
          }
        >
          Simulate {product.name} here
          <ArrowRight className="size-4" />
        </Button>
      </div>
    </div>
  )
}
