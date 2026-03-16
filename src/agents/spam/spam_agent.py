"""Hybrid multilingual spam detection agent.

Detection layers:
1. Pattern-based signals (language independent),
2. Semantic similarity against spam templates, and
3. Behaviour-based author activity signals.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

URL_PATTERN = re.compile(r"(https?://|www\.|bit\.ly|t\.me|telegram\.me|wa\.me)", re.IGNORECASE)
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{3,}", re.UNICODE)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


@dataclass
class SpamAgentConfig:
    """Configuration for hybrid spam detection."""

    text_column: str = "text"
    author_column: str = "author"
    published_at_column: str = "published_at"
    comment_id_column: str = "comment_id"
    video_id_column: str = "video_id"
    spam_threshold: float = 0.7
    pattern_weight: float = 0.4
    semantic_weight: float = 0.3
    behaviour_weight: float = 0.3
    enable_semantic: bool = True
    model_name: str = "models/multilingual-e5-small"
    model_cache_dir: Optional[str] = None
    device: Optional[str] = None
    semantic_similarity_threshold: float = 0.85
    emoji_spam_threshold: int = 6
    url_spam_threshold: int = 2
    burst_comments_per_minute_threshold: int = 10
    abnormal_link_ratio_threshold: float = 0.7
    abnormal_link_ratio_min_comments: int = 3
    keyword_weight_in_pattern: float = 0.15
    spam_templates: List[str] = field(
        default_factory=lambda: [
            "subscribe my channel",
            "check my profile",
            "earn money online",
            "free crypto",
            "join my telegram",
            "contact me on telegram",
            "dm me for investment",
            "giveaway click link",
            "get rich quick",
            "work from home income",
        ]
    )
    spam_keywords: List[str] = field(
        default_factory=lambda: [
            "subscribe",
            "subscribe balik",
            "check my channel",
            "kunjungi channel saya",
            "free",
            "earn money",
            "crypto",
            "telegram",
            "bitcoin",
            "giveaway",
        ]
    )


def _ensure_schema(df: pd.DataFrame, cfg: SpamAgentConfig) -> pd.DataFrame:
    normalized = df.copy()
    for column in [
        cfg.text_column,
        cfg.author_column,
        cfg.published_at_column,
        cfg.comment_id_column,
        cfg.video_id_column,
    ]:
        if column not in normalized.columns:
            normalized[column] = None

    normalized[cfg.text_column] = normalized[cfg.text_column].fillna("").astype(str)
    normalized[cfg.author_column] = normalized[cfg.author_column].fillna("unknown").astype(str)
    normalized[cfg.comment_id_column] = normalized[cfg.comment_id_column].fillna("").astype(str)
    normalized[cfg.video_id_column] = normalized[cfg.video_id_column].fillna("").astype(str)
    normalized[cfg.published_at_column] = pd.to_datetime(
        normalized[cfg.published_at_column], errors="coerce", utc=True
    )

    normalized = normalized.reset_index(drop=True)
    normalized["_row_id"] = normalized.index.astype(int)
    normalized["_text_norm"] = normalized[cfg.text_column].str.strip().str.lower()
    normalized["_text_hash"] = normalized["_text_norm"].apply(
        lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()
    )
    return normalized


def _count_emojis(text: str) -> int:
    matches = EMOJI_PATTERN.findall(text)
    return sum(len(item) for item in matches)


def _keyword_hits(text: str, keywords: List[str]) -> int:
    lowered = text.lower()
    return sum(1 for kw in keywords if kw.lower() in lowered)


def _compute_pattern_signals(df: pd.DataFrame, cfg: SpamAgentConfig) -> Tuple[List[float], List[List[str]], pd.Series]:
    reasons: List[List[str]] = [[] for _ in range(len(df))]
    scores = [0.0] * len(df)

    url_counts = df[cfg.text_column].apply(lambda x: len(URL_PATTERN.findall(x)))
    repeated_chars = df[cfg.text_column].apply(lambda x: bool(REPEATED_CHAR_PATTERN.search(x)))
    emoji_counts = df[cfg.text_column].apply(_count_emojis)
    duplicate_counts = df["_text_hash"].value_counts()

    for idx, row in df.iterrows():
        local_score = 0.0
        row_reasons: List[str] = reasons[idx]

        if url_counts.iloc[idx] >= cfg.url_spam_threshold:
            local_score += 0.35
            row_reasons.append("multiple_urls")
        if repeated_chars.iloc[idx]:
            local_score += 0.2
            row_reasons.append("repeated_characters")
        if emoji_counts.iloc[idx] >= cfg.emoji_spam_threshold:
            local_score += 0.2
            row_reasons.append("emoji_spam")
        if duplicate_counts.get(row["_text_hash"], 0) > 1 and row["_text_norm"] != "":
            local_score += 0.25
            row_reasons.append("duplicate_comment")

        keyword_hits = _keyword_hits(row[cfg.text_column], cfg.spam_keywords)
        if keyword_hits > 0:
            local_score += min(cfg.keyword_weight_in_pattern, 0.05 * keyword_hits)
            row_reasons.append("spam_keyword")

        scores[idx] = min(local_score, 1.0)

    return scores, reasons, url_counts


def _compute_semantic_scores(df: pd.DataFrame, cfg: SpamAgentConfig) -> Tuple[List[float], List[List[str]]]:
    reasons: List[List[str]] = [[] for _ in range(len(df))]
    scores = [0.0] * len(df)
    if not cfg.enable_semantic:
        return scores, reasons

    try:
        from utils.sentence_transformer_wrapper import SentenceTransformerWrapper

        embedder = SentenceTransformerWrapper(
            model_name=cfg.model_name,
            device=cfg.device,
            cache_folder=cfg.model_cache_dir,
        )
        comment_embeddings = embedder.encode(
            df[cfg.text_column].tolist(),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        template_embeddings = embedder.encode(
            cfg.spam_templates,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        max_similarity: List[float] = []
        for comment_vec in comment_embeddings:
            best = -1.0
            for template_vec in template_embeddings:
                sim = sum(float(a) * float(b) for a, b in zip(comment_vec, template_vec))
                if sim > best:
                    best = sim
            max_similarity.append(max(best, 0.0))

        for idx, sim in enumerate(max_similarity):
            if sim >= cfg.semantic_similarity_threshold:
                scores[idx] = min(1.0, sim)
                reasons[idx].append("semantic_spam_template_match")
            else:
                scores[idx] = max(0.0, sim * 0.5)
    except Exception as err:  # pragma: no cover - runtime fallback
        logger.warning("Semantic spam detection skipped: %s", err)
    return scores, reasons


def _compute_behaviour_scores(
    df: pd.DataFrame,
    cfg: SpamAgentConfig,
    url_counts: pd.Series,
) -> Tuple[List[float], List[List[str]]]:
    reasons: List[List[str]] = [[] for _ in range(len(df))]
    scores = [0.0] * len(df)

    work = df.copy()
    work["_url_count"] = url_counts.values
    work["_has_link"] = work["_url_count"] > 0
    work["_minute_bucket"] = work[cfg.published_at_column].dt.floor("min")

    burst_index: set[int] = set()
    valid_time = work.dropna(subset=[cfg.published_at_column])
    if not valid_time.empty:
        burst_groups = (
            valid_time.groupby([cfg.author_column, "_minute_bucket"])["_row_id"]
            .count()
            .reset_index(name="cnt")
        )
        burst_groups = burst_groups[
            burst_groups["cnt"] > cfg.burst_comments_per_minute_threshold
        ]
        if not burst_groups.empty:
            merged = valid_time.merge(
                burst_groups[[cfg.author_column, "_minute_bucket"]],
                on=[cfg.author_column, "_minute_bucket"],
                how="inner",
            )
            burst_index = set(int(i) for i in merged["_row_id"].tolist())

    duplicate_user_index: set[int] = set()
    dup_user = work[(work["_text_norm"] != "")].groupby(
        [cfg.author_column, "_text_hash"], as_index=False
    )["_row_id"].count()
    dup_user = dup_user[dup_user["_row_id"] > 1]
    if not dup_user.empty:
        merged = work.merge(
            dup_user[[cfg.author_column, "_text_hash"]],
            on=[cfg.author_column, "_text_hash"],
            how="inner",
        )
        duplicate_user_index = set(int(i) for i in merged["_row_id"].tolist())

    cross_video_index: set[int] = set()
    if cfg.video_id_column in work.columns:
        cross_video = (
            work[(work["_text_norm"] != "")]
            .groupby([cfg.author_column, "_text_hash"])[cfg.video_id_column]
            .nunique()
            .reset_index(name="video_count")
        )
        cross_video = cross_video[cross_video["video_count"] > 1]
        if not cross_video.empty:
            merged = work.merge(
                cross_video[[cfg.author_column, "_text_hash"]],
                on=[cfg.author_column, "_text_hash"],
                how="inner",
            )
            cross_video_index = set(int(i) for i in merged["_row_id"].tolist())

    link_profile = (
        work.groupby(cfg.author_column)
        .agg(comment_count=("_row_id", "count"), link_count=("_has_link", "sum"))
        .reset_index()
    )
    link_profile["link_ratio"] = (
        link_profile["link_count"] / link_profile["comment_count"].replace(0, 1)
    )
    suspicious_authors = set(
        link_profile[
            (link_profile["comment_count"] >= cfg.abnormal_link_ratio_min_comments)
            & (link_profile["link_ratio"] >= cfg.abnormal_link_ratio_threshold)
        ][cfg.author_column].tolist()
    )

    for idx, row in work.iterrows():
        local_score = 0.0
        row_reasons: List[str] = reasons[idx]
        row_id = int(row["_row_id"])

        if row_id in burst_index:
            local_score += 0.4
            row_reasons.append("comment_burst")
        if row_id in duplicate_user_index:
            local_score += 0.2
            row_reasons.append("repeated_user_comment")
        if row_id in cross_video_index:
            local_score += 0.2
            row_reasons.append("identical_comments_across_videos")
        if row[cfg.author_column] in suspicious_authors:
            local_score += 0.2
            row_reasons.append("abnormal_link_frequency")

        scores[idx] = min(local_score, 1.0)

    return scores, reasons


def run_spam_agent(
    comments: pd.DataFrame | List[Dict[str, Any]],
    config: Optional[SpamAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs hybrid multilingual spam detection and returns per-comment decisions."""
    cfg = config or SpamAgentConfig()
    df = comments if isinstance(comments, pd.DataFrame) else pd.DataFrame(comments)
    normalized = _ensure_schema(df, cfg)

    if normalized.empty:
        return {
            "total_comments": 0,
            "spam_comments": 0,
            "spam_ratio": 0.0,
            "results": [],
            "config": {
                "spam_threshold": cfg.spam_threshold,
                "weights": {
                    "pattern": cfg.pattern_weight,
                    "semantic": cfg.semantic_weight,
                    "behaviour": cfg.behaviour_weight,
                },
            },
        }

    pattern_scores, pattern_reasons, url_counts = _compute_pattern_signals(normalized, cfg)
    semantic_scores, semantic_reasons = _compute_semantic_scores(normalized, cfg)
    behaviour_scores, behaviour_reasons = _compute_behaviour_scores(normalized, cfg, url_counts)

    results: List[Dict[str, Any]] = []
    spam_count = 0
    for idx, row in normalized.iterrows():
        score = (
            cfg.pattern_weight * pattern_scores[idx]
            + cfg.semantic_weight * semantic_scores[idx]
            + cfg.behaviour_weight * behaviour_scores[idx]
        )
        score = float(min(max(score, 0.0), 1.0))
        reasons = sorted(
            set(pattern_reasons[idx] + semantic_reasons[idx] + behaviour_reasons[idx])
        )
        label = "spam" if score >= cfg.spam_threshold else "ham"
        if label == "spam":
            spam_count += 1

        comment_id = row[cfg.comment_id_column]
        if not comment_id:
            comment_id = f"row_{int(row['_row_id'])}"

        results.append(
            {
                "comment_id": str(comment_id),
                "author": row[cfg.author_column],
                "video_id": row[cfg.video_id_column],
                "text": row[cfg.text_column],
                "spam_score": round(score, 4),
                "label": label,
                "reason": reasons,
                "layer_scores": {
                    "pattern_score": round(float(pattern_scores[idx]), 4),
                    "semantic_score": round(float(semantic_scores[idx]), 4),
                    "behaviour_score": round(float(behaviour_scores[idx]), 4),
                },
            }
        )

    results = sorted(results, key=lambda x: x["spam_score"], reverse=True)
    return {
        "total_comments": int(len(normalized)),
        "spam_comments": int(spam_count),
        "spam_ratio": round(spam_count / len(normalized), 4),
        "results": results,
        "config": {
            "spam_threshold": cfg.spam_threshold,
            "weights": {
                "pattern": cfg.pattern_weight,
                "semantic": cfg.semantic_weight,
                "behaviour": cfg.behaviour_weight,
            },
        },
    }


def run_spam_agent_from_csv(
    csv_path: str,
    *,
    output_json_path: Optional[str] = None,
    config: Optional[SpamAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs spam agent from CSV and optionally saves output as JSON."""
    logger.info("Loading comments CSV for spam detection: %s", csv_path)
    df = pd.read_csv(csv_path)
    result = run_spam_agent(df, config=config)

    if output_json_path:
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Spam-agent output saved: %s", output_json_path)

    return result
