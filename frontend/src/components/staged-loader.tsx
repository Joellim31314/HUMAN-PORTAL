"use client"

import { useEffect, useState } from "react"
import { Check, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

export function StagedLoader({
  steps,
  onDone,
  stepMs = 1500,
}: {
  steps: string[]
  onDone: () => void
  stepMs?: number
}) {
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    if (current >= steps.length) {
      const t = setTimeout(onDone, 600)
      return () => clearTimeout(t)
    }
    const t = setTimeout(() => setCurrent((c) => c + 1), stepMs)
    return () => clearTimeout(t)
  }, [current, steps.length, stepMs, onDone])

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-8 bg-background/97 backdrop-blur-sm">
      <div className="flex flex-col gap-3">
        {steps.map((step, i) => {
          const done = i < current
          const active = i === current
          return (
            <div
              key={step}
              className={cn(
                "flex items-center gap-3 text-sm transition-all duration-300",
                done && "text-foreground",
                active && "text-foreground",
                !done && !active && "text-muted-foreground/50"
              )}
            >
              <span
                className={cn(
                  "grid size-6 place-items-center rounded-full border",
                  done && "border-primary bg-primary text-primary-foreground",
                  active && "border-primary",
                  !done && !active && "border-muted"
                )}
              >
                {done ? (
                  <Check className="size-3.5" />
                ) : active ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <span className="size-1 rounded-full bg-muted-foreground/40" />
                )}
              </span>
              {step}
            </div>
          )
        })}
      </div>
    </div>
  )
}
