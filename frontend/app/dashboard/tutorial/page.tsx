import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Tutorial" section="Main Workflow">
      <div className="rounded-xl bg-muted/50 p-6 text-sm text-muted-foreground">
        Tutorial workspace will live here.
      </div>
    </DashboardPageShell>
  )
}
