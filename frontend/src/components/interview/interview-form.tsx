"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight } from "lucide-react"

import {
  DemoFillButton,
  DEMO_FILL_EVENT,
} from "@/components/demo/demo-fill-button"
import { StagedLoader } from "@/components/staged-loader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { EXAMPLE_PRODUCT, LONDON_AREAS } from "@/lib/fixtures"
import {
  decrementSearches,
  loadProduct,
  saveProduct,
} from "@/lib/storage"
import type { ProductAnswers } from "@/lib/types"
import { cn } from "@/lib/utils"

const CATEGORIES = [
  "Beverages",
  "Snacks & confectionery",
  "Sauces & condiments",
  "Dairy & alternatives",
  "Bakery",
  "Ready meals",
]

const CHANNEL_OPTIONS = [
  "Supermarket",
  "Convenience",
  "D2C online",
  "Cafés",
  "Markets",
  "Food halls",
]

const RESEARCH_STEPS = [
  "Scraping TikTok & Reddit",
  "Reading product reviews",
  "Clustering London personas",
  "Scoring 7 areas",
]

const EMPTY: ProductAnswers = {
  slug: "",
  name: "",
  tagline: "",
  category: "",
  price: "",
  packSize: "",
  status: "prelaunch",
  channels: [],
  buyerGuess: "",
  choiceReason: "",
  rejectReason: "",
  placementGuess: "",
}

export function InterviewForm() {
  const router = useRouter()
  const [form, setForm] = useState<ProductAnswers>(EMPTY)
  const [loaded, setLoaded] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (sessionStorage.getItem(DEMO_FILL_EVENT) === "1") {
      sessionStorage.removeItem(DEMO_FILL_EVENT)
      setForm({ ...EXAMPLE_PRODUCT })
    } else {
      const saved = loadProduct()
      if (saved) setForm({ ...EMPTY, ...saved })
    }
    setLoaded(true)
  }, [])

  useEffect(() => {
    function fill() {
      setForm({ ...EXAMPLE_PRODUCT })
    }
    window.addEventListener(DEMO_FILL_EVENT, fill)
    return () => window.removeEventListener(DEMO_FILL_EVENT, fill)
  }, [])

  function set<K extends keyof ProductAnswers>(key: K, value: ProductAnswers[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function slugify(name: string) {
    return (
      name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "") || "product"
    )
  }

  const valid =
    form.name.trim().length > 0 &&
    form.category !== "" &&
    Number(form.price) > 0 &&
    form.buyerGuess.trim().length > 0 &&
    form.choiceReason.trim().length > 0 &&
    form.placementGuess !== ""

  function submit() {
    if (!valid) return
    const product = { ...form, slug: slugify(form.name) }
    saveProduct(product)
    decrementSearches()
    setSubmitting(true)
  }

  if (!loaded) return null

  return (
    <div className="mx-auto h-full w-full max-w-2xl overflow-y-auto px-6 py-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Where should you sell it?
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Tell us about your product — then we&rsquo;ll show you where it
            wins in London.
          </p>
        </div>
        <DemoFillButton className="mt-0.5 shrink-0" />
      </div>

      <section className="rounded-xl border bg-card p-5 shadow-xs">
        <h2 className="mb-4 text-sm font-semibold">Product facts</h2>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Product name</Label>
            <Input
              id="name"
              placeholder="e.g. Hojicha Bloom"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="tagline">One-liner (optional)</Label>
            <Input
              id="tagline"
              placeholder="Ready-to-drink roasted green tea…"
              value={form.tagline}
              onChange={(e) => set("tagline", e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="category">Category</Label>
              <Select
                value={form.category}
                onValueChange={(v) => set("category", v)}
              >
                <SelectTrigger id="category">
                  <SelectValue placeholder="Pick a category" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="price">Price</Label>
              <div className="relative">
                <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm text-muted-foreground">
                  £
                </span>
                <Input
                  id="price"
                  type="number"
                  min="0"
                  step="0.05"
                  placeholder="3.50"
                  className="pl-7"
                  value={form.price}
                  onChange={(e) => set("price", e.target.value)}
                />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="packSize">Pack size (optional)</Label>
              <Input
                id="packSize"
                placeholder="330ml can"
                value={form.packSize}
                onChange={(e) => set("packSize", e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Status</Label>
              <div className="flex gap-2">
                {(["selling", "prelaunch"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => set("status", s)}
                    className={cn(
                      "h-9 flex-1 rounded-md border text-sm font-medium transition-colors",
                      form.status === s
                        ? "border-primary bg-primary/5 text-primary"
                        : "text-muted-foreground hover:bg-muted"
                    )}
                  >
                    {s === "selling" ? "Selling today" : "Pre-launch"}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Channels (optional)</Label>
            <div className="flex flex-wrap gap-2">
              {CHANNEL_OPTIONS.map((c) => {
                const on = form.channels.includes(c)
                return (
                  <button
                    key={c}
                    type="button"
                    onClick={() =>
                      set(
                        "channels",
                        on
                          ? form.channels.filter((x) => x !== c)
                          : [...form.channels, c]
                      )
                    }
                    className={cn(
                      "h-8 rounded-md border px-3 text-sm font-medium transition-colors",
                      on
                        ? "border-primary bg-primary/5 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {c}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-4 rounded-xl border bg-card p-5 shadow-xs">
        <h2 className="mb-1 text-sm font-semibold">Your bets</h2>
        <p className="mb-4 text-xs text-muted-foreground">
          Your honest guesses — we&rsquo;ll settle them against the signals.
        </p>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="buyerGuess">Who do you think buys it?</Label>
            <Textarea
              id="buyerGuess"
              placeholder="Health-conscious millennial professionals…"
              value={form.buyerGuess}
              onChange={(e) => set("buyerGuess", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="choiceReason">
              Why do they choose it over the alternative?
            </Label>
            <Textarea
              id="choiceReason"
              placeholder="Calmer caffeine, antioxidants, no bitterness…"
              value={form.choiceReason}
              onChange={(e) => set("choiceReason", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="rejectReason">
              Why would someone distrust or reject it? (optional)
            </Label>
            <Textarea
              id="rejectReason"
              placeholder="Unknown brand, price vs canned coffee…"
              value={form.rejectReason}
              onChange={(e) => set("rejectReason", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="placementGuess">
              Where in London would it sell best?
            </Label>
            <Select
              value={form.placementGuess}
              onValueChange={(v) => set("placementGuess", v)}
            >
              <SelectTrigger id="placementGuess">
                <SelectValue placeholder="Pick an area — this one gets settled on the map" />
              </SelectTrigger>
              <SelectContent>
                {LONDON_AREAS.map((a) => (
                  <SelectItem key={a} value={a.toLowerCase()}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      <div className="sticky bottom-0 -mx-6 mt-6 bg-background/95 px-6 py-4 backdrop-blur">
        <Button
          className="w-full gap-2"
          disabled={!valid}
          onClick={submit}
        >
          Research London
          <ArrowRight className="size-4" />
        </Button>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Costs 1 of your 35 free searches
        </p>
      </div>

      {submitting && (
        <StagedLoader
          steps={RESEARCH_STEPS}
          onDone={() => router.push(`/research?product=${slugify(form.name)}`)}
        />
      )}
    </div>
  )
}
