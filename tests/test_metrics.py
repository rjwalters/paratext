"""Metric/classifier tests."""

from __future__ import annotations

import numpy as np

from paratext.analysis.classifiers import classify_response
from paratext.analysis.metrics import (
    aggregate_explicit,
    aggregate_implicit,
    bootstrap_paired_delta_ci,
    comparison_table,
    comparison_table_with_ci,
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


def test_bootstrap_ci_is_deterministic_under_seed():
    diffs = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    a = bootstrap_paired_delta_ci(diffs, n_bootstrap=500, seed=42)
    b = bootstrap_paired_delta_ci(diffs, n_bootstrap=500, seed=42)
    assert a == b


def test_bootstrap_ci_brackets_the_mean():
    rng = np.random.default_rng(0)
    diffs = rng.normal(loc=0.4, scale=0.05, size=50)
    lo, hi = bootstrap_paired_delta_ci(diffs, n_bootstrap=2000, seed=0)
    assert lo <= float(diffs.mean()) <= hi
    # CI should also exclude zero for a clearly-positive effect at this n.
    assert lo > 0


def test_bootstrap_ci_returns_nan_for_singleton():
    lo, hi = bootstrap_paired_delta_ci(np.array([0.5]))
    assert np.isnan(lo) and np.isnan(hi)


def test_bootstrap_ci_ignores_nan_inputs():
    diffs = np.array([0.4, 0.5, np.nan, 0.6])
    lo, hi = bootstrap_paired_delta_ci(diffs, n_bootstrap=500, seed=0)
    assert lo > 0 and hi > lo


def test_paired_deltas_include_ci_columns():
    records = [
        _explicit_record("p1", "polished_neutral", 0.10),
        _explicit_record("p1", "fatigue_coded", 0.50),
        _explicit_record("p2", "polished_neutral", 0.05),
        _explicit_record("p2", "fatigue_coded", 0.45),
        _explicit_record("p3", "polished_neutral", 0.10),
        _explicit_record("p3", "fatigue_coded", 0.50),
    ]
    out = aggregate_explicit(records)
    deltas = out["paired_deltas"]
    row = deltas[
        (deltas["variant_class"] == "fatigue_coded") & (deltas["field"] == "fatigue")
    ].iloc[0]
    assert "ci_lo" in row and "ci_hi" in row
    assert row["ci_lo"] <= row["delta_mean"] <= row["ci_hi"]
    assert row["n"] == 3


def test_comparison_table_with_ci_formats_cells():
    records = [
        _explicit_record("p1", "polished_neutral", 0.10),
        _explicit_record("p1", "fatigue_coded", 0.50),
        _explicit_record("p2", "polished_neutral", 0.10),
        _explicit_record("p2", "fatigue_coded", 0.50),
    ]
    out = aggregate_explicit(records)
    wide = comparison_table_with_ci(out["paired_deltas"], ("fatigue",))
    cell = wide.loc["fatigue_coded", "fatigue"]
    assert cell.startswith("+0.400 [")
    assert cell.endswith("]")


def test_comparison_table_with_ci_tags_singleton_cells():
    """When n=1 the CI is not computable; the cell should still render the
    delta but tagged with `(n=1)` so the reader knows it's not stable."""
    records = [
        _explicit_record("p1", "polished_neutral", 0.10),
        _explicit_record("p1", "fatigue_coded", 0.50),
    ]
    out = aggregate_explicit(records)
    wide = comparison_table_with_ci(out["paired_deltas"], ("fatigue",))
    assert wide.loc["fatigue_coded", "fatigue"] == "+0.400 (n=1)"
