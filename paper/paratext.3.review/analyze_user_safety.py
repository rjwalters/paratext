#!/usr/bin/env python3
"""Analyze the Opus-coder user-safety codings:
1. Per (model, variant_class) rate + paired Δ vs polished_neutral
2. IRR check against user's 35-response codings on the overlap
3. Per-model "protect vs punish" matrix

Run from repo root:
    .venv/bin/python paper/paratext.3.review/analyze_user_safety.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OPUS_CODINGS = REPO / "paper" / "paratext.3.review" / "llm_user_safety_codings.csv"
USER_CODINGS = REPO / "paper" / "paratext.3" / "data" / "hardware_safety_coded.csv"


def main():
    # Load Opus codings: {(model, base_id, vc): 0/1}
    opus = {}
    with open(OPUS_CODINGS) as f:
        for r in csv.DictReader(f):
            k = (r["model"], r["base_id"], r["variant_class"])
            opus[k] = int(r["llm_safety"])

    # ----- 1. Per (model, variant_class) rates and paired Δ -----
    VARIANT_ORDER = [
        "polished_neutral", "polite_collaborative", "rushed_mobile_coded",
        "rude_frustrated", "typo_light", "typo_heavy", "random_typo_control",
        "cue_only", "fatigue_coded",
    ]
    MODELS = ["haiku", "sonnet", "opus"]

    # Group by (model, vc) -> list of (base_id, code)
    grouped = defaultdict(list)
    for (m, b, vc), code in opus.items():
        grouped[(m, vc)].append((b, code))

    print("=" * 75)
    print(f"User-safety rate by (model, variant_class) — Opus 4.7 as coder")
    print("=" * 75)
    print(f"\n{'model':8s} {'variant_class':20s} {'rate':>10s} {'paired Δ':>12s} {'n':>3s}")
    print("-" * 60)
    # Build per-model baseline lookup
    baselines = {}
    for m in MODELS:
        b_codes = {b: c for b, c in grouped[(m, "polished_neutral")]}
        baselines[m] = b_codes
    for m in MODELS:
        for vc in VARIANT_ORDER:
            entries = grouped.get((m, vc), [])
            if not entries:
                continue
            rate = sum(c for _, c in entries) / len(entries)
            # Paired Δ vs polished_neutral on the same base_id
            paired = []
            for b, c in entries:
                if b in baselines[m]:
                    paired.append(c - baselines[m][b])
            n = len(paired)
            d = sum(paired) / n if n else 0.0
            print(f"{m:8s} {vc:20s} {rate:>10.2f} {d:>+12.3f} {n:>3d}")

    # ----- 2. IRR vs user's existing 35 codings on the overlap -----
    user = {}
    with open(USER_CODINGS) as f:
        for r in csv.DictReader(f):
            if r.get("user_safety") in ("", None):
                continue
            k = (r["model"], r["base_id"], r["variant_class"])
            user[k] = int(r["user_safety"])

    overlap = [k for k in user if k in opus]
    agree = sum(1 for k in overlap if user[k] == opus[k])
    pa = agree / len(overlap)
    p_u1 = sum(user[k] for k in overlap) / len(overlap)
    p_o1 = sum(opus[k] for k in overlap) / len(overlap)
    p_e = p_u1 * p_o1 + (1 - p_u1) * (1 - p_o1)
    kappa = (pa - p_e) / (1 - p_e) if p_e < 1 else 0.0

    print()
    print("=" * 75)
    print(f"IRR check: Opus-as-coder vs user, on {len(overlap)}-response overlap")
    print("=" * 75)
    print(f"  Percent agreement: {pa:.2%} ({agree}/{len(overlap)})")
    print(f"  Cohen's κ:         {kappa:.3f}")
    disagree = [k for k in overlap if user[k] != opus[k]]
    if disagree:
        print(f"\n  Disagreements ({len(disagree)}):")
        for k in disagree[:15]:
            print(f"    {'/'.join(k):42s}  user={user[k]}  opus={opus[k]}")

    # ----- 3. Protect vs punish matrix -----
    print()
    print("=" * 75)
    print("Protect vs punish matrix: paired Δ user-safety rate per (model, class)")
    print("=" * 75)
    interesting = ["fatigue_coded", "cue_only", "random_typo_control",
                   "rude_frustrated", "polite_collaborative", "typo_heavy"]
    print(f"\n{'variant_class':22s} {'Haiku 4.5':>14s} {'Sonnet 4.6':>14s} {'Opus 4.7':>14s}")
    print("-" * 70)
    for vc in interesting:
        row = [vc]
        for m in MODELS:
            entries = grouped.get((m, vc), [])
            paired = [c - baselines[m].get(b, 0) for b, c in entries if b in baselines[m]]
            if paired:
                d = sum(paired) / len(paired)
                row.append(f"Δ={d:+.2f} (n={len(paired)})")
            else:
                row.append("—")
        print(f"{row[0]:22s} {row[1]:>14s} {row[2]:>14s} {row[3]:>14s}")


if __name__ == "__main__":
    main()
