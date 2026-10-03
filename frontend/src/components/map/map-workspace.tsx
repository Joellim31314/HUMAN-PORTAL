"use client"

import { useState } from "react"
import { SlidersHorizontal } from "lucide-react"

import { SearchPanel } from "@/components/map/search-panel"
import { SignalMap } from "@/components/map/signal-map"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { useIsMobile } from "@/hooks/use-mobile"

export function MapWorkspace() {
  const [panelOpen, setPanelOpen] = useState(true)
  const isMobile = useIsMobile()

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-start justify-between gap-4 px-5 pt-4 pb-3">
        <div className="space-y-0.5">
          <h1 className="text-xl font-semibold tracking-tight">Market Radar</h1>
          <p className="text-sm text-muted-foreground">
            Find food & beverage signals on the map
          </p>
          <p className="text-xs text-muted-foreground">
            34 free searches left this month
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2 rounded-lg bg-card shadow-sm"
          onClick={() => setPanelOpen((open) => !open)}
        >
          <SlidersHorizontal className="size-4" />
          <span className="font-medium">Search & signals</span>
          <Separator orientation="vertical" className="h-4!" />
          <span className="text-xs font-normal text-muted-foreground">
            500 m · 12 m
          </span>
        </Button>
      </header>
      <div className="flex min-h-0 flex-1">
        {isMobile ? (
          <Sheet open={panelOpen} onOpenChange={setPanelOpen}>
            <SheetContent
              side="left"
              className="w-[340px] gap-0 overflow-y-auto p-0 sm:max-w-none"
            >
              <SheetHeader className="sr-only">
                <SheetTitle>Search & signals</SheetTitle>
              </SheetHeader>
              <SearchPanel />
            </SheetContent>
          </Sheet>
        ) : panelOpen ? (
          <aside className="w-[340px] shrink-0 overflow-y-auto border-r bg-muted/30">
            <SearchPanel />
          </aside>
        ) : null}
        <main className="relative min-w-0 flex-1">
          <SignalMap />
        </main>
      </div>
    </div>
  )
}
