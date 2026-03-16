import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="AI Insights" section="Main Workflow">
      <div className="rounded-xl bg-muted/50 p-6 text-sm text-muted-foreground">
        AI insights and analytics will appear here.
      </div>
    </DashboardPageShell>
  )
}
