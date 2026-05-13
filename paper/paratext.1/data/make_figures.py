#!/usr/bin/env python3
"""Generate the four headline figures for paratext.1.

Run from repo root:
    .venv/bin/python paper/paratext.1/data/make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from paratext.analysis.metrics import aggregate_explicit, aggregate_implicit

REPO = Path(__file__).resolve().parents[3]
FIGDIR = REPO / "paper" / "paratext.1" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

MODELS = ["haiku", "sonnet", "opus"]
MODEL_LABELS = {"haiku": "Haiku 4.5", "sonnet": "Sonnet 4.6", "opus": "Opus 4.7"}
MODEL_COLORS = {"haiku": "#7AA1D8", "sonnet": "#6EAF7C", "opus": "#D87A7A"}

VARIANT_ORDER = [
    "polite_collaborative",
    "rushed_mobile_coded",
    "rude_frustrated",
    "typo_light",
    "typo_heavy",
    "random_typo_control",
    "cue_only",
    "fatigue_coded",
]
VARIANT_LABELS = {
    "polite_collaborative": "polite",
    "rushed_mobile_coded": "rushed/mobile",
    "rude_frustrated": "rude",
    "typo_light": "typo (light)",
    "typo_heavy": "typo (heavy)",
    "random_typo_control": "random typos",
    "cue_only": "cues only",
    "fatigue_coded": "fatigue coded",
}


def _load_paired(experiment: str) -> dict[str, "pd.DataFrame"]:
    out = {}
    for m in MODELS:
        path = REPO / "data" / "runs" / "cross_model" / f"{m}_{experiment}.jsonl"
        records = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        agg = aggregate_explicit(records) if experiment == "explicit" else aggregate_implicit(records)
        out[m] = agg["paired_deltas"]
    return out


def _delta_row(paired, variant_class: str, field: str):
    row = paired[(paired.variant_class == variant_class) & (paired.field == field)]
    if row.empty:
        return None
    r = row.iloc[0]
    return float(r["delta_mean"]), float(r["ci_lo"]), float(r["ci_hi"])


def _bar_with_ci(ax, x, vals, errs, color, label):
    yerr = np.array([[v - lo for v, (lo, _) in zip(vals, errs)],
                     [hi - v for v, (_, hi) in zip(vals, errs)]])
    ax.bar(x, vals, color=color, label=label, alpha=0.85, edgecolor="black", linewidth=0.5)
    ax.errorbar(x, vals, yerr=yerr, fmt="none", ecolor="black", elinewidth=0.8, capsize=2)


def fig1_fatigue_sensitivity(per_model: dict):
    """Fatigue Δ by model and variant_class — the sensitivity story."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    width = 0.28
    x_idx = np.arange(len(VARIANT_ORDER))
    for i, m in enumerate(MODELS):
        vals, errs = [], []
        for vc in VARIANT_ORDER:
            d = _delta_row(per_model[m], vc, "fatigue")
            if d is None:
                vals.append(0.0); errs.append((0.0, 0.0))
            else:
                vals.append(d[0]); errs.append((d[1], d[2]))
        offsets = x_idx + (i - 1) * width
        _bar_with_ci(ax, offsets, vals, errs, MODEL_COLORS[m], MODEL_LABELS[m])
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x_idx)
    ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANT_ORDER], rotation=30, ha="right")
    ax.set_ylabel(r"$\Delta$ fatigue vs polished\_neutral")
    ax.set_title("Fatigue inference by variant class and model")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout()
    out = FIGDIR / "fig1_fatigue_sensitivity.pdf"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def fig2_specificity_inversion(per_model: dict):
    """cue_only vs random_typo_control on fatigue — the specificity inversion."""
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    width = 0.32
    x_idx = np.arange(len(MODELS))
    classes = ["cue_only", "random_typo_control"]
    class_colors = {"cue_only": "#2E7D32", "random_typo_control": "#E64A19"}
    class_labels = {"cue_only": "cues only (no typos)",
                    "random_typo_control": "random typos (no cues)"}
    for j, vc in enumerate(classes):
        vals, errs = [], []
        for m in MODELS:
            d = _delta_row(per_model[m], vc, "fatigue")
            vals.append(d[0]); errs.append((d[1], d[2]))
        offsets = x_idx + (j - 0.5) * width
        _bar_with_ci(ax, offsets, vals, errs, class_colors[vc], class_labels[vc])
    ax.set_xticks(x_idx)
    ax.set_xticklabels([MODEL_LABELS[m] for m in MODELS])
    ax.set_ylabel(r"$\Delta$ fatigue vs polished\_neutral")
    ax.set_title("Cues vs random typos — specificity inversion")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.axhline(0, color="black", linewidth=0.5)
    fig.tight_layout()
    out = FIGDIR / "fig2_specificity_inversion.pdf"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def fig3_confidence_asymmetry(per_model: dict):
    """Confidence Δ across all variant classes by model — Opus's asymmetry under rudeness."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    width = 0.28
    x_idx = np.arange(len(VARIANT_ORDER))
    for i, m in enumerate(MODELS):
        vals, errs = [], []
        for vc in VARIANT_ORDER:
            d = _delta_row(per_model[m], vc, "confidence")
            if d is None:
                vals.append(0.0); errs.append((0.0, 0.0))
            else:
                vals.append(d[0]); errs.append((d[1], d[2]))
        offsets = x_idx + (i - 1) * width
        _bar_with_ci(ax, offsets, vals, errs, MODEL_COLORS[m], MODEL_LABELS[m])
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x_idx)
    ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANT_ORDER], rotation=30, ha="right")
    ax.set_ylabel(r"$\Delta$ confidence vs polished\_neutral")
    ax.set_title("Confidence shifts by variant class and model")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout()
    out = FIGDIR / "fig3_confidence_asymmetry.pdf"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def fig4_num_words_compression(per_model_impl: dict):
    """Response length Δ by model and variant class — compression patterns."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    width = 0.28
    x_idx = np.arange(len(VARIANT_ORDER))
    for i, m in enumerate(MODELS):
        vals, errs = [], []
        for vc in VARIANT_ORDER:
            d = _delta_row(per_model_impl[m], vc, "num_words")
            if d is None:
                vals.append(0.0); errs.append((0.0, 0.0))
            else:
                vals.append(d[0]); errs.append((d[1], d[2]))
        offsets = x_idx + (i - 1) * width
        _bar_with_ci(ax, offsets, vals, errs, MODEL_COLORS[m], MODEL_LABELS[m])
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x_idx)
    ax.set_xticklabels([VARIANT_LABELS[v] for v in VARIANT_ORDER], rotation=30, ha="right")
    ax.set_ylabel(r"$\Delta$ words vs polished\_neutral")
    ax.set_title("Response length adaptation")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    fig.tight_layout()
    out = FIGDIR / "fig4_num_words_compression.pdf"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    plt.rcParams.update({
        "font.size": 9,
        "font.family": "serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    explicit = _load_paired("explicit")
    implicit = _load_paired("implicit")
    fig1_fatigue_sensitivity(explicit)
    fig2_specificity_inversion(explicit)
    fig3_confidence_asymmetry(explicit)
    fig4_num_words_compression(implicit)


if __name__ == "__main__":
    main()
