import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Tentang Pembuat" section="General">
      <div className="rounded-xl bg-muted/50 p-6 text-sm text-muted-foreground">
        Profil singkat pembuat dan informasi kontak akan ditampilkan di sini.
      </div>
    </DashboardPageShell>
  )
}
