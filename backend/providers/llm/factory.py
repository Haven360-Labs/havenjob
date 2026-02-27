"""Factory to get the configured LLM provider."""

import os

from providers.llm.anthropic_provider import AnthropicProvider
from providers.llm.base import LLMProvider
from providers.llm.openai_provider import OpenAIProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_llm(
    provider: str | None = None,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """
    Return the configured LLM provider instance.

    Args:
        provider: "openai" or "anthropic". Defaults to env LLM_PROVIDER or "openai".
        api_key: Override API key (otherwise from OPENAI_API_KEY / ANTHROPIC_API_KEY).
        model: Optional model name override.

    Returns:
        LLMProvider instance.
    """
    name = (provider or os.environ.get("LLM_PROVIDER", "openai")).lower()
    if name not in PROVIDERS:
        name = "openai"
    cls = PROVIDERS[name]
    if name == "openai":
        return cls(api_key=api_key, model=model or "gpt-4o-mini")
    return cls(api_key=api_key, model=model or "claude-3-5-haiku-20241022")
