import { LicenseContent } from "@/components/dashboard/license-content"
import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="License" section="General">
      <LicenseContent />
    </DashboardPageShell>
  )
}
