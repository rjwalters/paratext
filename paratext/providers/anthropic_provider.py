"""Anthropic provider adapter.

Lazy-imports the `anthropic` package so the rest of the project works without it
installed. Set `ANTHROPIC_API_KEY` (or pass `api_key` at construction time).

Notes specific to Anthropic vs the OpenAI adapter:

- The Anthropic API takes `system` as a top-level kwarg, not as a message role.
  We extract the first system message from the OpenAI-style `messages` list
  and pass it through; remaining messages must alternate user/assistant.
- Anthropic does not support a `seed` parameter. We silently ignore it (per
  the Provider interface design rule).
- **Sampling parameters on Opus 4.7**: `temperature`, `top_p`, and `top_k`
  return 400 on `claude-opus-4-7`. The adapter silently drops `temperature`
  for any model whose ID contains `opus-4-7`. Other Claude 4.x models still
  accept `temperature`.
- No native JSON-mode equivalent to OpenAI's `response_format`. Paratext's
  explicit-state experiment relies on the system prompt instructing JSON-only
  output, plus the existing `_sanitize_json` parser to handle Opus's
  occasional bare-enum quirk.
- Prompt caching: we mark the system prompt with `cache_control: ephemeral`.
  For paratext's short ~150-token system prompts this is below the 4096-token
  caching threshold on Opus and won't actually cache, but the marker is
  harmless and will activate automatically if the system prompt grows.
- Retries: the official `anthropic` SDK already retries 408/409/429/5xx with
  exponential backoff. We just configure `max_retries` and let it run.
"""

from __future__ import annotations

import os
from typing import Any

from ..schemas import ModelResponse


def _model_supports_sampling_params(model: str) -> bool:
    """Opus 4.7 rejects temperature/top_p/top_k. Strip them silently for that model."""
    return "opus-4-7" not in model.lower()


def _split_system_and_messages(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[dict[str, str]]]:
    """Pull the first system message out; Anthropic takes it as a kwarg."""
    system: str | None = None
    rest: list[dict[str, str]] = []
    for m in messages:
        role = m.get("role")
        if role == "system" and system is None:
            system = m.get("content", "")
            continue
        rest.append({"role": role, "content": m.get("content", "")})
    return system, rest


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = 4,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or copy .env.example to .env."
            )
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. Install with: pip install '.[anthropic]'"
            ) from e
        # The SDK auto-retries 408/409/429/5xx with exponential backoff.
        self._client = Anthropic(api_key=self._api_key, max_retries=max_retries)

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.7,
        seed: int | None = None,  # ignored — Anthropic API does not support it
        max_tokens: int | None = None,
        response_format: str | None = None,  # ignored — see module docstring
        **kwargs: Any,
    ) -> ModelResponse:
        system_text, anthropic_messages = _split_system_and_messages(messages)

        request: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            # max_tokens is required by the Anthropic API. 4096 is plenty for
            # the explicit-state JSON output (~500 tokens) and reasonable for
            # the implicit-response experiment (~1000-2000 tokens). Caller can
            # override.
            "max_tokens": max_tokens if max_tokens is not None else 4096,
        }

        if system_text is not None:
            # Mark the system prompt as cacheable. For paratext's short system
            # prompts this is below the per-model caching threshold and won't
            # actually cache, but the marker is harmless and will activate
            # automatically if the system prompt grows.
            request["system"] = [
                {
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        if _model_supports_sampling_params(model):
            request["temperature"] = temperature
        # Else: silently drop. Opus 4.7 returns 400 on temperature.

        resp = self._client.messages.create(**request)

        # Concatenate text blocks; ignore any thinking blocks (they're empty by
        # default on Opus 4.7 anyway).
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )

        meta: dict[str, Any] = {
            "provider": "anthropic",
            "model": getattr(resp, "model", model),
            "stop_reason": getattr(resp, "stop_reason", None),
        }
        usage = getattr(resp, "usage", None)
        if usage is not None:
            meta["usage"] = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "cache_creation_input_tokens": getattr(
                    usage, "cache_creation_input_tokens", None
                ),
                "cache_read_input_tokens": getattr(
                    usage, "cache_read_input_tokens", None
                ),
            }

        return ModelResponse(text=text, model=model, provider_metadata=meta)
