"use client"

import { useEffect, useRef, type MutableRefObject } from "react"
import { MapContainer, TileLayer, useMap, ZoomControl } from "react-leaflet"
import "leaflet/dist/leaflet.css"

import {
  EVENT_OFFSET,
  STATE_COLORS,
  type Derived,
} from "@/components/simulate/playback-shared"
import type { Playback } from "@/lib/sim-api"

const TRAVEL_START = 0.55
const PULSE_TICKS = 1.1

function smooth(x: number) {
  const k = Math.min(1, Math.max(0, x))
  return k * k * (3 - 2 * k)
}

function lowerBound(events: Playback["events"], tick: number) {
  let lo = 0
  let hi = events.length
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (events[mid][1] < tick) lo = mid + 1
    else hi = mid
  }
  return lo
}

function pointAt(a: Playback["agents"][number], tick: number, ns: number) {
  const path = Math.floor(tick / ns) < 5 ? a.weekday : a.weekend
  return path[tick % ns]
}

function PlaybackCanvas({
  data,
  derived,
  tickRef,
  selected,
  onSelect,
}: {
  data: Playback
  derived: Derived
  tickRef: MutableRefObject<number>
  selected: number | null
  onSelect: (i: number | null) => void
}) {
  const map = useMap()
  const selectedRef = useRef(selected)
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    selectedRef.current = selected
    onSelectRef.current = onSelect
  }, [selected, onSelect])

  useEffect(() => {
    const container = map.getContainer()
    const canvas = document.createElement("canvas")
    canvas.style.cssText =
      "position:absolute;inset:0;z-index:450;pointer-events:none"
    container.appendChild(canvas)
    const ctx = canvas.getContext("2d")!
    const ns = data.slots.length
    const last = data.days.length * ns - 1
    const xy = new Float32Array(data.agents.length * 2).fill(NaN)

    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      canvas.width = container.clientWidth * dpr
      canvas.height = container.clientHeight * dpr
      canvas.style.width = `${container.clientWidth}px`
      canvas.style.height = `${container.clientHeight}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(container)

    const dot = (x: number, y: number, r: number, color: string) => {
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(x, y, r, 0, Math.PI * 2)
      ctx.fill()
    }

    let raf = 0
    const draw = () => {
      raf = requestAnimationFrame(draw)
      const t = tickRef.current
      const s = Math.min(Math.floor(t), last)
      const k = smooth((t - s - TRAVEL_START) / (1 - TRAVEL_START))
      const n = Math.min(s + 1, last)
      ctx.clearRect(0, 0, container.clientWidth, container.clientHeight)

      // Stocking shops: fixed cyan diamonds, drawn unlike the round agent dots.
      ctx.strokeStyle = STATE_COLORS.store
      ctx.fillStyle = STATE_COLORS.store
      ctx.lineWidth = 1
      for (const st of data.stores) {
        const p = map.latLngToContainerPoint([st.lat, st.lon])
        ctx.beginPath()
        ctx.moveTo(p.x, p.y - 4)
        ctx.lineTo(p.x + 4, p.y)
        ctx.lineTo(p.x, p.y + 4)
        ctx.lineTo(p.x - 4, p.y)
        ctx.closePath()
        ctx.globalAlpha = 0.25
        ctx.fill()
        ctx.globalAlpha = 0.8
        ctx.stroke()
      }
      ctx.globalCompositeOperation = "lighter"

      // Agents, coloured by the furthest funnel stage reached so far.
      const at = t - EVENT_OFFSET
      for (let i = 0; i < data.agents.length; i++) {
        const a = data.agents[i]
        if (a.weekday.length < ns || a.weekend.length < ns) continue
        const p0 = pointAt(a, s, ns)
        const p1 = pointAt(a, n, ns)
        const p = map.latLngToContainerPoint([
          p0[0] + (p1[0] - p0[0]) * k,
          p0[1] + (p1[1] - p0[1]) * k,
        ])
        xy[i * 2] = p.x
        xy[i * 2 + 1] = p.y
        let color: string = STATE_COLORS.idle
        let r = 1.6
        if (derived.bought[i] <= at) [color, r] = [STATE_COLORS.bought, 3.2]
        else if (derived.rejected[i] <= at) [color, r] = [STATE_COLORS.rejected, 2.8]
        else if (derived.noticed[i] <= at) [color, r] = [STATE_COLORS.noticed, 2.6]
        else if (derived.seen[i] <= at) [color, r] = [STATE_COLORS.seen, 2]
        ctx.globalAlpha = 1
        dot(p.x, p.y, r, color)
      }

      // Pulses for events happening right now.
      ctx.lineWidth = 1.5
      for (let e = lowerBound(data.events, Math.ceil(at - PULSE_TICKS)); e < data.events.length; e++) {
        const [i, tick, kind] = data.events[e]
        const age = at - tick
        if (age < 0) break
        if (age > PULSE_TICKS || kind === "seen" || Number.isNaN(xy[i * 2])) continue
        const life = age / PULSE_TICKS
        const big = kind === "bought" || kind === "rejected"
        ctx.globalAlpha = (1 - life) * (kind === "missed" ? 0.35 : 0.9)
        ctx.strokeStyle = STATE_COLORS[kind]
        ctx.beginPath()
        ctx.arc(xy[i * 2], xy[i * 2 + 1], 3 + life * (big ? 22 : kind === "missed" ? 9 : 14), 0, Math.PI * 2)
        ctx.stroke()
      }

      // The followed agent: today's route plus a highlighted marker.
      const sel = selectedRef.current
      if (sel !== null && !Number.isNaN(xy[sel * 2])) {
        const a = data.agents[sel]
        const day = Math.floor(s / ns)
        ctx.globalCompositeOperation = "source-over"
        ctx.globalAlpha = 0.85
        ctx.strokeStyle = "#ffffff"
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        for (let j = 0; j < ns; j++) {
          const q = pointAt(a, day * ns + j, ns)
          const p = map.latLngToContainerPoint([q[0], q[1]])
          if (j === 0) ctx.moveTo(p.x, p.y)
          else ctx.lineTo(p.x, p.y)
        }
        ctx.stroke()
        ctx.setLineDash([])
        ctx.globalAlpha = 1
        ctx.lineWidth = 2.5
        ctx.beginPath()
        ctx.arc(xy[sel * 2], xy[sel * 2 + 1], 8, 0, Math.PI * 2)
        ctx.stroke()
      }
      ctx.globalAlpha = 1
      ctx.globalCompositeOperation = "source-over"
    }
    raf = requestAnimationFrame(draw)

    const onClick = (ev: { containerPoint: { x: number; y: number } }) => {
      const { x, y } = ev.containerPoint
      let best: number | null = null
      let bestD = 12 * 12
      for (let i = 0; i < data.agents.length; i++) {
        const dx = xy[i * 2] - x
        const dy = xy[i * 2 + 1] - y
        const d = dx * dx + dy * dy
        if (d < bestD) [best, bestD] = [i, d]
      }
      onSelectRef.current(best)
    }
    map.on("click", onClick)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      map.off("click", onClick)
      canvas.remove()
    }
  }, [map, data, derived, tickRef])

  return null
}

export default function WeekPlaybackMap({
  center,
  ...rest
}: {
  center: [number, number]
  data: Playback
  derived: Derived
  tickRef: MutableRefObject<number>
  selected: number | null
  onSelect: (i: number | null) => void
}) {
  return (
    <MapContainer
      center={center}
      zoom={11.5}
      zoomSnap={0.5}
      zoomControl={false}
      zoomAnimation={false}
      scrollWheelZoom={false}
      className="h-full w-full"
      style={{ height: "100%", width: "100%", background: "#0b0f17" }}
    >
      <TileLayer
        attribution="Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        maxNativeZoom={16}
      />
      <ZoomControl position="bottomright" />
      <PlaybackCanvas {...rest} />
    </MapContainer>
  )
}
