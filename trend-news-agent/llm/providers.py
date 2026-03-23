"""LLM client/provider helpers."""
from __future__ import annotations

from openai import OpenAI

from app.config import settings


_PROVIDER_CONFIG = {
    "openai": {
        "api_key": lambda: settings.OPENAI_API_KEY,
        "base_url": None,
        "default_model": "gpt-4o-mini",
    },
    "glm": {
        "api_key": lambda: settings.GLM_API_KEY,
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
    },
    "kimi": {
        "api_key": lambda: settings.KIMI_API_KEY,
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "minimax": {
        "api_key": lambda: settings.MINIMAX_API_KEY,
        "base_url": "https://api.minimax.chat/v1",
        "default_model": "MiniMax-Text-01",
    },
    "qwen": {
        "api_key": lambda: settings.QWEN_API_KEY,
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
}


def _provider_name() -> str:
    provider = settings.LLM_PROVIDER.strip().lower()
    if provider not in _PROVIDER_CONFIG:
        supported = ", ".join(sorted(_PROVIDER_CONFIG))
        raise ValueError(f"Unsupported LLM_PROVIDER={settings.LLM_PROVIDER!r}, supported: {supported}")
    return provider


def get_llm_model() -> str:
    """Return configured model or provider default model."""
    provider = _provider_name()
    if settings.LLM_MODEL.strip():
        return settings.LLM_MODEL.strip()
    return _PROVIDER_CONFIG[provider]["default_model"]


def get_llm_client() -> OpenAI:
    """Build OpenAI-compatible client for the selected provider."""
    provider = _provider_name()
    config = _PROVIDER_CONFIG[provider]
    api_key = config["api_key"]()
    if not api_key or api_key == "replace-me":
        env_name = f"{provider.upper()}_API_KEY" if provider != "openai" else "OPENAI_API_KEY"
        raise ValueError(f"Missing API key for provider '{provider}'. Set {env_name}.")

    if config["base_url"]:
        return OpenAI(api_key=api_key, base_url=config["base_url"])
    return OpenAI(api_key=api_key)
