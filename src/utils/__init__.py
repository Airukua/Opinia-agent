"""Utility helpers shared across modules."""

from utils.logger import configure_logging, get_logger
from utils.youtube_url_normalizer import extract_video_id

__all__ = [
    "configure_logging",
    "get_logger",
    "extract_video_id",
]

try:
    from utils.sentence_transformer_wrapper import SentenceTransformerWrapper

    __all__.append("SentenceTransformerWrapper")
except Exception:  # pragma: no cover - optional dependency boundary
    pass

try:
    from utils.cluster_comment import HDBSCANConfig, TopicClusterer, UMAPConfig

    __all__.extend(["TopicClusterer", "UMAPConfig", "HDBSCANConfig"])
except Exception:  # pragma: no cover - optional dependency boundary
    pass
