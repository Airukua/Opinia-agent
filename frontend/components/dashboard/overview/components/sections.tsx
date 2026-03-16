"use client"

export function StatCard({ label, value, sub, accent }: {
  label: string; value: string; sub?: string; accent?: string
}) {
  return (
    <div className="rounded-xl border border-border/40 bg-card p-4">
      <p className="text-[11px] font-medium uppercase tracking-[.07em] text-muted-foreground/60 mb-1">{label}</p>
      <p className={`text-2xl font-medium tracking-tight ${accent ?? "text-foreground"}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground/60 mt-0.5">{sub}</p>}
    </div>
  )
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-medium uppercase tracking-[.07em] text-muted-foreground/50 mb-4 pb-3 border-b border-border/30">
      {children}
    </p>
  )
}
