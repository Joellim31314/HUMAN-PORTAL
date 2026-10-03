"use client"

import { MapContainer, ScaleControl, TileLayer, ZoomControl } from "react-leaflet"
import "leaflet/dist/leaflet.css"

export default function LeafletMap() {
  return (
    <MapContainer
      center={[39.8283, -98.5795]}
      zoom={4}
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
    </MapContainer>
  )
}
