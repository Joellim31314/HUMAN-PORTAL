"use client"

import { useEffect } from "react"
import {
  Circle,
  MapContainer,
  ScaleControl,
  TileLayer,
  Tooltip,
  useMap,
  ZoomControl,
} from "react-leaflet"
import "leaflet/dist/leaflet.css"

import type { Area } from "@/lib/types"

const AREA_COLOR = "#3D74F6"

function PanTo({ area }: { area: Area | null }) {
  const map = useMap()
  useEffect(() => {
    if (area) map.flyTo(area.center, 13, { duration: 0.8 })
  }, [area, map])
  return null
}

export default function LeafletMap({
  areas,
  selectedSlug,
  onSelect,
}: {
  areas: Area[]
  selectedSlug: string | null
  onSelect: (slug: string) => void
}) {
  const selected = areas.find((a) => a.slug === selectedSlug) ?? null

  return (
    <MapContainer
      center={[51.545, -0.05]}
      zoom={11}
      zoomControl={false}
      scrollWheelZoom
      className="h-full w-full"
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ZoomControl position="topright" />
      <ScaleControl position="bottomleft" imperial />
      <PanTo area={selected} />
      {areas.map((area) => {
        const isSelected = selectedSlug === area.slug
        return (
          <Circle
            key={area.slug}
            center={area.center}
            radius={area.radiusM}
            pathOptions={{
              color: AREA_COLOR,
              weight: isSelected ? 3 : 1.5,
              fillColor: AREA_COLOR,
              fillOpacity: isSelected ? 0.3 : 0.16,
            }}
            eventHandlers={{ click: () => onSelect(area.slug) }}
          >
            <Tooltip
              permanent
              direction="center"
              interactive={false}
              className="area-rank-label"
            >
              {area.rank}
            </Tooltip>
          </Circle>
        )
      })}
    </MapContainer>
  )
}
