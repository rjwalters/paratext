"""Provider abstraction for LLM backends."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..schemas import ModelResponse


@runtime_checkable
class ModelProvider(Protocol):
    """Minimal interface every provider must implement.

    `complete` takes a list of OpenAI-style messages (`{"role": ..., "content": ...}`)
    and returns a normalized `ModelResponse`. Provider-specific request options
    can be passed via `**kwargs`; providers that don't recognize a kwarg should
    silently ignore it (so callers don't need provider-specific branches).
    """

    name: str

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        seed: int | None = None,
        max_tokens: int | None = None,
        response_format: str | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        ...
