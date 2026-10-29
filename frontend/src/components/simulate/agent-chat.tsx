"use client"

import { useEffect, useRef, useState, type FormEvent } from "react"
import { Loader2, SendHorizontal } from "lucide-react"

import { chatWithAgent, type ChatTurn } from "@/lib/sim-api"
import { cn } from "@/lib/utils"

const SUGGESTIONS = (product: string) => [
  `What would make you buy ${product}?`,
  "Would a lower price change your mind?",
  "Where do you usually shop during the week?",
]

export function AgentChat({
  simId,
  agentId,
  firstName,
  productName,
}: {
  simId: string
  agentId: string
  firstName: string
  productName: string
}) {
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [draft, setDraft] = useState("")
  const [busy, setBusy] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" })
  }, [turns, busy])

  const ask = async (question: string) => {
    const q = question.trim().slice(0, 600)
    if (!q || busy) return
    const next: ChatTurn[] = [...turns, { role: "retailer", content: q }]
    setTurns(next)
    setDraft("")
    setBusy(true)
    try {
      const { reply } = await chatWithAgent(simId, agentId, next)
      setTurns([...next, { role: "agent", content: reply }])
    } catch {
      setTurns([...next, { role: "agent", content: "(Couldn't reach the simulation backend.)" }])
    } finally {
      setBusy(false)
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    void ask(draft)
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 space-y-2 overflow-y-auto p-3 text-sm">
        {turns.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-white/50">
              Ask {firstName} anything. Answers stay true to the week they just lived.
            </p>
            {SUGGESTIONS(productName).map((s) => (
              <button
                key={s}
                onClick={() => void ask(s)}
                className="block w-full rounded-md border border-white/15 px-2.5 py-1.5 text-left text-xs text-white/80 hover:bg-white/10"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {turns.map((t, k) => (
          <div
            key={k}
            className={cn(
              "max-w-[88%] rounded-lg px-2.5 py-1.5 leading-relaxed",
              t.role === "retailer"
                ? "ml-auto bg-[#3D74F6] text-white"
                : "bg-white/10 text-white/90"
            )}
          >
            {t.content}
          </div>
        ))}
        {busy && (
          <div className="flex w-fit items-center gap-1.5 rounded-lg bg-white/10 px-2.5 py-1.5 text-xs text-white/60">
            <Loader2 className="size-3 animate-spin" />
            {firstName} is thinking
          </div>
        )}
        <div ref={bottom} />
      </div>
      <form onSubmit={onSubmit} className="flex gap-2 border-t border-white/10 p-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Ask ${firstName} a question…`}
          maxLength={600}
          className="min-w-0 flex-1 rounded-md bg-white/10 px-2.5 py-1.5 text-sm text-white placeholder:text-white/40 focus:ring-1 focus:ring-[#60a5fa] focus:outline-none"
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="rounded-md bg-[#3D74F6] px-2.5 text-white disabled:opacity-40"
          aria-label="Send"
        >
          <SendHorizontal className="size-4" />
        </button>
      </form>
    </div>
  )
}
