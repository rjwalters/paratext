"""Metric/classifier tests."""

from __future__ import annotations

from paratext.analysis.classifiers import classify_response
from paratext.analysis.metrics import (
    aggregate_explicit,
    aggregate_implicit,
    comparison_table,
)


def test_classify_counts_rest_break_safety():
    text = (
        "I'll keep this short. Take a break if you need to revisit later. "
        "Safety note: unplug the device first."
    )
    feats = classify_response(text)
    assert feats["mentions_sleep_or_rest"] is True
    assert feats["mentions_break_or_pause"] is True
    assert feats["says_keep_it_short"] is True
    assert feats["contains_safety_warning"] is True
    assert feats["num_words"] > 5


def test_classify_does_not_misfire_on_neutral_text():
    text = "Here is a structured answer:\n1. First step.\n2. Second step.\n3. Third step."
    feats = classify_response(text)
    assert feats["mentions_sleep_or_rest"] is False
    assert feats["mentions_break_or_pause"] is False
    assert feats["explicitly_labels_user_state"] is False
    assert feats["num_steps"] >= 3


def test_classify_detects_user_state_labeling():
    text = "You seem tired — let's keep this brief."
    feats = classify_response(text)
    assert feats["explicitly_labels_user_state"] is True


def _explicit_record(base_id: str, variant_class: str, fatigue: float):
    return {
        "model": "mock/echo",
        "experiment": "explicit_state",
        "prompt_variant_id": f"{base_id}__{variant_class}__v1",
        "base_id": base_id,
        "variant_class": variant_class,
        "domain": "test",
        "input_text": "...",
        "raw_output": "{}",
        "parsed_output": {
            "fatigue": fatigue,
            "rushed_or_mobile": 0.1,
            "frustration": 0.0,
            "confusion": 0.0,
            "urgency": 0.0,
            "expertise": 0.3,
            "low_bandwidth": 0.0,
            "confidence": 0.5,
        },
        "provider_metadata": {},
    }


def test_aggregate_explicit_paired_deltas_match_expectation():
    records = [
        _explicit_record("p1", "polished_neutral", 0.10),
        _explicit_record("p1", "fatigue_coded", 0.50),
        _explicit_record("p1", "random_typo_control", 0.20),
        _explicit_record("p2", "polished_neutral", 0.05),
        _explicit_record("p2", "fatigue_coded", 0.45),
        _explicit_record("p2", "random_typo_control", 0.10),
    ]
    out = aggregate_explicit(records)
    assert not out["per_class"].empty
    deltas = out["paired_deltas"]
    fatigue_row = deltas[
        (deltas["variant_class"] == "fatigue_coded") & (deltas["field"] == "fatigue")
    ].iloc[0]
    # mean((0.50 - 0.10), (0.45 - 0.05)) == 0.40
    assert abs(fatigue_row["delta_mean"] - 0.40) < 1e-9
    control_row = deltas[
        (deltas["variant_class"] == "random_typo_control") & (deltas["field"] == "fatigue")
    ].iloc[0]
    # mean((0.20 - 0.10), (0.10 - 0.05)) == 0.075
    assert abs(control_row["delta_mean"] - 0.075) < 1e-9


def test_comparison_table_pivot():
    records = [
        _explicit_record("p1", "polished_neutral", 0.1),
        _explicit_record("p1", "fatigue_coded", 0.5),
    ]
    out = aggregate_explicit(records)
    wide = comparison_table(out["paired_deltas"], ("fatigue",))
    assert "fatigue" in wide.columns
    assert "fatigue_coded" in wide.index


def test_aggregate_implicit_handles_empty_input():
    out = aggregate_implicit([])
    assert out["per_class"].empty
    assert out["paired_deltas"].empty
