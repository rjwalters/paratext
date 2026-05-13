"""Pydantic schemas for prompts, variants, model outputs, and run records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Variant cue classes
# ---------------------------------------------------------------------------

VariantClass = Literal[
    "polished_neutral",
    "typo_light",
    "typo_heavy",
    "fatigue_coded",
    "rushed_mobile_coded",
    "polite_collaborative",
    "rude_frustrated",
    "random_typo_control",
    # Optional / stretch
    "explicit_fatigue",
    "expert_precise",
    "novice_confused",
    "skeptical",
    "playful",
    "dictation_artifact",
    "non_native_english_like",
    "high_stakes_safety",
]

ALL_VARIANT_CLASSES: tuple[str, ...] = (
    "polished_neutral",
    "typo_light",
    "typo_heavy",
    "fatigue_coded",
    "rushed_mobile_coded",
    "polite_collaborative",
    "rude_frustrated",
    "random_typo_control",
)

ExperimentName = Literal["explicit_state", "implicit_response"]

SemanticChangeRisk = Literal["low", "medium", "high"]

CueStrength = Literal["weak", "moderate", "strong"]

ResponseLength = Literal["short", "medium", "long"]


# ---------------------------------------------------------------------------
# Seed prompts
# ---------------------------------------------------------------------------


class SeedPrompt(BaseModel):
    """A base prompt before any cue perturbation."""

    id: str
    domain: str
    base_prompt: str
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class CueAnnotation(BaseModel):
    cue_type: str
    description: str


class PromptVariant(BaseModel):
    """A surface-form perturbation of a SeedPrompt."""

    id: str
    base_id: str
    domain: str
    variant_class: str
    text: str
    semantic_change_risk: SemanticChangeRisk = "low"
    cue_annotations: list[CueAnnotation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Explicit-state inference output
# ---------------------------------------------------------------------------


class EvidenceItem(BaseModel):
    cue: str
    interpretation: str
    strength: CueStrength = "weak"


class LatentStateInference(BaseModel):
    """The structured inference returned by the explicit-state experiment."""

    fatigue: float = 0.0
    rushed_or_mobile: float = 0.0
    frustration: float = 0.0
    confusion: float = 0.0
    urgency: float = 0.0
    expertise: float = 0.0
    low_bandwidth: float = 0.0
    desired_response_length: ResponseLength = "medium"
    desired_response_style: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[EvidenceItem] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

    @field_validator(
        "fatigue",
        "rushed_or_mobile",
        "frustration",
        "confusion",
        "urgency",
        "expertise",
        "low_bandwidth",
        "confidence",
    )
    @classmethod
    def _clip_unit_interval(cls, v: float) -> float:
        if v is None:
            return 0.0
        return max(0.0, min(1.0, float(v)))


# ---------------------------------------------------------------------------
# Model response wrapper (provider-level)
# ---------------------------------------------------------------------------


class ModelResponse(BaseModel):
    """A normalized response from any provider."""

    text: str
    model: str
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Run records (one row per (variant, model, experiment) trial)
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunRecord(BaseModel):
    """A single trial result, written one-per-line to a JSONL run file."""

    run_id: str
    model: str
    experiment: ExperimentName
    prompt_variant_id: str
    base_id: str
    variant_class: str
    domain: str
    input_text: str
    raw_output: str
    parsed_output: dict[str, Any] = Field(default_factory=dict)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utcnow_iso)
