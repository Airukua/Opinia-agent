"use client"
import { OverviewContent } from "@/components/dashboard/overview-content"
import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Overview" section="Main Workflow">
      <OverviewContent />
    </DashboardPageShell>
  )
}
