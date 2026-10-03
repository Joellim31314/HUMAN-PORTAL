"use client"

import { MapPin } from "lucide-react"

import { ScoreBreakdown } from "@/components/research/score-bars"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { Area } from "@/lib/types"

export function AreaList({
  areas,
  selectedSlug,
  placementSlug,
  onSelect,
}: {
  areas: Area[]
  selectedSlug: string | null
  placementSlug: string | null
  onSelect: (slug: string) => void
}) {
  return (
    <div className="flex flex-col">
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold">Where it could win</h2>
        <p className="text-xs text-muted-foreground">
          {areas.length} London areas, ranked by opportunity
        </p>
      </div>
      <div className="flex flex-col gap-2 overflow-y-auto p-3">
        {areas.map((area) => {
          const isSelected = selectedSlug === area.slug
          const isBet = placementSlug === area.slug
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
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                    {area.rank}
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
                  {area.score.total}
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
