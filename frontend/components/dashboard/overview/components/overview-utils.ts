import type { InsightsData } from "../../analysis-types"

export function fmt(n: number) { return n.toLocaleString("id-ID") }
export function fmtPct(n: number) { return `${(n * 100).toFixed(1)}%` }

export function sentimentColor(score: number) {
  if (score > 0.1) return "text-emerald-600 dark:text-emerald-400"
  if (score < -0.1) return "text-red-600 dark:text-red-400"
  return "text-slate-500"
}

export function sentimentBg(score: number) {
  if (score > 0.1) return "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-100 dark:border-emerald-900"
  if (score < -0.1) return "bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900"
  return "bg-slate-50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800"
}

export function normalizeLlmMarkdown(value: unknown, fallback: string) {
  if (typeof value === "string") {
    const normalized = value.replace(/\r\n?/g, "\n").trim()
    if (normalized) return normalized
  }
  return fallback.trim()
}

export function getInsightText(
  insights: InsightsData,
  key: keyof Omit<InsightsData, "available" | "mode" | "raw">,
) {
  const rawValue = insights.raw?.[key]
  return normalizeLlmMarkdown(rawValue, insights[key])
}

export function splitInsightItems(text: string) {
  const trimmed = text.trim()
  if (!trimmed) return []
  const lines = trimmed.split("\n").map((line) => line.trim()).filter(Boolean)
  const bulletLines = lines.filter((line) => /^(\d+\.|-|\*|•)\s+/.test(line))
  if (bulletLines.length > 0) {
    return bulletLines.map((line) => line.replace(/^(\d+\.|-|\*|•)\s+/, ""))
  }
  const commaParts = trimmed.split(",").map((part) => part.trim()).filter(Boolean)
  if (commaParts.length > 1) return commaParts
  return [trimmed]
}
