from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from llm.generation_config import OllamaGenerationConfig
from llm.ollama_client import LLMClient
from utils.cluster_comment import HDBSCANConfig, TopicClusterer, UMAPConfig
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TopicAgentConfig:
    """Configuration for topic agent pipeline.

    Attributes:
        text_column: Column containing comment text.
        like_column: Column containing engagement score used for ranking.
        model_name: SentenceTransformer model name/path for embeddings.
        model_cache_dir: Optional mounted cache directory for embedding model.
        device: Optional inference device for embeddings.
        top_comments_per_cluster: Number of highest-engagement comments per cluster.
        lda_max_features: Maximum vocabulary size for LDA vectorization.
        lda_top_words: Number of top words returned per cluster topic.
        generate_topic_with_llm: Enables LLM-based final topic naming.
        llm_model: Optional override model name for Ollama topic naming.
        llm_base_url: Ollama base URL.
        llm_timeout_seconds: Timeout for Ollama requests.
        include_noise_cluster: Includes cluster ``-1`` output when ``True``.
    """

    text_column: str = "text"
    like_column: str = "like_count"
    model_name: str = "models/multilingual-e5-small"
    model_cache_dir: Optional[str] = None
    device: Optional[str] = None
    top_comments_per_cluster: int = 5
    lda_max_features: int = 1500
    lda_top_words: int = 10
    generate_topic_with_llm: bool = True
    llm_model: Optional[str] = None
    llm_base_url: str = "http://localhost:11434"
    llm_provider: str = "ollama"
    llm_api_key: Optional[str] = None
    llm_api_base_url: Optional[str] = None
    llm_timeout_seconds: int = 120
    include_noise_cluster: bool = False


def _normalize_comments(df: pd.DataFrame, cfg: TopicAgentConfig) -> pd.DataFrame:
    """Normalizes comment dataframe for topic processing."""
    out = df.copy()
    if cfg.text_column not in out.columns:
        raise ValueError(f"Required text column not found: {cfg.text_column}")

    if cfg.like_column not in out.columns:
        out[cfg.like_column] = 0

    out[cfg.text_column] = out[cfg.text_column].fillna("").astype(str)
    out[cfg.like_column] = (
        pd.to_numeric(out[cfg.like_column], errors="coerce").fillna(0).astype(int)
    )
    out = out[out[cfg.text_column].str.strip() != ""].reset_index(drop=True)
    return out


def _build_clusterer(cfg: TopicAgentConfig) -> TopicClusterer:
    """Creates topic clusterer instance from config."""
    return TopicClusterer(
        model_name=cfg.model_name,
        device=cfg.device,
        model_cache_dir=cfg.model_cache_dir,
        umap_config=UMAPConfig(),
        hdbscan_config=HDBSCANConfig(),
    )


def _extract_lda_keywords(
    texts: List[str],
    *,
    max_features: int,
    top_words: int,
) -> List[str]:
    """Extracts LDA top keywords from cluster text."""
    if len(texts) < 2:
        return []
    if not any(str(t).strip() for t in texts):
        return []

    vectorizer = CountVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english",
    )

    try:
        dtm = vectorizer.fit_transform(texts)
    except ValueError as err:
        # Sklearn raises "empty vocabulary" when all tokens are filtered out.
        logger.warning("LDA skipped due to vectorizer error: %s", err)
        return []
    if dtm.shape[1] == 0:
        return []

    lda = LatentDirichletAllocation(
        n_components=1,
        random_state=42,
        learning_method="batch",
    )
    lda.fit(dtm)

    feature_names = vectorizer.get_feature_names_out()
    topic_weights = lda.components_[0]
    top_indices = topic_weights.argsort()[::-1][:top_words]
    return [str(feature_names[idx]) for idx in top_indices]


def _prepare_llm_payload(cluster_data: Dict[str, Any], *, cfg: TopicAgentConfig) -> str:
    """Creates compact JSON payload for LLM topic-label generation."""
    payload = {
        "cluster_label": cluster_data["cluster_label"],
        "cluster_size": cluster_data["cluster_size"],
        "lda_keywords": cluster_data["lda_keywords"],
        "top_comments": [
            {
                "like_count": item.get("like_count", 0),
                "text": item.get("text", ""),
            }
            for item in cluster_data["top_comments"]
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _build_system_prompt() -> str:
    return (
        "Anda adalah asisten pelabelan topik. "
        "Kembalikan JSON valid dengan kunci: topic_label, rationale. "
        "topic_label harus singkat (2-6 kata). "
        "Prioritas utama: top_comments dan lda_keywords. "
        "Jangan gunakan judul/deskripsi video sama sekali. "
        "Utamakan generalisasi topik (mis. 'dukungan/pujian', 'doa/ungkapan syukur', "
        "'kritik/ketidakpuasan', 'seruan/pernyataan politik') daripada nama entitas spesifik. "
        "Rationale wajib merujuk ke komentar/keyword."
    )


def _label_topic_with_llm(
    cluster_data: Dict[str, Any],
    *,
    client: LLMClient,
    llm_model: Optional[str],
    cfg: TopicAgentConfig,
) -> Dict[str, str]:
    """Asks LLM to produce concise topic label and rationale."""
    system_prompt = _build_system_prompt()
    user_prompt = (
        "Buat satu label topik berdasarkan bukti cluster ini:\n"
        f"{_prepare_llm_payload(cluster_data, cfg=cfg)}"
    )
    try:
        result = client.chat(system_prompt=system_prompt, user_prompt=user_prompt, model=llm_model)
        return {
            "topic_label": str(result.get("topic_label", "Unknown topic")).strip(),
            "rationale": str(result.get("rationale", "")).strip(),
        }
    except Exception as err:  # pragma: no cover - runtime fallback
        logger.warning("LLM topic labeling failed for cluster=%s error=%s", cluster_data["cluster_label"], err)
        fallback = ", ".join(cluster_data["lda_keywords"][:3]) or "general discussion"
        return {
            "topic_label": fallback,
            "rationale": "Fallback label generated from LDA keywords due to LLM error.",
        }


def run_topic_agent(comments: pd.DataFrame | List[Dict[str, Any]], config: Optional[TopicAgentConfig] = None) -> Dict[str, Any]:
    """Runs topic agent pipeline: cluster -> LDA -> top comments -> LLM labeling.

    Args:
        comments: DataFrame or list of comment dictionaries.
        config: Optional topic-agent configuration.

    Returns:
        Structured result containing cluster analytics and topic labels.

    Example usage:
        >>> sample = [{"text": "Great video", "like_count": 10}]
        >>> out = run_topic_agent(sample, TopicAgentConfig(generate_topic_with_llm=False))
        >>> "clusters" in out
        True
    """
    cfg = config or TopicAgentConfig()
    df = comments if isinstance(comments, pd.DataFrame) else pd.DataFrame(comments)
    df = _normalize_comments(df, cfg)

    if df.empty:
        return {"total_comments": 0, "clusters": [], "cluster_summary": {"num_clusters": 0}}

    clusterer = _build_clusterer(cfg)
    clustering_output = clusterer.cluster_texts(df[cfg.text_column].tolist())
    clustered_df = df.copy()
    clustered_df["topic_cluster"] = clustering_output["labels"]
    clustered_df["topic_confidence"] = clustering_output["probabilities"]
    cluster_summary = clustering_output["summary"]

    llm_client: Optional[LLMClient] = None
    if cfg.generate_topic_with_llm:
        llm_client = LLMClient(
            OllamaGenerationConfig(
                base_url=cfg.llm_base_url,
                provider=cfg.llm_provider,
                api_key=cfg.llm_api_key,
                api_base_url=cfg.llm_api_base_url,
                timeout_seconds=cfg.llm_timeout_seconds,
            )
        )

    clusters_output: List[Dict[str, Any]] = []
    grouped = clustered_df.groupby("topic_cluster", sort=True)
    for label, group in grouped:
        label_int = int(label)
        if label_int == -1 and not cfg.include_noise_cluster:
            continue

        top_comments = (
            group.sort_values(cfg.like_column, ascending=False)
            .head(cfg.top_comments_per_cluster)[[cfg.text_column, cfg.like_column]]
            .rename(columns={cfg.text_column: "text", cfg.like_column: "like_count"})
            .to_dict(orient="records")
        )
        lda_keywords = _extract_lda_keywords(
            group[cfg.text_column].tolist(),
            max_features=cfg.lda_max_features,
            top_words=cfg.lda_top_words,
        )
        cluster_data: Dict[str, Any] = {
            "cluster_label": label_int,
            "cluster_size": int(len(group)),
            "lda_keywords": lda_keywords,
            "top_comments": top_comments,
            "topic_confidence_mean": float(group["topic_confidence"].mean()),
        }

        if llm_client is not None:
            llm_label = _label_topic_with_llm(
                cluster_data,
                client=llm_client,
                llm_model=cfg.llm_model,
                cfg=cfg,
            )
            cluster_data.update(llm_label)
        else:
            cluster_data["topic_label"] = ", ".join(lda_keywords[:3]) or "unlabeled topic"
            cluster_data["rationale"] = "LLM labeling disabled; label derived from LDA keywords."

        clusters_output.append(cluster_data)

    return {
        "total_comments": int(len(df)),
        "clusters": clusters_output,
        "cluster_summary": cluster_summary,
    }


def run_topic_agent_from_csv(
    csv_path: str,
    *,
    output_json_path: Optional[str] = None,
    config: Optional[TopicAgentConfig] = None,
) -> Dict[str, Any]:
    """Runs topic agent pipeline from CSV and optionally saves JSON output.

    Args:
        csv_path: Input comments CSV path.
        output_json_path: Optional JSON output path.
        config: Optional topic-agent configuration.

    Returns:
        Topic-agent result dictionary.
    """
    logger.info("Running topic agent from CSV: %s", csv_path)
    df = pd.read_csv(csv_path)
    result = run_topic_agent(df, config=config)

    if output_json_path:
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Topic-agent output saved: %s", output_json_path)

    return result
