"""Toxic comment detection and moderation analytics agent."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{2,}", re.UNICODE)

CATEGORY_ALIASES = {
    "toxic": "toxic",
    "toxicity": "toxic",
    "insult": "insult",
    "obscene": "obscene",
    "threat": "threat",
    "identity_hate": "identity_hate",
    "identity hate": "identity_hate",
    "severe_toxic": "severe_toxic",
    "severe toxic": "severe_toxic",
    "label_0": "non_toxic",
    "label_1": "toxic",
    "non-toxic": "non_toxic",
    "nontoxic": "non_toxic",
    "non_toxic": "non_toxic",
}

TOXIC_CATEGORIES = ["toxic", "insult", "obscene", "threat", "identity_hate", "severe_toxic"]


@dataclass
class ToxicAgentConfig:
    """Configuration for toxic comment detection pipeline."""

    text_column: str = "text"
    comment_id_column: str = "comment_id"
    author_column: str = "author"
    published_at_column: str = "published_at"
    like_column: str = "like_count"
    model_name: str = "models/toxic-bert"
    use_fast_tokenizer: bool = True
    batch_size: int = 32
    max_length: int = 256
    toxic_threshold: float = 0.8
    suspicious_threshold: float = 0.5
    category_threshold: float = 0.5
    top_k_highlights: int = 5
    temporal_resample_rule: str = "min"
    spike_std_threshold: float = 2.0


def _normalize_schema(df: pd.DataFrame, cfg: ToxicAgentConfig) -> pd.DataFrame:
    out = df.copy()
    for col in [
        cfg.text_column,
        cfg.comment_id_column,
        cfg.author_column,
        cfg.published_at_column,
        cfg.like_column,
    ]:
        if col not in out.columns:
            out[col] = None

    out[cfg.text_column] = out[cfg.text_column].fillna("").astype(str)
    out[cfg.comment_id_column] = out[cfg.comment_id_column].fillna("").astype(str)
    out[cfg.author_column] = out[cfg.author_column].fillna("unknown").astype(str)
    out[cfg.like_column] = pd.to_numeric(out[cfg.like_column], errors="coerce").fillna(0).astype(int)
    out[cfg.published_at_column] = pd.to_datetime(out[cfg.published_at_column], errors="coerce", utc=True)
    out = out.reset_index(drop=True)
    out["_row_id"] = out.index.astype(int)
    return out


def _preprocess_text(text: str) -> str:
    lowered = (text or "").lower()
    no_url = URL_PATTERN.sub(" ", lowered)
    compressed = REPEATED_CHAR_PATTERN.sub(r"\1", no_url)
    cleaned = WHITESPACE_PATTERN.sub(" ", compressed).strip()
    return cleaned


def _normalize_label(raw_label: str) -> str:
    normalized = (raw_label or "").strip().lower()
    return CATEGORY_ALIASES.get(normalized, normalized or "toxic")


def _fallback_lexical_scores(text: str) -> Dict[str, float]:
    lowered = text.lower()
    lexicons = {
        "insult": ["bodoh", "tolol", "goblok", "stupid", "idiot", "dumb"],
        "obscene": ["anjing", "bangsat", "fuck", "shit", "bitch"],
        "threat": ["bunuh", "kill", "hajar", "hancurin", "mati kau"],
        "identity_hate": ["ras", "agama", "suku", "kafir", "cina", "pribumi"],
    }
    scores = {cat: 0.0 for cat in TOXIC_CATEGORIES}
    for cat, terms in lexicons.items():
        hits = sum(1 for term in terms if term in lowered)
        if hits > 0:
            scores[cat] = min(1.0, 0.55 + (0.15 * hits))
    scores["toxic"] = max(scores["insult"], scores["obscene"], scores["threat"], scores["identity_hate"])
    scores["severe_toxic"] = 0.9 if sum(v >= 0.7 for k, v in scores.items() if k != "severe_toxic") >= 2 else 0.0
    return scores


def _predict_toxicity(df: pd.DataFrame, cfg: ToxicAgentConfig) -> List[Dict[str, Any]]:
    texts = df["processed_text"].tolist()
    output: List[Dict[str, Any]] = []

    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(cfg.model_name, use_fast=cfg.use_fast_tokenizer)
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
            category_scores: Dict[str, float] = {cat: 0.0 for cat in TOXIC_CATEGORIES}
            non_toxic_score = 0.0
            for item in pred:
                label = _normalize_label(str(item.get("label", "")))
                score = float(item.get("score", 0.0))
                if label == "non_toxic":
                    non_toxic_score = max(non_toxic_score, score)
                elif label in category_scores:
                    category_scores[label] = max(category_scores[label], score)
                elif label:
                    category_scores["toxic"] = max(category_scores["toxic"], score)

            if max(category_scores.values()) <= 0.0 and non_toxic_score > 0:
                category_scores["toxic"] = max(0.0, 1.0 - non_toxic_score)

            top_label = max(category_scores.items(), key=lambda x: x[1])[0]
            toxic_score = float(category_scores[top_label])
            output.append(
                {
                    "toxicity_score": toxic_score,
                    "toxicity_label": top_label,
                    "category_scores": category_scores,
                }
            )
        return output
    except Exception as err:  # pragma: no cover - runtime fallback
        logger.warning("Toxic model unavailable. Falling back to lexical mode: %s", err)

    for text in texts:
        category_scores = _fallback_lexical_scores(text)
        top_label = max(category_scores.items(), key=lambda x: x[1])[0]
        output.append(
            {
                "toxicity_score": float(category_scores[top_label]),
                "toxicity_label": top_label,
                "category_scores": category_scores,
            }
        )
    return output


def _flag_from_score(score: float, cfg: ToxicAgentConfig) -> str:
    if score >= cfg.toxic_threshold:
        return "toxic"
    if score >= cfg.suspicious_threshold:
        return "suspicious"
    return "safe"


def _summary(df: pd.DataFrame) -> Dict[str, Any]:
    total = len(df)
    toxic_count = int((df["flag"] == "toxic").sum())
    suspicious_count = int((df["flag"] == "suspicious").sum())
    return {
        "total_comments": int(total),
        "toxic_comments": toxic_count,
        "suspicious_comments": suspicious_count,
        "safe_comments": int(total - toxic_count - suspicious_count),
        "toxic_ratio": round(toxic_count / total, 4) if total else 0.0,
        "suspicious_ratio": round(suspicious_count / total, 4) if total else 0.0,
    }


def _category_distribution(df: pd.DataFrame, cfg: ToxicAgentConfig) -> Dict[str, int]:
    counts = {cat: 0 for cat in TOXIC_CATEGORIES}
    for _, row in df.iterrows():
        scores: Dict[str, float] = row["category_scores"]
        for cat in TOXIC_CATEGORIES:
            if float(scores.get(cat, 0.0)) >= cfg.category_threshold:
                counts[cat] += 1
    return counts


def _toxic_burst(df: pd.DataFrame, cfg: ToxicAgentConfig) -> Dict[str, Any]:
    valid = df.dropna(subset=[cfg.published_at_column]).copy()
    if valid.empty:
        return {"timeline": [], "spikes": []}

    valid = valid.set_index(cfg.published_at_column)
    timeline_series = valid["flag"].isin(["toxic", "suspicious"]).resample(cfg.temporal_resample_rule).sum()
    timeline = [{"bucket": ts.isoformat(), "toxic_or_suspicious_count": int(cnt)} for ts, cnt in timeline_series.items()]

    mean = float(timeline_series.mean())
    std = float(timeline_series.std(ddof=0))
    threshold = mean + (cfg.spike_std_threshold * std if std > 0 else 0.0)
    spikes = timeline_series[timeline_series > threshold]
    spike_records = [
        {
            "bucket": ts.isoformat(),
            "toxic_or_suspicious_count": int(cnt),
            "threshold": round(float(threshold), 4),
        }
        for ts, cnt in spikes.items()
    ]
    return {"timeline": timeline, "spikes": spike_records}


def _top_toxic_comments(df: pd.DataFrame, cfg: ToxicAgentConfig) -> List[Dict[str, Any]]:
    toxic_df = df[df["flag"] == "toxic"].copy()
    if toxic_df.empty:
        return []
    ranked = toxic_df.sort_values(["toxicity_score", cfg.like_column], ascending=[False, False]).head(
        cfg.top_k_highlights
    )
    return [
        {
            "comment_id": str(row[cfg.comment_id_column] or f"row_{int(row['_row_id'])}"),
            "author": row[cfg.author_column],
            "text": row[cfg.text_column],
            "toxicity_score": round(float(row["toxicity_score"]), 4),
            "toxicity_label": row["toxicity_label"],
            "flag": row["flag"],
        }
        for _, row in ranked.iterrows()
    ]


def _comment_level(df: pd.DataFrame, cfg: ToxicAgentConfig) -> List[Dict[str, Any]]:
    return [
        {
            "comment_id": str(row[cfg.comment_id_column] or f"row_{int(row['_row_id'])}"),
            "text": row[cfg.text_column],
            "processed_text": row["processed_text"],
            "toxicity_score": round(float(row["toxicity_score"]), 4),
            "toxicity_label": row["toxicity_label"],
            "flag": row["flag"],
            "category_scores": {k: round(float(v), 4) for k, v in row["category_scores"].items()},
        }
        for _, row in df.iterrows()
    ]


def run_toxic_agent(
    comments: pd.DataFrame | List[Dict[str, Any]],
    config: Optional[ToxicAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs toxic detection and analytics on comment collections."""
    cfg = config or ToxicAgentConfig()
    df = comments if isinstance(comments, pd.DataFrame) else pd.DataFrame(comments)
    normalized = _normalize_schema(df, cfg)

    if normalized.empty:
        return {
            "summary": _summary(normalized),
            "categories": {cat: 0 for cat in TOXIC_CATEGORIES},
            "toxic_burst": {"timeline": [], "spikes": []},
            "top_toxic_comments": [],
            "comment_level": [],
        }

    normalized["processed_text"] = normalized[cfg.text_column].apply(_preprocess_text)
    predictions = _predict_toxicity(normalized, cfg)
    normalized["toxicity_score"] = [item["toxicity_score"] for item in predictions]
    normalized["toxicity_label"] = [item["toxicity_label"] for item in predictions]
    normalized["category_scores"] = [item["category_scores"] for item in predictions]
    normalized["flag"] = normalized["toxicity_score"].apply(lambda s: _flag_from_score(float(s), cfg))

    return {
        "summary": _summary(normalized),
        "categories": _category_distribution(normalized, cfg),
        "toxic_burst": _toxic_burst(normalized, cfg),
        "top_toxic_comments": _top_toxic_comments(normalized, cfg),
        "comment_level": _comment_level(normalized, cfg),
    }


def run_toxic_agent_from_csv(
    csv_path: str,
    *,
    output_json_path: Optional[str] = None,
    config: Optional[ToxicAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs toxic agent from CSV and optionally writes JSON output."""
    logger.info("Loading comments CSV for toxic analysis: %s", csv_path)
    df = pd.read_csv(csv_path)
    result = run_toxic_agent(df, config=config)

    if output_json_path:
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Toxic-agent output saved: %s", output_json_path)

    return result
