"use client"

import { useRef } from "react"
import { ImagePlus, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

export const SALIENCE_LABELS: Record<number, string> = {
  1: "Bland — blends into the shelf",
  2: "Muted — easy to miss",
  3: "Average shelf presence",
  4: "Bold — stands out",
  5: "Loud — impossible to miss",
}

// Downscale the upload (keeps localStorage small) and score how eye-catching it
// is from colour saturation and contrast. DeepSeek is text-only, so this score
// is what the simulation's "notice it on the shelf" step consumes.
async function analyse(file: File): Promise<{ dataUrl: string; salience: number }> {
  const url = URL.createObjectURL(file)
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image()
      el.onload = () => resolve(el)
      el.onerror = reject
      el.src = url
    })
    const scale = Math.min(1, 320 / Math.max(img.width, img.height))
    const canvas = document.createElement("canvas")
    canvas.width = Math.max(1, Math.round(img.width * scale))
    canvas.height = Math.max(1, Math.round(img.height * scale))
    const ctx = canvas.getContext("2d")!
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height)

    let satSum = 0
    let lumSum = 0
    let lumSq = 0
    const n = data.length / 4
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i] / 255
      const g = data[i + 1] / 255
      const b = data[i + 2] / 255
      const max = Math.max(r, g, b)
      const min = Math.min(r, g, b)
      satSum += max === 0 ? 0 : (max - min) / max
      const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
      lumSum += lum
      lumSq += lum * lum
    }
    const saturation = satSum / n
    const contrast = Math.sqrt(Math.max(0, lumSq / n - (lumSum / n) ** 2))
    const score = 0.65 * saturation + 0.35 * Math.min(1, contrast * 3)
    const salience = Math.min(5, Math.max(1, Math.round(1 + score * 5)))
    return { dataUrl: canvas.toDataURL("image/jpeg", 0.8), salience }
  } finally {
    URL.revokeObjectURL(url)
  }
}

export function PackagingUpload({
  image,
  salience,
  onChange,
}: {
  image?: string
  salience?: number
  onChange: (image: string | undefined, salience: number | undefined) => void
}) {
  const input = useRef<HTMLInputElement>(null)

  async function pick(file: File | undefined) {
    if (!file) return
    const result = await analyse(file)
    onChange(result.dataUrl, result.salience)
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label>Packaging photo (optional)</Label>
      <div className="flex items-start gap-4">
        <button
          type="button"
          onClick={() => input.current?.click()}
          className={cn(
            "relative grid size-24 shrink-0 place-items-center overflow-hidden rounded-lg border border-dashed text-muted-foreground transition-colors hover:bg-muted",
            image && "border-solid"
          )}
        >
          {image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={image} alt="Packaging" className="size-full object-cover" />
          ) : (
            <ImagePlus className="size-6" />
          )}
        </button>
        <div className="flex min-w-0 flex-1 flex-col gap-2 text-sm">
          {image ? (
            <>
              <p className="text-xs text-muted-foreground">
                Shelf standout, estimated from colour and contrast — this drives how
                often simulated shoppers notice it.
              </p>
              <div className="flex flex-wrap gap-1.5">
                {[1, 2, 3, 4, 5].map((s) => (
                  <button
                    key={s}
                    type="button"
                    title={SALIENCE_LABELS[s]}
                    onClick={() => onChange(image, s)}
                    className={cn(
                      "h-8 w-8 rounded-md border text-sm font-medium",
                      salience === s
                        ? "border-primary bg-primary/5 text-primary"
                        : "text-muted-foreground hover:bg-muted"
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <p className="text-xs font-medium">
                {salience ? SALIENCE_LABELS[salience] : ""}
              </p>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-fit gap-1.5 px-2 text-muted-foreground"
                onClick={() => onChange(undefined, undefined)}
              >
                <X className="size-3.5" /> Remove photo
              </Button>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">
              Upload a photo of the pack. We score how much it stands out on a shelf,
              and simulated shoppers notice it accordingly.
            </p>
          )}
        </div>
      </div>
      <input
        ref={input}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          void pick(e.target.files?.[0])
          e.target.value = ""
        }}
      />
    </div>
  )
}
