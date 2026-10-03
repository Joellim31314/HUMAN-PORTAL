import type { Metadata } from "next"

import { ResearchWorkspace } from "@/components/research/research-workspace"

export const metadata: Metadata = {
  title: "Research",
}

export default async function ResearchPage({
  searchParams,
}: {
  searchParams: Promise<{ product?: string; area?: string }>
}) {
  const { product, area } = await searchParams
  return <ResearchWorkspace productSlug={product ?? ""} initialArea={area ?? null} />
}
