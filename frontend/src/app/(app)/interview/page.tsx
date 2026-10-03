import type { Metadata } from "next"

import { InterviewForm } from "@/components/interview/interview-form"

export const metadata: Metadata = {
  title: "New product",
}

export default function InterviewPage() {
  return <InterviewForm />
}
