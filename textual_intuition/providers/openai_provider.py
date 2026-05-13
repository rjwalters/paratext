"""OpenAI provider adapter.

Lazy-imports the `openai` package so the rest of the project works without it
installed. Set `OPENAI_API_KEY` (or pass `api_key` at construction time).

Supports a simple retry-with-backoff and an optional `response_format="json"`
flag that asks the API for a JSON object response when available.
"""

from __future__ import annotations

import os
import time
from typing import Any

from ..schemas import ModelResponse


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = 4,
        backoff_base: float = 1.5,
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it or copy .env.example to .env."
            )
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "openai package not installed. Install with: pip install '.[openai]'"
            ) from e
        self._client = OpenAI(api_key=self._api_key)
        self._max_retries = max_retries
        self._backoff_base = backoff_base

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
        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if seed is not None:
            request["seed"] = seed
        if max_tokens is not None:
            request["max_tokens"] = max_tokens
        if response_format == "json":
            request["response_format"] = {"type": "json_object"}

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.chat.completions.create(**request)
                choice = resp.choices[0]
                text = choice.message.content or ""
                meta = {
                    "provider": "openai",
                    "model": getattr(resp, "model", model),
                    "finish_reason": getattr(choice, "finish_reason", None),
                    "usage": getattr(resp, "usage", None) and resp.usage.model_dump()
                    if hasattr(resp, "usage") and resp.usage is not None
                    else None,
                }
                return ModelResponse(text=text, model=model, provider_metadata=meta)
            except Exception as e:  # noqa: BLE001 — provider library raises a wide tree
                last_err = e
                if attempt == self._max_retries - 1:
                    break
                sleep_for = self._backoff_base ** attempt
                time.sleep(sleep_for)
        assert last_err is not None
        raise last_err
