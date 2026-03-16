from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EvidenceMergeConfig:
    """Controls evidence reduction and LLM batching.

    Attributes:
        top_spam_examples: Maximum spam examples passed to LLM.
        top_sentiment_highlights: Highlights per sentiment label.
        top_toxic_examples: Maximum toxic examples passed to LLM.
        top_topic_clusters: Maximum topic clusters passed to LLM.
        comment_sample_limit: Cap on merged comments for LLM batches.
        llm_enabled: Enables or disables LLM insight generation.
        llm_batch_size: Comments per LLM batch.
        llm_model: Optional model override for Ollama.
        llm_base_url: Ollama base URL.
        llm_timeout_seconds: Request timeout for Ollama.

    Example usage:
        >>> cfg = EvidenceMergeConfig(llm_batch_size=80, comment_sample_limit=200)
        >>> cfg.llm_batch_size
        80
    """

    top_spam_examples: int = 8
    top_sentiment_highlights: int = 5
    top_toxic_examples: int = 8
    top_topic_clusters: int = 10
    comment_sample_limit: int = 120
    llm_enabled: bool = True
    llm_batch_size: int = 60
    llm_model: Optional[str] = None
    llm_base_url: str = "http://localhost:11434"
    llm_provider: str = "ollama"
    llm_api_key: Optional[str] = None
    llm_api_base_url: Optional[str] = None
    llm_timeout_seconds: int = 120
    llm_simple_mode: bool = False


@dataclass
class RecursiveInsightConfig:
    """Controls recursive insight extraction prompt flow.

    Attributes:
        max_batches: Upper limit on processed batches.
        include_environment_history: Includes prior environment state in prompts.

    Example usage:
        >>> cfg = RecursiveInsightConfig(max_batches=5)
        >>> cfg.max_batches
        5
    """

    max_batches: int = 20
    include_environment_history: bool = True
