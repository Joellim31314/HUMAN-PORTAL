"use client"

import { usePathname, useRouter } from "next/navigation"
import { FlaskConical } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

export const DEMO_FILL_EVENT = "hp-fill-demo"

/**
 * Small, placeable button that pre-fills the interview with the hojicha RTD
 * example. Dispatches an event when the interview is already mounted, or sets
 * a one-shot flag and navigates there otherwise.
 */
export function DemoFillButton({
  className,
  label = "Demo data",
}: {
  className?: string
  label?: string
}) {
  const router = useRouter()
  const pathname = usePathname()

  function onClick() {
    sessionStorage.setItem(DEMO_FILL_EVENT, "1")
    window.dispatchEvent(new Event(DEMO_FILL_EVENT))
    if (pathname !== "/interview") router.push("/interview")
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn("gap-1.5", className)}
          onClick={onClick}
        >
          <FlaskConical className="size-3.5 text-primary" />
          {label}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        Pre-fill the interview with the hojicha RTD example
      </TooltipContent>
    </Tooltip>
  )
}
