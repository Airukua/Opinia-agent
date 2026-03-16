"use client"

import { useEffect, useState } from "react"
import type { VideoAnalysis } from "../analysis-types"
import { VideoDetailPage } from "./video-detail"
import { VideoListPage } from "./video-list"

export function AnalysisDashboard({ videos, filename }: { videos: VideoAnalysis[]; filename: string }) {
  const allVideos = videos
  const [selected, setSelected] = useState<VideoAnalysis | null>(null)

  useEffect(() => {
    setSelected(null)
  }, [allVideos])

  if (selected) {
    return <VideoDetailPage analysis={selected} filename={filename} onBack={() => setSelected(null)} />
  }
  if (allVideos.length === 0) {
    return (
      <div className="flex flex-col px-10 py-12">
        <p className="text-[13px] text-muted-foreground">Belum ada data untuk ditampilkan.</p>
      </div>
    )
  }
  return <VideoListPage videos={allVideos} onSelect={setSelected} />
}
