from __future__ import annotations
from typing import Any, Dict, Iterable, List
from .config import EvidenceMergeConfig


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely casts a value to int, falling back to default on failure.

    Args:
        value: Value to convert.
        default: Value to return on conversion failure.

    Returns:
        Converted integer or ``default``.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _take_top(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Returns the first ``limit`` items, handling non-positive limits.

    Args:
        items: List to slice.
        limit: Maximum number of items to return.

    Returns:
        Truncated list of items.
    """
    if limit <= 0:
        return []
    return items[:limit]


def _build_comment_index(items: Iterable[Dict[str, Any]]) -> Dict[Any, Dict[str, Any]]:
    """Builds a lookup table by ``comment_id``.

    Args:
        items: Iterable of comment-like dictionaries.

    Returns:
        Mapping of comment_id to item payload.
    """
    return {item.get("comment_id"): item for item in items}


def build_comment_records(
    comments: List[Dict[str, Any]],
    spam_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
    *,
    limit: int,
) -> List[Dict[str, Any]]:
    """Merges per-comment signals from multiple agents for LLM processing.

    Args:
        comments: Raw comment list from the scraper.
        spam_result: Output from spam agent.
        sentiment_result: Output from sentiment agent.
        toxic_result: Output from toxicity agent.
        limit: Maximum number of merged records to return.

    Returns:
        List of merged comment records with per-agent annotations.

    Example usage:
        >>> merged = build_comment_records([], {}, {}, {}, limit=10)
        >>> isinstance(merged, list)
        True
    """
    spam_map = _build_comment_index(spam_result.get("results", []))
    sentiment_map = _build_comment_index(sentiment_result.get("comment_level", []))
    toxic_map = _build_comment_index(toxic_result.get("comment_level", []))

    merged: List[Dict[str, Any]] = []
    for item in comments:
        comment_id = item.get("comment_id")
        spam_item = spam_map.get(comment_id, {})
        sentiment_item = sentiment_map.get(comment_id, {})
        toxic_item = toxic_map.get(comment_id, {})

        merged.append(
            {
                "comment_id": comment_id,
                "text": item.get("text"),
                "author": item.get("author"),
                "published_at": item.get("published_at"),
                "like_count": _safe_int(item.get("like_count"), 0),
                "spam": {
                    "label": spam_item.get("label"),
                    "score": spam_item.get("spam_score"),
                    "reason": spam_item.get("reason"),
                },
                "sentiment": {
                    "label": sentiment_item.get("sentiment"),
                    "confidence": sentiment_item.get("confidence"),
                    "scores": sentiment_item.get("scores"),
                },
                "toxicity": {
                    "label": toxic_item.get("toxicity_label"),
                    "score": toxic_item.get("toxicity_score"),
                    "flag": toxic_item.get("flag"),
                    "categories": toxic_item.get("category_scores"),
                },
            }
        )

        if limit and len(merged) >= limit:
            break

    return merged


def build_evidence_snapshot(
    *,
    video: Dict[str, Any],
    comments_total: int,
    eda_result: Dict[str, Any],
    spam_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
    topic_result: Dict[str, Any],
    config: EvidenceMergeConfig,
) -> Dict[str, Any]:
    """Reduces agent outputs into a compact evidence snapshot for LLM prompts.

    Args:
        video: Video metadata dictionary.
        comments_total: Total number of scraped comments.
        eda_result: EDA agent output.
        spam_result: Spam agent output.
        sentiment_result: Sentiment agent output.
        toxic_result: Toxicity agent output.
        topic_result: Topic agent output.
        config: Evidence merge configuration.

    Returns:
        Compact evidence dictionary for LLM analysis.

    Example usage:
        >>> snapshot = build_evidence_snapshot(
        ...     video={},
        ...     comments_total=0,
        ...     eda_result={},
        ...     spam_result={},
        ...     sentiment_result={},
        ...     toxic_result={},
        ...     topic_result={},
        ...     config=EvidenceMergeConfig(),
        ... )
        >>> "eda" in snapshot
        True
    """
    return {
        "video": video,
        "comment_totals": _build_comment_totals(
            comments_total=comments_total,
            spam_result=spam_result,
            toxic_result=toxic_result,
        ),
        "eda": _build_eda_block(eda_result),
        "spam": _build_spam_block(spam_result, config),
        "sentiment": _build_sentiment_block(sentiment_result, config),
        "toxicity": _build_toxicity_block(toxic_result, config),
        "topics": _build_topics_block(topic_result, config),
    }


def _build_comment_totals(
    *,
    comments_total: int,
    spam_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
) -> Dict[str, int]:
    """Builds a summary of comment totals across signals.

    Args:
        comments_total: Total scraped comment count.
        spam_result: Spam agent output.
        toxic_result: Toxicity agent output.

    Returns:
        Dictionary containing total, spam, and toxic counts.
    """
    return {
        "total_comments": int(comments_total),
        "spam_comments": int(spam_result.get("spam_comments", 0)),
        "toxic_comments": int(toxic_result.get("summary", {}).get("toxic_comments", 0)),
    }


def _build_eda_block(eda_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts EDA fields for the evidence snapshot.

    Args:
        eda_result: EDA agent output.

    Returns:
        EDA block for the snapshot payload.
    """
    return {
        "total_comments": eda_result.get("total_comments"),
        "volume_temporal_analysis": eda_result.get("volume_temporal_analysis"),
        "engagement_analysis": eda_result.get("engagement_analysis"),
        "text_statistics": eda_result.get("text_statistics"),
    }


def _build_spam_block(
    spam_result: Dict[str, Any], config: EvidenceMergeConfig
) -> Dict[str, Any]:
    """Builds the spam block for the evidence snapshot.

    Args:
        spam_result: Spam agent output.
        config: Evidence merge configuration.

    Returns:
        Spam block with summary and top examples.
    """
    spam_examples = _take_top(spam_result.get("results", []), config.top_spam_examples)
    return {
        "summary": {
            "total_comments": spam_result.get("total_comments"),
            "spam_comments": spam_result.get("spam_comments"),
            "spam_ratio": spam_result.get("spam_ratio"),
        },
        "top_examples": spam_examples,
    }


def _build_sentiment_block(
    sentiment_result: Dict[str, Any], config: EvidenceMergeConfig
) -> Dict[str, Any]:
    """Builds the sentiment block for the evidence snapshot.

    Args:
        sentiment_result: Sentiment agent output.
        config: Evidence merge configuration.

    Returns:
        Sentiment block with summary and highlights.
    """
    sentiment_highlights = sentiment_result.get("highlights", {}) or {}
    return {
        "summary": {
            "total_comments": sentiment_result.get("total_comments"),
            "distribution": sentiment_result.get("distribution"),
            "video_sentiment": sentiment_result.get("video_sentiment"),
            "sentiment_score": sentiment_result.get("sentiment_score"),
            "toxicity_integration": sentiment_result.get("toxicity_integration"),
        },
        "highlights": {
            "positive": _take_top(
                sentiment_highlights.get("positive", []),
                config.top_sentiment_highlights,
            ),
            "neutral": _take_top(
                sentiment_highlights.get("neutral", []),
                config.top_sentiment_highlights,
            ),
            "negative": _take_top(
                sentiment_highlights.get("negative", []),
                config.top_sentiment_highlights,
            ),
        },
    }


def _build_toxicity_block(
    toxic_result: Dict[str, Any], config: EvidenceMergeConfig
) -> Dict[str, Any]:
    """Builds the toxicity block for the evidence snapshot.

    Args:
        toxic_result: Toxicity agent output.
        config: Evidence merge configuration.

    Returns:
        Toxicity block with summary, categories, and top examples.
    """
    toxicity_examples = _take_top(
        toxic_result.get("top_toxic_comments", []), config.top_toxic_examples
    )
    return {
        "summary": toxic_result.get("summary"),
        "categories": toxic_result.get("categories"),
        "top_examples": toxicity_examples,
    }


def _build_topics_block(
    topic_result: Dict[str, Any], config: EvidenceMergeConfig
) -> Dict[str, Any]:
    """Builds the topics block for the evidence snapshot.

    Args:
        topic_result: Topic agent output.
        config: Evidence merge configuration.

    Returns:
        Topics block with cluster summary and clusters.
    """
    topic_clusters = _take_top(topic_result.get("clusters", []), config.top_topic_clusters)
    return {
        "cluster_summary": topic_result.get("cluster_summary"),
        "clusters": topic_clusters,
    }
