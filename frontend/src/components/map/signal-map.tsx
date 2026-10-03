"use client"

import dynamic from "next/dynamic"

const LeafletMap = dynamic(() => import("@/components/map/leaflet-map"), {
  ssr: false,
  loading: () => <div className="absolute inset-0 animate-pulse bg-muted" />,
})

export function SignalMap() {
  return (
    <div className="relative h-full w-full">
      <LeafletMap />
    </div>
  )
}
