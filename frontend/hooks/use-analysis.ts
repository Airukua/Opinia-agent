"use client"

import { useEffect, useMemo, useState } from "react"
import type { VideoAnalysis } from "@/components/dashboard/analysis-types"

export type AnalysisLoadState = {
  isLoading: boolean
  error: string | null
  videos: VideoAnalysis[]
}

function normalizeToVideos(data: unknown): VideoAnalysis[] {
  if (!data || typeof data !== "object") return []
  if (Array.isArray(data)) return data as VideoAnalysis[]
  const record = data as Record<string, unknown>
  if (Array.isArray(record.videos)) return record.videos as VideoAnalysis[]
  if (record.evidence) {
    const insights = (record.insights ?? record.llm_insights) as VideoAnalysis["insights"] | undefined
    if (insights) {
      return [{ ...(record as VideoAnalysis), insights }]
    }
    return [{
      ...(record as VideoAnalysis),
      insights: {
        available: false,
        mode: "none",
        emotional_triggers: "",
        viral_formula: "",
        audience_persona: "",
        content_hooks: "",
        opportunities: "",
        risks: "",
        summary: "",
        raw: {},
      },
    }]
  }
  return []
}

export function useAnalysisData(filename: string): AnalysisLoadState {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<VideoAnalysis[]>([])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setIsLoading(true)
      setError(null)

      try {
        const res = await fetch(`/results/${encodeURIComponent(filename)}`)
        if (!res.ok) throw new Error(`Gagal memuat hasil (${res.status})`)
        const json = await res.json()
        const normalized = normalizeToVideos(json)
        if (!cancelled) {
          setData(normalized)
          if (normalized.length === 0) {
            setError("Format data tidak dikenali")
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Gagal memuat hasil")
          setData([])
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [filename])

  return useMemo(() => ({ isLoading, error, videos: data }), [isLoading, error, data])
}
