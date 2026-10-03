"use client"

import { MapPin, Zap } from "lucide-react"

import { ScoreBreakdown } from "@/components/research/score-bars"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { Area } from "@/lib/types"
import type { LiveAreaScore } from "@/lib/sim-api"

export function AreaList({
  areas,
  selectedSlug,
  placementSlug,
  liveScores,
  onSelect,
}: {
  areas: Area[]
  selectedSlug: string | null
  placementSlug: string | null
  liveScores?: Record<string, LiveAreaScore> | null
  onSelect: (slug: string) => void
}) {
  const ordered = liveScores
    ? [...areas].sort(
        (a, b) => (liveScores[a.slug]?.rank ?? 99) - (liveScores[b.slug]?.rank ?? 99)
      )
    : areas
  return (
    <div className="flex flex-col">
      <div className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">Where it could win</h2>
          {liveScores && (
            <Badge className="gap-1 bg-emerald-100 text-[10px] text-emerald-800 hover:bg-emerald-100">
              <Zap className="size-3" />
              Live ranking
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          {areas.length} London areas,{" "}
          {liveScores
            ? "ranked by simulating 2,000 locals per area with your product"
            : "ranked by opportunity"}
        </p>
      </div>
      <div className="flex flex-col gap-2 overflow-y-auto p-3">
        {ordered.map((area) => {
          const isSelected = selectedSlug === area.slug
          const isBet = placementSlug === area.slug
          const live = liveScores?.[area.slug]
          return (
            <button
              key={area.slug}
              type="button"
              onClick={() => onSelect(area.slug)}
              className={cn(
                "rounded-xl border bg-card p-3 text-left transition-colors",
                isSelected
                  ? "border-primary ring-1 ring-primary/30"
                  : "hover:border-primary/40"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex min-w-0 items-center gap-2">
                  <span
                    className={cn(
                      "grid size-6 shrink-0 place-items-center rounded-full text-xs font-bold",
                      live
                        ? "bg-emerald-600 text-white"
                        : "bg-primary text-primary-foreground"
                    )}
                  >
                    {live?.rank ?? area.rank}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">
                      {area.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {area.borough}
                    </p>
                  </div>
                </div>
                <span className="text-lg font-bold tabular-nums">
                  {live?.score ?? area.score.total}
                </span>
              </div>
              <div className="mt-2">
                <ScoreBreakdown score={area.score} compact />
              </div>
              <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                {area.summary}
              </p>
              {isBet && (
                <div className="mt-2 flex items-center gap-1.5">
                  <Badge className="gap-1 bg-amber-100 text-amber-800 hover:bg-amber-100">
                    <MapPin className="size-3" />
                    Your bet
                  </Badge>
                  {area.rank > 1 && (
                    <Badge className="bg-rose-100 text-rose-800 hover:bg-rose-100">
                      Contradicted
                    </Badge>
                  )}
                </div>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
