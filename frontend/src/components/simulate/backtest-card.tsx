"use client"

import { useState } from "react"
import { FlaskConical } from "lucide-react"

import { cn } from "@/lib/utils"

export function BacktestCard() {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border bg-card shadow-xs">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <FlaskConical className="size-4 shrink-0 text-primary" />
        <div className="min-w-0">
          <p className="text-sm font-semibold">
            How do we know this works?
          </p>
          <p className="text-xs text-muted-foreground">
            Back-test: Prime Hydration&rsquo;s UK launch, 2023
          </p>
        </div>
        <span
          className={cn(
            "ml-auto text-xs font-medium text-primary transition-transform",
            open && "rotate-180"
          )}
        >
          ▾
        </span>
      </button>
      {open && (
        <div className="border-t px-4 py-3">
          <p className="text-sm leading-relaxed text-muted-foreground">
            We ran MISO on Prime Hydration using only{" "}
            <span className="font-medium text-foreground">
              pre-launch signals
            </span>{" "}
            (US hype velocity, UK import-demand chatter, corner-shop
            under-stocking): the model predicted{" "}
            <span className="font-medium text-foreground">
              71% adoption concentrated in London convenience stores
            </span>
            , driven by social-proof contagion in the 13–19 cluster.
          </p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            What happened: Aldi launch queues, 300%+ resale markup, and
            national stockouts within weeks.
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Retrospective illustrative analysis — demo fixture, not a live
            re-run.
          </p>
        </div>
      )}
    </div>
  )
}
