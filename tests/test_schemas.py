"""Schema validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from textual_intuition.schemas import (
    CueAnnotation,
    LatentStateInference,
    PromptVariant,
    RunRecord,
    SeedPrompt,
)


def test_seed_prompt_minimal():
    p = SeedPrompt(id="x_001", domain="x", base_prompt="hello")
    assert p.tags == []
    assert p.notes is None


def test_prompt_variant_roundtrip():
    v = PromptVariant(
        id="x_001__fatigue_coded__v1",
        base_id="x_001",
        domain="x",
        variant_class="fatigue_coded",
        text="hello ...",
        cue_annotations=[CueAnnotation(cue_type="ellipsis", description="hesitation")],
    )
    blob = v.model_dump_json()
    parsed = PromptVariant.model_validate_json(blob)
    assert parsed == v


def test_latent_state_clips_unit_interval():
    inf = LatentStateInference(fatigue=1.5, rushed_or_mobile=-0.2, confidence=0.7)
    assert inf.fatigue == 1.0
    assert inf.rushed_or_mobile == 0.0
    assert inf.confidence == 0.7


def test_latent_state_default_lists_are_empty():
    inf = LatentStateInference()
    assert inf.evidence == []
    assert inf.caveats == []
    assert inf.desired_response_style == []


def test_run_record_required_fields():
    rec = RunRecord(
        run_id="r1",
        model="mock/echo",
        experiment="explicit_state",
        prompt_variant_id="x_001__polished_neutral__v1",
        base_id="x_001",
        variant_class="polished_neutral",
        domain="x",
        input_text="hello",
        raw_output="{}",
    )
    assert rec.created_at  # set by default factory


def test_run_record_rejects_unknown_experiment():
    with pytest.raises(ValidationError):
        RunRecord(
            run_id="r1",
            model="mock/echo",
            experiment="not_an_experiment",  # type: ignore[arg-type]
            prompt_variant_id="x",
            base_id="x",
            variant_class="polished_neutral",
            domain="x",
            input_text="",
            raw_output="",
        )
