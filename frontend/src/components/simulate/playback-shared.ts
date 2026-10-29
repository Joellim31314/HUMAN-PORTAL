// Shared between the week playback controls and its Leaflet canvas, kept free
// of Leaflet imports so the controls can render on the server.

// Events happen this far into their slot; agents travel in the last part of it.
export const EVENT_OFFSET = 0.3

export const STATE_COLORS = {
  idle: "rgba(148, 163, 184, 0.6)",
  seen: "#60a5fa",
  noticed: "#fbbf24",
  rejected: "#f87171",
  bought: "#4ade80",
  missed: "#a78bfa",
  store: "#22d3ee",
} as const

export interface Derived {
  /** First tick each agent reached a state (Infinity = never). */
  seen: Float32Array
  noticed: Float32Array
  rejected: Float32Array
  bought: Float32Array
}
