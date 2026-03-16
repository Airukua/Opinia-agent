from __future__ import annotations
from typing import Any, Dict, List, Optional
from .config import EvidenceMergeConfig, RecursiveInsightConfig
from .llm_insights import generate_llm_insights
from .snapshot import build_comment_records, build_evidence_snapshot


def merge_evidence_and_insights(
    *,
    video: Dict[str, Any],
    comments: List[Dict[str, Any]],
    eda_result: Dict[str, Any],
    spam_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
    topic_result: Dict[str, Any],
    config: Optional[EvidenceMergeConfig] = None,
    recursive_config: Optional[RecursiveInsightConfig] = None,
) -> Dict[str, Any]:
    """Builds evidence snapshot and viral LLM insights.

    Args:
        video: Video metadata payload.
        comments: Raw comment list.
        eda_result: EDA agent output.
        spam_result: Spam agent output.
        sentiment_result: Sentiment agent output.
        toxic_result: Toxicity agent output.
        topic_result: Topic agent output.
        config: Optional evidence merge configuration.
        recursive_config: Optional recursive insight configuration.

    Returns:
        Dictionary with ``evidence_snapshot`` and ``llm_insights``.

    Example usage:
        >>> result = merge_evidence_and_insights(
        ...     video={},
        ...     comments=[],
        ...     eda_result={},
        ...     spam_result={},
        ...     sentiment_result={},
        ...     toxic_result={},
        ...     topic_result={},
        ... )
        >>> "evidence_snapshot" in result
        True
    """
    cfg = config or EvidenceMergeConfig()

    evidence_snapshot = build_evidence_snapshot(
        video=video,
        comments_total=len(comments),
        eda_result=eda_result,
        spam_result=spam_result,
        sentiment_result=sentiment_result,
        toxic_result=toxic_result,
        topic_result=topic_result,
        config=cfg,
    )

    comment_records = build_comment_records(
        comments,
        spam_result,
        sentiment_result,
        toxic_result,
        limit=cfg.comment_sample_limit,
    )

    llm_insights = generate_llm_insights(
        evidence_snapshot=evidence_snapshot,
        comment_records=comment_records,
        config=cfg,
        recursive_config=recursive_config,
    )

    return {
        "evidence_snapshot": evidence_snapshot,
        "llm_insights": llm_insights,
    }
