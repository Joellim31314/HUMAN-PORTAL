import type { Metadata } from "next"
import { redirect } from "next/navigation"

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
  if (!product) redirect("/interview")
  return <ResearchWorkspace productSlug={product} initialArea={area ?? null} />
}
