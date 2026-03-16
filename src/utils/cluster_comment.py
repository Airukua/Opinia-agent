from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
import pandas as pd
from utils.logger import get_logger
from utils.sentence_transformer_wrapper import SentenceTransformerWrapper

logger = get_logger(__name__)

try:
    import hdbscan
except ImportError:  # pragma: no cover - runtime dependency guard
    hdbscan = None  # type: ignore[assignment]

try:
    import umap
except ImportError:  # pragma: no cover - runtime dependency guard
    umap = None  # type: ignore[assignment]


@dataclass
class UMAPConfig:
    """Configuration for UMAP dimensionality reduction.

    Attributes:
        n_neighbors: Size of local neighborhood used for manifold approximation.
        n_components: Number of output dimensions after projection.
        min_dist: Minimum distance between points in low-dimensional space.
        metric: Distance metric used in high-dimensional space.
        random_state: Seed for deterministic UMAP initialization.
    """

    n_neighbors: int = 15
    n_components: int = 5
    min_dist: float = 0.0
    metric: str = "cosine"
    random_state: Optional[int] = None


@dataclass
class HDBSCANConfig:
    """Configuration for HDBSCAN automatic cluster discovery.

    Attributes:
        min_cluster_size: Smallest cluster size allowed.
        min_samples: Core-point threshold; ``None`` lets HDBSCAN infer default.
        metric: Distance metric used during clustering.
        cluster_selection_method: Cluster extraction strategy (e.g. ``"eom"``).
    """

    min_cluster_size: int = 8
    min_samples: Optional[int] = None
    metric: str = "euclidean"
    cluster_selection_method: str = "eom"


class TopicClusterer:
    """Embeds comments and clusters them without manual K selection.

    Example usage:
        >>> clusterer = TopicClusterer(model_name="all-MiniLM-L6-v2")
        >>> output = clusterer.cluster_texts(["great video", "buy now!!!"])
        >>> "labels" in output
        True
    """

    def __init__(
        self,
        *,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        model_cache_dir: Optional[str] = None,
        umap_config: Optional[UMAPConfig] = None,
        hdbscan_config: Optional[HDBSCANConfig] = None,
    ) -> None:
        """Initializes topic clusterer with embedding and clustering settings.

        Args:
            model_name: SentenceTransformer model identifier/path.
            device: Optional execution device (e.g. ``"cpu"``, ``"cuda"``).
            model_cache_dir: Optional mounted cache directory for model weights.
            umap_config: Optional UMAP configuration override.
            hdbscan_config: Optional HDBSCAN configuration override.
        """
        self.embedder = SentenceTransformerWrapper(
            model_name=model_name,
            device=device,
            cache_folder=model_cache_dir,
        )
        self.umap_config = umap_config or UMAPConfig()
        self.hdbscan_config = hdbscan_config or HDBSCANConfig()

    def _build_umap(self):
        """Builds a configured UMAP reducer.

        Returns:
            Configured ``umap.UMAP`` reducer.

        Raises:
            RuntimeError: If ``umap-learn`` package is unavailable.
        """
        if umap is None:
            raise RuntimeError(
                "umap-learn is not installed. Install it with: pip install umap-learn"
            )
        cfg = self.umap_config
        return umap.UMAP(
            n_neighbors=cfg.n_neighbors,
            n_components=cfg.n_components,
            min_dist=cfg.min_dist,
            metric=cfg.metric,
            random_state=cfg.random_state,
        )

    def _build_hdbscan(self):
        """Builds a configured HDBSCAN clusterer.

        Returns:
            Configured ``hdbscan.HDBSCAN`` clusterer.

        Raises:
            RuntimeError: If ``hdbscan`` package is unavailable.
        """
        if hdbscan is None:
            raise RuntimeError(
                "hdbscan is not installed. Install it with: pip install hdbscan"
            )
        cfg = self.hdbscan_config
        return hdbscan.HDBSCAN(
            min_cluster_size=cfg.min_cluster_size,
            min_samples=cfg.min_samples,
            metric=cfg.metric,
            cluster_selection_method=cfg.cluster_selection_method,
            prediction_data=True,
        )

    def cluster_texts(self, texts: Sequence[str]) -> Dict[str, Any]:
        """Clusters text into topic groups using UMAP + HDBSCAN.

        Args:
            texts: Sequence of comments/documents.

        Returns:
            Dictionary with:
            - ``labels``: integer cluster label per text (``-1`` for noise),
            - ``probabilities``: cluster confidence score per text,
            - ``summary``: compact cluster-level overview.

        Example usage:
            >>> clusterer = TopicClusterer(model_name="all-MiniLM-L6-v2")
            >>> out = clusterer.cluster_texts(["komentar bagus", "klik link ini sekarang"])
            >>> "summary" in out
            True
        """
        text_list = [text if text is not None else "" for text in texts]
        if not text_list:
            return {"labels": [], "probabilities": [], "summary": {"num_clusters": 0}}

        logger.info("Topic clustering started for %d texts", len(text_list))
        embeddings = self.embedder.encode(
            text_list,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        reducer = self._build_umap()
        reduced = reducer.fit_transform(embeddings)

        clusterer = self._build_hdbscan()
        labels = clusterer.fit_predict(reduced)
        probabilities = clusterer.probabilities_

        summary = _build_cluster_summary(labels, text_list)
        logger.info(
            "Topic clustering completed: clusters=%d noise=%d",
            summary["num_clusters"],
            summary["num_noise_points"],
        )
        return {
            "labels": [int(x) for x in labels],
            "probabilities": [float(x) for x in probabilities],
            "summary": summary,
        }

    def cluster_dataframe(
        self,
        df: pd.DataFrame,
        *,
        text_column: str = "text",
    ) -> pd.DataFrame:
        """Clusters DataFrame rows using the text column and returns enriched DataFrame.

        Args:
            df: Input DataFrame containing text.
            text_column: Column containing text to cluster.

        Returns:
            Copy of DataFrame with added ``topic_cluster`` and ``topic_confidence``.

        Example usage:
            >>> df = pd.DataFrame({"text": ["bagus", "spam link"]})
            >>> out = TopicClusterer().cluster_dataframe(df)
            >>> "topic_cluster" in out.columns
            True
        """
        if text_column not in df.columns:
            raise ValueError(f"DataFrame missing required text column: {text_column}")

        output = self.cluster_texts(df[text_column].fillna("").astype(str).tolist())
        enriched = df.copy()
        enriched["topic_cluster"] = output["labels"]
        enriched["topic_confidence"] = output["probabilities"]
        return enriched


def _build_cluster_summary(labels: Sequence[int], texts: Sequence[str]) -> Dict[str, Any]:
    """Builds compact summary object for discovered clusters.

    Args:
        labels: Cluster labels from HDBSCAN.
        texts: Original text sequence aligned with labels.

    Returns:
        Dictionary containing number of clusters, noise statistics, and samples.
    """
    summary_df = pd.DataFrame({"label": labels, "text": list(texts)})
    total = int(len(summary_df))

    noise_mask = summary_df["label"] == -1
    noise_count = int(noise_mask.sum())
    non_noise = summary_df[~noise_mask]

    cluster_sizes = (
        non_noise.groupby("label", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )

    clusters: List[Dict[str, Any]] = []
    for _, row in cluster_sizes.iterrows():
        label = int(row["label"])
        cluster_texts = non_noise[non_noise["label"] == label]["text"].head(3).tolist()
        clusters.append(
            {
                "label": label,
                "count": int(row["count"]),
                "sample_texts": cluster_texts,
            }
        )

    return {
        "num_clusters": int(cluster_sizes.shape[0]),
        "num_noise_points": noise_count,
        "noise_ratio": float(noise_count / total) if total else 0.0,
        "clusters": clusters,
    }
