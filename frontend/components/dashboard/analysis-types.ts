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
