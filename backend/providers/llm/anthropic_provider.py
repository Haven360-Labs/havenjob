"""Anthropic LLM provider."""

import os
from collections.abc import Iterator

from providers.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API (Claude)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-haiku-20241022",
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key or None)
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=messages,
        )
        if not response.content:
            return ""
        text_parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        return "".join(text_parts).strip()

    def stream_complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key or None)
        with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text
