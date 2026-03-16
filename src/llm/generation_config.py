from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
import os
from dotenv import load_dotenv

# Ensure env vars are available for defaults.
load_dotenv()


@dataclass
class OllamaGenerationConfig:
    """Runtime configuration for Ollama generation options.

    Attributes:
        model: Default model name used for chat requests.
        provider: Backend provider (``"ollama"``, ``"openai_compatible"``, or ``"gemini"``).
        base_url: Base URL of the Ollama server.
        api_key: API key for OpenAI-compatible providers.
        api_base_url: Base URL for OpenAI-compatible providers.
        temperature: Sampling temperature.
        top_p: Nucleus sampling probability.
        top_k: Top-k sampling limit.
        num_ctx: Context window size.
        num_predict: Maximum number of generated tokens.
        repeat_penalty: Penalty applied to repeated tokens.
        seed: Optional random seed for deterministic output.
        timeout_seconds: HTTP timeout for Ollama requests.
        response_format: Optional response format (e.g. ``"json"``).
        rate_limit_rpm: Optional requests-per-minute cap for hosted providers.
        min_request_interval_seconds: Optional minimum seconds between requests.

    Example usage:
        >>> config = OllamaGenerationConfig(model="llama3.1:8b", temperature=0.3)
        >>> config.model
        'llama3.1:8b'
    """

    model: str = "llama3.1:8b"
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    num_ctx: int = 8192
    num_predict: int = 1024
    repeat_penalty: float = 1.1
    seed: Optional[int] = None
    timeout_seconds: int = 120
    response_format: Optional[str] = "json"
    rate_limit_rpm: Optional[int] = None
    min_request_interval_seconds: Optional[float] = None

    def to_ollama_options(self) -> Dict[str, Any]:
        """Converts runtime config into Ollama-compatible ``options`` payload.

        Returns:
            Dictionary that can be sent as ``options`` to Ollama chat API.

        Example usage:
            >>> config = OllamaGenerationConfig(temperature=0.3, top_p=0.95)
            >>> options = config.to_ollama_options()
            >>> options["temperature"]
            0.3
        """
        options: Dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
            "repeat_penalty": self.repeat_penalty,
        }
        if self.seed is not None:
            options["seed"] = self.seed
        return options

    def __post_init__(self) -> None:
        """Backfill configuration from environment variables when unset."""
        if not self.model:
            self.model = os.getenv("OLLAMA_MODEL", self.model)
        if not self.provider:
            self.provider = os.getenv("LLM_PROVIDER", self.provider)
        if not self.base_url:
            self.base_url = os.getenv("OLLAMA_BASE_URL", self.base_url)
        if not self.api_key:
            self.api_key = os.getenv("LLM_API_KEY", self.api_key)
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_base_url:
            self.api_base_url = os.getenv("LLM_API_BASE_URL", self.api_base_url)
        if not self.timeout_seconds:
            env_timeout = os.getenv("OLLAMA_TIMEOUT")
            if env_timeout and env_timeout.isdigit():
                self.timeout_seconds = int(env_timeout)
        if self.rate_limit_rpm is None:
            env_rpm = os.getenv("LLM_RATE_LIMIT_RPM") or os.getenv("GEMINI_RATE_LIMIT_RPM")
            if env_rpm and env_rpm.isdigit():
                self.rate_limit_rpm = int(env_rpm)
        if self.min_request_interval_seconds is None:
            env_min = os.getenv("LLM_MIN_REQUEST_INTERVAL_SECONDS") or os.getenv(
                "GEMINI_MIN_REQUEST_INTERVAL_SECONDS"
            )
            if env_min:
                try:
                    self.min_request_interval_seconds = float(env_min)
                except ValueError:
                    pass
        if self.min_request_interval_seconds is None and self.rate_limit_rpm:
            self.min_request_interval_seconds = 60.0 / float(self.rate_limit_rpm)


@dataclass
class AgentAnalysisConfig:
    """Controls preprocessing and chunking strategy for comment analysis.

    Attributes:
        max_comments: Maximum comments processed in one run.
        min_comment_length: Minimum character length to keep a comment.
        chunk_size: Number of comments per chunk for model calls.
        include_like_count: Includes like-count metadata in prompt payload.
        include_timestamp: Includes publish timestamp in prompt payload.
        sentiment_labels: Allowed sentiment labels produced by analysis.

    Example usage:
        >>> cfg = AgentAnalysisConfig(max_comments=200, chunk_size=50)
        >>> cfg.chunk_size
        50
    """

    max_comments: int = 500
    min_comment_length: int = 2
    chunk_size: int = 120
    include_like_count: bool = True
    include_timestamp: bool = False
    sentiment_labels: Tuple[str, ...] = field(
        default_factory=lambda: ("positive", "neutral", "negative")
    )
