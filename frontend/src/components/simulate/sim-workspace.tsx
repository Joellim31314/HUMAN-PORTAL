"use client"

import { useState } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  FlaskConical,
  Lock,
} from "lucide-react"

import { BacktestCard } from "@/components/simulate/backtest-card"
import { StagedLoader } from "@/components/staged-loader"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AREAS, SIM_RESULTS } from "@/lib/fixtures"
import type { AgentNarrative, Verdict } from "@/lib/types"
import { cn } from "@/lib/utils"

const SIM_STEPS = (areaName: string) => [
  "Waking 4 persona clusters",
  `Grounding agents in ${areaName} signals`,
  "Simulating first encounters",
  "Reading the verdict",
]

const VERDICT_STYLES: Record<
  Verdict,
  { badge: string; label: string; dot: string }
> = {
  adopt: {
    badge: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100",
    label: "Adopts",
    dot: "bg-emerald-500",
  },
  reject: {
    badge: "bg-rose-100 text-rose-800 hover:bg-rose-100",
    label: "Rejects",
    dot: "bg-rose-500",
  },
  ignore: {
    badge: "bg-slate-100 text-slate-700 hover:bg-slate-100",
    label: "Ignores",
    dot: "bg-slate-400",
  },
}

function NarrativeCard({ narrative }: { narrative: AgentNarrative }) {
  const style = VERDICT_STYLES[narrative.verdict]
  return (
    <div className="rounded-xl border bg-card p-4 shadow-xs">
      <div className="flex items-center gap-2">
        <span className={cn("size-2 rounded-full", style.dot)} />
        <p className="text-sm font-semibold">
          {narrative.name}, {narrative.age}
        </p>
        <p className="truncate text-xs text-muted-foreground">
          {narrative.job} · {narrative.cluster}
        </p>
        <Badge className={cn("ml-auto shrink-0", style.badge)}>
          {style.label}
        </Badge>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {narrative.text}
      </p>
    </div>
  )
}

export function SimWorkspace({
  productSlug,
  areaSlug,
}: {
  productSlug: string | null
  areaSlug: string | null
}) {
  const [running, setRunning] = useState(true)
  const [showAll, setShowAll] = useState(false)

  const area = AREAS.find((a) => a.slug === areaSlug) ?? null

  if (!productSlug || !areaSlug || !area) {
    return (
      <div className="flex flex-1 items-center justify-center overflow-y-auto p-6">
        <div className="flex max-w-sm flex-col items-center gap-3 text-center">
          <div className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary">
            <FlaskConical className="size-6" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            MISO Simulation
          </h1>
          <p className="text-sm text-muted-foreground">
            Pick an area on the map first — then watch simulated people meet your
            product there.
          </p>
          <Button asChild>
            <Link href="/research">Back to the map</Link>
          </Button>
        </div>
      </div>
    )
  }

  const result = SIM_RESULTS[area.slug]
  const hidden = result.allNarratives.slice(result.heroNarratives.length)

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-6 py-8">
        <Button
          variant="ghost"
          size="sm"
          className="mb-4 -ml-2 gap-2 text-muted-foreground"
          asChild
        >
          <Link href={`/research?product=${productSlug}&area=${area.slug}`}>
            <ArrowLeft className="size-4" />
            Back to {area.name}
          </Link>
        </Button>

        <h1 className="text-2xl font-semibold tracking-tight">
          MISO Simulation — {area.name}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {result.clusters.length} persona clusters, grounded in{" "}
          {area.signals.length} scraped signals from this area.
        </p>

        <div className="mt-6 rounded-xl border bg-card p-4 shadow-xs">
          <div className="flex h-3 w-full overflow-hidden rounded-full">
            <div
              className="bg-emerald-500"
              style={{ width: `${result.overall.adopt}%` }}
            />
            <div
              className="bg-rose-400"
              style={{ width: `${result.overall.reject}%` }}
            />
            <div
              className="bg-slate-300"
              style={{ width: `${result.overall.ignore}%` }}
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            <span>
              <span className="font-semibold text-emerald-600">
                {result.overall.adopt}% adopt
              </span>{" "}
              ·
            </span>
            <span>
              <span className="font-semibold text-rose-500">
                {result.overall.reject}% reject
              </span>{" "}
              ·
            </span>
            <span className="font-semibold text-slate-500">
              {result.overall.ignore}% ignore
            </span>
            <span className="ml-auto text-muted-foreground">
              Modelled first-encounter outcome · deterministic demo
            </span>
          </div>
        </div>

        <h2 className="mt-8 mb-3 text-sm font-semibold">
          First encounters
        </h2>
        <div className="flex flex-col gap-3">
          {result.heroNarratives.map((n) => (
            <NarrativeCard key={n.name + n.cluster} narrative={n} />
          ))}
          {showAll &&
            hidden.map((n) => (
              <NarrativeCard key={n.name + n.cluster} narrative={n} />
            ))}
        </div>
        {hidden.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="mt-3 gap-1.5 text-muted-foreground"
            onClick={() => setShowAll((s) => !s)}
          >
            {showAll ? (
              <>
                <ChevronUp className="size-4" />
                Show fewer
              </>
            ) : (
              <>
                <ChevronDown className="size-4" />
                Show all {result.allNarratives.length} encounters
              </>
            )}
          </Button>
        )}

        <h2 className="mt-8 mb-3 text-sm font-semibold">
          Verdict by persona cluster
        </h2>
        <div className="overflow-hidden rounded-xl border bg-card shadow-xs">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cluster</TableHead>
                <TableHead className="w-16">Share</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Drivers</TableHead>
                <TableHead className="w-32">Adopt / reject</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.clusters.map((cluster) => (
                <TableRow key={cluster.name}>
                  <TableCell>
                    <p className="font-medium">{cluster.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {cluster.ages} · {cluster.occupations}
                    </p>
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {cluster.share}%
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={cn(
                        VERDICT_STYLES[cluster.verdict].badge
                      )}
                    >
                      {VERDICT_STYLES[cluster.verdict].label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {cluster.drivers.map((d) => (
                        <Badge
                          key={d}
                          variant="outline"
                          className="text-[10px] capitalize"
                        >
                          {d}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex h-2 w-full overflow-hidden rounded-full">
                      <div
                        className="bg-emerald-500"
                        style={{ width: `${cluster.adoptPct}%` }}
                      />
                      <div
                        className="bg-rose-400"
                        style={{ width: `${cluster.rejectPct}%` }}
                      />
                    </div>
                    <p className="mt-1 text-[10px] text-muted-foreground tabular-nums">
                      {cluster.adoptPct}% / {cluster.rejectPct}%
                    </p>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="mt-8 rounded-xl border border-primary/30 bg-primary/5 p-4">
          <p className="text-sm font-semibold">What this means</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
            {result.takeaway}
          </p>
        </div>

        <div className="mt-6">
          <BacktestCard />
        </div>

        <div className="mt-8 flex items-center gap-3 border-t pt-6 pb-4">
          <Button asChild>
            <Link href={`/research?product=${productSlug}&area=${area.slug}`}>
              Back to Research
            </Link>
          </Button>
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Lock className="size-3.5" />
            Full decision briefs are a Pro feature — no payments in the demo
          </span>
        </div>
      </div>

      {running && (
        <StagedLoader
          steps={SIM_STEPS(area.name)}
          onDone={() => setRunning(false)}
        />
      )}
    </div>
  )
}
