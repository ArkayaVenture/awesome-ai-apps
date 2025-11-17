"""Factory helpers for building LLM model instances."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Tuple

from agno.models.nebius import Nebius
from agno.models.openai import OpenAIChat

logger = logging.getLogger(__name__)

try:
    from agno.models.anthropic import Claude

    ANTHROPIC_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    Claude = None
    ANTHROPIC_AVAILABLE = False

DEFAULT_LLM_PROVIDER = "nebius"
DEFAULT_LLM_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"


LLM_PROVIDER_OPTIONS: Dict[str, Dict] = {
    "nebius": {
        "label": "Nebius (Meta-Llama)",
        "engine": "nebius",
        "requires": ["nebius"],
        "description": "High-context Nebius-hosted Meta-Llama models",
        "default_model": DEFAULT_LLM_MODEL,
        "models": [
            {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct", "label": "Meta-Llama 3.1 70B"},
            {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct", "label": "Meta-Llama 3.1 8B"},
            {"id": "google/gemini-1.5-pro", "label": "Gemini 1.5 Pro (via Nebius)"},
        ],
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "engine": "openai",
        "requires": ["openai"],
        "description": "ChatGPT models for conversational analysis",
        "default_model": "gpt-4o",
        "models": [
            {"id": "gpt-5", "label": "ChatGPT-5"},
            {"id": "gpt-4.1", "label": "GPT-4.1"},
            {"id": "gpt-4.1-mini", "label": "GPT-4.1 Mini"},
            {"id": "gpt-4.1-nano", "label": "GPT-4.1 Nano"},
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o Mini"},
        ],
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "engine": "anthropic",
        "requires": ["anthropic"],
        "description": "Claude models for high reasoning workloads",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": [
            {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"id": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
            {"id": "claude-3-haiku-20240307", "label": "Claude 3 Haiku"},
        ],
    },
    "qwen": {
        "label": "Qwen (via Nebius)",
        "engine": "nebius",
        "requires": ["nebius"],
        "description": "Alibaba Qwen models hosted on Nebius",
        "default_model": "Qwen/Qwen2.5-72B-Instruct",
        "models": [
            {"id": "Qwen/Qwen2.5-72B-Instruct", "label": "Qwen2.5 72B Instruct"},
            {"id": "Qwen/Qwen2.5-Coder-32B-Instruct", "label": "Qwen2.5 Coder 32B"},
        ],
    },
}


def provider_requirements_met(provider_key: str) -> bool:
    """Return True if the provider's dependencies are satisfied."""
    provider = LLM_PROVIDER_OPTIONS.get(provider_key)
    if not provider:
        return False
    for requirement in provider.get("requires", []):
        if requirement == "anthropic" and not ANTHROPIC_AVAILABLE:
            return False
    return True


def provider_dependency_warning(provider_key: str) -> Optional[str]:
    """Return a user-friendly warning if dependencies are missing."""
    if provider_key == "anthropic" and not ANTHROPIC_AVAILABLE:
        return "Install the `anthropic` package to enable Claude models: pip install anthropic"
    return None


def get_provider_labels(include_unavailable: bool = False) -> List[Tuple[str, str]]:
    """Return provider key/label pairs."""
    providers: List[Tuple[str, str]] = []
    for key, data in LLM_PROVIDER_OPTIONS.items():
        available = provider_requirements_met(key)
        if not include_unavailable and not available:
            continue
        label = data["label"]
        if not available:
            label = f"{label} (install dependency)"
        providers.append((key, label))
    return providers


def get_model_options(provider_key: str) -> List[Dict[str, str]]:
    """Return available models for a provider."""
    if not provider_requirements_met(provider_key):
        provider_key = DEFAULT_LLM_PROVIDER
    provider = LLM_PROVIDER_OPTIONS.get(provider_key) or LLM_PROVIDER_OPTIONS[DEFAULT_LLM_PROVIDER]
    return provider.get("models", [])


def _resolve_provider(provider_key: Optional[str]) -> Tuple[str, Dict]:
    key = (provider_key or DEFAULT_LLM_PROVIDER).lower()
    if key not in LLM_PROVIDER_OPTIONS:
        logger.warning("Unknown LLM provider '%s'. Falling back to default.", provider_key)
        key = DEFAULT_LLM_PROVIDER
    if not provider_requirements_met(key):
        logger.warning("Provider '%s' is unavailable (missing dependencies). Using default.", key)
        key = DEFAULT_LLM_PROVIDER
    return key, LLM_PROVIDER_OPTIONS[key]


def create_llm_model(
    provider_key: Optional[str],
    model_id: Optional[str],
    api_keys: Optional[Dict[str, Optional[str]]] = None,
):
    """Create a model instance for the requested provider."""
    api_keys = api_keys or {}
    provider_key, provider = _resolve_provider(provider_key)
    if not provider_requirements_met(provider_key):
        warning = provider_dependency_warning(provider_key)
        if warning:
            raise ImportError(warning)
        raise ImportError(f"Provider '{provider_key}' is unavailable on this system.")
    engine = provider.get("engine", "nebius")
    model = model_id or provider.get("default_model") or DEFAULT_LLM_MODEL

    if engine == "openai":
        api_key = api_keys.get("openai") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required for ChatGPT models.")
        return OpenAIChat(id=model, api_key=api_key)

    if engine == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic support requires the `anthropic` package. Install with `pip install anthropic`.")
        api_key = api_keys.get("anthropic") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required for Claude models.")
        return Claude(id=model, api_key=api_key)

    # Default to Nebius-hosted models (including Qwen variants)
    api_key = api_keys.get("nebius") or os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise ValueError("Nebius API key is required for this model.")
    return Nebius(id=model, api_key=api_key)

