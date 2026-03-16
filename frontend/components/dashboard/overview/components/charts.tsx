"use client"

import type { EvidenceData } from "../../analysis-types"

export function InlineBar({ data }: {
  data: { label: string; value: number; color: string }[]
}) {
  const total = data.reduce((s, d) => s + d.value, 0)
  return (
    <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-muted/30">
      {data.map((d, i) => (
        <div
          key={d.label}
          style={{ width: `${(d.value / total) * 100}%`, background: d.color, marginLeft: i > 0 ? 1 : 0 }}
        />
      ))}
    </div>
  )
}

export function TemporalChart({ hours }: { hours: { bucket: string; count: number }[] }) {
  const max = Math.max(...hours.map(h => h.count))
  const peak = hours.find(h => h.count === max)
  const peakLabel = peak ? new Date(peak.bucket).toLocaleString("id-ID", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" }) : ""
  return (
    <div>
      <div className="flex items-end gap-px h-14 mb-1">
        {hours.map((h, i) => {
          const pct = (h.count / max) * 100
          const color = h.count === max ? "#EF4444" : h.count > max * 0.5 ? "#F97316" : "#378ADD"
          return (
            <div
              key={i}
              title={`${new Date(h.bucket).toLocaleString("id-ID")} — ${h.count} komentar`}
              className="flex-1 rounded-sm rounded-b-none transition-opacity hover:opacity-70 cursor-default"
              style={{ height: `${Math.max(pct, 2)}%`, background: color, minWidth: 2 }}
            />
          )
        })}
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground/40 mb-1">
        <span>{hours[0] ? new Date(hours[0].bucket).toLocaleString("id-ID", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" }) : ""}</span>
        <span>{peakLabel ? `Puncak ${peakLabel}` : ""}</span>
        <span>{hours[hours.length - 1] ? new Date(hours[hours.length - 1].bucket).toLocaleString("id-ID", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" }) : ""}</span>
      </div>
    </div>
  )
}

export function ClusterList({ clusters }: { clusters: EvidenceData["topics"]["clusters"] }) {
  return (
    <div className="space-y-3">
      {clusters.map((c) => (
        <div key={c.cluster_label} className="rounded-lg border border-border/40 bg-card/50 p-3 flex items-start gap-3">
          <div className="min-w-[40px] text-right">
            <span className="text-lg font-medium tracking-tight text-foreground">{c.cluster_size}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium text-foreground leading-snug">{c.topic_label}</p>
            <p className="text-[11px] text-muted-foreground/60 mt-0.5 truncate">
              {c.lda_keywords.slice(0, 5).join(" · ")}
            </p>
            <div className="mt-1 flex items-center gap-1.5">
              <div className="h-1.5 rounded-full bg-muted/40 flex-1">
                <div
                  className="h-full rounded-full bg-blue-500/60"
                  style={{ width: `${c.topic_confidence_mean * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-muted-foreground/40">{(c.topic_confidence_mean * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
