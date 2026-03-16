from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv

# Ensure both repo root and src are available for mixed import styles.
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _path in (str(_ROOT), str(_SRC)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from agents.EDA.eda_agent import EDAConfig, run_eda
from agents.sentiment.sentiment_agent import SentimentAgentConfig, run_sentiment_agent
from agents.spam.spam_agent import SpamAgentConfig, run_spam_agent
from agents.toxicity.toxic_agent import ToxicAgentConfig, run_toxic_agent
from agents.topic.topic_agent import TopicAgentConfig, run_topic_agent
from pipeline.evidence import (
    EvidenceMergeConfig,
    merge_evidence_and_insights,
    save_split_outputs,
)
from services.comment_scrapper import fetch_video_metadata, fetch_youtube_comments
from utils.logger import get_logger
from utils.youtube_url_normalizer import extract_video_id

logger = get_logger(__name__)

# Load environment variables from .env if present.
load_dotenv()


def _resolve_api_key(api_key: Optional[str]) -> str:
    if api_key:
        return api_key
    for key_name in ("YOUTUBE_API_KEY", "GOOGLE_API_KEY", "API_KEY"):
        value = os.getenv(key_name)
        if value:
            return value
    raise ValueError("Missing API key. Set YOUTUBE_API_KEY or pass --api-key.")


def _anonymize_authors(comments: List[Dict[str, Any]]) -> Dict[str, str]:
    authors = sorted({str(item.get("author") or "").strip() for item in comments if item.get("author")})
    mapping = {author: f"user_{idx + 1}" for idx, author in enumerate(authors)}
    for item in comments:
        author = str(item.get("author") or "").strip()
        if author in mapping:
            item["author"] = mapping[author]
    return mapping


def _attach_comment_ids(comments: List[Dict[str, Any]]) -> None:
    for idx, item in enumerate(comments):
        if not item.get("comment_id"):
            item["comment_id"] = f"row_{idx}"


def _collect_video_inputs(args: argparse.Namespace) -> List[str]:
    if args.videos:
        return [item.strip() for item in args.videos.split(",") if item.strip()]
    if args.videos_file:
        with open(args.videos_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return [args.video]


def _apply_video_metadata(
    comments: List[Dict[str, Any]],
    *,
    video_id: str,
    metadata: Dict[str, Any],
) -> None:
    for item in comments:
        item["video_id"] = video_id
        item["video_title"] = metadata.get("video_title")
        item["video_description"] = metadata.get("video_description")


def _prepare_comments(
    *,
    comments: List[Dict[str, Any]],
    video_id: str,
    metadata: Dict[str, Any],
    anonymize_authors: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    _apply_video_metadata(comments, video_id=video_id, metadata=metadata)
    mapping = _anonymize_authors(comments) if anonymize_authors else {}
    _attach_comment_ids(comments)
    return comments, mapping


def _apply_topic_overrides(
    *,
    base_config: Optional[TopicAgentConfig],
    topic_with_llm: bool,
    llm_model: Optional[str],
    llm_base_url: Optional[str],
    llm_provider: Optional[str],
    llm_api_key: Optional[str],
    llm_api_base_url: Optional[str],
) -> TopicAgentConfig:
    cfg = base_config or TopicAgentConfig(generate_topic_with_llm=topic_with_llm)
    cfg.generate_topic_with_llm = topic_with_llm
    if llm_model:
        cfg.llm_model = llm_model
    if llm_base_url:
        cfg.llm_base_url = llm_base_url
    if llm_provider:
        cfg.llm_provider = llm_provider
    if llm_api_key:
        cfg.llm_api_key = llm_api_key
    if llm_api_base_url:
        cfg.llm_api_base_url = llm_api_base_url
    return cfg


def _apply_llm_overrides(
    *,
    base_config: Optional[EvidenceMergeConfig],
    llm_model: Optional[str],
    llm_base_url: Optional[str],
    llm_provider: Optional[str],
    llm_api_key: Optional[str],
    llm_api_base_url: Optional[str],
    llm_timeout_seconds: Optional[int],
    llm_batch_size: Optional[int],
    llm_comment_limit: Optional[int],
    llm_simple_mode: Optional[bool],
    llm_enabled: bool,
) -> EvidenceMergeConfig:
    cfg = base_config or EvidenceMergeConfig()
    if llm_model:
        cfg.llm_model = llm_model
    if llm_base_url:
        cfg.llm_base_url = llm_base_url
    if llm_provider:
        cfg.llm_provider = llm_provider
    if llm_api_key:
        cfg.llm_api_key = llm_api_key
    if llm_api_base_url:
        cfg.llm_api_base_url = llm_api_base_url
    if llm_timeout_seconds:
        cfg.llm_timeout_seconds = llm_timeout_seconds
    if llm_simple_mode is None:
        llm_simple_mode = _infer_small_model(llm_model)
    cfg.llm_simple_mode = bool(llm_simple_mode)
    cfg.llm_enabled = llm_enabled
    if llm_batch_size:
        cfg.llm_batch_size = llm_batch_size
    if llm_comment_limit:
        cfg.comment_sample_limit = llm_comment_limit
    return cfg


def _build_video_payload(video_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "video_id": video_id,
        "video_title": metadata.get("video_title"),
        "video_description": metadata.get("video_description"),
    }


def _build_payload(
    *,
    video_payload: Dict[str, Any],
    comments: List[Dict[str, Any]],
    mapping: Dict[str, str],
    anonymize_authors: bool,
    eda_result: Dict[str, Any],
    spam_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
    topic_result: Dict[str, Any],
    merged: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "video": video_payload,
        "run_metadata": {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_comments": int(len(comments)),
            "anonymized": anonymize_authors,
        },
        "author_mapping": mapping,
        "comments": comments,
        "eda": eda_result,
        "spam": spam_result,
        "sentiment": sentiment_result,
        "toxicity": toxic_result,
        "topics": topic_result,
        "evidence": merged.get("evidence_snapshot"),
        "llm_insights": merged.get("llm_insights"),
    }


def _save_payload(
    *,
    payload: Dict[str, Any],
    output_dir: str,
    output_json_name: Optional[str],
    video_id: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    if not output_json_name:
        output_json_name = f"orchestrator_{video_id}.json"
    output_path = os.path.join(output_dir, output_json_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    return output_path


def run_orchestrator(
    *,
    video_input: str,
    api_key: Optional[str] = None,
    output_dir: str = "outputs",
    output_json_name: Optional[str] = None,
    anonymize_authors: bool = True,
    topic_with_llm: bool = True,
    llm_model: Optional[str] = None,
    llm_base_url: Optional[str] = None,
    llm_enabled: bool = True,
    llm_batch_size: Optional[int] = None,
    llm_comment_limit: Optional[int] = None,
    llm_include_history: Optional[bool] = None,
    llm_timeout_seconds: Optional[int] = None,
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_api_base_url: Optional[str] = None,
    llm_simple_mode: Optional[bool] = None,
    llm_insight_config: Optional[EvidenceMergeConfig] = None,
    save_split_outputs_flag: bool = True,
    eda_config: Optional[EDAConfig] = None,
    spam_config: Optional[SpamAgentConfig] = None,
    sentiment_config: Optional[SentimentAgentConfig] = None,
    toxic_config: Optional[ToxicAgentConfig] = None,
    topic_config: Optional[TopicAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs the full pipeline: scrape -> EDA -> spam -> sentiment -> toxicity -> topic.

    Args:
        video_input: YouTube video URL or video ID.
        api_key: YouTube Data API key; defaults to env vars if None.
        output_dir: Output directory for the merged JSON payload.
        output_json_name: Optional output file name.
        anonymize_authors: Masks author names when True.
        topic_with_llm: Enables LLM topic labeling when True.
        llm_insight_config: Optional configuration for LLM insight generation.
        save_split_outputs_flag: Writes evidence/insights as separate JSON files.
        eda_config: Optional EDA configuration.
        spam_config: Optional spam-agent configuration.
        sentiment_config: Optional sentiment-agent configuration.
        toxic_config: Optional toxic-agent configuration.
        topic_config: Optional topic-agent configuration.

    Returns:
        Full pipeline payload including evidence and LLM insights.

    Example usage:
        >>> result = run_orchestrator(video_input=\"dQw4w9WgXcQ\", api_key=\"KEY\")
        >>> \"eda\" in result
        True
    """
    resolved_key = _resolve_api_key(api_key)
    video_id = extract_video_id(video_input)

    logger.info("Scraping comments for video_id=%s", video_id)
    metadata = fetch_video_metadata(resolved_key, video_id)
    comments = fetch_youtube_comments(resolved_key, video_id)

    comments, mapping = _prepare_comments(
        comments=comments,
        video_id=video_id,
        metadata=metadata,
        anonymize_authors=anonymize_authors,
    )

    df = pd.DataFrame(comments)

    logger.info("Running EDA")
    eda_result = run_eda(df, config=eda_config)

    logger.info("Running spam detection")
    spam_result = run_spam_agent(df, config=spam_config)

    logger.info("Running sentiment analysis")
    sentiment_result = run_sentiment_agent(df, config=sentiment_config)

    logger.info("Running toxicity analysis")
    toxic_result = run_toxic_agent(df, config=toxic_config)

    logger.info("Running topic discovery")
    topic_cfg = _apply_topic_overrides(
        base_config=topic_config,
        topic_with_llm=topic_with_llm,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_api_base_url=llm_api_base_url,
    )
    topic_result = run_topic_agent(df, config=topic_cfg)

    llm_cfg = _apply_llm_overrides(
        base_config=llm_insight_config,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_api_base_url=llm_api_base_url,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_batch_size=llm_batch_size,
        llm_comment_limit=llm_comment_limit,
        llm_simple_mode=llm_simple_mode,
        llm_enabled=llm_enabled,
    )

    recursive_config = None
    if llm_include_history is not None:
        from pipeline.evidence import RecursiveInsightConfig

        recursive_config = RecursiveInsightConfig(include_environment_history=llm_include_history)

    video_payload = _build_video_payload(video_id, metadata)
    merged = merge_evidence_and_insights(
        video=video_payload,
        comments=comments,
        eda_result=eda_result,
        spam_result=spam_result,
        sentiment_result=sentiment_result,
        toxic_result=toxic_result,
        topic_result=topic_result,
        config=llm_cfg,
        recursive_config=recursive_config,
    )

    payload = _build_payload(
        video_payload=video_payload,
        comments=comments,
        mapping=mapping,
        anonymize_authors=anonymize_authors,
        eda_result=eda_result,
        spam_result=spam_result,
        sentiment_result=sentiment_result,
        toxic_result=toxic_result,
        topic_result=topic_result,
        merged=merged,
    )

    output_path = _save_payload(
        payload=payload,
        output_dir=output_dir,
        output_json_name=output_json_name,
        video_id=video_id,
    )

    logger.info("Pipeline output saved: %s", output_path)

    if save_split_outputs_flag:
        save_split_outputs(
            evidence_snapshot=payload.get("evidence") or {},
            llm_insights=payload.get("llm_insights") or {},
            output_dir=output_dir,
            evidence_filename=f"evidence_{video_id}.json",
            insights_filename=f"llm_insights_{video_id}.json",
        )
    return payload


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run comment analytics orchestrator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--video", help="YouTube video URL or ID")
    group.add_argument("--videos", help="Comma-separated YouTube video URLs or IDs")
    group.add_argument("--videos-file", help="Text file with one YouTube URL/ID per line")
    parser.add_argument("--api-key", default=None, help="YouTube Data API key")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--output-json", default=None, help="Output JSON file name")
    parser.add_argument("--no-anonymize", action="store_true", help="Disable author anonymization")
    parser.add_argument("--topic-no-llm", action="store_true", help="Disable LLM topic labeling")
    parser.add_argument("--llm-disable", action="store_true", help="Disable LLM insights")
    parser.add_argument("--llm-model", default=None, help="Ollama model name (e.g. llama3.1:8b)")
    parser.add_argument("--llm-base-url", default=None, help="Ollama base URL")
    parser.add_argument(
        "--llm-provider",
        default=None,
        help="LLM provider: ollama, openai_compatible, or gemini",
    )
    parser.add_argument("--llm-api-key", default=None, help="API key for OpenAI-compatible provider")
    parser.add_argument("--llm-api-base-url", default=None, help="Base URL for OpenAI-compatible provider")
    parser.add_argument("--llm-batch-size", type=int, default=None, help="LLM batch size")
    parser.add_argument("--llm-comment-limit", type=int, default=None, help="LLM comment sample limit")
    parser.add_argument("--llm-no-history", action="store_true", help="Disable LLM environment history")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--llm-simple", action="store_true", help="Use simple (non-recursive) LLM insights")
    mode_group.add_argument("--llm-recursive", action="store_true", help="Use recursive LLM insights")
    parser.add_argument("--llm-timeout", type=int, default=None, help="LLM request timeout in seconds")
    parser.add_argument("--no-split-outputs", action="store_true", help="Disable split outputs")
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    video_inputs = _collect_video_inputs(args)

    for video_input in video_inputs:
        run_orchestrator(
            video_input=video_input,
            api_key=args.api_key,
            output_dir=args.output_dir,
            output_json_name=args.output_json,
            anonymize_authors=not args.no_anonymize,
            topic_with_llm=not args.topic_no_llm,
            llm_model=args.llm_model or os.getenv("OLLAMA_MODEL"),
            llm_base_url=args.llm_base_url or os.getenv("OLLAMA_BASE_URL"),
            llm_provider=args.llm_provider or os.getenv("LLM_PROVIDER"),
            llm_api_key=args.llm_api_key or os.getenv("LLM_API_KEY"),
            llm_api_base_url=args.llm_api_base_url or os.getenv("LLM_API_BASE_URL"),
            llm_enabled=not args.llm_disable,
            llm_batch_size=args.llm_batch_size,
            llm_comment_limit=args.llm_comment_limit,
            llm_include_history=not args.llm_no_history,
            llm_simple_mode=(
                True if args.llm_simple else (False if args.llm_recursive else None)
            ),
            llm_timeout_seconds=args.llm_timeout
            or (int(os.getenv("OLLAMA_TIMEOUT", "0")) or None),
            save_split_outputs_flag=not args.no_split_outputs,
        )


def _infer_small_model(model_name: Optional[str]) -> bool:
    if not model_name:
        return False
    lowered = model_name.lower()
    return any(token in lowered for token in ("0.5b", "1b", "mini", "small"))


if __name__ == "__main__":
    main()
