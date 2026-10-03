"use client"

import { MapContainer, ScaleControl, TileLayer, ZoomControl } from "react-leaflet"
import "leaflet/dist/leaflet.css"

export default function LeafletMap() {
  return (
    <MapContainer
      center={[51.5054, -0.0901]}
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
    </MapContainer>
  )
}
