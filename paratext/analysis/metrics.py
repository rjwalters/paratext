"""Aggregation metrics over run records.

Two main entry points:

- `aggregate_explicit(records)`: per-variant-class summary of latent-state scores
- `aggregate_implicit(records)`: per-variant-class summary of response features

Both also compute *paired deltas* relative to `polished_neutral` for the same
`base_id`. The paired view is the right one for sensitivity / specificity
claims because it controls for prompt content.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from ..schemas import ALL_VARIANT_CLASSES

EXPLICIT_NUMERIC_FIELDS = (
    "fatigue",
    "rushed_or_mobile",
    "frustration",
    "confusion",
    "urgency",
    "expertise",
    "low_bandwidth",
    "confidence",
)

IMPLICIT_NUMERIC_FIELDS = (
    "num_chars",
    "num_words",
    "num_steps",
    "num_questions",
    "apology_count",
    "hedge_count",
)

IMPLICIT_BOOL_FIELDS = (
    "mentions_sleep_or_rest",
    "mentions_break_or_pause",
    "says_keep_it_short",
    "explicitly_labels_user_state",
    "contains_safety_warning",
)


# ---------------------------------------------------------------------------
# DataFrame construction
# ---------------------------------------------------------------------------


def _records_to_df(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    rows = list(records)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df


def _expand_parsed(df: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    """Pull the listed fields out of `parsed_output` into top-level columns."""
    if df.empty:
        return df
    parsed = df["parsed_output"].apply(lambda x: x if isinstance(x, dict) else {})
    for f in fields:
        df[f] = parsed.apply(lambda d, f=f: d.get(f))
    return df


# ---------------------------------------------------------------------------
# Public aggregations
# ---------------------------------------------------------------------------


def aggregate_explicit(records: Iterable[dict[str, Any]]) -> dict[str, pd.DataFrame]:
    """Return tables: per-class means, per-(class,domain) means, paired deltas."""
    df = _records_to_df(records)
    if df.empty:
        return {"per_class": pd.DataFrame(), "per_class_domain": pd.DataFrame(),
                "paired_deltas": pd.DataFrame()}
    df = _expand_parsed(df, EXPLICIT_NUMERIC_FIELDS)

    # Coerce numeric, dropping anything the model produced as non-numeric.
    for f in EXPLICIT_NUMERIC_FIELDS:
        df[f] = pd.to_numeric(df[f], errors="coerce")

    per_class = (
        df.groupby("variant_class")[list(EXPLICIT_NUMERIC_FIELDS)]
        .mean()
        .reindex([c for c in ALL_VARIANT_CLASSES if c in df["variant_class"].unique()])
    )

    per_class_domain = (
        df.groupby(["domain", "variant_class"])[list(EXPLICIT_NUMERIC_FIELDS)]
        .mean()
        .reset_index()
    )

    paired = _paired_deltas(df, EXPLICIT_NUMERIC_FIELDS)

    return {
        "per_class": per_class,
        "per_class_domain": per_class_domain,
        "paired_deltas": paired,
    }


def aggregate_implicit(records: Iterable[dict[str, Any]]) -> dict[str, pd.DataFrame]:
    """Return tables: per-class means, per-(class,domain) means, paired deltas."""
    df = _records_to_df(records)
    if df.empty:
        return {"per_class": pd.DataFrame(), "per_class_domain": pd.DataFrame(),
                "paired_deltas": pd.DataFrame()}
    df = _expand_parsed(df, IMPLICIT_NUMERIC_FIELDS + IMPLICIT_BOOL_FIELDS)

    for f in IMPLICIT_NUMERIC_FIELDS:
        df[f] = pd.to_numeric(df[f], errors="coerce")
    for f in IMPLICIT_BOOL_FIELDS:
        df[f] = df[f].apply(lambda v: 1.0 if bool(v) else 0.0)

    cols = list(IMPLICIT_NUMERIC_FIELDS) + list(IMPLICIT_BOOL_FIELDS)
    per_class = (
        df.groupby("variant_class")[cols]
        .mean()
        .reindex([c for c in ALL_VARIANT_CLASSES if c in df["variant_class"].unique()])
    )
    per_class_domain = (
        df.groupby(["domain", "variant_class"])[cols].mean().reset_index()
    )
    paired = _paired_deltas(df, tuple(cols))

    return {
        "per_class": per_class,
        "per_class_domain": per_class_domain,
        "paired_deltas": paired,
    }


# ---------------------------------------------------------------------------
# Paired deltas
# ---------------------------------------------------------------------------


def _paired_deltas(df: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    """For each (base_id, variant_class), subtract the matching polished_neutral row.

    Returns a long-format DataFrame with columns:
        variant_class, field, delta_mean, n
    where `delta_mean` is the mean over all base_ids of
    (variant_value - polished_neutral_value).

    The `random_typo_control` row is the most interesting comparator for
    `fatigue_coded` and `rushed_mobile_coded`; the report consumes both deltas.
    """
    if df.empty:
        return pd.DataFrame()
    baseline = df[df["variant_class"] == "polished_neutral"][["base_id", *fields]]
    if baseline.empty:
        return pd.DataFrame()
    baseline = baseline.set_index("base_id")

    rows = []
    for variant_class, sub in df.groupby("variant_class"):
        if variant_class == "polished_neutral":
            continue
        merged = sub.merge(
            baseline, left_on="base_id", right_index=True, suffixes=("", "_base")
        )
        for f in fields:
            base_col = f"{f}_base"
            if base_col not in merged.columns:
                continue
            diff = merged[f] - merged[base_col]
            rows.append(
                {
                    "variant_class": variant_class,
                    "field": f,
                    "delta_mean": float(diff.mean()) if len(diff) else float("nan"),
                    "n": int(diff.notna().sum()),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Targeted comparisons used in the report narrative
# ---------------------------------------------------------------------------


def comparison_table(deltas: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    """Pivot a paired-deltas long table to a (variant_class x field) wide table."""
    if deltas.empty:
        return pd.DataFrame()
    keep = deltas[deltas["field"].isin(fields)]
    wide = keep.pivot(index="variant_class", columns="field", values="delta_mean")
    return wide.reindex(
        [c for c in ALL_VARIANT_CLASSES if c in wide.index]
    )
