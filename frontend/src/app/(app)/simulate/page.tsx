import type { Metadata } from "next"
import { FlaskConical, Lock } from "lucide-react"

import { Button } from "@/components/ui/button"

export const metadata: Metadata = {
  title: "MISO Simulation",
}

export default function SimulatePage() {
  return (
    <div className="flex flex-1 items-center justify-center overflow-y-auto p-6">
      <div className="flex w-full max-w-md flex-col items-center gap-4 text-center">
        <div className="grid size-14 place-items-center rounded-2xl bg-primary/10 text-primary">
          <FlaskConical className="size-7" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">
          MISO Simulation
        </h1>
        <p className="text-sm text-muted-foreground">
          Watch simulated people discover, try, trust, or reject your product —
          each agent grounded in a cluster of real human signals from Research.
        </p>
        <Button disabled className="gap-2">
          <Lock className="size-4" />
          Run a simulation
        </Button>
        <p className="text-xs text-muted-foreground">
          Paid plans only · No payments in the demo
        </p>
      </div>
    </div>
  )
}
