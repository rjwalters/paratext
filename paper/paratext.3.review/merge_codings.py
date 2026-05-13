#!/usr/bin/env python3
"""Merge user hand-codings with Claude's, compute inter-rater agreement,
and write the final hardware_safety_coded.csv for v4.

Usage:
    .venv/bin/python paper/paratext.3.review/merge_codings.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHEET = REPO / "paper" / "paratext.3.review" / "HAND_CODE_THIS.md"
CLAUDE_CSV = REPO / "paper" / "paratext.3" / "data" / "hardware_safety_coded_claude.csv"
OUT_CSV = REPO / "paper" / "paratext.3" / "data" / "hardware_safety_coded.csv"


def parse_sheet(text: str) -> dict[tuple[str, str, str], tuple[int, str]]:
    """Parse HAND_CODE_THIS.md into {(model, base_id, variant_class): (code, note)}."""
    out: dict[tuple[str, str, str], tuple[int, str]] = {}
    current_model = None
    current_key = None
    model_map = {"Haiku 4.5": "haiku", "Sonnet 4.6": "sonnet", "Opus 4.7": "opus"}
    for line in text.splitlines():
        # Detect model section
        m = re.match(r"^##\s+(Haiku 4\.5|Sonnet 4\.6|Opus 4\.7)\s*$", line)
        if m:
            current_model = model_map[m.group(1)]
            continue
        # Detect response block header
        m = re.match(r"^###\s+(hardware_\d+)\s*/\s*(\w+)\s*$", line)
        if m and current_model:
            current_key = (current_model, m.group(1), m.group(2))
            continue
        # Detect HUMAN: code
        m = re.match(r"^HUMAN:\s*([01?])\s*$", line)
        if m and current_key:
            code = m.group(1)
            if code != "?":
                # Note may be on next line; we'll fill it in below
                out[current_key] = (int(code), "")
            current_key_recent = current_key
        # Detect NOTE: line
        m = re.match(r"^NOTE:\s*(.*)$", line)
        if m and current_key:
            note = m.group(1).strip()
            if current_key in out:
                code, _ = out[current_key]
                out[current_key] = (code, note)
            current_key = None  # reset until next response block
    return out


def main() -> None:
    if not SHEET.exists():
        print(f"ERROR: {SHEET} not found. Generate it first.")
        return
    user_codings = parse_sheet(SHEET.read_text())

    # Load Claude's codings
    claude_codings: dict[tuple[str, str, str], tuple[int, str]] = {}
    with open(CLAUDE_CSV) as f:
        for row in csv.DictReader(f):
            k = (row["model"], row["base_id"], row["variant_class"])
            claude_codings[k] = (int(row["human_safety"]), row.get("notes", ""))

    all_keys = sorted(set(claude_codings) | set(user_codings))
    unanswered = [k for k in claude_codings if k not in user_codings]
    if unanswered:
        print(f"⚠ {len(unanswered)} of {len(claude_codings)} responses are not yet coded:")
        for k in unanswered[:5]:
            print(f"   {'/'.join(k)}")
        if len(unanswered) > 5:
            print(f"   ...and {len(unanswered) - 5} more")
        print("\nFill them in (set HUMAN: 0 or 1) and re-run.")
        return

    # Compute agreement on the keys where both coded
    both = [k for k in all_keys if k in claude_codings and k in user_codings]
    agree = sum(1 for k in both if claude_codings[k][0] == user_codings[k][0])
    n = len(both)
    pa = agree / n if n else 0.0

    # Cohen's kappa
    # p_o = pa; p_e = sum_i p_a(i) * p_b(i)
    a_codes = [claude_codings[k][0] for k in both]
    u_codes = [user_codings[k][0] for k in both]
    p_a1 = sum(a_codes) / n
    p_u1 = sum(u_codes) / n
    p_e = p_a1 * p_u1 + (1 - p_a1) * (1 - p_u1)
    kappa = (pa - p_e) / (1 - p_e) if p_e < 1 else 0.0

    print(f"Agreement on {n}/{n} responses:")
    print(f"  Percent agreement: {pa:.2%} ({agree}/{n})")
    print(f"  Cohen's κ:         {kappa:.3f}")
    print()

    # Write disagreements summary
    disagreements = [k for k in both if claude_codings[k][0] != user_codings[k][0]]
    if disagreements:
        print(f"Disagreements ({len(disagreements)}):")
        for k in disagreements:
            c, _ = claude_codings[k]
            u, un = user_codings[k]
            print(f"  {'/'.join(k):40s}  claude={c}  user={u}  note={un}")
        print()

    # Merge: write CSV with both columns + consensus
    # Consensus rule: when both agree, that's the value. When they disagree,
    # default to the user (human first-author) as the tie-breaker.
    rows = []
    for k in sorted(claude_codings):
        c, c_note = claude_codings[k]
        u, u_note = user_codings.get(k, (None, ""))
        consensus = u if u is not None else c
        rows.append({
            "model": k[0],
            "base_id": k[1],
            "variant_class": k[2],
            "claude_safety": c,
            "user_safety": u if u is not None else "",
            "consensus_safety": consensus,
            "claude_note": c_note,
            "user_note": u_note,
        })

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV} (n={len(rows)} rows).")

    # Summary per (model, variant_class) on consensus values
    print()
    print("Consensus-coded summary:")
    from collections import defaultdict
    agg = defaultdict(list)
    for r in rows:
        agg[(r["model"], r["variant_class"])].append(r["consensus_safety"])
    for (model, vc), vals in sorted(agg.items()):
        rate = sum(vals) / len(vals)
        print(f"  {model:8s} {vc:18s}  {sum(vals)}/{len(vals)}  ({rate:.0%})")


if __name__ == "__main__":
    main()
