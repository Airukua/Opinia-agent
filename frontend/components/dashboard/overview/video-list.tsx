"use client"

import { useState } from "react"
import {
  AlertTriangleIcon,
  BotIcon,
  ChevronRightIcon,
  EyeOffIcon,
  HashIcon,
  MessageSquareIcon,
  SparklesIcon,
  YoutubeIcon,
} from "lucide-react"
import type { VideoAnalysis } from "../analysis-types"
import { Button } from "@/components/ui/button"
import { InlineBar } from "./components/charts"
import { fmt, sentimentBg, sentimentColor } from "./components/overview-utils"

export function VideoListPage({ videos, onSelect }: {
  videos: VideoAnalysis[]
  onSelect: (v: VideoAnalysis) => void
}) {
  const [anonymizeAuthor, setAnonymizeAuthor] = useState(true)
  const [enableLlm, setEnableLlm] = useState(true)

  return (
    <div className="flex flex-col px-10 py-12 gap-0">

      {/* Hero */}
      <div className="pb-12 border-b border-border/40">
        <p className="text-[11px] font-medium tracking-[.08em] uppercase text-muted-foreground mb-5 flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-foreground/30" />
          AI agent untuk analisa komentar Youtube
        </p>
        <h1 className="text-4xl font-medium tracking-tight leading-[1.15] text-foreground max-w-xl mb-4">
          Pahami audiensmu dari setiap komentar
        </h1>
        <p className="text-[15px] text-muted-foreground leading-relaxed max-w-md mb-10">
          Dari ribuan komentar YouTube, temukan sentimen audiens, filter komentar bermasalah, dan tangkap kata kunci yang paling penting.
        </p>
      </div>

      {/* Feature columns */}
      <div className="grid grid-cols-3 border-b border-border/40">
        {[
          {
            num: "01",
            title: "Kumpulkan komentar",
            desc: "Masukkan URL video dan kami tarik komentar terbaru secara otomatis.",
          },
          {
            num: "02",
            title: "Analisa sentimen & toksisitas",
            desc: "Klasifikasi emosi, deteksi komentar toxic, dan highlight risiko moderasi.",
          },
          {
            num: "03",
            title: "Insight & topik utama",
            desc: "Ringkas topik dominan, kata kunci, serta peluang konten berikutnya.",
          },
        ].map((f, i) => (
          <div
            key={f.num}
            className={`py-7 ${i < 2 ? "border-r border-border/40 pr-7" : ""} ${i > 0 ? "pl-7" : ""}`}
          >
            <p className="text-[11px] font-medium text-muted-foreground/50 tracking-[.06em] mb-3.5">{f.num}</p>
            <p className="text-sm font-medium text-foreground mb-1.5">{f.title}</p>
            <p className="text-[13px] text-muted-foreground leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="py-10 border-b border-border/40">
        <div className="flex items-baseline gap-3 mb-2.5">
          <label className="text-[13px] font-medium text-foreground" htmlFor="youtube-urls">
            URL Video YouTube
          </label>
          <span className="text-xs text-muted-foreground/60">satu URL per baris — maks. 20 video</span>
        </div>
        <div className="rounded-md border border-input bg-muted/20 px-4 py-3">
          <div className="relative">
            <YoutubeIcon className="absolute left-0 top-1 h-4 w-4 text-muted-foreground/60" />
            <textarea
              id="youtube-urls"
              name="youtube-urls"
              rows={5}
              placeholder={`https://www.youtube.com/watch?v=xxxx\nhttps://youtu.be/yyyy`}
              className="w-full resize-none bg-transparent pl-6 pr-0 text-[13px] font-mono text-foreground placeholder:text-muted-foreground/40 focus-visible:outline-none transition leading-relaxed"
            />
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              aria-pressed={anonymizeAuthor}
              onClick={() => setAnonymizeAuthor((v) => !v)}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[12px] font-medium transition ${anonymizeAuthor ? "bg-foreground text-background border-foreground/80" : "bg-muted/30 text-muted-foreground border-border/60 hover:bg-muted/50"}`}
            >
              <EyeOffIcon className="h-3.5 w-3.5" />
              Anonimkan author
            </button>
            <button
              type="button"
              aria-pressed={enableLlm}
              onClick={() => setEnableLlm((v) => !v)}
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[12px] font-medium transition ${enableLlm ? "bg-foreground text-background border-foreground/80" : "bg-muted/30 text-muted-foreground border-border/60 hover:bg-muted/50"}`}
            >
              <BotIcon className="h-3.5 w-3.5" />
              Aktifkan LLM
            </button>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-muted-foreground/50">Estimasi ~1–3 menit per video</p>
          <Button size="sm" className="gap-2 rounded-md px-4 h-9 text-[13px] font-medium">
            <SparklesIcon className="h-3.5 w-3.5 opacity-70" />
            Analisa dengan AI
          </Button>
        </div>
      </div>

      <div className="border-t border-border/40 my-8" />
      {videos.length === 0 ? (
        <div className="rounded-xl border border-border/40 bg-muted/20 px-5 py-6">
          <p className="text-[13px] text-muted-foreground">
            Belum ada video yang dianalisa. Masukkan URL di atas lalu klik "Analisa dengan AI".
          </p>
        </div>
      ) : (
        <>
          {/* Header */}
          <div className="pb-6 border-b border-border/40">
            <h2 className="text-2xl font-medium tracking-tight text-foreground leading-tight mb-2">
              Semua video yang dianalisa
            </h2>
            <p className="text-[13px] text-muted-foreground">
              {videos.length} video · klik untuk lihat detail analisa
            </p>
          </div>

          {/* Video list */}
          <div className="border-t border-border/40">
            {videos.map((v) => {
              const s = v.evidence.sentiment.summary
              const score = s.sentiment_score.score
              return (
                <button
                  key={v.evidence.video.video_id}
                  onClick={() => onSelect(v)}
                  className="w-full text-left py-6 border-b border-border/30 hover:bg-muted/20 transition-colors group"
                >
                  <div className="flex items-start gap-6">
                    {/* Score pill */}
                    <div className={`shrink-0 rounded-lg border px-3 py-2 min-w-[72px] text-center ${sentimentBg(score)}`}>
                      <p className="text-[9px] tracking-[.05em] uppercase text-muted-foreground/60 mb-0.5">score</p>
                      <p className={`text-base font-medium tabular-nums ${sentimentColor(score)}`}>{score.toFixed(3)}</p>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] text-muted-foreground/50 mb-1">{v.evidence.video.video_id}</p>
                      <p className="text-[15px] font-medium text-foreground tracking-tight leading-snug mb-2 group-hover:text-foreground/80 transition-colors">
                        {v.evidence.video.video_title}
                      </p>
                      <div className="flex items-center gap-4 text-[12px] text-muted-foreground/60">
                        <span className="flex items-center gap-1">
                          <MessageSquareIcon className="h-3 w-3" />
                          {fmt(s.total_comments)} komentar
                        </span>
                        <span className="flex items-center gap-1">
                          <AlertTriangleIcon className="h-3 w-3" />
                          {fmt(v.evidence.comment_totals.toxic_comments)} toxic
                        </span>
                        <span className="flex items-center gap-1">
                          <HashIcon className="h-3 w-3" />
                          {v.evidence.topics.cluster_summary.num_clusters} topik
                        </span>
                      </div>
                    </div>

                    {/* Sentiment bar inline */}
                    <div className="shrink-0 w-32">
                      <p className="text-[10px] text-muted-foreground/40 mb-1.5 text-right">{(s.video_sentiment.negative * 100).toFixed(0)}% negatif</p>
                      <InlineBar data={[
                        { label: "neg", value: s.distribution.negative, color: "#EF4444" },
                        { label: "neu", value: s.distribution.neutral, color: "#CBD5E1" },
                        { label: "pos", value: s.distribution.positive, color: "#22C55E" },
                      ]} />
                    </div>

                    <ChevronRightIcon className="h-4 w-4 text-muted-foreground/30 shrink-0 mt-1 group-hover:text-muted-foreground/60 transition-colors" />
                  </div>
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
