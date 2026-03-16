from __future__ import annotations
from typing import Any, Iterable, List, Optional
from utils.logger import get_logger
logger = get_logger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - runtime dependency guard
    SentenceTransformer = None  # type: ignore[assignment]

_MODEL_CACHE: dict[tuple, Any] = {}


class SentenceTransformerWrapper:
    """Loads and serves any SentenceTransformer model through one interface.

    This wrapper is intentionally generic so topic/spam/sentiment agents can
    share one embedding path without coupling to a specific model name.

    Example usage:
        >>> wrapper = SentenceTransformerWrapper("all-MiniLM-L6-v2")
        >>> embeddings = wrapper.encode(["great video", "I disagree"])
        >>> len(embeddings) == 2
        True
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        *,
        device: Optional[str] = None,
        cache_folder: Optional[str] = None,
        trust_remote_code: bool = False,
    ) -> None:
        """Initializes wrapper and loads the requested model.

        Args:
            model_name: Any valid SentenceTransformer model identifier/path.
            device: Optional device override (e.g. ``"cpu"``, ``"cuda"``).
            cache_folder: Optional local directory for model cache.
            trust_remote_code: Forwarded to SentenceTransformer initializer.
        """
        self.model_name = model_name
        self.device = device
        self.cache_folder = cache_folder
        self.trust_remote_code = trust_remote_code
        self._model = self._load_model(model_name)

    @property
    def model(self) -> Any:
        """Returns the active SentenceTransformer model instance.

        Returns:
            Instantiated ``SentenceTransformer`` model.
        """
        return self._model

    def _load_model(self, model_name: str) -> Any:
        """Loads a SentenceTransformer model with dependency safeguards.

        Args:
            model_name: SentenceTransformer model identifier/path.

        Returns:
            Instantiated ``SentenceTransformer`` model.

        Raises:
            RuntimeError: If ``sentence-transformers`` package is unavailable.
        """
        if SentenceTransformer is None:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )
        cache_key = (model_name, self.device, self.cache_folder, self.trust_remote_code)
        if cache_key in _MODEL_CACHE:
            logger.info("Reusing sentence-transformer model=%s from cache", model_name)
            return _MODEL_CACHE[cache_key]

        logger.info("Loading sentence-transformer model=%s", model_name)
        model = SentenceTransformer(
            model_name,
            device=self.device,
            cache_folder=self.cache_folder,
            trust_remote_code=self.trust_remote_code,
        )
        _MODEL_CACHE[cache_key] = model
        return model

    def set_model(self, model_name: str) -> None:
        """Switches the active embedding model at runtime.

        Args:
            model_name: Any valid SentenceTransformer model identifier/path.

        Example usage:
            >>> wrapper = SentenceTransformerWrapper("all-MiniLM-L6-v2")
            >>> wrapper.set_model("all-mpnet-base-v2")
        """
        if model_name == self.model_name:
            logger.debug("set_model skipped; model unchanged: %s", model_name)
            return
        self.model_name = model_name
        self._model = self._load_model(model_name)

    def encode(
        self,
        texts: Iterable[str],
        *,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> Any:
        """Encodes text into sentence embeddings.

        Args:
            texts: Iterable of input text.
            batch_size: Batch size for embedding inference.
            normalize_embeddings: Whether to L2-normalize embeddings.
            convert_to_numpy: Returns ``numpy.ndarray`` when ``True``.
            show_progress_bar: Enables progress bar during encoding.

        Returns:
            Embedding matrix from SentenceTransformer ``encode``.

        Example usage:
            >>> wrapper = SentenceTransformerWrapper("all-MiniLM-L6-v2")
            >>> vectors = wrapper.encode(["alpha", "beta"], batch_size=2)
            >>> len(vectors) == 2
            True
        """
        text_list: List[str] = [text if text is not None else "" for text in texts]
        logger.info(
            "Encoding text with model=%s items=%d batch_size=%d",
            self.model_name,
            len(text_list),
            batch_size,
        )
        return self._model.encode(
            text_list,
            batch_size=batch_size,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=convert_to_numpy,
            show_progress_bar=show_progress_bar,
        )
