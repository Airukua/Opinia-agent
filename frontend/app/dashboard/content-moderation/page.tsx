import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Content Moderation" section="Main Workflow">
      <div className="rounded-xl bg-muted/50 p-6 text-sm text-muted-foreground">
        Content moderation queue and rules will be shown here.
      </div>
    </DashboardPageShell>
  )
}
