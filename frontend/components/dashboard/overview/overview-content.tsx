"use client"

import { AnalysisDashboard } from "./analysis-dashboard"
import { useAnalysisData } from "@/hooks/use-analysis"

export function OverviewContent({ filename = "hasil.json" }: { filename?: string }) {
  const { isLoading, error, videos } = useAnalysisData(filename)

  if (isLoading) {
    return (
      <div className="flex flex-col px-10 py-12">
        <p className="text-[13px] text-muted-foreground">Memuat hasil dari {`/results/${filename}`}...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col px-10 py-12">
        <p className="text-[13px] text-muted-foreground">Gagal memuat data: {error}.</p>
      </div>
    )
  }

  return <AnalysisDashboard videos={videos} filename={filename} />
}
