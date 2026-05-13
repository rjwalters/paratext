"""Provider registry.

Models are addressed as `scheme/model_id`, e.g. `mock/echo` or
`openai/gpt-4o-mini`. The scheme picks the provider; the model id is passed
through to the provider's `complete()`.
"""

from __future__ import annotations

from .base import ModelProvider
from .mock import MockProvider


def parse_model_spec(spec: str) -> tuple[str, str]:
    """Split a `scheme/model_id` spec, e.g. `openai/gpt-4o-mini`."""
    if "/" not in spec:
        raise ValueError(
            f"Model spec must be of the form 'scheme/model_id', got: {spec!r}"
        )
    scheme, _, model_id = spec.partition("/")
    return scheme, model_id


def get_provider(scheme: str) -> ModelProvider:
    """Return an instance of the requested provider scheme."""
    if scheme == "mock":
        return MockProvider()
    if scheme == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    raise ValueError(
        f"Unknown provider scheme: {scheme!r}. "
        "Known schemes: mock, openai. "
        "To add one, implement the ModelProvider protocol and register it here."
    )


__all__ = ["ModelProvider", "MockProvider", "get_provider", "parse_model_spec"]
