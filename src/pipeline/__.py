# from __future__ import annotations
# import json
# import os
# from dataclasses import dataclass
# from typing import Any, Dict, Iterable, List, Optional
# from llm.generation_config import OllamaGenerationConfig
# from llm.ollama_client import LLMClient, chunk_list
# from utils.logger import get_logger

# logger = get_logger(__name__)


# def _safe_int(value: Any, default: int = 0) -> int:
#     try:
#         return int(value)
#     except (TypeError, ValueError):
#         return default


# def _take_top(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
#     if limit <= 0:
#         return []
#     return items[:limit]


# @dataclass
# class EvidenceMergeConfig:
#     """Controls evidence reduction and LLM batching.

#     Attributes:
#         top_spam_examples: Maximum spam examples passed to LLM.
#         top_sentiment_highlights: Highlights per sentiment label.
#         top_toxic_examples: Maximum toxic examples passed to LLM.
#         top_topic_clusters: Maximum topic clusters passed to LLM.
#         comment_sample_limit: Cap on merged comments for LLM batches.
#         llm_enabled: Enables or disables LLM insight generation.
#         llm_batch_size: Comments per LLM batch.
#         llm_model: Optional model override for Ollama.
#         llm_base_url: Ollama base URL.
#         llm_timeout_seconds: Request timeout for Ollama.

#     Example usage:
#         >>> cfg = EvidenceMergeConfig(llm_batch_size=80, comment_sample_limit=200)
#         >>> cfg.llm_batch_size
#         80
#     """

#     top_spam_examples: int = 8
#     top_sentiment_highlights: int = 5
#     top_toxic_examples: int = 8
#     top_topic_clusters: int = 10
#     comment_sample_limit: int = 120
#     llm_enabled: bool = True
#     llm_batch_size: int = 60
#     llm_model: Optional[str] = None
#     llm_base_url: str = "http://localhost:11434"
#     llm_provider: str = "ollama"
#     llm_api_key: Optional[str] = None
#     llm_api_base_url: Optional[str] = None
#     llm_timeout_seconds: int = 120
#     llm_simple_mode: bool = False


# @dataclass
# class RecursiveInsightConfig:
#     """Controls recursive insight extraction prompt flow.

#     Attributes:
#         max_batches: Upper limit on processed batches.
#         include_environment_history: Includes prior environment state in prompts.

#     Example usage:
#         >>> cfg = RecursiveInsightConfig(max_batches=5)
#         >>> cfg.max_batches
#         5
#     """

#     max_batches: int = 20
#     include_environment_history: bool = True


# def build_comment_records(
#     comments: List[Dict[str, Any]],
#     spam_result: Dict[str, Any],
#     sentiment_result: Dict[str, Any],
#     toxic_result: Dict[str, Any],
#     *,
#     limit: int,
# ) -> List[Dict[str, Any]]:
#     """Merges per-comment signals from multiple agents for LLM processing.

#     Args:
#         comments: Raw comment records from the scraper.
#         spam_result: Output from spam agent.
#         sentiment_result: Output from sentiment agent.
#         toxic_result: Output from toxicity agent.
#         limit: Maximum number of merged records returned.

#     Returns:
#         List of merged comment records with spam/sentiment/toxicity signals.

#     Example usage:
#         >>> merged = build_comment_records([], {}, {}, {}, limit=10)
#         >>> isinstance(merged, list)
#         True
#     """
#     spam_map = {item.get("comment_id"): item for item in spam_result.get("results", [])}
#     sentiment_map = {
#         item.get("comment_id"): item for item in sentiment_result.get("comment_level", [])
#     }
#     toxic_map = {item.get("comment_id"): item for item in toxic_result.get("comment_level", [])}

#     merged: List[Dict[str, Any]] = []
#     for item in comments:
#         comment_id = item.get("comment_id")
#         spam_item = spam_map.get(comment_id, {})
#         sentiment_item = sentiment_map.get(comment_id, {})
#         toxic_item = toxic_map.get(comment_id, {})

#         merged.append(
#             {
#                 "comment_id": comment_id,
#                 "text": item.get("text"),
#                 "author": item.get("author"),
#                 "published_at": item.get("published_at"),
#                 "like_count": _safe_int(item.get("like_count"), 0),
#                 "spam": {
#                     "label": spam_item.get("label"),
#                     "score": spam_item.get("spam_score"),
#                     "reason": spam_item.get("reason"),
#                 },
#                 "sentiment": {
#                     "label": sentiment_item.get("sentiment"),
#                     "confidence": sentiment_item.get("confidence"),
#                     "scores": sentiment_item.get("scores"),
#                 },
#                 "toxicity": {
#                     "label": toxic_item.get("toxicity_label"),
#                     "score": toxic_item.get("toxicity_score"),
#                     "flag": toxic_item.get("flag"),
#                     "categories": toxic_item.get("category_scores"),
#                 },
#             }
#         )

#         if limit and len(merged) >= limit:
#             break

#     return merged


# def build_evidence_snapshot(
#     *,
#     video: Dict[str, Any],
#     comments_total: int,
#     eda_result: Dict[str, Any],
#     spam_result: Dict[str, Any],
#     sentiment_result: Dict[str, Any],
#     toxic_result: Dict[str, Any],
#     topic_result: Dict[str, Any],
#     config: EvidenceMergeConfig,
# ) -> Dict[str, Any]:
#     """Reduces agent outputs into a compact evidence snapshot for LLM prompts.

#     Args:
#         video: Video metadata dictionary.
#         comments_total: Total number of scraped comments.
#         eda_result: EDA agent output.
#         spam_result: Spam agent output.
#         sentiment_result: Sentiment agent output.
#         toxic_result: Toxicity agent output.
#         topic_result: Topic agent output.
#         config: Evidence merge configuration.

#     Returns:
#         Condensed evidence dictionary for LLM analysis.

#     Example usage:
#         >>> snapshot = build_evidence_snapshot(
#         ...     video={},
#         ...     comments_total=0,
#         ...     eda_result={},
#         ...     spam_result={},
#         ...     sentiment_result={},
#         ...     toxic_result={},
#         ...     topic_result={},
#         ...     config=EvidenceMergeConfig(),
#         ... )
#         >>> "eda" in snapshot
#         True
#     """
#     spam_examples = _take_top(spam_result.get("results", []), config.top_spam_examples)
#     sentiment_highlights = sentiment_result.get("highlights", {}) or {}
#     toxicity_examples = _take_top(
#         toxic_result.get("top_toxic_comments", []), config.top_toxic_examples
#     )
#     topic_clusters = _take_top(topic_result.get("clusters", []), config.top_topic_clusters)

#     return {
#         "video": video,
#         "comment_totals": {
#             "total_comments": int(comments_total),
#             "spam_comments": int(spam_result.get("spam_comments", 0)),
#             "toxic_comments": int(
#                 toxic_result.get("summary", {}).get("toxic_comments", 0)
#             ),
#         },
#         "eda": {
#             "total_comments": eda_result.get("total_comments"),
#             "volume_temporal_analysis": eda_result.get("volume_temporal_analysis"),
#             "engagement_analysis": eda_result.get("engagement_analysis"),
#             "text_statistics": eda_result.get("text_statistics"),
#         },
#         "spam": {
#             "summary": {
#                 "total_comments": spam_result.get("total_comments"),
#                 "spam_comments": spam_result.get("spam_comments"),
#                 "spam_ratio": spam_result.get("spam_ratio"),
#             },
#             "top_examples": spam_examples,
#         },
#         "sentiment": {
#             "summary": {
#                 "total_comments": sentiment_result.get("total_comments"),
#                 "distribution": sentiment_result.get("distribution"),
#                 "video_sentiment": sentiment_result.get("video_sentiment"),
#                 "sentiment_score": sentiment_result.get("sentiment_score"),
#                 "toxicity_integration": sentiment_result.get("toxicity_integration"),
#             },
#             "highlights": {
#                 "positive": _take_top(
#                     sentiment_highlights.get("positive", []),
#                     config.top_sentiment_highlights,
#                 ),
#                 "neutral": _take_top(
#                     sentiment_highlights.get("neutral", []),
#                     config.top_sentiment_highlights,
#                 ),
#                 "negative": _take_top(
#                     sentiment_highlights.get("negative", []),
#                     config.top_sentiment_highlights,
#                 ),
#             },
#         },
#         "toxicity": {
#             "summary": toxic_result.get("summary"),
#             "categories": toxic_result.get("categories"),
#             "top_examples": toxicity_examples,
#         },
#         "topics": {
#             "cluster_summary": topic_result.get("cluster_summary"),
#             "clusters": topic_clusters,
#         },
#     }


# def _build_system_prompt() -> str:
#     return (
#         "Anda adalah agen analisis. Tugas Anda mengekstrak insight dari bukti terstruktur"
#         " yang dihasilkan oleh agen analitik. Gunakan konteks environment sebagai memori"
#         " berjalan. Gunakan Bahasa Indonesia. "
#         "Jawab dengan teks biasa, tanpa JSON atau markdown."
#     )


# def _build_recursive_user_prompt(payload: Dict[str, Any]) -> str:
#     return json.dumps(payload, ensure_ascii=False, indent=2)


# def run_recursive_llm_insights(
#     *,
#     evidence_snapshot: Dict[str, Any],
#     comment_records: List[Dict[str, Any]],
#     llm_client: LLMClient,
#     config: EvidenceMergeConfig,
#     recursive_config: Optional[RecursiveInsightConfig] = None,
# ) -> Dict[str, Any]:
#     """Runs recursive LLM batch analysis using environment-style prompts.

#     Args:
#         evidence_snapshot: Condensed evidence payload.
#         comment_records: Merged comment records to analyze.
#         llm_client: LLM client for inference.
#         config: Evidence merge configuration.
#         recursive_config: Recursive prompt configuration.

#     Returns:
#         Dictionary containing environment state and batch outputs.

#     Example usage:
#         >>> result = run_recursive_llm_insights(
#         ...     evidence_snapshot={},
#         ...     comment_records=[],
#         ...     llm_client=OllamaClient(OllamaGenerationConfig()),
#         ...     config=EvidenceMergeConfig(llm_enabled=False),
#         ... )
#         >>> "batch_outputs" in result
#         True
#     """
#     r_cfg = recursive_config or RecursiveInsightConfig()
#     batches = chunk_list(comment_records, config.llm_batch_size)
#     if r_cfg.max_batches and len(batches) > r_cfg.max_batches:
#         batches = batches[: r_cfg.max_batches]

#     environment: Dict[str, Any] = {
#         "insights": [],
#         "risks": [],
#         "opportunities": [],
#         "anomalies": [],
#         "open_questions": [],
#     }

#     batch_outputs: List[Dict[str, Any]] = []
#     system_prompt = _build_system_prompt()

#     for idx, batch in enumerate(batches, start=1):
#         user_payload = {
#             "batch_index": idx,
#             "batch_total": len(batches),
#             "environment": environment if r_cfg.include_environment_history else {},
#             "evidence_snapshot": evidence_snapshot,
#             "comment_batch": batch,
#         }

#         section_prompts = {
#             "summary": "Berikan ringkasan batch ini (2-4 kalimat).",
#             "insights": "Tuliskan 5-8 insight utama dalam poin singkat.",
#             "risks": "Tuliskan risiko utama (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#             "opportunities": "Tuliskan peluang/aksi yang bisa dilakukan (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#             "anomalies": "Tuliskan anomali/pola tidak biasa (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#             "open_questions": "Tuliskan pertanyaan terbuka (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#         }

#         batch_result: Dict[str, str] = {}
#         for key, prompt in section_prompts.items():
#             user_prompt = (
#                 f"{prompt}\n\nKonteks:\n{_build_recursive_user_prompt(user_payload)}"
#             )
#             try:
#                 text = llm_client.chat(
#                     system_prompt=system_prompt,
#                     user_prompt=user_prompt,
#                     model=config.llm_model,
#                 )
#                 # In case a JSON-ish object is returned, stringify it.
#                 if isinstance(text, dict):
#                     text = json.dumps(text, ensure_ascii=False)
#                 batch_result[key] = str(text).strip()
#             except RuntimeError as err:
#                 logger.warning("LLM insight batch failed: %s", err)
#                 batch_result[key] = "Tidak ada"

#         # Update running environment by simple concatenation.
#         environment["insights"].append(batch_result.get("insights", ""))
#         environment["risks"].append(batch_result.get("risks", ""))
#         environment["opportunities"].append(batch_result.get("opportunities", ""))
#         environment["anomalies"].append(batch_result.get("anomalies", ""))
#         environment["open_questions"].append(batch_result.get("open_questions", ""))

#         batch_outputs.append(batch_result)

#     combined = "\n\n".join(
#         f"BATCH {i+1}:\n"
#         f"SUMMARY:\n{b.get('summary','')}\n\n"
#         f"INSIGHTS:\n{b.get('insights','')}\n\n"
#         f"RISKS:\n{b.get('risks','')}\n\n"
#         f"OPPORTUNITIES:\n{b.get('opportunities','')}\n\n"
#         f"ANOMALIES:\n{b.get('anomalies','')}\n\n"
#         f"OPEN QUESTIONS:\n{b.get('open_questions','')}"
#         for i, b in enumerate(batch_outputs)
#     )

#     return {
#         "available": True,
#         "batch_count": len(batches),
#         "environment": environment,
#         "batch_outputs": batch_outputs,
#         "combined": combined,
#     }


# def generate_llm_insights(
#     *,
#     evidence_snapshot: Dict[str, Any],
#     comment_records: List[Dict[str, Any]],
#     config: EvidenceMergeConfig,
#     recursive_config: Optional[RecursiveInsightConfig] = None,
# ) -> Dict[str, Any]:
#     """Creates LLM insight report if enabled and server is reachable.

#     Args:
#         evidence_snapshot: Condensed evidence payload.
#         comment_records: Merged comment records to analyze.
#         config: Evidence merge configuration.

#     Returns:
#         LLM insight payload with availability status.

#     Example usage:
#         >>> out = generate_llm_insights(
#         ...     evidence_snapshot={},
#         ...     comment_records=[],
#         ...     config=EvidenceMergeConfig(llm_enabled=False),
#         ... )
#         >>> out["available"]
#         False
#     """
#     if not config.llm_enabled:
#         return {"available": False, "reason": "llm_disabled"}

#     client = LLMClient(
#         OllamaGenerationConfig(
#             model=config.llm_model or "llama3.1:8b",
#             provider=config.llm_provider,
#             base_url=config.llm_base_url,
#             api_key=config.llm_api_key,
#             api_base_url=config.llm_api_base_url,
#             timeout_seconds=config.llm_timeout_seconds,
#         )
#     )

#     if not client.health_check():
#         return {"available": False, "reason": "llm_unreachable"}

#     if config.llm_simple_mode:
#         return run_simple_llm_insights(
#             evidence_snapshot=evidence_snapshot,
#             comment_records=comment_records,
#             config=config,
#         )

#     return run_recursive_llm_insights(
#         evidence_snapshot=evidence_snapshot,
#         comment_records=comment_records,
#         llm_client=client,
#         config=config,
#         recursive_config=recursive_config,
#     )


# def run_simple_llm_insights(
#     *,
#     evidence_snapshot: Dict[str, Any],
#     comment_records: List[Dict[str, Any]],
#     config: EvidenceMergeConfig,
# ) -> Dict[str, Any]:
#     """Runs a single-pass LLM insight prompt (no recursive environment)."""
#     system_prompt = (
#         "Anda adalah analis komentar. Gunakan Bahasa Indonesia. "
#         "Jawab sesuai permintaan bagian, tanpa JSON atau markdown."
#     )
#     base_payload = {
#         "evidence_snapshot": evidence_snapshot,
#         "comment_samples": comment_records[: config.comment_sample_limit],
#     }
#     base_context = json.dumps(base_payload, ensure_ascii=False, indent=2)

#     section_prompts = {
#         "summary": "Berikan ringkasan singkat (2-4 kalimat).",
#         "insights": "Tuliskan 3-5 insight utama dalam bentuk bullet atau kalimat singkat.",
#         "risks": "Tuliskan risiko utama (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#         "opportunities": "Tuliskan peluang/aksi yang bisa dilakukan (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#         "anomalies": "Tuliskan anomali/pola tidak biasa (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#         "open_questions": "Tuliskan pertanyaan terbuka (jika ada). Jika tidak ada, tulis 'Tidak ada'.",
#     }

#     responses: Dict[str, str] = {}
#     try:
#         from llm.langchain_client import langchain_chat_text

#         cfg = OllamaGenerationConfig(
#             model=config.llm_model or "llama3.1:8b",
#             provider=config.llm_provider,
#             base_url=config.llm_base_url,
#             api_key=config.llm_api_key,
#             api_base_url=config.llm_api_base_url,
#             timeout_seconds=config.llm_timeout_seconds,
#         )
#         for key, prompt in section_prompts.items():
#             user_prompt = f"{prompt}\n\nKonteks:\n{base_context}"
#             responses[key] = langchain_chat_text(
#                 system_prompt=system_prompt,
#                 user_prompt=user_prompt,
#                 config=cfg,
#             ).strip()
#     except Exception as err:
#         logger.warning("LangChain simple LLM failed; using fallback insights: %s", err)
#         fallback = _fallback_simple_insights(evidence_snapshot, comment_records)
#         fallback["raw"] = {}
#         return fallback

#     combined = "\n\n".join(f"{k.upper()}:\n{v}" for k, v in responses.items())
#     return {
#         "available": True,
#         "mode": "simple_sections",
#         "summary": responses.get("summary"),
#         "insights": responses.get("insights"),
#         "risks": responses.get("risks"),
#         "opportunities": responses.get("opportunities"),
#         "anomalies": responses.get("anomalies"),
#         "open_questions": responses.get("open_questions"),
#         "combined": combined,
#         "raw": responses,
#     }


# def _fallback_simple_insights(
#     evidence_snapshot: Dict[str, Any],
#     comment_records: List[Dict[str, Any]],
# ) -> Dict[str, Any]:
#     comment_totals = evidence_snapshot.get("comment_totals", {})
#     topics = evidence_snapshot.get("topics", {})
#     clusters = topics.get("clusters", []) or []
#     top_topics = []
#     for item in clusters[:3]:
#         keywords = item.get("lda_keywords", []) or []
#         if keywords:
#             top_topics.append(", ".join(keywords[:3]))

#     summary_parts = [
#         f"Total komentar: {comment_totals.get('total_comments', 0)}",
#         f"Spam terdeteksi: {comment_totals.get('spam_comments', 0)}",
#         f"Toxic terdeteksi: {comment_totals.get('toxic_comments', 0)}",
#     ]
#     summary = ". ".join(summary_parts) + "."

#     insights = []
#     if top_topics:
#         insights.append(f"Topik dominan berdasarkan LDA: {', '.join(top_topics)}.")
#     if comment_records:
#         insights.append("Komentar sampel menunjukkan variasi sentimen dan reaksi emosional.")

#     return {
#         "available": True,
#         "mode": "simple_fallback",
#         "summary": summary,
#         "insights": insights,
#         "risks": [],
#         "opportunities": [],
#         "anomalies": [],
#         "open_questions": [],
#     }


# def merge_evidence_and_insights(
#     *,
#     video: Dict[str, Any],
#     comments: List[Dict[str, Any]],
#     eda_result: Dict[str, Any],
#     spam_result: Dict[str, Any],
#     sentiment_result: Dict[str, Any],
#     toxic_result: Dict[str, Any],
#     topic_result: Dict[str, Any],
#     config: Optional[EvidenceMergeConfig] = None,
#     recursive_config: Optional[RecursiveInsightConfig] = None,
# ) -> Dict[str, Any]:
#     """Builds evidence snapshot and optional LLM insights.

#     Args:
#         video: Video metadata dictionary.
#         comments: Raw comment records.
#         eda_result: EDA agent output.
#         spam_result: Spam agent output.
#         sentiment_result: Sentiment agent output.
#         toxic_result: Toxicity agent output.
#         topic_result: Topic agent output.
#         config: Evidence merge configuration.

#     Returns:
#         Dictionary containing evidence snapshot and LLM insights.

#     Example usage:
#         >>> payload = merge_evidence_and_insights(
#         ...     video={},
#         ...     comments=[],
#         ...     eda_result={},
#         ...     spam_result={},
#         ...     sentiment_result={},
#         ...     toxic_result={},
#         ...     topic_result={},
#         ... )
#         >>> "evidence_snapshot" in payload
#         True
#     """
#     cfg = config or EvidenceMergeConfig()

#     evidence_snapshot = build_evidence_snapshot(
#         video=video,
#         comments_total=len(comments),
#         eda_result=eda_result,
#         spam_result=spam_result,
#         sentiment_result=sentiment_result,
#         toxic_result=toxic_result,
#         topic_result=topic_result,
#         config=cfg,
#     )

#     comment_records = build_comment_records(
#         comments,
#         spam_result,
#         sentiment_result,
#         toxic_result,
#         limit=cfg.comment_sample_limit,
#     )

#     llm_insights = generate_llm_insights(
#         evidence_snapshot=evidence_snapshot,
#         comment_records=comment_records,
#         config=cfg,
#         recursive_config=recursive_config,
#     )

#     return {
#         "evidence_snapshot": evidence_snapshot,
#         "llm_insights": llm_insights,
#     }


# def save_merged_output(payload: Dict[str, Any], output_path: str) -> None:
#     """Writes merged evidence payload to disk as JSON.

#     Args:
#         payload: Merged evidence and insight payload.
#         output_path: Target output path.

#     Example usage:
#         >>> save_merged_output({\"evidence_snapshot\": {}}, \"outputs/merged.json\")
#     """
#     output_dir = os.path.dirname(output_path)
#     if output_dir:
#         os.makedirs(output_dir, exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
#     logger.info("Merged evidence output saved: %s", output_path)


# def save_split_outputs(
#     *,
#     evidence_snapshot: Dict[str, Any],
#     llm_insights: Dict[str, Any],
#     output_dir: str,
#     evidence_filename: str,
#     insights_filename: str,
# ) -> Dict[str, str]:
#     """Writes evidence snapshot and LLM insights to separate JSON files.

#     Args:
#         evidence_snapshot: Condensed evidence payload.
#         llm_insights: LLM insight payload.
#         output_dir: Target directory for outputs.
#         evidence_filename: Output filename for evidence snapshot.
#         insights_filename: Output filename for LLM insights.

#     Returns:
#         Dictionary with resolved file paths.

#     Example usage:
#         >>> paths = save_split_outputs(
#         ...     evidence_snapshot={},
#         ...     llm_insights={},
#         ...     output_dir="outputs",
#         ...     evidence_filename="evidence.json",
#         ...     insights_filename="llm_insights.json",
#         ... )
#         >>> "evidence" in paths
#         True
#     """
#     os.makedirs(output_dir, exist_ok=True)
#     evidence_path = os.path.join(output_dir, evidence_filename)
#     insights_path = os.path.join(output_dir, insights_filename)

#     with open(evidence_path, "w", encoding="utf-8") as f:
#         json.dump(evidence_snapshot, f, ensure_ascii=False, indent=2, default=str)
#     logger.info("Evidence snapshot saved: %s", evidence_path)

#     with open(insights_path, "w", encoding="utf-8") as f:
#         json.dump(llm_insights, f, ensure_ascii=False, indent=2, default=str)
#     logger.info("LLM insights saved: %s", insights_path)

#     return {"evidence": evidence_path, "llm_insights": insights_path}

