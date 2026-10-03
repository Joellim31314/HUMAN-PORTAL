import type { Metadata } from "next"

import { MapWorkspace } from "@/components/map/map-workspace"

export const metadata: Metadata = {
  title: "Research",
}

export default function ResearchPage() {
  return <MapWorkspace />
}
