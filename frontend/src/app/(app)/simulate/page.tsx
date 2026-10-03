import type { Metadata } from "next"

import { SimWorkspace } from "@/components/simulate/sim-workspace"

export const metadata: Metadata = {
  title: "MISO Simulation",
}

export default async function SimulatePage({
  searchParams,
}: {
  searchParams: Promise<{ product?: string; area?: string }>
}) {
  const { product, area } = await searchParams
  return <SimWorkspace productSlug={product ?? null} areaSlug={area ?? null} />
}
