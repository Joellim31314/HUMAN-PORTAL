import type { AreaScore } from "@/lib/types"
import { cn } from "@/lib/utils"

const DIMENSIONS: { key: keyof Omit<AreaScore, "total">; label: string }[] = [
  { key: "trend", label: "Trend heat" },
  { key: "gap", label: "Competitor gap" },
  { key: "shelf", label: "Shelf whitespace" },
  { key: "demo", label: "Demographic fit" },
]

export function ScoreBreakdown({
  score,
  compact = false,
}: {
  score: AreaScore
  compact?: boolean
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {DIMENSIONS.map(({ key, label }) => (
        <div key={key} className="flex items-center gap-2">
          {!compact && (
            <span className="w-32 shrink-0 text-xs text-muted-foreground">
              {label}
            </span>
          )}
          <div className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full",
                score[key] >= 70
                  ? "bg-primary"
                  : score[key] >= 50
                    ? "bg-amber-500"
                    : "bg-rose-400"
              )}
              style={{ width: `${score[key]}%` }}
            />
          </div>
          <span className="w-7 shrink-0 text-right text-xs font-medium tabular-nums">
            {score[key]}
          </span>
        </div>
      ))}
    </div>
  )
}
