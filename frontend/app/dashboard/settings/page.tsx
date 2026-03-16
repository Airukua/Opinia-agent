import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Settings" section="General">
      <div className="rounded-xl bg-muted/50 p-6 text-sm text-muted-foreground">
        Manage preferences, teams, and system settings here.
      </div>
    </DashboardPageShell>
  )
}
