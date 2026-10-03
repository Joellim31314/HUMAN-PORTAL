"use client"

import { useState } from "react"
import { Scale, X } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { BetSettlement } from "@/lib/types"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<
  BetSettlement["status"],
  { badge: string; label: string }
> = {
  confirmed: {
    badge: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
    label: "Confirmed",
  },
  contradicted: {
    badge: "bg-amber-100 text-amber-800 hover:bg-amber-100",
    label: "Contradicted",
  },
  partial: {
    badge: "bg-sky-100 text-sky-800 hover:bg-sky-100",
    label: "Partially confirmed",
  },
}

export function BetStrip({
  settlements,
}: {
  settlements: BetSettlement[]
}) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null

  return (
    <div className="mx-5 mb-3 flex items-center gap-3 rounded-xl border bg-card px-4 py-2.5 shadow-xs">
      <Scale className="size-4 shrink-0 text-muted-foreground" />
      <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
        <span className="text-xs font-semibold">Your bets vs the signals</span>
        {settlements.map((s) => (
          <span key={s.key} className="flex min-w-0 items-center gap-1.5 text-xs">
            <span className="shrink-0 text-muted-foreground">{s.label}:</span>
            <span className="max-w-40 truncate">{s.userSaid}</span>
            <Badge
              className={cn("shrink-0", STATUS_STYLES[s.status].badge)}
            >
              {STATUS_STYLES[s.status].label}
            </Badge>
          </span>
        ))}
      </div>
      <button
        type="button"
        aria-label="Dismiss"
        onClick={() => setDismissed(true)}
        className="ml-auto shrink-0 rounded p-1 text-muted-foreground hover:bg-muted"
      >
        <X className="size-3.5" />
      </button>
    </div>
  )
}
