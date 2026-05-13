"""Experiment 2: implicit behavioral adaptation.

Ask the model to answer the user's message normally. We then look at the
response with a small set of regex/heuristic classifiers to see whether
behavior shifts with the cue class.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import UTC, datetime

from ..providers import ModelProvider
from ..schemas import PromptVariant, RunRecord

EXPERIMENT_NAME = "implicit_response"

SYSTEM_PROMPT = """\
You are a thoughtful, honest assistant. Answer the user's message helpfully.

Adapt your response naturally to the message — its tone, format, and length —
but do not psychoanalyze the user or label their emotional state. If the user
seems to want a short answer, give one. If they seem to want detail, give it.
Stay technically correct regardless of how the user writes.
"""


def _build_messages(variant: PromptVariant) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": variant.text},
    ]


def _run_id(model: str) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    safe_model = model.replace("/", "_")
    return f"{ts}_{safe_model}_{EXPERIMENT_NAME}"


def run(
    variants: Iterable[PromptVariant],
    provider: ModelProvider,
    model: str,
    temperature: float = 0.7,
    seed: int | None = 0,
) -> Iterator[RunRecord]:
    """Yield one RunRecord per variant."""
    rid = _run_id(model)
    for v in variants:
        messages = _build_messages(v)
        response = provider.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            seed=seed,
            experiment=EXPERIMENT_NAME,
        )
        # Lazy import to avoid a circular dep with the analysis package.
        from ..analysis.classifiers import classify_response

        features = classify_response(response.text)
        yield RunRecord(
            run_id=rid,
            model=f"{provider.name}/{model}",
            experiment=EXPERIMENT_NAME,
            prompt_variant_id=v.id,
            base_id=v.base_id,
            variant_class=v.variant_class,
            domain=v.domain,
            input_text=v.text,
            raw_output=response.text,
            parsed_output=features,
            provider_metadata=response.provider_metadata,
        )
