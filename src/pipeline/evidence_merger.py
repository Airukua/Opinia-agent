from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from llm.generation_config import OllamaGenerationConfig
from llm.ollama_client import LLMClient, chunk_list
from utils.logger import get_logger

logger = get_logger(__name__)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _take_top(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    return items[:limit]


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


def build_comment_records(
    comments: List[Dict[str, Any]],
    spam_result: Dict[str, Any],
    sentiment_result: Dict[str, Any],
    toxic_result: Dict[str, Any],
    *,
    limit: int,
) -> List[Dict[str, Any]]:
    """Merges per-comment signals from multiple agents for LLM processing."""
    spam_map = {item.get("comment_id"): item for item in spam_result.get("results", [])}
    sentiment_map = {
        item.get("comment_id"): item for item in sentiment_result.get("comment_level", [])
    }
    toxic_map = {item.get("comment_id"): item for item in toxic_result.get("comment_level", [])}

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
    """Reduces agent outputs into a compact evidence snapshot for LLM prompts."""
    spam_examples = _take_top(spam_result.get("results", []), config.top_spam_examples)
    sentiment_highlights = sentiment_result.get("highlights", {}) or {}
    toxicity_examples = _take_top(
        toxic_result.get("top_toxic_comments", []), config.top_toxic_examples
    )
    topic_clusters = _take_top(topic_result.get("clusters", []), config.top_topic_clusters)

    return {
        "video": video,
        "comment_totals": {
            "total_comments": int(comments_total),
            "spam_comments": int(spam_result.get("spam_comments", 0)),
            "toxic_comments": int(
                toxic_result.get("summary", {}).get("toxic_comments", 0)
            ),
        },
        "eda": {
            "total_comments": eda_result.get("total_comments"),
            "volume_temporal_analysis": eda_result.get("volume_temporal_analysis"),
            "engagement_analysis": eda_result.get("engagement_analysis"),
            "text_statistics": eda_result.get("text_statistics"),
        },
        "spam": {
            "summary": {
                "total_comments": spam_result.get("total_comments"),
                "spam_comments": spam_result.get("spam_comments"),
                "spam_ratio": spam_result.get("spam_ratio"),
            },
            "top_examples": spam_examples,
        },
        "sentiment": {
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
        },
        "toxicity": {
            "summary": toxic_result.get("summary"),
            "categories": toxic_result.get("categories"),
            "top_examples": toxicity_examples,
        },
        "topics": {
            "cluster_summary": topic_result.get("cluster_summary"),
            "clusters": topic_clusters,
        },
    }


# ---------------------------------------------------------------------------
# VIRAL INSIGHT PROMPTS
# Semua prompt dirancang untuk menghasilkan insight yang actionable
# agar konten dapat direplikasi menjadi viral.
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    return (
        "Anda adalah analis konten media sosial Indonesia yang ahli dalam strategi viral. "
        "Tugas Anda menganalisis data komentar YouTube dan menghasilkan insight yang TAJAM, "
        "SPESIFIK, dan ACTIONABLE untuk membantu kreator konten membuat video berikutnya menjadi viral. "
        "Gunakan Bahasa Indonesia. "
        "Gunakan bahasa sederhana untuk orang awam: hindari jargon, jelaskan istilah sulit, "
        "tulis seperti menjelaskan ke teman yang tidak paham data. "
        "Jawab dengan teks biasa, tanpa JSON atau markdown."
    )


def _build_viral_section_prompts() -> Dict[str, str]:
    """
    Mengembalikan kumpulan prompt per-seksi yang fokus pada strategi viral.
    Setiap seksi menghasilkan satu aspek insight yang berbeda.
    """
    return {
        "emotional_triggers": (
            "Berdasarkan data komentar, identifikasi PEMICU EMOSI UTAMA yang menyebabkan "
            "video ini mendapat banyak engagement. Sebutkan 3-5 pemicu spesifik berdasarkan "
            "kata-kata dominan, komentar paling disukai, dan distribusi sentimen. "
            "Jelaskan MENGAPA setiap pemicu bekerja pada audiens Indonesia ini. "
            "Gunakan bahasa awam dan contoh singkat."
        ),
        "viral_formula": (
            "Berdasarkan pola komentar, bigram dominan, dan topik cluster, rumuskan "
            "FORMULA KONTEN VIRAL yang bisa direplikasi. "
            "Sertakan: (1) elemen judul yang terbukti menarik klik, "
            "(2) angle berita yang paling memancing reaksi, "
            "(3) waktu terbaik posting berdasarkan data volume temporal, "
            "(4) 3 contoh judul video konkret yang bisa langsung dipakai. "
            "Jika ada istilah teknis seperti 'bigram' atau 'cluster', jelaskan artinya singkat."
        ),
        "audience_persona": (
            "Berdasarkan pola bahasa, kata-kata religius, ekspresi emosi, dan topik yang "
            "muncul di komentar, bangun PROFIL PERSONA PENONTON yang detail. "
            "Jelaskan: siapa mereka, apa yang mereka percaya, apa yang membuat mereka "
            "bereaksi, dan bagaimana cara berbicara kepada mereka agar konten resonan. "
            "Gunakan kalimat sederhana, hindari istilah psikologi yang rumit."
        ),
        "content_hooks": (
            "Dari komentar paling banyak disukai dan kata-kata paling sering muncul, "
            "ekstrak HOOK DAN FRASA AJAIB yang terbukti memicu engagement tinggi. "
            "Buat daftar: (1) 5-7 kata/frasa yang harus ada di judul atau thumbnail, "
            "(2) pola kalimat opening video yang paling efektif untuk audiens ini, "
            "(3) kata-kata yang HARUS DIHINDARI karena menurunkan engagement. "
            "Jelaskan arti 'hook' dan 'engagement' dengan bahasa awam."
        ),
        "opportunities": (
            "Berdasarkan pertanyaan terbuka di komentar, topik yang belum tuntas dibahas, "
            "dan cluster skeptisisme penonton, identifikasi PELUANG KONTEN LANJUTAN. "
            "Sebutkan 3-5 ide video konkret yang berpotensi viral berdasarkan 'unfinished business' "
            "dari diskusi komentar video ini. Sertakan alasan mengapa setiap ide berpotensi viral. "
            "Gunakan bahasa awam dan jelaskan manfaatnya bagi penonton."
        ),
        "risks": (
            "Identifikasi RISIKO dan hal yang perlu diwaspadai jika membuat konten serupa: "
            "(1) topik atau framing yang berpotensi memancing kontroversi negatif, "
            "(2) pola komentar toxic atau hoax yang bisa merusak reputasi channel, "
            "(3) rekomendasi konkret cara memitigasi risiko tersebut tanpa kehilangan engagement. "
            "Jelaskan dengan bahasa awam dan langkah praktis."
        ),
        "summary": (
            "Buat RINGKASAN EKSEKUTIF dalam 3-4 kalimat: apa yang membuat video ini viral, "
            "siapa audiensnya, dan satu rekomendasi terpenting yang harus dilakukan kreator "
            "untuk video berikutnya agar bisa mengulangi atau melampaui performa ini. "
            "Ringkas dan mudah dipahami."
        ),
    }


def _build_recursive_user_prompt(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_recursive_llm_insights(
    *,
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
    llm_client: LLMClient,
    config: EvidenceMergeConfig,
    recursive_config: Optional[RecursiveInsightConfig] = None,
) -> Dict[str, Any]:
    """Runs recursive LLM batch analysis with viral content insight prompts.

    Setiap batch memproses sekumpulan komentar dan mengakumulasi insight
    ke dalam environment berjalan. Pada akhir semua batch, insight dari
    seluruh batch digabungkan menjadi satu laporan viral strategy.
    """
    r_cfg = recursive_config or RecursiveInsightConfig()
    batches = chunk_list(comment_records, config.llm_batch_size)
    if r_cfg.max_batches and len(batches) > r_cfg.max_batches:
        batches = batches[: r_cfg.max_batches]

    environment: Dict[str, Any] = {
        "emotional_triggers": [],
        "viral_formula": [],
        "audience_persona": [],
        "content_hooks": [],
        "opportunities": [],
        "risks": [],
        "summary": [],
    }

    batch_outputs: List[Dict[str, Any]] = []
    system_prompt = _build_system_prompt()
    section_prompts = _build_viral_section_prompts()

    for idx, batch in enumerate(batches, start=1):
        user_payload = {
            "batch_index": idx,
            "batch_total": len(batches),
            "environment": environment if r_cfg.include_environment_history else {},
            "evidence_snapshot": evidence_snapshot,
            "comment_batch": batch,
        }

        batch_result: Dict[str, str] = {}
        for key, prompt in section_prompts.items():
            user_prompt = (
                f"{prompt}\n\nKonteks data:\n{_build_recursive_user_prompt(user_payload)}"
            )
            try:
                text = llm_client.chat_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=config.llm_model,
                )
                batch_result[key] = str(text).strip()
            except RuntimeError as err:
                logger.warning("LLM viral insight batch %d [%s] failed: %s", idx, key, err)
                batch_result[key] = "Tidak ada"

        # Akumulasi ke environment berjalan
        for key in environment:
            environment[key].append(batch_result.get(key, ""))

        batch_outputs.append(batch_result)

    section_labels = {
        "emotional_triggers": "PEMICU EMOSI UTAMA",
        "viral_formula":      "FORMULA VIRAL",
        "audience_persona":   "PERSONA AUDIENS",
        "content_hooks":      "HOOK & FRASA KUNCI",
        "opportunities":      "PELUANG KONTEN",
        "risks":              "RISIKO",
        "summary":            "RINGKASAN EKSEKUTIF",
    }

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
            f"Berikut adalah insight '{label}' yang dikumpulkan dari {len(raw_parts)} batch analisis komentar.\n\n"
            f"{accumulated}\n\n"
            f"Tugas Anda: Sintesiskan semua insight di atas menjadi SATU laporan final '{label}' "
            f"yang kohesif, tidak ada pengulangan, tajam, dan langsung actionable. "
            f"Buang informasi yang redundan. Prioritaskan insight yang paling kuat dan spesifik."
        )
        try:
            synthesized = llm_client.chat_text(
                system_prompt=system_prompt,
                user_prompt=synthesis_prompt,
                model=config.llm_model,
            )
            final_insights[key] = str(synthesized).strip()
        except RuntimeError as err:
            logger.warning("LLM synthesis failed for [%s]: %s", key, err)
            # Fallback: gabungkan raw tanpa sintesis
            final_insights[key] = accumulated

    # Laporan akhir dibangun dari final_insights per-seksi (bukan per-batch)
    combined = "\n\n".join(
        f"{'=' * 60}\n{label}\n{'=' * 60}\n{final_insights.get(key, 'Tidak ada')}"
        for key, label in section_labels.items()
    )

    return {
        "available": True,
        "mode": "recursive_viral",
        "batch_count": len(batches),
        "environment": environment,
        "batch_outputs": batch_outputs,
        # final_insights: insight final per-seksi hasil sintesis lintas batch
        "emotional_triggers": final_insights.get("emotional_triggers"),
        "viral_formula":      final_insights.get("viral_formula"),
        "audience_persona":   final_insights.get("audience_persona"),
        "content_hooks":      final_insights.get("content_hooks"),
        "opportunities":      final_insights.get("opportunities"),
        "risks":              final_insights.get("risks"),
        "summary":            final_insights.get("summary"),
        "combined": combined,
    }


def generate_llm_insights(
    *,
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
    config: EvidenceMergeConfig,
    recursive_config: Optional[RecursiveInsightConfig] = None,
) -> Dict[str, Any]:
    """Creates viral LLM insight report if enabled and server is reachable."""
    if not config.llm_enabled:
        return {"available": False, "reason": "llm_disabled"}

    client = LLMClient(
        OllamaGenerationConfig(
            model=config.llm_model or "llama3.1:8b",
            provider=config.llm_provider,
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            api_base_url=config.llm_api_base_url,
            timeout_seconds=config.llm_timeout_seconds,
        )
    )

    if not client.health_check():
        return {"available": False, "reason": "llm_unreachable"}

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
    """Single-pass viral insight analysis — lebih cepat, cocok untuk produksi."""
    system_prompt = _build_system_prompt()
    base_payload = {
        "evidence_snapshot": evidence_snapshot,
        "comment_samples": comment_records[: config.comment_sample_limit],
    }
    base_context = json.dumps(base_payload, ensure_ascii=False, indent=2)
    section_prompts = _build_viral_section_prompts()

    responses: Dict[str, str] = {}
    cfg = OllamaGenerationConfig(
        model=config.llm_model or "llama3.1:8b",
        provider=config.llm_provider,
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        api_base_url=config.llm_api_base_url,
        timeout_seconds=config.llm_timeout_seconds,
    )
    provider = (cfg.provider or "ollama").lower()
    if provider == "gemini":
        try:
            client = LLMClient(cfg)
            for key, prompt in section_prompts.items():
                user_prompt = f"{prompt}\n\nKonteks data:\n{base_context}"
                responses[key] = client.chat_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=cfg.model,
                ).strip()
        except Exception as err:
            logger.warning("Gemini viral LLM failed; using fallback: %s", err)
            fallback = _fallback_simple_insights(evidence_snapshot, comment_records)
            fallback["raw"] = {}
            return fallback
    else:
        try:
            from llm.langchain_client import langchain_chat_text

            for key, prompt in section_prompts.items():
                user_prompt = f"{prompt}\n\nKonteks data:\n{base_context}"
                responses[key] = langchain_chat_text(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    config=cfg,
                ).strip()
        except Exception as err:
            logger.warning("LangChain viral LLM failed; using fallback: %s", err)
            fallback = _fallback_simple_insights(evidence_snapshot, comment_records)
            fallback["raw"] = {}
            return fallback

    combined = "\n\n".join(
        f"{key.upper().replace('_', ' ')}:\n{val}"
        for key, val in responses.items()
    )

    return {
        "available": True,
        "mode": "simple_viral",
        "emotional_triggers": responses.get("emotional_triggers"),
        "viral_formula": responses.get("viral_formula"),
        "audience_persona": responses.get("audience_persona"),
        "content_hooks": responses.get("content_hooks"),
        "opportunities": responses.get("opportunities"),
        "risks": responses.get("risks"),
        "summary": responses.get("summary"),
        "combined": combined,
        "raw": responses,
    }


def _fallback_simple_insights(
    evidence_snapshot: Dict[str, Any],
    comment_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Fallback statis jika LLM tidak tersedia — menggunakan data EDA langsung."""
    comment_totals = evidence_snapshot.get("comment_totals", {})
    eda = evidence_snapshot.get("eda", {})
    text_stats = eda.get("text_statistics", {}) or {}
    vocab = text_stats.get("vocabulary", {}) or {}
    top_words = vocab.get("token_frequency_top", []) or []
    top_bigrams = vocab.get("bigram_frequency_top", []) or []

    sentiment = evidence_snapshot.get("sentiment", {}).get("summary", {}) or {}
    distribution = sentiment.get("distribution", {}) or {}

    engagement = eda.get("engagement_analysis", {}) or {}
    top_liked = (
        engagement.get("top_liked_comments", []) or []
    )[:3]

    topics = evidence_snapshot.get("topics", {})
    clusters = topics.get("clusters", []) or []

    top_word_list = ", ".join(w for w, _ in top_words[:8]) if top_words else "-"
    top_bigram_list = ", ".join(b for b, _ in top_bigrams[:5]) if top_bigrams else "-"
    top_liked_texts = "; ".join(
        f'"{c.get("text", "")[:60]}" ({c.get("like_count", 0)} likes)'
        for c in top_liked
    ) if top_liked else "-"
    top_cluster_labels = ", ".join(
        c.get("topic_label", "") for c in clusters[:5] if c.get("topic_label")
    ) or "-"

    pos = distribution.get("positive", 0)
    neg = distribution.get("negative", 0)
    neu = distribution.get("neutral", 0)
    total = max(pos + neg + neu, 1)

    return {
        "available": True,
        "mode": "fallback_viral",
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
    }


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
    """Builds evidence snapshot and viral LLM insights."""
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


def save_merged_output(payload: Dict[str, Any], output_path: str) -> None:
    """Writes merged evidence payload to disk as JSON."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Merged evidence output saved: %s", output_path)


def save_split_outputs(
    *,
    evidence_snapshot: Dict[str, Any],
    llm_insights: Dict[str, Any],
    output_dir: str,
    evidence_filename: str,
    insights_filename: str,
) -> Dict[str, str]:
    """Writes evidence snapshot and viral LLM insights to separate JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    evidence_path = os.path.join(output_dir, evidence_filename)
    insights_path = os.path.join(output_dir, insights_filename)

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_snapshot, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Evidence snapshot saved: %s", evidence_path)

    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(llm_insights, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Viral LLM insights saved: %s", insights_path)

    return {"evidence": evidence_path, "llm_insights": insights_path}
