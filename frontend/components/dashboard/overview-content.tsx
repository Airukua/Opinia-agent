"use client"

import { useState } from "react"
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  YoutubeIcon,
  AlertTriangleIcon,
  HashIcon,
  MessageSquareIcon,
  SparklesIcon,
  EyeOffIcon,
  BotIcon,
  DownloadIcon,
  FileTextIcon,
} from "lucide-react"
import { Button } from "@/components/ui/button"

// ─── Types ───────────────────────────────────────────────────────────────────

export type VideoAnalysis = {
  evidence: EvidenceData
  insights: InsightsData
}

export type EvidenceData = {
  video: {
    video_id: string
    video_title: string
    video_description: string
  }
  comment_totals: {
    total_comments: number
    spam_comments: number
    toxic_comments: number
  }
  eda: {
    total_comments: number
    volume_temporal_analysis: {
      comments_per_hour: { bucket: string; count: number }[]
    }
    engagement_analysis: {
      like_count_distribution: {
        min: number; max: number; mean: number; median: number; std: number
      }
      engagement_per_comment: { mean_like_count: number; median_like_count: number }
      top_liked_comments: {
        author: string; text: string; published_at: string; like_count: number
      }[]
    }
    text_statistics: {
      comment_length_distribution: {
        characters: { min: number; max: number; mean: number }
        words: { min: number; max: number; mean: number }
      }
      basic_metrics: { avg_words_per_comment: number; avg_characters_per_comment: number }
      vocabulary: {
        unique_words: number
        vocabulary_size: number
        token_frequency_top: [string, number][]
        bigram_frequency_top: [string, number][]
        trigram_frequency_top: [string, number][]
      }
    }
  }
  spam: {
    summary: { total_comments: number; spam_comments: number; spam_ratio: number }
    top_examples: {
      comment_id: string; author: string; text: string
      spam_score: number; label: string; reason: string[]
      layer_scores: { pattern_score: number; semantic_score: number; behaviour_score: number }
    }[]
  }
  sentiment: {
    summary: {
      total_comments: number
      distribution: { positive: number; neutral: number; negative: number }
      video_sentiment: { positive: number; neutral: number; negative: number }
      sentiment_score: { score: number; label: string; formula: string }
    }
    highlights: {
      positive: SentimentComment[]
      neutral: SentimentComment[]
      negative: SentimentComment[]
    }
  }
  toxicity: {
    summary: {
      total_comments: number; toxic_comments: number
      suspicious_comments: number; safe_comments: number
      toxic_ratio: number; suspicious_ratio: number
    }
    categories: {
      toxic: number; insult: number; obscene: number
      threat: number; identity_hate: number; severe_toxic: number
    }
    top_examples: {
      comment_id: string; author: string; text: string
      toxicity_score: number; toxicity_label: string; flag: string
    }[]
  }
  topics: {
    cluster_summary: {
      num_clusters: number
      num_noise_points: number
      noise_ratio: number
      clusters: { label: number; count: number; sample_texts: string[] }[]
    }
    clusters: {
      cluster_label: number
      cluster_size: number
      lda_keywords: string[]
      top_comments: { text: string; like_count: number }[]
      topic_confidence_mean: number
      topic_label: string
      rationale: string
    }[]
  }
}

type SentimentComment = {
  comment_id: string; author: string; text: string
  confidence: number; like_count: number
}

export type InsightsData = {
  available: boolean
  mode: string
  emotional_triggers: string
  viral_formula: string
  audience_persona: string
  content_hooks: string
  opportunities: string
  risks: string
  summary: string
  raw: Record<string, unknown>
}

// ─── Sample Data ─────────────────────────────────────────────────────────────
// Replace with your real loader: fetch(`/api/analysis/${videoId}`)

const SAMPLE_ANALYSIS: VideoAnalysis = {
  evidence: {
    video: {
      video_id: "yKNPxkk1nfY",
      video_title: "IRAN DISERANG, DUNIA BERGEJOLAK, INDONESIA DIAM?",
      video_description: "Podcast Terus Terang Mahfud MD · PT TERUS TERANG MEDIA",
    },
    comment_totals: { total_comments: 3071, spam_comments: 0, toxic_comments: 11 },
    eda: {
      total_comments: 3071,
      volume_temporal_analysis: {
        comments_per_hour: [
          { bucket: "2026-03-03 12:00:00+00:00", count: 2 },
          { bucket: "2026-03-03 13:00:00+00:00", count: 40 },
          { bucket: "2026-03-03 14:00:00+00:00", count: 183 },
          { bucket: "2026-03-03 15:00:00+00:00", count: 253 },
          { bucket: "2026-03-03 16:00:00+00:00", count: 201 },
          { bucket: "2026-03-03 17:00:00+00:00", count: 169 },
          { bucket: "2026-03-03 18:00:00+00:00", count: 118 },
          { bucket: "2026-03-03 19:00:00+00:00", count: 79 },
          { bucket: "2026-03-03 20:00:00+00:00", count: 79 },
          { bucket: "2026-03-03 21:00:00+00:00", count: 97 },
          { bucket: "2026-03-03 22:00:00+00:00", count: 56 },
          { bucket: "2026-03-03 23:00:00+00:00", count: 70 },
          { bucket: "2026-03-04 00:00:00+00:00", count: 60 },
          { bucket: "2026-03-04 01:00:00+00:00", count: 73 },
          { bucket: "2026-03-04 02:00:00+00:00", count: 73 },
          { bucket: "2026-03-04 03:00:00+00:00", count: 60 },
          { bucket: "2026-03-04 04:00:00+00:00", count: 44 },
          { bucket: "2026-03-04 05:00:00+00:00", count: 54 },
          { bucket: "2026-03-04 06:00:00+00:00", count: 50 },
          { bucket: "2026-03-04 07:00:00+00:00", count: 47 },
          { bucket: "2026-03-04 08:00:00+00:00", count: 44 },
          { bucket: "2026-03-04 09:00:00+00:00", count: 31 },
          { bucket: "2026-03-04 10:00:00+00:00", count: 25 },
          { bucket: "2026-03-04 11:00:00+00:00", count: 22 },
          { bucket: "2026-03-04 12:00:00+00:00", count: 35 },
          { bucket: "2026-03-04 13:00:00+00:00", count: 30 },
          { bucket: "2026-03-04 14:00:00+00:00", count: 22 },
          { bucket: "2026-03-04 15:00:00+00:00", count: 27 },
          { bucket: "2026-03-04 16:00:00+00:00", count: 24 },
          { bucket: "2026-03-04 17:00:00+00:00", count: 21 },
          { bucket: "2026-03-04 18:00:00+00:00", count: 23 },
          { bucket: "2026-03-04 19:00:00+00:00", count: 17 },
          { bucket: "2026-03-04 20:00:00+00:00", count: 13 },
          { bucket: "2026-03-04 21:00:00+00:00", count: 21 },
          { bucket: "2026-03-04 22:00:00+00:00", count: 18 },
          { bucket: "2026-03-04 23:00:00+00:00", count: 12 },
          { bucket: "2026-03-05 00:00:00+00:00", count: 6 },
          { bucket: "2026-03-05 01:00:00+00:00", count: 13 },
          { bucket: "2026-03-05 02:00:00+00:00", count: 9 },
          { bucket: "2026-03-05 03:00:00+00:00", count: 12 },
          { bucket: "2026-03-05 04:00:00+00:00", count: 10 },
          { bucket: "2026-03-05 05:00:00+00:00", count: 12 },
          { bucket: "2026-03-05 06:00:00+00:00", count: 9 },
          { bucket: "2026-03-05 07:00:00+00:00", count: 19 },
          { bucket: "2026-03-05 08:00:00+00:00", count: 13 },
          { bucket: "2026-03-05 09:00:00+00:00", count: 11 },
        ],
      },
      engagement_analysis: {
        like_count_distribution: { min: 0, max: 750, mean: 2.02, median: 0, std: 21.26 },
        engagement_per_comment: { mean_like_count: 2.02, median_like_count: 0 },
        top_liked_comments: [
          { author: "user_2586", text: "Sepakat jika indonesia keluar dari BOP", published_at: "2026-03-03T14:03:05+00:00", like_count: 750 },
          { author: "user_1296", text: "Prabowo ngurus koruptor gabecus sok2an ngurus dunia negara kita kacau miskin", published_at: "2026-03-03T15:22:16+00:00", like_count: 598 },
          { author: "user_1333", text: "Pak Mahfud, tolong teruskan aspirasi rakyat Indonesia untuk mendorong Presiden Prabowo keluar dari BOP", published_at: "2026-03-03T14:19:00+00:00", like_count: 337 },
        ],
      },
      text_statistics: {
        comment_length_distribution: {
          characters: { min: 1, max: 4346, mean: 128.33 },
          words: { min: 0, max: 656, mean: 19.54 },
        },
        basic_metrics: { avg_words_per_comment: 19.54, avg_characters_per_comment: 128.33 },
        vocabulary: {
          unique_words: 9173,
          vocabulary_size: 9173,
          token_frequency_top: [
            ["iran", 1101], ["yg", 958], ["indonesia", 691], ["negara", 552],
            ["pak", 491], ["israel", 472], ["prabowo", 470], ["bop", 438],
            ["amerika", 397], ["presiden", 344],
          ],
          bigram_frequency_top: [
            ["pak mahfud", 144], ["keluar bop", 127], ["pak prabowo", 92],
            ["amerika israel", 86], ["timur tengah", 85], ["iran menang", 64],
            ["as israel", 57], ["indonesia keluar", 51], ["presiden prabowo", 50], ["pak faisal", 47],
          ],
          trigram_frequency_top: [
            ["indonesia keluar bop", 35], ["keluar dr bop", 23], ["pak mahfud md", 22],
            ["prabowo keluar bop", 13], ["negara timur tengah", 12], ["board of peace", 11],
            ["bilang iran menang", 10], ["kilang minyak arab", 10], ["politik bebas aktif", 8], ["pangkalan militer amerika", 8],
          ],
        },
      },
    },
    spam: {
      summary: { total_comments: 3071, spam_comments: 0, spam_ratio: 0 },
      top_examples: [],
    },
    sentiment: {
      summary: {
        total_comments: 3071,
        distribution: { positive: 584, neutral: 290, negative: 2197 },
        video_sentiment: { positive: 0.1902, neutral: 0.0944, negative: 0.7154 },
        sentiment_score: { score: -0.5252, label: "negatif", formula: "(positive - negative) / total" },
      },
      highlights: {
        positive: [
          { comment_id: "row_2820", author: "user_835", text: "Abang Faisal... aku suka... penjelasan nya enak di dengar dan di pahami....sehat2 selalu abang Faisal", confidence: 0.9989, like_count: 0 },
          { comment_id: "row_2797", author: "user_891", text: "Cakep pernyataan dan pendapat paling logis dr pak Mahfud dan pak Faisal salut dgn belia bertiga.", confidence: 0.9985, like_count: 158 },
        ],
        neutral: [
          { comment_id: "row_1956", author: "user_2574", text: "Pak Mahfud perlu menginisiasi ajak para tokoh nasional memberikan advis resmi ke presiden", confidence: 0.9986, like_count: 0 },
        ],
        negative: [
          { comment_id: "row_2759", author: "user_1296", text: "Prabowo ngurus koruptor gabecus sok2an ngurus dunia negara kita kacau miskin", confidence: 0.9995, like_count: 598 },
          { comment_id: "row_2876", author: "user_1933", text: "Prabowo bodoh amerika negara licik kok didekatii disembah... Mau jadi penengah perang..", confidence: 0.9995, like_count: 0 },
        ],
      },
    },
    toxicity: {
      summary: {
        total_comments: 3071, toxic_comments: 11, suspicious_comments: 146,
        safe_comments: 2914, toxic_ratio: 0.0036, suspicious_ratio: 0.0475,
      },
      categories: { toxic: 157, insult: 1, obscene: 4, threat: 0, identity_hate: 2, severe_toxic: 0 },
      top_examples: [
        { comment_id: "row_2762", author: "user_1761", text: "Weleh si wowo dan wakilnya itu sungguh sama-sama idiot. Hanya karena punya uang saja bisa beli suara 58%", toxicity_score: 0.9594, toxicity_label: "toxic", flag: "toxic" },
        { comment_id: "row_1369", author: "user_1320", text: "Ya Allah sadarkan prabowo ya Allah, capek bgt siapapun yg ngomong nggak didengerin.", toxicity_score: 0.8872, toxicity_label: "toxic", flag: "toxic" },
      ],
    },
    topics: {
      cluster_summary: {
        num_clusters: 54,
        num_noise_points: 1716,
        noise_ratio: 0.5588,
        clusters: [
          { label: 5, count: 88, sample_texts: ["Gelagapan apanya, orang di Washington DC nggak ada apa2"] },
          { label: 1, count: 63, sample_texts: ["Syarat di Iran jadi president S2"] },
          { label: 22, count: 62, sample_texts: ["Indonesia harus keluar dari BOP"] },
        ],
      },
      clusters: [
        { cluster_label: 5, cluster_size: 88, lda_keywords: ["iran", "arab", "mossad", "teheran", "pangkalan"], top_comments: [{ text: "Iran sudah menyatakan bukan mereka yg menyerang bandara dubai", like_count: 0 }], topic_confidence_mean: 0.9, topic_label: "Ketegangan Geopolitik Iran-Arab", rationale: "Diskusi seputar dinamika militer dan geopolitik Iran vs AS-Israel" },
        { cluster_label: 1, cluster_size: 63, lda_keywords: ["s2", "presiden", "sma", "ijazah", "syarat"], top_comments: [{ text: "Syarat di Iran jadi president S2, KLO di Konoha ijazah GK jelas pun jd", like_count: 0 }], topic_confidence_mean: 0.666, topic_label: "Perbandingan Syarat Presiden Iran-Indonesia", rationale: "Membandingkan kualifikasi presiden Iran vs Indonesia" },
        { cluster_label: 22, cluster_size: 62, lda_keywords: ["keluar", "bop", "indonesia", "desak", "presiden"], top_comments: [{ text: "Indonesia harus keluar dari BOP", like_count: 0 }], topic_confidence_mean: 0.9, topic_label: "Seruan Keluar BOP", rationale: "Desakan publik agar Indonesia keluar dari Board of Peace" },
        { cluster_label: 2, cluster_size: 19, lda_keywords: ["amerika", "percaya", "wowo", "boneka", "antek"], top_comments: [{ text: "Wowo boneka Amerika", like_count: 0 }], topic_confidence_mean: 0.885, topic_label: "Kritik Pengaruh dan Peran Amerika", rationale: "Kritik terhadap dominasi Amerika dan Prabowo sebagai boneka" },
        { cluster_label: 4, cluster_size: 12, lda_keywords: ["timur", "tengah", "faisal", "analisis", "sangat"], top_comments: [{ text: "Pak Faisal sangat fasih soal Iran dan Timur Tengah", like_count: 0 }], topic_confidence_mean: 0.958, topic_label: "Faisal Assegaf: Analisis Kawasan Timur Tengah", rationale: "Apresiasi terhadap analisis Faisal Assegaf" },
      ],
    },
  },
  insights: {
    available: true,
    mode: "fallback_viral",
    emotional_triggers: "Kata yang paling sering muncul: iran, yg, indonesia, negara, pak, israel, prabowo, bop. Komentar paling disukai: 'Sepakat jika indonesia keluar dari BOP' (750 likes).",
    viral_formula: "Frasa berulang: pak mahfud, keluar bop, pak prabowo, amerika israel, timur tengah.",
    audience_persona: "Distribusi sentimen: 19.0% positif, 71.5% negatif, 9.4% netral. Total komentar: 3071.",
    content_hooks: "Bigram dominan: pak mahfud, keluar bop, pak prabowo, amerika israel, timur tengah.",
    opportunities: "Topik yang bisa dikembangkan: Ijazah palsu Presiden, Perbandingan Syarat Presiden Iran-Indonesia, Kritik Pengaruh dan Peran Amerika, Faisal Assegaf: Analisis Kawasan Timur Tengah.",
    risks: "Toxic comments: 11 dari 3071 total komentar.",
    summary: "Video mendapat 3071 komentar dengan sentimen dominan negatif (71.5%). Topik utama: BOP, Geopolitik Iran, Kritik Prabowo.",
    raw: {},
  },
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function fmt(n: number) { return n.toLocaleString("id-ID") }
function fmtPct(n: number) { return `${(n * 100).toFixed(1)}%` }
function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
function sentimentColor(score: number) {
  if (score > 0.1) return "text-emerald-600 dark:text-emerald-400"
  if (score < -0.1) return "text-red-600 dark:text-red-400"
  return "text-slate-500"
}
function sentimentBg(score: number) {
  if (score > 0.1) return "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-100 dark:border-emerald-900"
  if (score < -0.1) return "bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900"
  return "bg-slate-50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800"
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({ label, value, sub, accent }: {
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

function InlineBar({ data }: {
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

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-medium uppercase tracking-[.07em] text-muted-foreground/50 mb-4 pb-3 border-b border-border/30">
      {children}
    </p>
  )
}

// ─── Temporal Chart ───────────────────────────────────────────────────────────

function TemporalChart({ hours }: { hours: { bucket: string; count: number }[] }) {
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
        <span>{new Date(hours[0].bucket).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}</span>
        <span>{new Date(hours[Math.floor(hours.length / 2)].bucket).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}</span>
        <span>{new Date(hours[hours.length - 1].bucket).toLocaleDateString("id-ID", { day: "numeric", month: "short" })}</span>
      </div>
      <p className="text-xs text-muted-foreground/60">
        Peak <span className="font-medium text-foreground">{fmt(max)} komentar</span> — {peakLabel}
      </p>
    </div>
  )
}

// ─── Cluster List ─────────────────────────────────────────────────────────────

function ClusterList({ clusters }: { clusters: EvidenceData["topics"]["clusters"] }) {
  const sorted = [...clusters].sort((a, b) => b.cluster_size - a.cluster_size)
  return (
    <div className="flex flex-col divide-y divide-border/30">
      {sorted.map((c) => (
        <div key={c.cluster_label} className="py-3 flex items-start gap-3">
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

// ─── Video Detail Page ────────────────────────────────────────────────────────

function VideoDetailPage({
  analysis,
  onBack,
}: {
  analysis: VideoAnalysis
  onBack: () => void
}) {
  const { evidence: ev, insights } = analysis
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
              {insights.opportunities.split(", ").filter(Boolean).map((opp, i) => (
                <div key={i} className="flex items-start gap-2.5 py-2 border-b border-border/30 last:border-0">
                  <span className="text-[11px] text-muted-foreground/40 mt-0.5">{i + 1}</span>
                  <span className="text-[13px] text-foreground leading-snug">{opp.replace("Topik yang bisa dikembangkan: ", "")}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

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
        <p className="text-[15px] text-muted-foreground leading-relaxed max-w-2xl">{insights.summary}</p>
      </div>

      {/* Downloads */}
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Button
          size="sm"
          variant="outline"
          className="gap-2 h-9 text-[13px] font-medium"
          onClick={() => downloadJson(`laporan_${ev.video.video_id}.json`, analysis)}
        >
          <FileTextIcon className="h-3.5 w-3.5 opacity-70" />
          Download full laporan
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-2 h-9 text-[13px] font-medium"
          onClick={() => downloadJson(`raw_komen_${ev.video.video_id}.json`, ev)}
        >
          <DownloadIcon className="h-3.5 w-3.5 opacity-70" />
          Download raw komen
        </Button>
      </div>

    </div>
  )
}

// ─── Multi-Video List ─────────────────────────────────────────────────────────

function VideoListPage({ videos, onSelect }: {
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

      {/* Header */}
      <div className="pb-6 border-b border-border/40 my-6">
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
    </div>
  )
}

// ─── Root Component ───────────────────────────────────────────────────────────

export function AnalysisDashboard({ videos }: { videos?: VideoAnalysis[] }) {
  const allVideos = videos ?? [SAMPLE_ANALYSIS]
  const [selected, setSelected] = useState<VideoAnalysis | null>(null)

  if (selected) {
    return <VideoDetailPage analysis={selected} onBack={() => setSelected(null)} />
  }
  return <VideoListPage videos={allVideos} onSelect={setSelected} />
}

export function OverviewContent() {
  return <AnalysisDashboard />
}
