from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

LABEL_ALIASES = {
    "positive": "positive",
    "negatif": "negative",
    "negative": "negative",
    "neutral": "neutral",
    "netral": "neutral",
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
}


@dataclass
class SentimentAgentConfig:
    """Configuration for sentiment analytics agent."""

    text_column: str = "text"
    author_column: str = "author"
    published_at_column: str = "published_at"
    like_column: str = "like_count"
    comment_id_column: str = "comment_id"
    cluster_column: str = "topic_cluster"
    toxic_label_column: str = "toxic_label"
    toxic_score_column: str = "toxic_score"
    model_name: str = "models/indonesian-roberta-sentiment"
    use_fast_tokenizer: bool = True
    batch_size: int = 32
    max_length: int = 256
    sentiment_score_positive_threshold: float = 0.4
    sentiment_score_negative_threshold: float = -0.1
    sentiment_score_neutral_lower_bound: float = -0.1
    sentiment_score_neutral_upper_bound: float = 0.1
    top_k_highlights: int = 5
    temporal_resample_rule: str = "h"
    spike_std_threshold: float = 2.0
    min_text_length_for_highlight: int = 8


def _normalize_schema(df: pd.DataFrame, cfg: SentimentAgentConfig) -> pd.DataFrame:
    out = df.copy()
    required_columns = [
        cfg.text_column,
        cfg.author_column,
        cfg.published_at_column,
        cfg.like_column,
        cfg.comment_id_column,
    ]
    for col in required_columns:
        if col not in out.columns:
            out[col] = None

    out[cfg.text_column] = out[cfg.text_column].fillna("").astype(str)
    out[cfg.author_column] = out[cfg.author_column].fillna("unknown").astype(str)
    out[cfg.comment_id_column] = out[cfg.comment_id_column].fillna("").astype(str)
    out[cfg.like_column] = pd.to_numeric(out[cfg.like_column], errors="coerce").fillna(0).astype(int)
    out[cfg.published_at_column] = pd.to_datetime(out[cfg.published_at_column], errors="coerce", utc=True)
    out = out.reset_index(drop=True)
    out["_row_id"] = out.index.astype(int)
    return out


def _normalize_label(raw_label: str) -> str:
    normalized = (raw_label or "").strip().lower()
    return LABEL_ALIASES.get(normalized, normalized or "neutral")


def _label_from_scores(scores: Dict[str, float]) -> str:
    if not scores:
        return "neutral"
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return _normalize_label(ordered[0][0])


def _fallback_lexical_sentiment(text: str) -> Dict[str, float]:
    lowered = text.lower()
    positive_terms = [
        "bagus",
        "mantap",
        "keren",
        "jelas",
        "membantu",
        "terima kasih",
        "good",
        "great",
        "awesome",
    ]
    negative_terms = [
        "jelek",
        "buruk",
        "tidak jelas",
        "ga jelas",
        "bingung",
        "error",
        "susah",
        "bad",
        "worst",
    ]
    pos_hits = sum(1 for term in positive_terms if term in lowered)
    neg_hits = sum(1 for term in negative_terms if term in lowered)
    if pos_hits == neg_hits:
        return {"neutral": 1.0}
    if pos_hits > neg_hits:
        return {"positive": min(1.0, 0.6 + 0.1 * pos_hits), "neutral": 0.2, "negative": 0.0}
    return {"negative": min(1.0, 0.6 + 0.1 * neg_hits), "neutral": 0.2, "positive": 0.0}


def _predict_sentiment(df: pd.DataFrame, cfg: SentimentAgentConfig) -> List[Dict[str, Any]]:
    texts = df[cfg.text_column].tolist()
    outputs: List[Dict[str, Any]] = []

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(
            cfg.model_name,
            use_fast=cfg.use_fast_tokenizer,
        )
        model = AutoModelForSequenceClassification.from_pretrained(cfg.model_name)
        clf = pipeline(
            task="text-classification",
            model=model,
            tokenizer=tokenizer,
            truncation=True,
            max_length=cfg.max_length,
            top_k=None,
        )
        raw_predictions = clf(texts, batch_size=cfg.batch_size)
        for pred in raw_predictions:
            score_map: Dict[str, float] = {}
            for item in pred:
                label = _normalize_label(str(item.get("label", "")))
                score_map[label] = max(score_map.get(label, 0.0), float(item.get("score", 0.0)))
            final_label = _label_from_scores(score_map)
            outputs.append(
                {
                    "sentiment": final_label,
                    "confidence": float(score_map.get(final_label, 0.0)),
                    "score_map": {
                        "positive": float(score_map.get("positive", 0.0)),
                        "neutral": float(score_map.get("neutral", 0.0)),
                        "negative": float(score_map.get("negative", 0.0)),
                    },
                }
            )
        return outputs
    except Exception as err:  # pragma: no cover - runtime fallback
        logger.warning("Transformer sentiment model unavailable. Falling back to lexical mode: %s", err)

    for text in texts:
        score_map = _fallback_lexical_sentiment(text)
        label = _label_from_scores(score_map)
        outputs.append(
            {
                "sentiment": label,
                "confidence": float(score_map.get(label, 0.0)),
                "score_map": {
                    "positive": float(score_map.get("positive", 0.0)),
                    "neutral": float(score_map.get("neutral", 0.0)),
                    "negative": float(score_map.get("negative", 0.0)),
                },
            }
        )
    return outputs


def _distribution(df: pd.DataFrame) -> Dict[str, int]:
    counts = df["sentiment"].value_counts()
    return {
        "positive": int(counts.get("positive", 0)),
        "neutral": int(counts.get("neutral", 0)),
        "negative": int(counts.get("negative", 0)),
    }


def _video_sentiment_score(distribution: Dict[str, int], cfg: SentimentAgentConfig) -> Dict[str, Any]:
    total = distribution["positive"] + distribution["neutral"] + distribution["negative"]
    if total == 0:
        return {"score": 0.0, "label": "neutral", "formula": "(positive - negative) / total"}

    score = (distribution["positive"] - distribution["negative"]) / total
    if score > cfg.sentiment_score_positive_threshold:
        label = "sangat_positif"
    elif score > cfg.sentiment_score_neutral_upper_bound:
        label = "positif"
    elif score < cfg.sentiment_score_negative_threshold:
        label = "negatif"
    elif cfg.sentiment_score_neutral_lower_bound <= score <= cfg.sentiment_score_neutral_upper_bound:
        label = "netral"
    else:
        label = "positif"
    return {
        "score": round(float(score), 4),
        "label": label,
        "formula": "(positive - negative) / total",
    }


def _sentiment_per_cluster(df: pd.DataFrame, cfg: SentimentAgentConfig) -> List[Dict[str, Any]]:
    if cfg.cluster_column not in df.columns:
        return []

    result: List[Dict[str, Any]] = []
    grouped = df.groupby(cfg.cluster_column, dropna=False)
    for cluster_value, group in grouped:
        distribution = _distribution(group)
        score = _video_sentiment_score(distribution, cfg)
        result.append(
            {
                "cluster": str(cluster_value),
                "total_comments": int(len(group)),
                "distribution": distribution,
                "sentiment_score": score["score"],
                "sentiment_label": score["label"],
            }
        )
    return result


def _sentiment_per_time(df: pd.DataFrame, cfg: SentimentAgentConfig) -> Dict[str, Any]:
    valid = df.dropna(subset=[cfg.published_at_column]).copy()
    if valid.empty:
        return {"timeline": [], "spikes": []}

    valid = valid.set_index(cfg.published_at_column)
    grouped = valid.groupby([pd.Grouper(freq=cfg.temporal_resample_rule), "sentiment"]).size()
    timeline_df = grouped.unstack(fill_value=0).sort_index()

    for col in ["positive", "neutral", "negative"]:
        if col not in timeline_df.columns:
            timeline_df[col] = 0

    timeline_df["total"] = timeline_df["positive"] + timeline_df["neutral"] + timeline_df["negative"]
    timeline_df["sentiment_score"] = (
        (timeline_df["positive"] - timeline_df["negative"])
        / timeline_df["total"].replace(0, 1)
    )

    timeline: List[Dict[str, Any]] = []
    for ts, row in timeline_df.iterrows():
        timeline.append(
            {
                "bucket": ts.isoformat(),
                "positive": int(row["positive"]),
                "neutral": int(row["neutral"]),
                "negative": int(row["negative"]),
                "total": int(row["total"]),
                "sentiment_score": round(float(row["sentiment_score"]), 4),
            }
        )

    negative_counts = timeline_df["negative"]
    mean = float(negative_counts.mean())
    std = float(negative_counts.std(ddof=0))
    threshold = mean + (cfg.spike_std_threshold * std if std > 0 else 0.0)
    spikes = negative_counts[negative_counts > threshold]

    spike_records: List[Dict[str, Any]] = []
    for ts, value in spikes.items():
        spike_records.append(
            {
                "bucket": ts.isoformat(),
                "negative_count": int(value),
                "threshold": round(float(threshold), 4),
            }
        )
    return {"timeline": timeline, "spikes": spike_records}


def _top_highlights(df: pd.DataFrame, cfg: SentimentAgentConfig) -> Dict[str, List[Dict[str, Any]]]:
    highlights: Dict[str, List[Dict[str, Any]]] = {
        "positive": [],
        "neutral": [],
        "negative": [],
    }
    enriched = df.copy()
    enriched = enriched[enriched[cfg.text_column].str.len() >= cfg.min_text_length_for_highlight]
    if enriched.empty:
        return highlights

    for sentiment in ["positive", "neutral", "negative"]:
        subset = enriched[enriched["sentiment"] == sentiment].copy()
        if subset.empty:
            continue
        subset = subset.sort_values(
            ["confidence", cfg.like_column],
            ascending=[False, False],
        ).head(cfg.top_k_highlights)
        highlights[sentiment] = [
            {
                "comment_id": str(row[cfg.comment_id_column] or f"row_{int(row['_row_id'])}"),
                "author": row[cfg.author_column],
                "text": row[cfg.text_column],
                "confidence": round(float(row["confidence"]), 4),
                "like_count": int(row[cfg.like_column]),
            }
            for _, row in subset.iterrows()
        ]
    return highlights


def _toxic_summary(df: pd.DataFrame, cfg: SentimentAgentConfig) -> Dict[str, Any]:
    has_toxic_label = cfg.toxic_label_column in df.columns
    has_toxic_score = cfg.toxic_score_column in df.columns
    if not has_toxic_label and not has_toxic_score:
        return {"available": False}

    toxic_ratio = 0.0
    if has_toxic_label:
        toxic_series = df[cfg.toxic_label_column].fillna("").astype(str).str.lower()
        toxic_ratio = float((toxic_series == "toxic").mean())
    elif has_toxic_score:
        toxic_scores = pd.to_numeric(df[cfg.toxic_score_column], errors="coerce").fillna(0.0)
        toxic_ratio = float((toxic_scores >= 0.5).mean())

    negative_ratio = float((df["sentiment"] == "negative").mean()) if not df.empty else 0.0
    constructive_criticism_ratio = max(negative_ratio - toxic_ratio, 0.0)

    return {
        "available": True,
        "negative_ratio": round(negative_ratio, 4),
        "toxic_ratio": round(toxic_ratio, 4),
        "constructive_criticism_ratio": round(constructive_criticism_ratio, 4),
    }


def _comment_level_results(df: pd.DataFrame, cfg: SentimentAgentConfig) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        comment_id = row[cfg.comment_id_column] or f"row_{int(row['_row_id'])}"
        results.append(
            {
                "comment_id": str(comment_id),
                "author": row[cfg.author_column],
                "text": row[cfg.text_column],
                "sentiment": row["sentiment"],
                "confidence": round(float(row["confidence"]), 4),
                "scores": {
                    "positive": round(float(row["score_positive"]), 4),
                    "neutral": round(float(row["score_neutral"]), 4),
                    "negative": round(float(row["score_negative"]), 4),
                },
            }
        )
    return results


def run_sentiment_agent(
    comments: pd.DataFrame | List[Dict[str, Any]],
    config: Optional[SentimentAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs sentiment analytics pipeline for YouTube comments."""
    cfg = config or SentimentAgentConfig()
    df = comments if isinstance(comments, pd.DataFrame) else pd.DataFrame(comments)
    normalized = _normalize_schema(df, cfg)

    if normalized.empty:
        return {
            "total_comments": 0,
            "video_sentiment": {"positive": 0.0, "neutral": 0.0, "negative": 0.0},
            "distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "sentiment_score": {"score": 0.0, "label": "neutral", "formula": "(positive - negative) / total"},
            "sentiment_per_cluster": [],
            "sentiment_over_time": {"timeline": [], "spikes": []},
            "highlights": {"positive": [], "neutral": [], "negative": []},
            "toxicity_integration": {"available": False},
            "comment_level": [],
        }

    predictions = _predict_sentiment(normalized, cfg)
    normalized["sentiment"] = [item["sentiment"] for item in predictions]
    normalized["confidence"] = [item["confidence"] for item in predictions]
    normalized["score_positive"] = [item["score_map"]["positive"] for item in predictions]
    normalized["score_neutral"] = [item["score_map"]["neutral"] for item in predictions]
    normalized["score_negative"] = [item["score_map"]["negative"] for item in predictions]

    distribution = _distribution(normalized)
    total = max(len(normalized), 1)
    video_sentiment = {
        "positive": round(distribution["positive"] / total, 4),
        "neutral": round(distribution["neutral"] / total, 4),
        "negative": round(distribution["negative"] / total, 4),
    }

    return {
        "total_comments": int(len(normalized)),
        "video_sentiment": video_sentiment,
        "distribution": distribution,
        "sentiment_score": _video_sentiment_score(distribution, cfg),
        "sentiment_per_cluster": _sentiment_per_cluster(normalized, cfg),
        "sentiment_over_time": _sentiment_per_time(normalized, cfg),
        "highlights": _top_highlights(normalized, cfg),
        "toxicity_integration": _toxic_summary(normalized, cfg),
        "comment_level": _comment_level_results(normalized, cfg),
    }


def run_sentiment_agent_from_csv(
    csv_path: str,
    *,
    output_json_path: Optional[str] = None,
    config: Optional[SentimentAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs sentiment agent from CSV and optionally persists JSON output."""
    logger.info("Loading comments CSV for sentiment analysis: %s", csv_path)
    df = pd.read_csv(csv_path)
    result = run_sentiment_agent(df, config=config)

    if output_json_path:
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Sentiment-agent output saved: %s", output_json_path)

    return result
