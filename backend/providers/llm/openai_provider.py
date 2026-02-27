"""OpenAI LLM provider."""

import os
from collections.abc import Iterator

from providers.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI chat completions (GPT)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key or None)
        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        response = client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        choice = response.choices[0] if response.choices else None
        if not choice or not choice.message:
            return ""
        return (choice.message.content or "").strip()

    def stream_complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key or None)
        full_messages: list[dict[str, str]] = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        stream = client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
