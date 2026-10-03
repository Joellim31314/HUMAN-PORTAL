"use client"

import { useCallback, useEffect, useState } from "react"
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
import { AREAS, EXAMPLE_PRODUCT, SIM_RESULTS } from "@/lib/fixtures"
import { runLiveSimulation, type LiveExtras } from "@/lib/sim-api"
import { useProduct } from "@/lib/storage"
import type { AgentNarrative, SimResult, Verdict } from "@/lib/types"
import { cn } from "@/lib/utils"

const SIM_STEPS = (areaName: string) => [
  "Waking 2,000 census-grounded Londoners",
  `Stocking shelves in ${areaName}`,
  "Living out a simulated week",
  "Interviewing the people who walked past",
  "Writing the verdict",
]

const VERDICT_STYLES: Record<
  Verdict,
  { badge: string; label: string; dot: string }
> = {
  adopt: {
    badge: "bg-success/10 text-success hover:bg-success/10",
    label: "Adopts",
    dot: "bg-success",
  },
  reject: {
    badge: "bg-danger/10 text-danger hover:bg-danger/10",
    label: "Rejects",
    dot: "bg-danger",
  },
  ignore: {
    badge: "bg-muted text-muted-foreground hover:bg-muted",
    label: "Ignores",
    dot: "bg-muted-foreground/30",
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
  const [loaderDone, setLoaderDone] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const [live, setLive] = useState<{ result: SimResult; extras: LiveExtras } | null>(null)
  const [failed, setFailed] = useState(false)
  const [progress, setProgress] = useState("")
  const stored = useProduct()
  const onLoaderDone = useCallback(() => setLoaderDone(true), [])

  const area = AREAS.find((a) => a.slug === areaSlug) ?? null
  const product =
    stored && stored.slug === productSlug ? stored : EXAMPLE_PRODUCT

  useEffect(() => {
    if (!productSlug || !area) return
    let cancelled = false
    runLiveSimulation(product, area.slug, (m) => !cancelled && setProgress(m))
      .then((r) => !cancelled && setLive(r))
      .catch((err) => {
        console.warn("Live simulation unavailable, using demo data", err)
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productSlug, area?.slug])

  const running = !loaderDone || (!live && !failed)

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

  const result = live?.result ?? SIM_RESULTS[area.slug]
  const extras = live?.extras
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

        <div className="flex items-center gap-3">
          {product.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.image}
              alt={product.name}
              className="size-14 shrink-0 rounded-lg border object-cover"
            />
          )}
          <h1 className="text-2xl font-semibold tracking-tight">
            MISO Simulation — {area.name}
          </h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {extras ? (
            <>
              2,000 census-grounded Londoners lived a simulated week with{" "}
              {product.name} on {extras.storesStocking} shelves in{" "}
              {extras.borough}. {extras.passersBy} walked past it;{" "}
              {extras.funnel.noticed} noticed it; {extras.funnel.bought} bought.
            </>
          ) : (
            <>
              {result.clusters.length} persona clusters, grounded in{" "}
              {area.signals.length} scraped signals from this area.
              {failed && " (Offline demo data — simulation backend unreachable.)"}
            </>
          )}
        </p>

        <div className="mt-6 rounded-xl border bg-card p-4 shadow-xs">
          <div className="flex h-3 w-full overflow-hidden rounded-full">
            <div
              className="bg-success"
              style={{ width: `${result.overall.adopt}%` }}
            />
            <div
              className="bg-danger/70"
              style={{ width: `${result.overall.reject}%` }}
            />
            <div
              className="bg-muted"
              style={{ width: `${result.overall.ignore}%` }}
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            <span>
              <span className="font-semibold text-success">
                {result.overall.adopt}% adopt
              </span>{" "}
              ·
            </span>
            <span>
              <span className="font-semibold text-danger">
                {result.overall.reject}% reject
              </span>{" "}
              ·
            </span>
            <span className="font-semibold text-muted-foreground">
              {result.overall.ignore}% ignore
            </span>
            <span className="ml-auto text-muted-foreground">
              {extras
                ? "Share of people who passed a stockist · seeded simulation"
                : "Modelled first-encounter outcome · deterministic demo"}
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

        {extras?.report && extras.report.action_items.length > 0 && (
          <div className="mt-6 rounded-xl border bg-card p-4 shadow-xs">
            <p className="text-sm font-semibold">Action list</p>
            <ul className="mt-2 flex flex-col gap-3">
              {extras.report.action_items.map((a) => (
                <li key={a.action} className="text-sm">
                  <div className="flex items-start gap-2">
                    <Badge variant="outline" className="shrink-0 text-[10px] capitalize">
                      {a.priority}
                    </Badge>
                    <span className="font-medium">{a.action}</span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {a.rationale}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}

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
        <>
          <StagedLoader
            steps={SIM_STEPS(area.name)}
            onDone={onLoaderDone}
            stepMs={2500}
          />
          {loaderDone && (
            <p className="fixed inset-x-0 bottom-16 z-50 text-center text-xs text-muted-foreground">
              {progress || "Finishing up"}…
            </p>
          )}
        </>
      )}
    </div>
  )
}
