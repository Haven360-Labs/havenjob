"""Abstract base for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMProvider(ABC):
    """Interface for LLM completion (OpenAI, Anthropic, etc.)."""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send messages and return the assistant reply as plain text.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}.
            system_prompt: Optional system instruction (prepended or sent as system).
            max_tokens: Maximum tokens in the response.

        Returns:
            Assistant message content.
        """
        pass

    def stream_complete(
        self,
        messages: list[dict[str, str]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """
        Send messages and stream the assistant reply as text chunks.
        Default implementation falls back to complete() and yields the full reply.
        """
        full = self.complete(
            messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )
        if full:
            yield full
