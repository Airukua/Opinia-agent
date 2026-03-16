import json
import os
import re
import time
from datetime import datetime
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

try:
    from .generation_config import OllamaGenerationConfig
except ImportError:
    from llm.generation_config import OllamaGenerationConfig

logger = get_logger(__name__)


class OllamaClient:
    """Minimal Ollama chat client via HTTP API.

    Example usage:
        >>> cfg = OllamaGenerationConfig(model="llama3.1:8b")
        >>> client = OllamaClient(cfg)
    """

    def __init__(self, config: OllamaGenerationConfig):
        """Initializes the client with generation/runtime configuration.

        Args:
            config: Ollama endpoint and generation options.

        Example usage:
            >>> cfg = OllamaGenerationConfig(model="llama3.1:8b")
            >>> client = OllamaClient(cfg)
        """
        self.config = config

    def health_check(self) -> bool:
        """Checks whether the Ollama server is reachable.

        Returns:
            ``True`` when ``/api/tags`` responds successfully, otherwise ``False``.

        Example usage:
            >>> client = OllamaClient(OllamaGenerationConfig())
            >>> isinstance(client.health_check(), bool)
            True
        """
        url = f"{self.config.base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds):
                logger.info("Ollama health check passed: %s", self.config.base_url)
                return True
        except Exception as err:
            logger.warning("Ollama health check failed: %s", err)
            return False

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sends a chat request and parses the model response as JSON.

        Args:
            system_prompt: Instruction context for the model.
            user_prompt: User input payload.
            model: Optional model override; defaults to configured model.

        Returns:
            Parsed JSON object from the model output.

        Raises:
            RuntimeError: If model returns empty or invalid JSON content.

        Example usage:
            >>> client = OllamaClient(OllamaGenerationConfig())
            >>> result = client.chat(
            ...     system_prompt="Always return JSON with key: summary",
            ...     user_prompt="Summarize: This project extracts comments.",
            ... )
            >>> "summary" in result
            True
        """
        active_model = model or self.config.model
        logger.info("Sending chat request to Ollama model=%s", active_model)
        url = f"{self.config.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": active_model,
            "stream": False,
            "options": self.config.to_ollama_options(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.config.response_format:
            payload["format"] = self.config.response_format

        raw = self._post_json(url, payload)
        content = raw.get("message", {}).get("content", "").strip()
        return _parse_json_response(content, active_model)

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> str:
        """Sends a chat request and returns raw text content."""
        active_model = model or self.config.model
        logger.info("Sending chat_text request to Ollama model=%s", active_model)
        url = f"{self.config.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": active_model,
            "stream": False,
            "options": self.config.to_ollama_options(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.config.response_format:
            payload["format"] = self.config.response_format

        raw = self._post_json(url, payload)
        content = raw.get("message", {}).get("content", "")
        if not content:
            logger.error("Model returned empty content for model=%s", active_model)
            raise RuntimeError("Model returned empty message content")
        _maybe_dump_raw_response(content, active_model, suffix="ok")
        return str(content).strip()

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs an HTTP POST request and decodes a JSON response.

        Args:
            url: HTTP endpoint URL.
            payload: JSON-serializable request body.

        Returns:
            Decoded JSON response dictionary.

        Raises:
            RuntimeError: If HTTP request fails or endpoint is unreachable.

        Example usage:
            >>> client = OllamaClient(OllamaGenerationConfig())
            >>> raw = client._post_json(
            ...     "http://localhost:11434/api/chat",
            ...     {
            ...         "model": "llama3.1:8b",
            ...         "stream": False,
            ...         "messages": [{"role": "user", "content": "Reply in JSON"}],
            ...     },
            ... )
            >>> isinstance(raw, dict)
            True
        """
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="ignore")
            logger.error("Ollama HTTPError %s: %s", err.code, detail)
            raise RuntimeError(f"Ollama HTTP {err.code}: {detail}") from err
        except urllib.error.URLError as err:
            logger.error("Ollama URLError: %s", err)
            raise RuntimeError(
                f"Cannot reach Ollama server at {self.config.base_url}: {err}"
            ) from err


def _parse_json_response(content: str, model_name: str) -> Any:
    if not content:
        logger.error("Model returned empty content for model=%s", model_name)
        raise RuntimeError("Model returned empty message content")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as err:
        _maybe_dump_raw_response(content, model_name)
        logger.warning("Direct JSON parse failed, attempting to extract JSON: %s", err)
        parsed = _extract_json(content)
        if parsed is None:
            repaired = _repair_json_text(content)
            try:
                parsed = json.loads(repaired)
            except Exception as repair_err:
                _maybe_dump_raw_response(repaired, model_name, suffix="repaired")
                logger.error("Failed to parse model response as JSON: %s", err)
                raise RuntimeError(
                    "Model output is not valid JSON. Tune prompt/model settings."
                ) from repair_err
    logger.info("Chat request completed model=%s", model_name)
    _maybe_dump_raw_response(content, model_name, suffix="ok")
    return parsed


def _extract_json(text: str) -> Optional[Any]:
    """Best-effort JSON extractor from a mixed model response."""
    decoder = json.JSONDecoder()
    for idx, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[idx:])
            return parsed
        except json.JSONDecodeError:
            continue
    return None


def _repair_json_text(text: str) -> str:
    """Attempts to repair common JSON issues from LLM output."""
    cleaned = text.strip()
    # Strip code fences if present.
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    # Extract the largest JSON-looking substring.
    start = min([i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1], default=0)
    end_curly = cleaned.rfind("}")
    end_bracket = cleaned.rfind("]")
    end = max(end_curly, end_bracket)
    if end > start:
        cleaned = cleaned[start : end + 1]

    # Normalize smart quotes to standard quotes.
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")

    # Remove trailing commas before object/array closure.
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _maybe_dump_raw_response(content: str, model_name: str, *, suffix: str = "raw") -> None:
    """Optionally dumps raw model output for debugging."""
    debug_dir = os.getenv("LLM_DEBUG_DIR")
    if not debug_dir:
        return
    always = os.getenv("LLM_DEBUG_ALWAYS") == "1"
    if suffix == "ok" and not always:
        return
    try:
        os.makedirs(debug_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_model = re.sub(r"[^a-zA-Z0-9_.-]+", "_", model_name or "model")
        filename = f"llm_{safe_model}_{suffix}_{ts}.txt"
        path = os.path.join(debug_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.warning("Saved LLM debug output to %s", path)
    except Exception as err:
        logger.warning("Failed to write LLM debug output: %s", err)


def _post_json_with_auth(
    url: str,
    payload: Dict[str, Any],
    *,
    api_key: str,
    timeout_seconds: int,
) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="ignore")
        if "<html" in detail.lower():
            detail = "HTML error page returned (check API base URL)."
        logger.error("OpenAI-compatible HTTPError %s: %s", err.code, detail)
        raise RuntimeError(f"OpenAI-compatible HTTP {err.code}: {detail}") from err
    except urllib.error.URLError as err:
        logger.error("OpenAI-compatible URLError: %s", err)
        raise RuntimeError(f"Cannot reach API server at {url}: {err}") from err


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat client via HTTP API."""

    def __init__(self, config: OllamaGenerationConfig):
        self.config = config

    def health_check(self) -> bool:
        if not self.config.api_base_url:
            logger.warning("OpenAI-compatible base URL not set")
            return False
        base = _normalize_openai_base(self.config.api_base_url)
        url = f"{base}/models"
        req = urllib.request.Request(url, method="GET")
        if self.config.api_key:
            req.add_header("Authorization", f"Bearer {self.config.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds):
                logger.info("OpenAI-compatible health check passed: %s", self.config.api_base_url)
                return True
        except Exception as err:
            logger.warning("OpenAI-compatible health check failed: %s", err)
            return False

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        active_model = model or self.config.model
        if not self.config.api_base_url:
            raise RuntimeError("API base URL is required for OpenAI-compatible provider")
        if not self.config.api_key:
            raise RuntimeError("API key is required for OpenAI-compatible provider")

        logger.info("Sending chat request to OpenAI-compatible model=%s", active_model)
        base = _normalize_openai_base(self.config.api_base_url)
        url = f"{base}/chat/completions"
        payload: Dict[str, Any] = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.num_predict,
        }
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        if self.config.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        raw = _post_json_with_auth(
            url,
            payload,
            api_key=self.config.api_key,
            timeout_seconds=self.config.timeout_seconds,
        )
        content = (
            raw.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        return _parse_json_response(content, active_model)

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> str:
        active_model = model or self.config.model
        if not self.config.api_base_url:
            raise RuntimeError("API base URL is required for OpenAI-compatible provider")
        if not self.config.api_key:
            raise RuntimeError("API key is required for OpenAI-compatible provider")

        logger.info("Sending chat_text request to OpenAI-compatible model=%s", active_model)
        base = _normalize_openai_base(self.config.api_base_url)
        url = f"{base}/chat/completions"
        payload: Dict[str, Any] = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.num_predict,
        }
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        if self.config.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        raw = _post_json_with_auth(
            url,
            payload,
            api_key=self.config.api_key,
            timeout_seconds=self.config.timeout_seconds,
        )
        content = (
            raw.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            logger.error("Model returned empty content for model=%s", active_model)
            raise RuntimeError("Model returned empty message content")
        _maybe_dump_raw_response(content, active_model, suffix="ok")
        return str(content).strip()


class GeminiClient:
    """Minimal Gemini client via google-genai SDK."""

    def __init__(self, config: OllamaGenerationConfig):
        self.config = config
        self._min_interval_seconds = self._resolve_min_interval_seconds(config)
        self._next_allowed_time = 0.0

    @staticmethod
    def _resolve_min_interval_seconds(config: OllamaGenerationConfig) -> float:
        if config.min_request_interval_seconds is not None:
            return max(0.0, float(config.min_request_interval_seconds))
        if config.rate_limit_rpm:
            return max(0.0, 60.0 / float(config.rate_limit_rpm))
        return 0.0

    def _throttle_if_needed(self) -> None:
        if self._min_interval_seconds <= 0:
            return
        now = time.monotonic()
        wait_seconds = self._next_allowed_time - now
        if wait_seconds > 0:
            logger.info("Gemini rate limit: sleeping %.2fs", wait_seconds)
            time.sleep(wait_seconds)
        self._next_allowed_time = time.monotonic() + self._min_interval_seconds

    def _get_client(self):
        try:
            from google import genai
        except Exception as err:
            raise RuntimeError("google-genai is required for Gemini provider") from err
        if not self.config.api_key:
            raise RuntimeError("API key is required for Gemini provider")
        return genai.Client(api_key=self.config.api_key)

    def _compose_prompt(self, system_prompt: str, user_prompt: str) -> str:
        if system_prompt and user_prompt:
            return f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"
        if system_prompt:
            return system_prompt
        return user_prompt

    def health_check(self) -> bool:
        if not self.config.api_key:
            logger.warning("Gemini API key not set")
            return False
        try:
            self._get_client()
            return True
        except Exception as err:
            logger.warning("Gemini client init failed: %s", err)
            return False

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        content = self.chat_text(system_prompt=system_prompt, user_prompt=user_prompt, model=model)
        return _parse_json_response(content, model or self.config.model)

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> str:
        client = self._get_client()
        active_model = model or self.config.model
        prompt = self._compose_prompt(system_prompt, user_prompt)
        logger.info("Sending chat_text request to Gemini model=%s", active_model)
        self._throttle_if_needed()
        response = client.models.generate_content(model=active_model, contents=prompt)
        text = getattr(response, "text", None)
        if not text:
            text = str(response)
        if not str(text).strip():
            logger.error("Model returned empty content for model=%s", active_model)
            raise RuntimeError("Model returned empty message content")
        _maybe_dump_raw_response(str(text), active_model, suffix="ok")
        return str(text).strip()


def _normalize_openai_base(base_url: str) -> str:
    """Ensure base URL ends with /v1 exactly once."""
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


class LLMClient:
    """Unified LLM client that supports Ollama or OpenAI-compatible providers."""

    def __init__(self, config: OllamaGenerationConfig):
        self.config = config
        self.provider = (config.provider or "ollama").lower()
        if self.provider == "ollama":
            self._client = OllamaClient(config)
        elif self.provider == "openai_compatible":
            self._client = OpenAICompatibleClient(config)
        elif self.provider == "gemini":
            self._client = GeminiClient(config)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def health_check(self) -> bool:
        return self._client.health_check()

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._client.chat(system_prompt=system_prompt, user_prompt=user_prompt, model=model)

    def chat_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: Optional[str] = None,
    ) -> str:
        return self._client.chat_text(system_prompt=system_prompt, user_prompt=user_prompt, model=model)


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Splits a list into fixed-size chunks.

    Args:
        items: Input list to split.
        chunk_size: Maximum number of elements per chunk; must be greater than 0.

    Returns:
        List of chunked sublists.

    Raises:
        ValueError: If ``chunk_size`` is less than or equal to zero.

    Example usage:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
