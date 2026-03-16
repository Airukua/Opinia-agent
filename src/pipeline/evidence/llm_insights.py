from __future__ import annotations

from typing import Any, Dict, List, Optional

from llm.generation_config import OllamaGenerationConfig
from llm.ollama_client import LLMClient, chunk_list
from utils.logger import get_logger

from .config import EvidenceMergeConfig, RecursiveInsightConfig
from .prompts import (
    build_recursive_user_prompt,
    build_system_prompt,
    build_suggested_topics_prompt,
    build_viral_section_prompts,
    hard_rules,
)

logger = get_logger(__name__)


def run_recursive_llm_insights(
    *,
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
    llm_client: LLMClient,
    config: EvidenceMergeConfig,
    recursive_config: Optional[RecursiveInsightConfig] = None,
) -> Dict[str, Any]:
    """Runs recursive LLM batch analysis with viral content insight prompts.

    Args:
        evidence_snapshot: Condensed evidence snapshot for the prompts.
        comment_records: Merged comment records for batching.
        llm_client: LLM client instance for chat calls.
        config: Evidence merge configuration.
        recursive_config: Optional recursive insight configuration.

    Returns:
        Dictionary containing recursive insight outputs.

    Example usage:
        >>> isinstance(run_recursive_llm_insights.__name__, str)
        True
    """
    r_cfg = recursive_config or RecursiveInsightConfig()
    batches = _build_batches(comment_records, config.llm_batch_size, r_cfg.max_batches)

    environment = _init_recursive_environment()
    batch_outputs: List[Dict[str, Any]] = []
    system_prompt = build_system_prompt()
    section_prompts = build_viral_section_prompts()

    for idx, batch in enumerate(batches, start=1):
        user_payload = _build_batch_payload(
            batch_index=idx,
            batch_total=len(batches),
            environment=environment,
            evidence_snapshot=evidence_snapshot,
            comment_batch=batch,
            include_environment=r_cfg.include_environment_history,
        )
        batch_result = _run_section_prompts(
            llm_client=llm_client,
            system_prompt=system_prompt,
            section_prompts=section_prompts,
            user_payload=user_payload,
            model=config.llm_model,
            batch_index=idx,
        )
        _accumulate_environment(environment, batch_result)
        batch_outputs.append(batch_result)

    section_labels = _build_section_labels()
    final_insights = _synthesize_recursive_insights(
        llm_client=llm_client,
        system_prompt=system_prompt,
        section_labels=section_labels,
        environment=environment,
        model=config.llm_model,
    )
    suggested_topics = _generate_suggested_topics(
        llm_client=llm_client,
        system_prompt=system_prompt,
        insights=final_insights,
        model=config.llm_model,
    )

    return {
        "available": True,
        "mode": "recursive_viral",
        "model_used": config.llm_model or llm_client.config.model,
        "batch_count": len(batches),
        "environment": environment,
        "batch_outputs": batch_outputs,
        "emotional_triggers": final_insights.get("emotional_triggers"),
        "viral_formula": final_insights.get("viral_formula"),
        "audience_persona": final_insights.get("audience_persona"),
        "content_hooks": final_insights.get("content_hooks"),
        "opportunities": final_insights.get("opportunities"),
        "risks": final_insights.get("risks"),
        "summary": final_insights.get("summary"),
        "suggested_topics": suggested_topics,
    }


def generate_llm_insights(
    *,
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
    config: EvidenceMergeConfig,
    recursive_config: Optional[RecursiveInsightConfig] = None,
) -> Dict[str, Any]:
    """Creates viral LLM insight report if enabled and server is reachable.

    Args:
        evidence_snapshot: Condensed evidence snapshot for the prompts.
        comment_records: Merged comment records for batching.
        config: Evidence merge configuration.
        recursive_config: Optional recursive insight configuration.

    Returns:
        LLM insights payload with availability metadata.

    Example usage:
        >>> isinstance(generate_llm_insights.__name__, str)
        True
    """
    availability = _ensure_llm_available(config)
    if availability is not None:
        return availability

    client = _build_llm_client(config)
    if config.llm_simple_mode:
        return run_simple_llm_insights(
            evidence_snapshot=evidence_snapshot,
            comment_records=comment_records,
            config=config,
        )

    return run_recursive_llm_insights(
        evidence_snapshot=evidence_snapshot,
        comment_records=comment_records,
        llm_client=client,
        config=config,
        recursive_config=recursive_config,
    )


def run_simple_llm_insights(
    *,
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
    config: EvidenceMergeConfig,
) -> Dict[str, Any]:
    """Single-pass viral insight analysis — lebih cepat, cocok untuk produksi.

    Args:
        evidence_snapshot: Condensed evidence snapshot for the prompts.
        comment_records: Merged comment records for sampling.
        config: Evidence merge configuration.

    Returns:
        LLM insights payload for the simple mode.

    Example usage:
        >>> isinstance(run_simple_llm_insights.__name__, str)
        True
    """
    system_prompt = build_system_prompt()
    base_payload = {
        "evidence_snapshot": evidence_snapshot,
        "comment_samples": comment_records[: config.comment_sample_limit],
    }
    base_context = build_recursive_user_prompt(base_payload)
    section_prompts = build_viral_section_prompts()

    cfg = _build_llm_config(config)
    try:
        responses = _run_simple_prompts(
            section_prompts=section_prompts,
            system_prompt=system_prompt,
            base_context=base_context,
            cfg=cfg,
        )
    except Exception as err:
        logger.warning("Simple viral LLM failed; using fallback: %s", err)
        fallback = _fallback_simple_insights(evidence_snapshot, comment_records)
        return fallback

    suggested_topics = _generate_suggested_topics(
        llm_client=LLMClient(cfg),
        system_prompt=system_prompt,
        insights=responses,
        model=cfg.model,
    )
    return _format_simple_results(responses, suggested_topics, cfg.model)


def _build_llm_config(config: EvidenceMergeConfig) -> OllamaGenerationConfig:
    """Builds the LLM generation config from evidence config.

    Args:
        config: Evidence merge configuration.

    Returns:
        Ollama generation configuration.
    """
    return OllamaGenerationConfig(
        model=config.llm_model or "llama3.1:8b",
        provider=config.llm_provider,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        api_base_url=config.llm_api_base_url,
        timeout_seconds=config.llm_timeout_seconds,
    )


def _build_llm_client(config: EvidenceMergeConfig) -> LLMClient:
    """Builds an LLM client instance.

    Args:
        config: Evidence merge configuration.

    Returns:
        LLM client configured for the target provider.
    """
    return LLMClient(_build_llm_config(config))


def _ensure_llm_available(config: EvidenceMergeConfig) -> Optional[Dict[str, Any]]:
    """Returns an availability payload if LLM is disabled or unreachable.

    Args:
        config: Evidence merge configuration.

    Returns:
        Availability payload when blocked, otherwise ``None``.
    """
    if not config.llm_enabled:
        return {"available": False, "reason": "llm_disabled"}

    client = _build_llm_client(config)
    if not client.health_check():
        return {"available": False, "reason": "llm_unreachable"}

    return None


def _run_simple_prompts(
    *,
    section_prompts: Dict[str, str],
    system_prompt: str,
    base_context: str,
    cfg: OllamaGenerationConfig,
) -> Dict[str, str]:
    """Routes simple prompt execution based on provider.

    Args:
        section_prompts: Mapping of section key to prompt.
        system_prompt: System prompt for the LLM.
        base_context: Serialized evidence context.
        cfg: LLM generation configuration.

    Returns:
        Mapping of section key to response text.
    """
    provider = (cfg.provider or "ollama").lower()
    if provider == "gemini":
        return _run_simple_prompts_gemini(
            section_prompts=section_prompts,
            system_prompt=system_prompt,
            base_context=base_context,
            cfg=cfg,
        )
    return _run_simple_prompts_langchain(
        section_prompts=section_prompts,
        system_prompt=system_prompt,
        base_context=base_context,
        cfg=cfg,
    )


def _run_simple_prompts_gemini(
    *,
    section_prompts: Dict[str, str],
    system_prompt: str,
    base_context: str,
    cfg: OllamaGenerationConfig,
) -> Dict[str, str]:
    """Executes simple prompt flow using the Gemini client.

    Args:
        section_prompts: Mapping of section key to prompt.
        system_prompt: System prompt for the LLM.
        base_context: Serialized evidence context.
        cfg: LLM generation configuration.

    Returns:
        Mapping of section key to response text.
    """
    client = LLMClient(cfg)
    responses: Dict[str, str] = {}
    for key, prompt in section_prompts.items():
        user_prompt = f"{prompt}\n\nData komentar:\n{base_context}"
        responses[key] = client.chat_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=cfg.model,
        ).strip()
    return responses


def _run_simple_prompts_langchain(
    *,
    section_prompts: Dict[str, str],
    system_prompt: str,
    base_context: str,
    cfg: OllamaGenerationConfig,
) -> Dict[str, str]:
    """Executes simple prompt flow using the LangChain client.

    Args:
        section_prompts: Mapping of section key to prompt.
        system_prompt: System prompt for the LLM.
        base_context: Serialized evidence context.
        cfg: LLM generation configuration.

    Returns:
        Mapping of section key to response text.
    """
    from llm.langchain_client import langchain_chat_text

    responses: Dict[str, str] = {}
    for key, prompt in section_prompts.items():
        user_prompt = f"{prompt}\n\nData komentar:\n{base_context}"
        responses[key] = langchain_chat_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config=cfg,
        ).strip()
    return responses


def _format_simple_results(
    responses: Dict[str, str], suggested_topics: str, model_used: str
) -> Dict[str, Any]:
    """Formats raw responses into the standard insight payload.

    Args:
        responses: Mapping of section key to response text.

    Returns:
        Standard insight payload for the simple mode.
    """
    return {
        "available": True,
        "mode": "simple_viral",
        "model_used": model_used,
        "emotional_triggers": responses.get("emotional_triggers"),
        "viral_formula": responses.get("viral_formula"),
        "audience_persona": responses.get("audience_persona"),
        "content_hooks": responses.get("content_hooks"),
        "opportunities": responses.get("opportunities"),
        "risks": responses.get("risks"),
        "summary": responses.get("summary"),
        "suggested_topics": suggested_topics,
    }


def _fallback_simple_insights(
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Fallback statis jika LLM tidak tersedia — menggunakan data EDA langsung.

    Args:
        evidence_snapshot: Condensed evidence snapshot for the prompts.
        comment_records: Merged comment records used for sampling.

    Returns:
        Deterministic insight payload based on EDA statistics.
    """
    comment_totals = evidence_snapshot.get("comment_totals", {})
    eda = evidence_snapshot.get("eda", {})
    text_stats = eda.get("text_statistics", {}) or {}
    vocab = text_stats.get("vocabulary", {}) or {}
    top_words = vocab.get("token_frequency_top", []) or []
    top_bigrams = vocab.get("bigram_frequency_top", []) or []

    sentiment = evidence_snapshot.get("sentiment", {}).get("summary", {}) or {}
    distribution = sentiment.get("distribution", {}) or {}

    engagement = eda.get("engagement_analysis", {}) or {}
    top_liked = (engagement.get("top_liked_comments", []) or [])[:3]

    topics = evidence_snapshot.get("topics", {})
    clusters = topics.get("clusters", []) or []

    top_word_list = ", ".join(w for w, _ in top_words[:8]) if top_words else "-"
    top_bigram_list = ", ".join(b for b, _ in top_bigrams[:5]) if top_bigrams else "-"
    top_liked_texts = (
        "; ".join(
            f'"{c.get("text", "")[:60]}" ({c.get("like_count", 0)} likes)'
            for c in top_liked
        )
        if top_liked
        else "-"
    )
    top_cluster_labels = (
        ", ".join(c.get("topic_label", "") for c in clusters[:5] if c.get("topic_label"))
        or "-"
    )

    pos = distribution.get("positive", 0)
    neg = distribution.get("negative", 0)
    neu = distribution.get("neutral", 0)
    total = max(pos + neg + neu, 1)

    return {
        "available": True,
        "mode": "fallback_viral",
        "model_used": None,
        "emotional_triggers": (
            f"Kata yang paling sering muncul di komentar: {top_word_list}. "
            f"Komentar yang paling banyak disukai (like) penonton: {top_liked_texts}."
        ),
        "viral_formula": (
            f"Frasa yang sering berulang (misalnya gabungan 2 kata/bigram): {top_bigram_list}. "
            f"Topik utama yang sering dibahas (kelompok/cluster komentar): {top_cluster_labels}."
        ),
        "audience_persona": (
            f"Distribusi sentimen: {pos/total:.1%} positif, "
            f"{neg/total:.1%} negatif, {neu/total:.1%} netral. "
            f"Total komentar: {comment_totals.get('total_comments', 0)}."
        ),
        "content_hooks": (
            f"Frasa 2 kata yang sering muncul (bigram): {top_bigram_list}. "
            f"Kata kunci utama: {top_word_list}."
        ),
        "opportunities": (
            f"Topik yang bisa dikembangkan jadi konten lanjutan: {top_cluster_labels}."
        ),
        "risks": (
            f"Toxic comments: {comment_totals.get('toxic_comments', 0)} "
            f"dari {comment_totals.get('total_comments', 0)} total komentar."
        ),
        "summary": (
            f"Video mendapat {comment_totals.get('total_comments', 0)} komentar "
            f"dengan sentimen dominan {'negatif' if neg > pos else 'positif'} "
            f"({max(neg, pos)/total:.1%}). "
            f"Topik utama: {top_cluster_labels}."
        ),
        "suggested_topics": "Tidak ada",
    }


def _build_batches(
    comment_records: List[Dict[str, Any]],
    batch_size: int,
    max_batches: int,
) -> List[List[Dict[str, Any]]]:
    """Builds comment batches with optional max batch cap.

    Args:
        comment_records: Merged comment list for batching.
        batch_size: Maximum number of comments per batch.
        max_batches: Optional cap on batch count.

    Returns:
        List of comment batches.
    """
    batches = chunk_list(comment_records, batch_size)
    if max_batches and len(batches) > max_batches:
        batches = batches[:max_batches]
    return batches


def _init_recursive_environment() -> Dict[str, List[str]]:
    """Initializes the recursive environment accumulator.

    Returns:
        Empty environment dictionary for accumulating batch results.
    """
    return {
        "emotional_triggers": [],
        "viral_formula": [],
        "audience_persona": [],
        "content_hooks": [],
        "opportunities": [],
        "risks": [],
        "summary": [],
    }


def _build_batch_payload(
    *,
    batch_index: int,
    batch_total: int,
    environment: Dict[str, Any],
    evidence_snapshot: Dict[str, Any],
    comment_batch: List[Dict[str, Any]],
    include_environment: bool,
) -> Dict[str, Any]:
    """Builds the payload for a single recursive batch.

    Args:
        batch_index: Current batch index.
        batch_total: Total number of batches.
        environment: Running environment state.
        evidence_snapshot: Condensed evidence snapshot.
        comment_batch: Current comment batch.
        include_environment: Includes environment history when ``True``.

    Returns:
        Payload dictionary for the recursive prompt.
    """
    return {
        "batch_index": batch_index,
        "batch_total": batch_total,
        "environment": environment if include_environment else {},
        "evidence_snapshot": evidence_snapshot,
        "comment_batch": comment_batch,
    }


def _run_section_prompts(
    *,
    llm_client: LLMClient,
    system_prompt: str,
    section_prompts: Dict[str, str],
    user_payload: Dict[str, Any],
    model: Optional[str],
    batch_index: int,
) -> Dict[str, str]:
    """Runs all section prompts for a single batch.

    Args:
        llm_client: LLM client instance.
        system_prompt: System prompt for the LLM.
        section_prompts: Mapping of section key to prompt.
        user_payload: Payload for the user prompt.
        model: Optional model override.
        batch_index: Current batch index for logging.

    Returns:
        Mapping of section key to response text.
    """
    batch_result: Dict[str, str] = {}
    for key, prompt in section_prompts.items():
        user_prompt = (
            f"{prompt}\n\nData komentar:\n{build_recursive_user_prompt(user_payload)}"
        )
        try:
            text = llm_client.chat_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
            )
            batch_result[key] = str(text).strip()
        except RuntimeError as err:
            logger.warning("LLM viral insight batch %d [%s] failed: %s", batch_index, key, err)
            batch_result[key] = "Tidak ada"
    return batch_result


def _accumulate_environment(
    environment: Dict[str, List[str]], batch_result: Dict[str, str]
) -> None:
    """Appends batch results into the recursive environment.

    Args:
        environment: Running environment state.
        batch_result: Batch outputs keyed by section.
    """
    for key in environment:
        environment[key].append(batch_result.get(key, ""))


def _build_section_labels() -> Dict[str, str]:
    """Returns section labels for final synthesis output.

    Returns:
        Mapping of section key to display label.
    """
    return {
        "emotional_triggers": "PEMICU EMOSI UTAMA",
        "viral_formula": "FORMULA VIRAL",
        "audience_persona": "PERSONA AUDIENS",
        "content_hooks": "HOOK & FRASA KUNCI",
        "opportunities": "PELUANG KONTEN",
        "risks": "RISIKO",
        "summary": "RINGKASAN EKSEKUTIF",
    }


def _synthesize_recursive_insights(
    *,
    llm_client: LLMClient,
    system_prompt: str,
    section_labels: Dict[str, str],
    environment: Dict[str, List[str]],
    model: Optional[str],
) -> Dict[str, str]:
    """Synthesizes batch insights into final per-section summaries.

    Args:
        llm_client: LLM client instance.
        system_prompt: System prompt for the LLM.
        section_labels: Mapping of section key to display label.
        environment: Running environment state.
        model: Optional model override.

    Returns:
        Mapping of section key to synthesized insight text.
    """
    final_insights: Dict[str, str] = {}
    for key, label in section_labels.items():
        raw_parts = [p for p in environment.get(key, []) if p and p != "Tidak ada"]
        if not raw_parts:
            final_insights[key] = "Tidak ada"
            continue

        accumulated = "\n\n".join(
            f"[Batch {i + 1}]\n{part}" for i, part in enumerate(raw_parts)
        )
        synthesis_prompt = (
            hard_rules()
            + f"\nBerikut insight '{label}' dari {len(raw_parts)} batch analisis komentar:\n\n"
            f"{accumulated}\n\n"
            f"Sintesiskan semua insight di atas menjadi SATU laporan final '{label}' "
            f"yang kohesif, tanpa pengulangan, tajam, dan langsung actionable. "
            f"Buang informasi redundan. Prioritaskan insight paling kuat dan spesifik."
        )
        try:
            synthesized = llm_client.chat_text(
                system_prompt=system_prompt,
                user_prompt=synthesis_prompt,
                model=model,
            )
            final_insights[key] = str(synthesized).strip()
        except RuntimeError as err:
            logger.warning("LLM synthesis failed for [%s]: %s", key, err)
            final_insights[key] = accumulated
    return final_insights


def _combine_sections(
    section_labels: Dict[str, str],
    final_insights: Dict[str, str],
) -> str:
    """Combines section results into a single formatted string.

    Args:
        section_labels: Mapping of section key to display label.
        final_insights: Mapping of section key to synthesized text.

    Returns:
        Combined formatted text block.
    """
    return "\n\n".join(
        f"{'=' * 60}\n{label}\n{'=' * 60}\n{final_insights.get(key, 'Tidak ada')}"
        for key, label in section_labels.items()
    )


def _generate_suggested_topics(
    *,
    llm_client: LLMClient,
    system_prompt: str,
    insights: Dict[str, Any],
    model: Optional[str],
) -> str:
    """Generates title-only suggested topics from existing insights."""
    prompt = build_suggested_topics_prompt()
    context = build_recursive_user_prompt({"insights": insights})
    user_prompt = f"{prompt}\n\nRingkasan insight:\n{context}"
    try:
        text = llm_client.chat_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
        )
        return _clean_suggested_topics(text)
    except Exception as err:
        logger.warning("Suggested topic generation failed: %s", err)
        return "Tidak ada"


def _clean_suggested_topics(text: str) -> str:
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    cleaned: List[str] = []
    for line in lines:
        if line.startswith(("-", "*")):
            line = line.lstrip("-* ").strip()
        if line and line[0].isdigit():
            line = line.lstrip("0123456789. )").strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned) if cleaned else "Tidak ada"
