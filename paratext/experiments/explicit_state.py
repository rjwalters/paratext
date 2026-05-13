"""Experiment 1: explicit latent-state inference.

Ask the model to read the user message and return a structured estimate of
likely latent state, with required textual evidence and explicit caveats.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from typing import Any

from ..providers import ModelProvider
from ..schemas import LatentStateInference, PromptVariant, RunRecord

EXPERIMENT_NAME = "explicit_state"

SYSTEM_PROMPT = """\
You are an analyst inferring likely *latent state* of a user from a single message.

Constraints:
- Use only textual evidence in the user's message.
- Treat surface cues (typos, capitalization, punctuation, hedging, ellipses,
  politeness markers, terse imperatives, autocorrect-flavored compression) as
  *weak* evidence.
- Do not overclaim. Prefer hedged language. Use 0.0-1.0 scores.
- Cite specific cues you used. Strength must be one of: weak, moderate, strong.
- If you are uncertain, say so via lower confidence and explicit caveats.

Return ONLY a single JSON object that matches this schema (no prose, no markdown):

{
  "fatigue": 0.0,
  "rushed_or_mobile": 0.0,
  "frustration": 0.0,
  "confusion": 0.0,
  "urgency": 0.0,
  "expertise": 0.0,
  "low_bandwidth": 0.0,
  "desired_response_length": "short" | "medium" | "long",
  "desired_response_style": ["direct" | "step_by_step" | "safety_first" | "reassuring" | "technical" | "conceptual"],
  "confidence": 0.0,
  "evidence": [{"cue": "...", "interpretation": "...", "strength": "weak|moderate|strong"}],
  "caveats": ["..."]
}
"""


def _build_messages(variant: PromptVariant) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": variant.text},
    ]


_BARE_ENUM_FIX = re.compile(
    r'("strength"\s*:\s*)(weak|moderate|strong)\b',
    re.IGNORECASE,
)
_BARE_LENGTH_FIX = re.compile(
    r'("desired_response_length"\s*:\s*)(short|medium|long)\b',
    re.IGNORECASE,
)


def _sanitize_json(s: str) -> str:
    """Patch common LLM JSON-output errors: bare enum values, trailing commas."""
    s = _BARE_ENUM_FIX.sub(lambda m: f'{m.group(1)}"{m.group(2).lower()}"', s)
    s = _BARE_LENGTH_FIX.sub(lambda m: f'{m.group(1)}"{m.group(2).lower()}"', s)
    # Trailing commas inside objects / arrays.
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s


def _parse_inference(text: str) -> dict[str, Any]:
    """Best-effort parse of a JSON object from a model response."""
    candidate = text.strip()
    # Strip ```json fences if the model added them despite the instruction.
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        # Drop a leading "json\n" tag if present.
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].lstrip("\n")

    def _try_load(s: str):
        try:
            return json.loads(s), None
        except json.JSONDecodeError as e:
            try:
                return json.loads(_sanitize_json(s)), None
            except json.JSONDecodeError as e2:
                return None, e2

    obj, err = _try_load(candidate)
    if obj is None:
        # Try to slice to the outermost braces.
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"_parse_error": "no JSON object found", "_raw": text}
        obj, err = _try_load(candidate[start : end + 1])
        if obj is None:
            return {"_parse_error": str(err), "_raw": text}

    # Validate softly: coerce to LatentStateInference, but keep the raw dict if it fails.
    try:
        validated = LatentStateInference.model_validate(obj).model_dump()
        return validated
    except Exception as e:  # noqa: BLE001
        return {"_validation_error": str(e), **obj}


def _run_id(model: str) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    safe_model = model.replace("/", "_")
    return f"{ts}_{safe_model}_{EXPERIMENT_NAME}"


def run(
    variants: Iterable[PromptVariant],
    provider: ModelProvider,
    model: str,
    temperature: float = 0.2,
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
            response_format="json",
            experiment=EXPERIMENT_NAME,
        )
        parsed = _parse_inference(response.text)
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
            parsed_output=parsed,
            provider_metadata=response.provider_metadata,
        )
