import { DashboardPageShell } from "@/components/dashboard/page-shell"

export default function Page() {
  return (
    <DashboardPageShell title="Tutorial" section="Main Workflow">
      <div className="rounded-xl border border-border/40 bg-card p-6">
        <p className="text-sm font-medium text-foreground mb-2">Panduan singkat</p>
        <p className="text-[13px] text-muted-foreground leading-relaxed">
          Tempel URL video YouTube di halaman Overview, lalu klik tombol analisa untuk memproses komentar.
          Setelah selesai, pilih video untuk melihat ringkasan, sentimen, topik, dan insight LLM.
        </p>
      </div>
    </DashboardPageShell>
  )
}
