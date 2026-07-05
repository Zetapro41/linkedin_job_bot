import logging
from dataclasses import dataclass
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIProvider:
    name: str
    api_key: str
    model: str
    base_url: str


def _openai_compatible_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def resolve_ai_provider(config: Config) -> Optional[AIProvider]:
    """Resuelve el proveedor de IA según AI_PROVIDER y las keys disponibles."""
    provider = config.ai_provider.lower().strip()

    providers = {
        "openai": lambda: _provider_if_key(
            "ChatGPT (OpenAI)",
            config.openai_api_key,
            config.openai_model,
            "https://api.openai.com/v1",
        ),
        "gemini": lambda: _provider_if_key(
            "Gemini (Google)",
            config.gemini_api_key,
            config.gemini_model,
            "https://generativelanguage.googleapis.com/v1beta/openai",
        ),
        "grok": lambda: _provider_if_key(
            "Grok (xAI)",
            config.xai_api_key,
            config.xai_model,
            "https://api.x.ai/v1",
        ),
        "venice": lambda: _provider_if_key(
            "Venice AI",
            config.venice_api_key,
            config.venice_model,
            "https://api.venice.ai/api/v1",
        ),
        "custom": lambda: _provider_if_key(
            "API personalizada",
            config.ai_api_key,
            config.ai_model,
            config.ai_api_base_url,
        ),
    }

    if provider != "auto" and provider in providers:
        return providers[provider]()

    if provider == "auto":
        for key in ("openai", "gemini", "grok", "venice", "custom"):
            resolved = providers[key]()
            if resolved:
                return resolved

    return None


def _provider_if_key(
    name: str, api_key: str, model: str, base_url: str
) -> Optional[AIProvider]:
    if not api_key or not model or not base_url:
        return None
    return AIProvider(name=name, api_key=api_key, model=model, base_url=base_url)


def chat_completion(
    config: Config,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.5,
) -> tuple[Optional[str], Optional[str]]:
    """
    Envía un chat completion al proveedor configurado.
    Retorna (respuesta, error).
    """
    provider = resolve_ai_provider(config)
    if not provider:
        return None, "No hay API de IA configurada en .env"

    url = _openai_compatible_url(provider.base_url)
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": provider.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            return content, None

        logger.error(
            "Error de API %s (HTTP %s): %s",
            provider.name,
            response.status_code,
            response.text,
        )
        return None, f"Error de {provider.name} (HTTP {response.status_code})"
    except Exception as exc:
        logger.error("Excepción en API %s: %s", provider.name, exc)
        return None, f"Error de red con {provider.name}"