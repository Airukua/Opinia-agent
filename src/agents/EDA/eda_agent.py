"""EDA agent for structured exploratory analysis of YouTube comments.

This module focuses on deterministic analytics (non-LLM) to produce:
1. Volume and temporal trends,
2. Engagement statistics, and
3. Core NLP text statistics.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")


def _load_sastrawi_stopwords() -> Set[str]:
    try:
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import (
            StopWordRemoverFactory,
        )
    except Exception as err:
        raise RuntimeError(
            "Sastrawi is required for stopword removal. Install it with 'pip install Sastrawi'."
        ) from err
    factory = StopWordRemoverFactory()
    return set(factory.get_stop_words())


@dataclass
class EDAConfig:
    """Configuration for EDA computation and output shape.

    Attributes:
        top_k: Number of top tokens/comments/ngrams included in ranked outputs.
        spike_std_threshold: Number of standard deviations above hourly mean
            used to classify a timestamp bucket as a spike.
        include_zero_temporal_buckets: Includes empty temporal buckets when
            generating hourly/daily/weekly volume outputs.
    """

    top_k: int = 20
    spike_std_threshold: float = 2.0
    include_zero_temporal_buckets: bool = False
    min_token_length: int = 2
    stopwords: Set[str] = None

    def __post_init__(self) -> None:
        env_min_len = os.getenv("EDA_MIN_TOKEN_LENGTH")
        if env_min_len and env_min_len.isdigit():
            self.min_token_length = int(env_min_len)
        if self.stopwords is None:
            stopwords = _load_sastrawi_stopwords()
            env_stopwords = os.getenv("EDA_STOPWORDS")
            if env_stopwords:
                stopwords.update(
                    {w.strip().lower() for w in env_stopwords.split(",") if w.strip()}
                )
            self.stopwords = stopwords


def _ensure_comment_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes input records into the expected comment schema.

    Expected columns:
        - ``author``
        - ``text``
        - ``published_at``
        - ``like_count``

    Args:
        df: Raw comments DataFrame.

    Returns:
        A normalized DataFrame with guaranteed columns and sanitized dtypes.
    """
    normalized = df.copy()
    required = ["author", "text", "published_at", "like_count"]
    for col in required:
        if col not in normalized.columns:
            normalized[col] = None

    normalized["text"] = normalized["text"].fillna("").astype(str)
    normalized["like_count"] = (
        pd.to_numeric(normalized["like_count"], errors="coerce").fillna(0).astype(int)
    )
    normalized["published_at"] = pd.to_datetime(
        normalized["published_at"], errors="coerce", utc=True
    )
    return normalized


def _to_records(series: pd.Series, *, include_zero: bool = True) -> List[Dict[str, Any]]:
    """Converts a pandas Series into serializable bucket-count records.

    Args:
        series: Series where index is treated as bucket label and value as count.
        include_zero: Keeps buckets with zero count when ``True``.

    Returns:
        List of ``{"bucket": str, "count": int}`` records.
    """
    if not include_zero:
        series = series[series > 0]

    records: List[Dict[str, Any]] = []
    for key, value in series.items():
        records.append({"bucket": str(key), "count": int(value)})
    return records


def _compute_temporal_volume(
    df: pd.DataFrame,
    *,
    spike_std_threshold: float,
    include_zero_temporal_buckets: bool,
) -> Dict[str, Any]:
    """Computes temporal comment volume and spike events.

    Args:
        df: Normalized comments DataFrame.
        spike_std_threshold: Spike threshold multiplier in ``mean + k * std``.

    Returns:
        Dictionary containing:
        - comments per hour/day/week
        - detected spike buckets with threshold metadata
    """
    temporal_df = df.dropna(subset=["published_at"]).copy()
    if temporal_df.empty:
        return {
            "comments_per_hour": [],
            "comments_per_day": [],
            "comments_per_week": [],
            "spikes": [],
        }

    by_hour = temporal_df.set_index("published_at").resample("h").size()
    by_day = temporal_df.set_index("published_at").resample("D").size()
    by_week = temporal_df.set_index("published_at").resample("W-MON").size()

    mean = float(by_hour.mean())
    std = float(by_hour.std(ddof=0))
    threshold = mean + (spike_std_threshold * std if std > 0 else 0.0)
    spikes = by_hour[by_hour > threshold]

    spike_records = []
    for ts, count in spikes.items():
        spike_records.append(
            {
                "bucket": ts.isoformat(),
                "count": int(count),
                "threshold": round(threshold, 4),
            }
        )

    return {
        "comments_per_hour": _to_records(
            by_hour, include_zero=include_zero_temporal_buckets
        ),
        "comments_per_day": _to_records(
            by_day, include_zero=include_zero_temporal_buckets
        ),
        "comments_per_week": _to_records(
            by_week, include_zero=include_zero_temporal_buckets
        ),
        "spikes": spike_records,
    }


def _serialize_timestamp(value: Any) -> str | None:
    """Converts pandas timestamp-like values into ISO-8601 string."""
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _compute_engagement(df: pd.DataFrame, top_k: int) -> Dict[str, Any]:
    """Computes engagement statistics from ``like_count`` signals.

    Args:
        df: Normalized comments DataFrame.
        top_k: Number of top liked comments to include.

    Returns:
        Dictionary containing distribution stats and top liked comments.
    """
    like_series = df["like_count"].fillna(0)
    top_liked_raw = (
        df.sort_values("like_count", ascending=False)
        .head(top_k)[["author", "text", "published_at", "like_count"]]
        .to_dict(orient="records")
    )
    top_liked = []
    for row in top_liked_raw:
        top_liked.append(
            {
                "author": row.get("author"),
                "text": row.get("text"),
                "published_at": _serialize_timestamp(row.get("published_at")),
                "like_count": int(row.get("like_count", 0)),
            }
        )

    return {
        "like_count_distribution": {
            "min": float(like_series.min()),
            "max": float(like_series.max()),
            "mean": float(like_series.mean()),
            "median": float(like_series.median()),
            "std": float(like_series.std(ddof=0)),
        },
        "engagement_per_comment": {
            "mean_like_count": float(like_series.mean()),
            "median_like_count": float(like_series.median()),
        },
        "top_liked_comments": top_liked,
    }


def _tokenize(
    texts: Iterable[str],
    *,
    stopwords: Set[str],
    min_token_length: int,
) -> List[str]:
    """Tokenizes iterable text into lowercase alphanumeric tokens.

    Args:
        texts: Iterable of raw comment text.

    Returns:
        Flattened list of tokens.
    """
    tokens: List[str] = []
    for text in texts:
        for token in TOKEN_PATTERN.findall(text):
            lowered = token.lower()
            if len(lowered) < min_token_length:
                continue
            if lowered in stopwords:
                continue
            tokens.append(lowered)
    return tokens


def _compute_ngrams(tokens: List[str], n: int) -> Counter:
    """Builds n-gram frequency counts from a token sequence.

    Args:
        tokens: Ordered token list.
        n: N-gram length.

    Returns:
        ``Counter`` of n-gram -> frequency.
    """
    if n <= 1 or len(tokens) < n:
        return Counter()
    grams = (" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1))
    return Counter(grams)


def _compute_ngrams_per_comment(
    texts: Iterable[str],
    n: int,
    *,
    stopwords: Set[str],
    min_token_length: int,
) -> Counter:
    """Builds n-gram frequency counts per comment to avoid cross-comment joins.

    Args:
        texts: Iterable of comment text.
        n: N-gram length.

    Returns:
        ``Counter`` of n-gram -> frequency.
    """
    combined = Counter()
    for text in texts:
        tokens = []
        for token in TOKEN_PATTERN.findall(text):
            lowered = token.lower()
            if len(lowered) < min_token_length:
                continue
            if lowered in stopwords:
                continue
            tokens.append(lowered)
        combined.update(_compute_ngrams(tokens, n))
    return combined


def _compute_text_stats(
    df: pd.DataFrame,
    top_k: int,
    *,
    stopwords: Set[str],
    min_token_length: int,
) -> Dict[str, Any]:
    """Computes descriptive NLP metrics for comment text.

    Args:
        df: Normalized comments DataFrame.
        top_k: Number of top-ranked tokens/ngrams to include.

    Returns:
        Dictionary containing text length metrics and vocabulary statistics.
    """
    text_series = df["text"].fillna("")
    char_lengths = text_series.str.len()
    word_lengths = text_series.apply(lambda x: len(TOKEN_PATTERN.findall(x)))

    all_tokens = _tokenize(
        text_series.tolist(),
        stopwords=stopwords,
        min_token_length=min_token_length,
    )
    token_counter = Counter(all_tokens)
    bigram_counter = _compute_ngrams_per_comment(
        text_series.tolist(),
        2,
        stopwords=stopwords,
        min_token_length=min_token_length,
    )
    trigram_counter = _compute_ngrams_per_comment(
        text_series.tolist(),
        3,
        stopwords=stopwords,
        min_token_length=min_token_length,
    )

    return {
        "comment_length_distribution": {
            "characters": {
                "min": int(char_lengths.min() if not char_lengths.empty else 0),
                "max": int(char_lengths.max() if not char_lengths.empty else 0),
                "mean": float(char_lengths.mean() if not char_lengths.empty else 0.0),
            },
            "words": {
                "min": int(word_lengths.min() if not word_lengths.empty else 0),
                "max": int(word_lengths.max() if not word_lengths.empty else 0),
                "mean": float(word_lengths.mean() if not word_lengths.empty else 0.0),
            },
        },
        "basic_metrics": {
            "avg_words_per_comment": float(word_lengths.mean() if not word_lengths.empty else 0.0),
            "avg_characters_per_comment": float(
                char_lengths.mean() if not char_lengths.empty else 0.0
            ),
        },
        "vocabulary": {
            "unique_words": len(set(all_tokens)),
            "vocabulary_size": len(token_counter),
            "token_frequency_top": token_counter.most_common(top_k),
            "bigram_frequency_top": bigram_counter.most_common(top_k),
            "trigram_frequency_top": trigram_counter.most_common(top_k),
        },
    }


def run_eda(comments: List[Dict[str, Any]] | pd.DataFrame, config: EDAConfig | None = None) -> Dict[str, Any]:
    """Runs EDA pipeline on comment records.

    Args:
        comments: List of comment dictionaries or a DataFrame.
        config: Optional EDA configuration.

    Returns:
        Dictionary containing temporal, engagement, and text-statistics analysis.

    Example usage:
        >>> sample = [{"author": "user_1", "text": "Great video!", "published_at": None, "like_count": 3}]
        >>> output = run_eda(sample)
        >>> "engagement_analysis" in output
        True
    """
    cfg = config or EDAConfig()
    df = comments if isinstance(comments, pd.DataFrame) else pd.DataFrame(comments)
    df = _ensure_comment_schema(df)

    logger.info("Running EDA on %d comments", len(df))
    result = {
        "total_comments": int(len(df)),
        "volume_temporal_analysis": _compute_temporal_volume(
            df,
            spike_std_threshold=cfg.spike_std_threshold,
            include_zero_temporal_buckets=cfg.include_zero_temporal_buckets,
        ),
        "engagement_analysis": _compute_engagement(df, top_k=cfg.top_k),
        "text_statistics": _compute_text_stats(
            df,
            top_k=cfg.top_k,
            stopwords=cfg.stopwords,
            min_token_length=cfg.min_token_length,
        ),
    }
    logger.info("EDA completed")
    return result


def run_eda_from_csv(
    csv_path: str,
    *,
    output_json_path: str | None = None,
    config: EDAConfig | None = None,
) -> Dict[str, Any]:
    """Runs EDA from a CSV file and optionally writes result to JSON.

    Args:
        csv_path: Path to comments CSV generated by scraper.
        output_json_path: Optional output file path for serialized EDA result.
        config: Optional EDA configuration.

    Returns:
        EDA result dictionary.

    Example usage:
        >>> result = run_eda_from_csv(
        ...     "comments/video_1.csv",
        ...     output_json_path="comments/eda/video_1_eda.json",
        ... )
        >>> "text_statistics" in result
        True
    """
    logger.info("Loading comments CSV for EDA: %s", csv_path)
    df = pd.read_csv(csv_path)
    result = run_eda(df, config=config)

    if output_json_path:
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        logger.info("EDA result saved: %s", output_json_path)

    return result
