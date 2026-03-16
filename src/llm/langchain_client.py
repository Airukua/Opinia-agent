from __future__ import annotations

from typing import Any, Dict, Optional

from utils.logger import get_logger
from llm.generation_config import OllamaGenerationConfig

logger = get_logger(__name__)


def langchain_chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    config: OllamaGenerationConfig,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs a JSON-only chat using LangChain with Ollama or OpenAI-compatible backend."""
    provider = (config.provider or "ollama").lower()
    active_model = model or config.model

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except Exception as err:
            raise RuntimeError("langchain-ollama is required for Ollama provider") from err

        llm = ChatOllama(
            model=active_model,
            base_url=config.base_url,
            temperature=config.temperature,
            top_p=config.top_p,
            num_predict=config.num_predict,
            format=config.response_format or "json",
        )
    else:
        try:
            from langchain_openai import ChatOpenAI
        except Exception as err:
            raise RuntimeError("langchain-openai is required for OpenAI-compatible provider") from err
        if not config.api_key:
            raise RuntimeError("API key is required for OpenAI-compatible provider")

        llm = ChatOpenAI(
            model=active_model,
            api_key=config.api_key,
            base_url=config.api_base_url,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.num_predict,
        )

    logger.info("LangChain chat model=%s provider=%s", active_model, provider)
    messages = [
        ("system", system_prompt),
        ("human", user_prompt),
    ]
    response = llm.invoke(messages)
    content = getattr(response, "content", "") or ""
    return _parse_json_response(content)


def langchain_chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    config: OllamaGenerationConfig,
    model: Optional[str] = None,
) -> str:
    """Runs a free-form chat using LangChain with Ollama or OpenAI-compatible backend."""
    provider = (config.provider or "ollama").lower()
    active_model = model or config.model

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except Exception as err:
            raise RuntimeError("langchain-ollama is required for Ollama provider") from err

        llm = ChatOllama(
            model=active_model,
            base_url=config.base_url,
            temperature=config.temperature,
            top_p=config.top_p,
            num_predict=config.num_predict,
        )
    else:
        try:
            from langchain_openai import ChatOpenAI
        except Exception as err:
            raise RuntimeError("langchain-openai is required for OpenAI-compatible provider") from err
        if not config.api_key:
            raise RuntimeError("API key is required for OpenAI-compatible provider")

        llm = ChatOpenAI(
            model=active_model,
            api_key=config.api_key,
            base_url=config.api_base_url,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.num_predict,
        )

    logger.info("LangChain chat (text) model=%s provider=%s", active_model, provider)
    messages = [
        ("system", system_prompt),
        ("human", user_prompt),
    ]
    response = llm.invoke(messages)
    return getattr(response, "content", "") or ""


def _parse_json_response(content: str) -> Dict[str, Any]:
    import json

    if not content:
        raise RuntimeError("LangChain returned empty content")
    try:
        return json.loads(content)
    except json.JSONDecodeError as err:
        raise RuntimeError("LangChain response is not valid JSON") from err
