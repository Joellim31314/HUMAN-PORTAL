"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowRight, Pencil, Search } from "lucide-react"

import { AreaList } from "@/components/research/area-list"
import { BetStrip } from "@/components/research/bet-strip"
import { EvidenceSidebar } from "@/components/research/evidence-sidebar"
import { SignalMap } from "@/components/map/signal-map"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { AREAS, EXAMPLE_PRODUCT, getSettlements } from "@/lib/fixtures"
import { scoreAreas } from "@/lib/sim-api"
import type { LiveAreaScore } from "@/lib/sim-api"
import { useProduct, useSearchesLeft } from "@/lib/storage"
import { useIsMobile } from "@/hooks/use-mobile"

export function ResearchWorkspace({
  productSlug,
  initialArea,
}: {
  productSlug: string
  initialArea: string | null
}) {
  const router = useRouter()
  const isMobile = useIsMobile()
  const saved = useProduct()
  const isExample = !saved
  const product = saved ?? EXAMPLE_PRODUCT
  const searchesLeft = useSearchesLeft()
  const [selectedSlug, setSelectedSlug] = useState<string | null>(initialArea)
  const [listOpen, setListOpen] = useState(false)
  const [liveScores, setLiveScores] = useState<Record<
    string,
    LiveAreaScore
  > | null>(null)

  const settlements = getSettlements(product)
  const placementSettlement = settlements.find((s) => s.key === "placement")
  const selectedArea = AREAS.find((a) => a.slug === selectedSlug) ?? null

  useEffect(() => {
    let cancelled = false
    setLiveScores(null)
    scoreAreas(product).then((scores) => {
      if (!cancelled && scores) setLiveScores(scores)
    })
    return () => {
      cancelled = true
    }
  }, [product])

  function selectArea(slug: string) {
    setSelectedSlug(slug)
    setListOpen(false)
    router.replace(`/research?product=${product.slug}&area=${slug}`)
  }

  const list = (
    <AreaList
      areas={AREAS}
      selectedSlug={selectedSlug}
      placementSlug={placementSettlement?.areaSlug ?? null}
      liveScores={liveScores}
      onSelect={selectArea}
    />
  )

  const evidence = selectedArea ? (
    <EvidenceSidebar area={selectedArea} product={product} />
  ) : null

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-start justify-between gap-4 px-5 pt-4 pb-3">
        <div className="space-y-0.5">
          <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            {product.name}
            {isExample && (
              <Badge variant="secondary" className="text-xs font-medium">
                Demo dataset
              </Badge>
            )}
          </h1>
          <p className="text-sm text-muted-foreground">
            {product.category} · £{product.price}
            {product.packSize ? ` · ${product.packSize}` : ""} —{" "}
            {AREAS.length} London areas scored
          </p>
          <p className="text-xs text-muted-foreground">
            {searchesLeft} free searches left this month
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isMobile && (
            <Button
              variant="outline"
              size="sm"
              className="gap-2 rounded-lg bg-card shadow-sm"
              onClick={() => setListOpen(true)}
            >
              <Search className="size-4" />
              Areas
            </Button>
          )}
          {isExample ? (
            <Button size="sm" className="gap-2 rounded-lg" asChild>
              <Link href="/interview">
                Test your product
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className="gap-2 rounded-lg bg-card shadow-sm"
              asChild
            >
              <Link href="/interview">
                <Pencil className="size-4" />
                Edit answers
              </Link>
            </Button>
          )}
        </div>
      </header>

      <BetStrip settlements={settlements} />

      <div className="flex min-h-0 flex-1">
        {isMobile ? (
          <Sheet open={listOpen} onOpenChange={setListOpen}>
            <SheetContent
              side="left"
              className="w-[320px] gap-0 overflow-y-auto p-0 sm:max-w-none"
            >
              <SheetHeader className="sr-only">
                <SheetTitle>Areas</SheetTitle>
              </SheetHeader>
              {list}
            </SheetContent>
          </Sheet>
        ) : (
          <aside className="w-[320px] shrink-0 overflow-y-auto border-r bg-muted/30">
            {list}
          </aside>
        )}

        <main className="relative min-w-0 flex-1">
          <SignalMap
            areas={AREAS}
            selectedSlug={selectedSlug}
            onSelect={selectArea}
          />
        </main>

        {evidence &&
          (isMobile ? (
            <Sheet
              open={!!selectedSlug}
              onOpenChange={(open) => {
                if (!open) {
                  setSelectedSlug(null)
                  router.replace(`/research?product=${product.slug}`)
                }
              }}
            >
              <SheetContent
                side="right"
                className="w-[380px] gap-0 overflow-hidden p-0 sm:max-w-none"
              >
                <SheetHeader className="sr-only">
                  <SheetTitle>
                    {selectedArea?.name ?? "Area evidence"}
                  </SheetTitle>
                </SheetHeader>
                {evidence}
              </SheetContent>
            </Sheet>
          ) : (
            <aside className="w-[380px] shrink-0 overflow-hidden border-l bg-muted/30">
              {evidence}
            </aside>
          ))}
      </div>
    </div>
  )
}
