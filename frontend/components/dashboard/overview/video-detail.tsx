"use client"

import {
  ArrowLeftIcon,
  DownloadIcon,
  FileTextIcon,
  YoutubeIcon,
} from "lucide-react"
import type { VideoAnalysis } from "../analysis-types"
import { Button } from "@/components/ui/button"
import { ClusterList, TemporalChart } from "./components/charts"
import { InsightCard, LlmMarkdown } from "./components/insights"
import { SectionTitle, StatCard } from "./components/sections"
import {
  fmt,
  fmtPct,
  getInsightText,
  sentimentBg,
  sentimentColor,
  splitInsightItems,
} from "./components/overview-utils"

export function VideoDetailPage({
  analysis,
  filename,
  onBack,
}: {
  analysis: VideoAnalysis
  filename: string
  onBack: () => void
}) {
  const { evidence: ev, insights } = analysis
  const emotionalTriggers = getInsightText(insights, "emotional_triggers")
  const viralFormula = getInsightText(insights, "viral_formula")
  const audiencePersona = getInsightText(insights, "audience_persona")
  const contentHooks = getInsightText(insights, "content_hooks")
  const opportunities = getInsightText(insights, "opportunities")
  const risks = getInsightText(insights, "risks")
  const summary = getInsightText(insights, "summary")
  const sent = ev.sentiment.summary
  const tox = ev.toxicity.summary
  const vocab = ev.eda.text_statistics.vocabulary
  const topLiked = ev.eda.engagement_analysis.top_liked_comments

  return (
    <div className="flex flex-col gap-0 px-10 py-12">

      {/* Back */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-[13px] text-muted-foreground hover:text-foreground transition-colors mb-8 w-fit"
      >
        <ArrowLeftIcon className="h-3.5 w-3.5" />
        Semua video
      </button>

      {/* Header */}
      <div className="pb-10 border-b border-border/40 mb-10">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-[11px] font-medium tracking-[.07em] uppercase text-muted-foreground/50 mb-3 flex items-center gap-2">
              <YoutubeIcon className="h-3 w-3 text-red-500" />
              {ev.video.video_id}
            </p>
            <h1 className="text-3xl font-medium tracking-tight text-foreground leading-tight max-w-2xl mb-3">
              {ev.video.video_title}
            </h1>
            <p className="text-sm text-muted-foreground/60">{ev.video.video_description}</p>
            <div className="mt-4 mb-4 w-full max-w-2xl overflow-hidden rounded-lg border border-border/40 bg-black/5">
              <div className="aspect-video w-full">
                <iframe
                  className="h-full w-full"
                  src={`https://www.youtube.com/embed/${ev.video.video_id}`}
                  title={ev.video.video_title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              </div>
            </div>
          </div>
          <div className={`shrink-0 rounded-xl border px-4 py-3 text-center ${sentimentBg(sent.sentiment_score.score)}`}>
            <p className="text-[10px] tracking-[.06em] uppercase text-muted-foreground/60 mb-0.5">Sentiment score</p>
            <p className={`text-2xl font-medium tracking-tight ${sentimentColor(sent.sentiment_score.score)}`}>
              {sent.sentiment_score.score.toFixed(3)}
            </p>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-5 gap-3 mb-10">
        <StatCard label="Total komentar" value={fmt(sent.total_comments)} />
        <StatCard label="Negatif" value={fmtPct(sent.video_sentiment.negative)} accent="text-red-600 dark:text-red-400" sub={fmt(sent.distribution.negative) + " komentar"} />
        <StatCard label="Positif" value={fmtPct(sent.video_sentiment.positive)} accent="text-emerald-600 dark:text-emerald-400" sub={fmt(sent.distribution.positive) + " komentar"} />
        <StatCard label="Toxic" value={fmt(tox.toxic_comments)} sub={`${fmtPct(tox.toxic_ratio)} dari total`} />
        <StatCard label="Unique words" value={fmt(ev.eda.text_statistics.vocabulary.unique_words)} sub="vocab size" />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-2 gap-8 mb-10">

        {/* Temporal */}
        <div className="border-t border-border/40 pt-6">
          <SectionTitle>Volume komentar per jam</SectionTitle>
          <TemporalChart hours={ev.eda.volume_temporal_analysis.comments_per_hour} />
        </div>

        {/* Sentiment bars */}
        <div className="border-t border-border/40 pt-6">
          <SectionTitle>Distribusi sentimen</SectionTitle>
          <div className="space-y-3">
            {[
              { label: "Negatif", val: sent.distribution.negative, total: sent.total_comments, color: "#EF4444" },
              { label: "Positif", val: sent.distribution.positive, total: sent.total_comments, color: "#22C55E" },
              { label: "Netral", val: sent.distribution.neutral, total: sent.total_comments, color: "#94A3B8" },
            ].map(s => (
              <div key={s.label}>
                <div className="flex justify-between text-[13px] mb-1.5">
                  <span className="text-muted-foreground">{s.label}</span>
                  <span className="font-medium tabular-nums text-foreground">{fmt(s.val)}</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted/30 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${(s.val / s.total) * 100}%`, background: s.color }} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6">
            <p className="text-[11px] uppercase tracking-[.07em] text-muted-foreground/50 mb-3">Top komentar (likes)</p>
            {topLiked.map((c, i) => (
              <div key={i} className="py-2.5 border-b border-border/30 last:border-0 flex gap-3">
                <span className="text-lg font-medium text-foreground min-w-[36px] tabular-nums">{fmt(c.like_count)}</span>
                <span className="text-[13px] text-muted-foreground leading-snug">{c.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Keywords */}
      <div className="border-t border-border/40 pt-6 mb-10">
        <SectionTitle>Kata kunci dominan</SectionTitle>
        <div className="grid grid-cols-3 gap-6">
          {/* Unigram */}
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3">Unigram — top 10</p>
            <div className="space-y-2">
              {vocab.token_frequency_top.map(([word, count], i) => (
                <div key={word} className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground/40 min-w-[14px] tabular-nums">{i + 1}</span>
                  <span className="text-[13px] text-foreground flex-1">{word}</span>
                  <span className="text-[13px] text-muted-foreground tabular-nums">{fmt(count)}</span>
                </div>
              ))}
            </div>
          </div>
          {/* Bigram */}
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3">Bigram — top 10</p>
            <div className="space-y-2">
              {vocab.bigram_frequency_top.map(([phrase, count], i) => (
                <div key={phrase} className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground/40 min-w-[14px] tabular-nums">{i + 1}</span>
                  <span className="text-[13px] text-foreground flex-1">{phrase}</span>
                  <span className="text-[13px] text-muted-foreground tabular-nums">{fmt(count)}</span>
                </div>
              ))}
            </div>
          </div>
          {/* Trigram */}
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3">Trigram — top 10</p>
            <div className="space-y-2">
              {vocab.trigram_frequency_top.map(([phrase, count], i) => (
                <div key={phrase} className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground/40 min-w-[14px] tabular-nums">{i + 1}</span>
                  <span className="text-[13px] text-foreground flex-1">{phrase}</span>
                  <span className="text-[13px] text-muted-foreground tabular-nums">{fmt(count)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Topics */}
      <div className="border-t border-border/40 pt-6 mb-10">
        <div className="flex items-baseline justify-between mb-4">
          <SectionTitle>Topik terdeteksi (LDA cluster)</SectionTitle>
        </div>
        <div className="flex gap-3 text-[12px] text-muted-foreground/60 mb-4">
          <span>{ev.topics.cluster_summary.num_clusters} cluster</span>
          <span>·</span>
          <span>{fmt(ev.topics.cluster_summary.num_noise_points)} noise points ({(ev.topics.cluster_summary.noise_ratio * 100).toFixed(1)}%)</span>
        </div>
        <div className="grid grid-cols-2 gap-6">
          <ClusterList clusters={ev.topics.clusters} />
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3 uppercase tracking-[.07em]">Topik yang diusulkan AI</p>
            <div className="space-y-2">
              {splitInsightItems(opportunities).map((opp, i) => (
                <div key={i} className="flex items-start gap-2.5 py-2 border-b border-border/30 last:border-0">
                  <span className="text-[11px] text-muted-foreground/40 mt-0.5">{i + 1}</span>
                  <span className="text-[13px] text-foreground leading-snug">{opp.replace("Topik yang bisa dikembangkan: ", "")}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* LLM Insights */}
      {insights.available && (
        <div className="border-t border-border/40 pt-6 mb-10">
          <div className="flex items-baseline justify-between mb-4">
            <SectionTitle>LLM insights</SectionTitle>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <InsightCard title="Emotional triggers" body={emotionalTriggers} />
            <InsightCard title="Viral formula" body={viralFormula} />
            <InsightCard title="Audience persona" body={audiencePersona} />
            <InsightCard title="Content hooks" body={contentHooks} />
            <InsightCard title="Opportunities" body={opportunities} />
            <InsightCard title="Risks" body={risks} />
          </div>
        </div>
      )}

      {/* Toxicity */}
      <div className="border-t border-border/40 pt-6 mb-10">
        <SectionTitle>Toksisitas &amp; moderasi</SectionTitle>
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatCard label="Toxic" value={fmt(tox.toxic_comments)} sub={fmtPct(tox.toxic_ratio)} accent="text-red-600 dark:text-red-400" />
          <StatCard label="Suspicious" value={fmt(tox.suspicious_comments)} sub={fmtPct(tox.suspicious_ratio)} accent="text-orange-600 dark:text-orange-400" />
          <StatCard label="Safe" value={fmt(tox.safe_comments)} sub="komentar aman" accent="text-emerald-600 dark:text-emerald-400" />
          <StatCard label="Spam" value={fmt(ev.spam.summary.spam_comments)} sub={`ratio ${(ev.spam.summary.spam_ratio * 100).toFixed(1)}%`} />
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3">Kategori toksik</p>
            {Object.entries(ev.toxicity.categories).map(([cat, val]) => (
              <div key={cat} className="flex justify-between text-[13px] py-1.5 border-b border-border/20 last:border-0">
                <span className="capitalize text-muted-foreground">{cat.replace("_", " ")}</span>
                <span className="font-medium tabular-nums text-foreground">{fmt(val)}</span>
              </div>
            ))}
          </div>
          <div>
            <p className="text-[11px] text-muted-foreground/50 mb-3">Contoh komentar toxic</p>
            {ev.toxicity.top_examples.map((t) => (
              <div key={t.comment_id} className="py-2.5 border-b border-border/30 last:border-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-medium text-red-600 dark:text-red-400 tabular-nums">{(t.toxicity_score * 100).toFixed(0)}%</span>
                  <span className="text-[10px] text-muted-foreground/40">{t.toxicity_label}</span>
                </div>
                <p className="text-[13px] text-muted-foreground leading-snug line-clamp-2">{t.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* LLM Summary */}
      <div className="border-t border-border/40 pt-6">
        <SectionTitle>Kesimpulan</SectionTitle>
        <div className="max-w-2xl">
          <LlmMarkdown text={summary} />
        </div>
      </div>

      {/* Downloads */}
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Button
          size="sm"
          variant="outline"
          className="gap-2 h-9 text-[13px] font-medium"
          onClick={() => {
            window.open(`/results/${encodeURIComponent(filename)}/report.pdf`, "_blank", "noopener,noreferrer")
          }}
        >
          <FileTextIcon className="h-3.5 w-3.5 opacity-70" />
          Download full laporan
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-2 h-9 text-[13px] font-medium"
          onClick={() => {
            window.open(`/results/${encodeURIComponent(filename)}/comments.csv`, "_blank", "noopener,noreferrer")
          }}
        >
          <DownloadIcon className="h-3.5 w-3.5 opacity-70" />
          Download raw komen
        </Button>
      </div>

    </div>
  )
}
