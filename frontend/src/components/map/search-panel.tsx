"use client"

import { useState } from "react"
import { MapPin, Pentagon, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

const radiusOptions = ["100 m", "250 m", "500 m", "1 km", "5 km"]
const dateOptions = ["3 m", "6 m", "12 m", "24 m", "5 y", "10 y"]

const filters = [
  {
    id: "category",
    label: "Category",
    placeholder: "All categories",
    options: [
      "Beverages",
      "Snacks & confectionery",
      "Sauces & condiments",
      "Dairy & alternatives",
      "Bakery",
      "Ready meals",
    ],
  },
  {
    id: "channel",
    label: "Channel",
    placeholder: "All channels",
    options: ["TikTok", "Reddit", "YouTube", "X / Twitter", "Product reviews"],
  },
  {
    id: "signal",
    label: "Signal",
    placeholder: "All signals",
    options: ["Rising", "Trusted", "Rejected", "Mixed"],
  },
] as const

export function SearchPanel() {
  const [mode, setMode] = useState<"pin" | "area">("pin")

  return (
    <div className="flex flex-col gap-4 p-4">
      <section className="rounded-xl border bg-card p-4 shadow-xs">
        <h2 className="mb-3 text-sm font-semibold">Search</h2>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="address">Address</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="address"
                placeholder="Search an address or postcode"
                className="pl-8"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setMode("pin")}
              className={cn(
                "justify-start",
                mode === "pin" &&
                  "border-primary bg-primary/5 text-primary hover:bg-primary/10 hover:text-primary"
              )}
            >
              <MapPin className="size-4" />
              Place pin
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setMode("area")}
              className={cn(
                "justify-start",
                mode === "area" &&
                  "border-primary bg-primary/5 text-primary hover:bg-primary/10 hover:text-primary"
              )}
            >
              <Pentagon className="size-4" />
              Draw area
            </Button>
          </div>
          <ChipGroup
            id="radius"
            label="Radius"
            options={radiusOptions}
            defaultValue="500 m"
          />
          <ChipGroup
            id="date-range"
            label="Date range"
            options={dateOptions}
            defaultValue="12 m"
          />
          {filters.map((filter) => (
            <div key={filter.id} className="flex flex-col gap-1.5">
              <Label htmlFor={filter.id}>{filter.label}</Label>
              <Select>
                <SelectTrigger id={filter.id} className="w-full">
                  <SelectValue placeholder={filter.placeholder} />
                </SelectTrigger>
                <SelectContent>
                  {filter.options.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
          <Button disabled className="w-full">
            Search this area
          </Button>
        </div>
      </section>
      <section className="rounded-xl border bg-card p-4 shadow-xs">
        <h2 className="text-sm font-semibold">Signal layers</h2>
        <p className="mt-1 mb-3 text-xs text-muted-foreground">
          Overlay human signals on the map. Hover a shape for details, or click
          to keep them open.
        </p>
        <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Sources
        </h3>
        <LayerRow label="TikTok signals" defaultChecked />
        <LayerRow label="Reddit signals" defaultChecked />
        <LayerRow label="Product reviews" defaultChecked />
        <LayerRow label="YouTube signals" />
        <LayerRow label="X / Twitter signals" />
        <Separator className="my-3" />
        <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Market intel
        </h3>
        <LayerRow label="Trend heat" defaultChecked />
        <LayerRow label="Competitor locations" defaultChecked />
        <LayerRow
          label="Shelf presence"
          hint="Search an area to see these"
          disabled
        />
        <LayerRow
          label="Persona clusters"
          hint="Run a simulation to see these"
          disabled
        />
        <Separator className="my-3" />
        <p className="text-xs text-muted-foreground">Data updated 03/10/2026</p>
      </section>
    </div>
  )
}

function ChipGroup({
  id,
  label,
  options,
  defaultValue,
}: {
  id: string
  label: string
  options: readonly string[]
  defaultValue: string
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>{label}</Label>
      <RadioGroup defaultValue={defaultValue} className="flex flex-wrap gap-2">
        {options.map((option) => {
          const itemId = `${id}-${option.replace(/\s/g, "-")}`
          return (
            <div key={option}>
              <RadioGroupItem
                id={itemId}
                value={option}
                className="peer sr-only"
              />
              <Label
                htmlFor={itemId}
                className={cn(
                  "flex h-8 cursor-pointer items-center justify-center rounded-md border bg-transparent px-3 text-sm font-medium text-muted-foreground transition-colors",
                  "hover:bg-muted hover:text-foreground",
                  "peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5 peer-data-[state=checked]:text-primary"
                )}
              >
                {option}
              </Label>
            </div>
          )
        })}
      </RadioGroup>
    </div>
  )
}

function LayerRow({
  label,
  hint,
  defaultChecked = false,
  disabled = false,
}: {
  label: string
  hint?: string
  defaultChecked?: boolean
  disabled?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <div className="min-w-0">
        <p className="text-sm leading-tight">{label}</p>
        {hint ? (
          <p className="text-xs text-muted-foreground">{hint}</p>
        ) : null}
      </div>
      <Switch
        defaultChecked={defaultChecked}
        disabled={disabled}
        aria-label={label}
      />
    </div>
  )
}
