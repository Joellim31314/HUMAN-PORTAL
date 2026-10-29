"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import dynamic from "next/dynamic"
import { Pause, Play, RotateCcw, X } from "lucide-react"

import { AgentChat } from "@/components/simulate/agent-chat"
import { Button } from "@/components/ui/button"
import {
  EVENT_OFFSET,
  STATE_COLORS,
  type Derived,
} from "@/components/simulate/playback-shared"
import {
  getAgentTrace,
  getPlayback,
  type AgentTrace,
  type Playback,
} from "@/lib/sim-api"
import { cn } from "@/lib/utils"

const PlaybackMap = dynamic(
  () => import("@/components/simulate/week-playback-map"),
  {
    ssr: false,
    loading: () => <div className="absolute inset-0 animate-pulse bg-[#0b0f17]" />,
  }
)

const SECONDS_PER_SLOT = [1.1, 0.55, 0.28]
const SPEED_LABELS = ["1×", "2×", "4×"]
const DAY_LABELS: Record<string, string> = {
  mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun",
}
// Hours each slot spans (backend/app/schemas.py SLOTS); night runs 23:00-06:00.
const SLOT_HOURS: Record<string, [number, number, string]> = {
  early_morning: [6, 8, "Early morning"],
  morning: [8, 10, "Morning commute"],
  midday: [10, 14, "Midday & lunch"],
  afternoon: [14, 17, "Afternoon"],
  evening: [17, 19, "Evening commute"],
  late_evening: [19, 23, "Late evening"],
  night: [23, 30, "Night"],
}
const ARCHETYPES: Record<string, string> = {
  office_commuter: "Office commuter",
  shift_worker: "Shift worker",
  student: "Student",
  wfh: "Works from home",
  retired: "Retiree",
  carer: "Carer",
}
const FEED_VERB = {
  noticed: "spotted it on the shelf",
  rejected: "picked it up, then put it back",
  bought: "bought it",
} as const
const OUTCOME_LABEL: Record<string, [string, string]> = {
  bought: ["Bought it", STATE_COLORS.bought],
  rejected: ["Turned it down", STATE_COLORS.rejected],
  no_need: ["Noticed, no need", STATE_COLORS.noticed],
  not_noticed: ["Walked past", STATE_COLORS.seen],
  never_exposed: ["Never near a stockist", "#94a3b8"],
}

function derive(data: Playback): Derived {
  const n = data.agents.length
  const d: Derived = {
    seen: new Float32Array(n).fill(Infinity),
    noticed: new Float32Array(n).fill(Infinity),
    rejected: new Float32Array(n).fill(Infinity),
    bought: new Float32Array(n).fill(Infinity),
  }
  for (const [i, tick, kind] of data.events) {
    if (kind === "missed") continue
    d[kind][i] = Math.min(d[kind][i], tick)
    // Anyone who noticed or decided was necessarily near the product.
    if (kind !== "seen") d.seen[i] = Math.min(d.seen[i], tick)
    if (kind === "rejected" || kind === "bought") d.noticed[i] = Math.min(d.noticed[i], tick)
  }
  return d
}

function clock(data: Playback, t: number) {
  const ns = data.slots.length
  const tick = Math.min(Math.floor(t), data.days.length * ns - 1)
  const [start, end, label] = SLOT_HOURS[data.slots[tick % ns]] ?? [0, 0, ""]
  const minutes = Math.floor((start + (end - start) * (t - tick)) * 60) % (24 * 60)
  const hh = String(Math.floor(minutes / 60)).padStart(2, "0")
  const mm = String(minutes % 60).padStart(2, "0")
  return { day: DAY_LABELS[data.days[Math.floor(tick / ns)]], time: `${hh}:${mm}`, label }
}

function Stat({
  color,
  label,
  value,
  shop,
}: {
  color: string
  label: string
  value: number
  shop?: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn("size-2", shop ? "rotate-45 border opacity-80" : "rounded-full")}
        style={shop ? { borderColor: color, background: `${color}40` } : { background: color }}
      />
      <span className="text-white/60">{label}</span>
      <span className="ml-auto pl-3 font-semibold tabular-nums text-white">
        {value.toLocaleString()}
      </span>
    </div>
  )
}

export function WeekPlayback({
  simId,
  center,
  productName,
}: {
  simId: string
  center: [number, number]
  productName: string
}) {
  const [data, setData] = useState<Playback | null>(null)
  const [failed, setFailed] = useState(false)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(0)
  const [tick, setTick] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [trace, setTrace] = useState<AgentTrace | null>(null)
  const [tab, setTab] = useState<"week" | "ask">("week")
  const tickRef = useRef(0)

  useEffect(() => {
    let cancelled = false
    getPlayback(simId)
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        console.warn("Playback unavailable", err)
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [simId])

  const derived = useMemo(() => (data ? derive(data) : null), [data])
  const total = data ? data.days.length * data.slots.length : 1

  // Advance the clock every frame; React only re-renders ~12 times a second.
  useEffect(() => {
    if (!data || !playing) return
    let raf = 0
    let prev = performance.now()
    let lastUi = 0
    const step = (now: number) => {
      tickRef.current = Math.min(total, tickRef.current + (now - prev) / 1000 / SECONDS_PER_SLOT[speed])
      prev = now
      if (now - lastUi > 80 || tickRef.current >= total) {
        lastUi = now
        setTick(tickRef.current)
      }
      if (tickRef.current >= total) setPlaying(false)
      else raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [data, playing, speed, total])

  useEffect(() => {
    if (!data || selected === null) return
    let cancelled = false
    getAgentTrace(simId, data.agents[selected].id)
      .then((t) => !cancelled && setTrace(t))
      .catch(() => !cancelled && setTrace(null))
    return () => {
      cancelled = true
    }
  }, [data, selected, simId])

  const select = useCallback((i: number | null) => {
    setTrace(null)
    setTab("week")
    setSelected(i)
  }, [])

  // Pause the week while talking so the map isn't racing behind the chat.
  const openTab = (t: "week" | "ask") => {
    setTab(t)
    if (t === "ask") setPlaying(false)
  }

  const seek = (t: number) => {
    tickRef.current = t
    setTick(t)
  }

  const togglePlay = () => {
    if (tickRef.current >= total) {
      seek(0)
      setPlaying(true)
    } else setPlaying((p) => !p)
  }

  const stats = useMemo(() => {
    if (!data || !derived) return null
    const at = tick - EVENT_OFFSET
    const count = (arr: Float32Array) => arr.reduce((n, v) => n + (v <= at ? 1 : 0), 0)
    let missed = 0
    const feed: { i: number; tick: number; kind: keyof typeof FEED_VERB }[] = []
    for (const [i, t, kind] of data.events) {
      if (t > at) break
      if (kind === "missed") missed++
      else if (kind !== "seen") feed.push({ i, tick: t, kind })
    }
    return {
      seen: count(derived.seen),
      noticed: count(derived.noticed),
      rejected: count(derived.rejected),
      bought: count(derived.bought),
      missed,
      feed: feed.slice(-4).reverse(),
    }
  }, [data, derived, tick])

  if (failed) return null

  const now = data ? clock(data, tick) : null
  const ns = data?.slots.length ?? 7
  const agent = data && selected !== null ? data.agents[selected] : null

  return (
    <section className="overflow-hidden rounded-xl border bg-[#0b0f17] shadow-sm">
      <div className="relative h-[520px] max-sm:h-[440px]">
        {data && derived ? (
          // isolate keeps Leaflet's own z-indexes (zoom buttons) under our overlays
          <div className="absolute inset-0 isolate">
            <PlaybackMap
              center={center}
              data={data}
              derived={derived}
              tickRef={tickRef}
              selected={selected}
              onSelect={select}
            />
          </div>
        ) : (
          <div className="absolute inset-0 grid place-items-center text-sm text-white/50">
            Loading the week…
          </div>
        )}

        {/* Clock */}
        <div className="pointer-events-none absolute top-3 left-3 z-[500] rounded-lg bg-black/55 px-3 py-2 text-white backdrop-blur">
          <p className="text-[10px] font-medium tracking-wider text-white/50 uppercase">
            The week, replayed
          </p>
          <p className="mt-0.5 text-2xl font-semibold tabular-nums">
            {now ? `${now.day} ${now.time}` : "—"}
          </p>
          <p className="text-xs text-white/60">{now?.label}</p>
        </div>

        {/* Running totals */}
        {stats && (
          <div className="pointer-events-none absolute top-3 right-3 z-[500] w-56 space-y-1 rounded-lg bg-black/55 px-3 py-2 text-xs backdrop-blur max-sm:hidden">
            <div className="border-b border-white/10 pb-1">
              <Stat color={STATE_COLORS.store} label="Shops stocking it" value={data!.stores.length} shop />
            </div>
            <Stat color={STATE_COLORS.seen} label="Walked past it" value={stats.seen} />
            <Stat color={STATE_COLORS.noticed} label="Noticed it" value={stats.noticed} />
            <Stat color={STATE_COLORS.rejected} label="Turned it down" value={stats.rejected} />
            <Stat color={STATE_COLORS.bought} label="Bought it" value={stats.bought} />
            <div className="border-t border-white/10 pt-1">
              <Stat
                color={STATE_COLORS.missed}
                label="Wanted one, no stockist near"
                value={stats.missed}
              />
            </div>
          </div>
        )}

        {/* Live feed */}
        {data && stats && stats.feed.length > 0 && (
          <div className="absolute bottom-3 left-3 z-[500] w-72 space-y-1 max-sm:hidden">
            {stats.feed.map((f, k) => {
              const a = data.agents[f.i]
              return (
                <button
                  key={`${f.i}-${f.tick}-${f.kind}`}
                  onClick={() => select(f.i)}
                  className="flex w-full items-center gap-2 rounded-md bg-black/55 px-2.5 py-1.5 text-left text-xs text-white backdrop-blur transition-opacity hover:bg-black/75"
                  style={{ opacity: 1 - k * 0.2 }}
                >
                  <span className="size-2 shrink-0 rounded-full" style={{ background: STATE_COLORS[f.kind] }} />
                  <span className="truncate">
                    <span className="font-medium">{a.name.split(" ")[0]}</span>
                    <span className="text-white/60">
                      {" "}({ARCHETYPES[a.archetype]?.toLowerCase()}) {FEED_VERB[f.kind]}
                    </span>
                  </span>
                  <span className="ml-auto shrink-0 text-white/40 tabular-nums">
                    {DAY_LABELS[data.days[Math.floor(f.tick / ns)]]}
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {/* Followed agent */}
        {agent && (
          <aside className="absolute top-3 right-3 bottom-3 z-[600] flex w-80 flex-col overflow-hidden rounded-lg border border-white/10 bg-[#111723]/95 text-white shadow-xl backdrop-blur max-sm:inset-x-3 max-sm:w-auto">
            <div className="flex items-start gap-2 border-b border-white/10 p-3">
              <div className="min-w-0">
                <p className="font-semibold">
                  {trace ? `${trace.agent.name}, ${trace.agent.age}` : agent.name}
                </p>
                <p className="truncate text-xs text-white/60">
                  {ARCHETYPES[agent.archetype]}
                  {trace && ` · ${trace.agent.borough}`}
                  {trace?.agent.work_label && ` → ${trace.agent.work_label}`}
                </p>
                <span
                  className="mt-1.5 inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2 py-0.5 text-[11px]"
                >
                  <span className="size-1.5 rounded-full" style={{ background: OUTCOME_LABEL[agent.outcome][1] }} />
                  {OUTCOME_LABEL[agent.outcome][0]} by Sunday
                </span>
              </div>
              <button
                onClick={() => select(null)}
                className="ml-auto rounded p-1 text-white/50 hover:bg-white/10 hover:text-white"
                aria-label="Stop following"
              >
                <X className="size-4" />
              </button>
            </div>
            <div className="flex border-b border-white/10 text-xs">
              {(["week", "ask"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => openTab(t)}
                  className={cn(
                    "flex-1 py-2 text-white/50 hover:text-white",
                    tab === t && "border-b-2 border-[#60a5fa] font-medium text-white"
                  )}
                >
                  {t === "week" ? "Their week" : `Ask ${agent.name.split(" ")[0]}`}
                </button>
              ))}
            </div>
            {tab === "ask" ? (
              <AgentChat
                key={agent.id}
                simId={simId}
                agentId={agent.id}
                firstName={agent.name.split(" ")[0]}
                productName={productName}
              />
            ) : (
              <>
                {trace?.interview && (
                  <p className="border-b border-white/10 p-3 text-sm leading-relaxed text-white/80 italic">
                    &ldquo;{trace.interview.quote}&rdquo;
                  </p>
                )}
                <ol className="flex-1 space-y-2 overflow-y-auto p-3 text-xs">
                  {!trace && <li className="text-white/50">Loading their week…</li>}
                  {trace?.trace.length === 0 && (
                    <li className="text-white/50">
                      Never came within walking distance of a shop stocking {productName}.
                    </li>
                  )}
                  {trace?.trace.map((e, k) => {
                    const t = data!.days.indexOf(e.day) * ns + data!.slots.indexOf(e.slot)
                    const happened = t <= tick - EVENT_OFFSET
                    return (
                      <li
                        key={k}
                        className={cn("flex gap-2 transition-opacity", !happened && "opacity-35")}
                      >
                        <span
                          className="mt-1 size-1.5 shrink-0 rounded-full"
                          style={{ background: e.passed ? STATE_COLORS.bought : STATE_COLORS.rejected }}
                        />
                        <span>
                          <span className="font-medium text-white/90">
                            {DAY_LABELS[e.day]} · {SLOT_HOURS[e.slot]?.[2].toLowerCase()}
                          </span>
                          <span className="block text-white/60">{e.detail}</span>
                        </span>
                      </li>
                    )
                  })}
                </ol>
              </>
            )}
          </aside>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 border-t border-white/10 px-3 py-2.5 text-white">
        <Button
          size="icon"
          variant="ghost"
          className="size-8 shrink-0 text-white hover:bg-white/10 hover:text-white"
          onClick={togglePlay}
          disabled={!data}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <Pause className="size-4" />
          ) : tick >= total ? (
            <RotateCcw className="size-4" />
          ) : (
            <Play className="size-4" />
          )}
        </Button>
        <div className="flex-1">
          <input
            type="range"
            min={0}
            max={total}
            step={0.01}
            value={tick}
            onChange={(e) => seek(Number(e.target.value))}
            className="w-full accent-[#60a5fa]"
            aria-label="Simulated time"
            disabled={!data}
          />
          <div className="flex justify-between text-[10px] text-white/40">
            {(data?.days ?? Object.keys(DAY_LABELS)).map((d) => (
              <span key={d}>{DAY_LABELS[d]}</span>
            ))}
          </div>
        </div>
        <button
          onClick={() => setSpeed((s) => (s + 1) % SPEED_LABELS.length)}
          className="w-10 shrink-0 rounded-md border border-white/15 py-1 text-xs tabular-nums text-white/80 hover:bg-white/10"
          aria-label="Playback speed"
        >
          {SPEED_LABELS[speed]}
        </button>
      </div>
      <p className="border-t border-white/10 px-3 py-2 text-[11px] text-white/45">
        Each round dot is one simulated Londoner moving between home, work and errands.
        Cyan diamonds are shops stocking {productName}; they stay put. Click a dot to follow
        that person&apos;s week.
      </p>
    </section>
  )
}
