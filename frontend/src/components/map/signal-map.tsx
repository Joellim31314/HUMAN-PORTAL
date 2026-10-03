"use client"

import dynamic from "next/dynamic"

import type { Area } from "@/lib/types"

const LeafletMap = dynamic(() => import("@/components/map/leaflet-map"), {
  ssr: false,
  loading: () => <div className="absolute inset-0 animate-pulse bg-muted" />,
})

export function SignalMap({
  areas,
  selectedSlug,
  onSelect,
}: {
  areas: Area[]
  selectedSlug: string | null
  onSelect: (slug: string) => void
}) {
  return (
    <div className="relative h-full w-full">
      <LeafletMap
        areas={areas}
        selectedSlug={selectedSlug}
        onSelect={onSelect}
      />
    </div>
  )
}
