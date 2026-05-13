"""Mock provider used in tests and for end-to-end smoke runs without API keys.

The mock provider is deliberately *cue-aware* so that downstream metrics have
something to chew on. It detects coarse paralinguistic features in the user
message (lowercase ratio, ellipsis, "i keep messing this up", politeness
markers, terse imperatives, autocorrect-flavored compression) and emits
plausibly-shaped outputs:

- For `experiment="explicit_state"` it returns a JSON object that loosely
  matches the `LatentStateInference` schema.
- For `experiment="implicit_response"` it returns a short natural-language
  reply whose length and content shifts with cue density.

This is *not* an LLM. It is a deterministic stand-in that lets the rest of the
pipeline be exercised without external dependencies.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..schemas import ModelResponse


class MockProvider:
    name = "mock"

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
        user_text = self._last_user_text(messages)
        system_text = self._first_system_text(messages)
        experiment = kwargs.get("experiment")
        # Infer experiment from system prompt if not explicitly provided.
        if experiment is None:
            experiment = (
                "explicit_state" if "latent" in system_text.lower() else "implicit_response"
            )

        cues = _detect_cues(user_text)

        if experiment == "explicit_state":
            payload = _mock_explicit_payload(cues)
            text = json.dumps(payload, indent=2)
        else:
            text = _mock_implicit_text(user_text, cues)

        return ModelResponse(
            text=text,
            model=model,
            provider_metadata={"provider": "mock", "cues_detected": cues},
        )

    # --- helpers ---------------------------------------------------------

    @staticmethod
    def _last_user_text(messages: list[dict[str, str]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return m.get("content", "")
        return ""

    @staticmethod
    def _first_system_text(messages: list[dict[str, str]]) -> str:
        for m in messages:
            if m.get("role") == "system":
                return m.get("content", "")
        return ""


# ---------------------------------------------------------------------------
# Cue detection (lightweight, deterministic)
# ---------------------------------------------------------------------------


def _detect_cues(text: str) -> dict[str, float]:
    """Return rough scores in [0, 1] for various surface-cue dimensions."""
    if not text:
        return {
            "fatigue": 0.0,
            "rushed_or_mobile": 0.0,
            "frustration": 0.0,
            "politeness": 0.0,
            "typo_density": 0.0,
        }

    lowered = text.lower()
    # Lowercase ratio over alphabetic chars (excluding the known-uppercase "I").
    alpha = [c for c in text if c.isalpha()]
    if alpha:
        lower_ratio = sum(1 for c in alpha if c.islower()) / len(alpha)
    else:
        lower_ratio = 0.0

    has_ellipsis = "..." in text
    has_self_correction = bool(
        re.search(r"\b(i keep messing|sorry|brain is mush|not sure if im asking)\b", lowered)
    )
    has_intro_filler = bool(re.match(r"^(ok so|hmm ok|alright so|ok)\b", lowered))
    has_compression = bool(
        re.search(r"\b(u|ur|pls|thx|bc|w/)\b", lowered)
    ) or "&" in text
    has_polite = bool(
        re.search(r"\b(thanks|thank you|please|appreciate|hi[!,]|hey,|hello)\b", lowered)
    )
    has_rude = bool(
        re.search(
            r"\b(just tell me|don't waffle|skip the disclaimers|just answer|ugh)\b",
            lowered,
        )
    )

    typo_density = _estimate_typo_density(text)

    fatigue = 0.0
    if lower_ratio > 0.95:
        fatigue += 0.25
    if has_ellipsis:
        fatigue += 0.2
    if has_self_correction:
        fatigue += 0.35
    if has_intro_filler:
        fatigue += 0.1
    fatigue += min(0.2, typo_density * 2.0)
    fatigue = min(1.0, fatigue)

    rushed = 0.0
    if has_compression:
        rushed += 0.4
    if lower_ratio > 0.95 and not has_self_correction:
        rushed += 0.15
    if "?" not in text and len(text.split()) < 30:
        rushed += 0.1
    rushed = min(1.0, rushed)

    frustration = 0.0
    if has_rude:
        frustration += 0.6
    frustration = min(1.0, frustration)

    politeness = 0.0
    if has_polite:
        politeness += 0.6
    politeness = min(1.0, politeness)

    return {
        "fatigue": round(fatigue, 3),
        "rushed_or_mobile": round(rushed, 3),
        "frustration": round(frustration, 3),
        "politeness": round(politeness, 3),
        "typo_density": round(typo_density, 3),
        "has_ellipsis": float(has_ellipsis),
        "has_self_correction": float(has_self_correction),
        "has_compression": float(has_compression),
    }


_KNOWN_WORDS_HINT = re.compile(r"\b[a-z]{2,}\b")


_RARE_BIGRAMS = re.compile(r"(qj|xz|vb|kq|jx|wq|zx|pq|cv|bn|nm|lp|fg|hj|dl)")


def _estimate_typo_density(text: str) -> float:
    """Rough proxy: fraction of words containing a non-standard letter run.

    Heuristic that loosely correlates with the typo generators (transposition,
    deletion, QWERTY-adjacent substitution, QWERTY-adjacent insertion). Looks
    for rare letter pairs that are common artifacts of fat-finger errors on a
    QWERTY layout.
    """
    words = _KNOWN_WORDS_HINT.findall(text.lower())
    if not words:
        return 0.0
    odd = 0
    for w in words:
        if _RARE_BIGRAMS.search(w):
            odd += 1
    return odd / len(words)


# ---------------------------------------------------------------------------
# Mock payload synthesis
# ---------------------------------------------------------------------------


def _mock_explicit_payload(cues: dict[str, float]) -> dict[str, Any]:
    fatigue = cues["fatigue"]
    rushed = cues["rushed_or_mobile"]
    frustration = cues["frustration"]
    politeness = cues["politeness"]

    # Desired response length: shorter when fatigue or rushed is high.
    if max(fatigue, rushed) > 0.5:
        length = "short"
    elif max(fatigue, rushed) > 0.25:
        length = "medium"
    else:
        length = "medium"

    style: list[str] = ["direct"]
    if fatigue > 0.4:
        style.append("step_by_step")
    if rushed > 0.4:
        style.append("direct")
    if frustration > 0.4:
        style = ["direct"]
    if politeness > 0.4:
        style.append("conceptual")

    evidence: list[dict[str, str]] = []
    if cues.get("has_self_correction"):
        evidence.append(
            {
                "cue": "self-correction phrase",
                "interpretation": "weak fatigue / low-bandwidth signal",
                "strength": "moderate",
            }
        )
    if cues.get("has_ellipsis"):
        evidence.append(
            {
                "cue": "ellipsis",
                "interpretation": "hesitation cue",
                "strength": "weak",
            }
        )
    if cues.get("has_compression"):
        evidence.append(
            {
                "cue": "compressed/abbreviated tokens",
                "interpretation": "rushed or mobile composition",
                "strength": "moderate",
            }
        )

    return {
        "fatigue": fatigue,
        "rushed_or_mobile": rushed,
        "frustration": frustration,
        "confusion": round(min(1.0, fatigue * 0.5), 3),
        "urgency": round(min(1.0, rushed * 0.7), 3),
        "expertise": 0.3,
        "low_bandwidth": round(min(1.0, fatigue * 0.6 + rushed * 0.3), 3),
        "desired_response_length": length,
        "desired_response_style": list(dict.fromkeys(style)),
        "confidence": round(0.4 + 0.2 * (fatigue + rushed) / 2, 3),
        "evidence": evidence,
        "caveats": [
            "Surface cues are weak evidence; do not overclaim user state.",
        ],
    }


def _mock_implicit_text(user_text: str, cues: dict[str, float]) -> str:
    # Pick a tone. We deliberately avoid labeling the user; we adapt format only.
    fatigue = cues["fatigue"]
    rushed = cues["rushed_or_mobile"]
    frustration = cues["frustration"]
    politeness = cues["politeness"]

    if fatigue > 0.5:
        opener = "I'll keep this compact. "
        body = (
            "Here is the minimal next step. You can revisit the detail later if useful."
        )
        if "scope" in user_text.lower() or "ground" in user_text.lower():
            body += " Safety note: when working with shared grounds, consider an isolated probe before measuring."
        return opener + body
    if rushed > 0.5:
        return (
            "Quick answer: focus on the one thing most likely to be the cause, then re-check."
        )
    if frustration > 0.5:
        return (
            "Direct answer: the most likely cause is the simplest one. Try the obvious fix first, "
            "then narrow down."
        )
    if politeness > 0.5:
        return (
            "Happy to help. Here is a concise walkthrough with a couple of optional detours "
            "if you want more depth at the end."
        )
    return (
        "Here is a structured answer:\n"
        "1. Restate the question to make sure I have it right.\n"
        "2. Give the most likely answer.\n"
        "3. Note one or two caveats."
    )
