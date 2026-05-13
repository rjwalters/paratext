#!/usr/bin/env python3
"""Cross-model report generator.

Reads explicit and implicit JSONL files for multiple models and produces a
single Markdown report that compares them. The headline view is a "model x
variant_class" pivot on the fatigue delta — that's where the
"can-Claude-read-the-room" question lives.

Usage:
    python scripts/cross_model_report.py \\
        --explicit haiku=data/runs/cross_model/haiku_explicit.jsonl \\
        --explicit sonnet=data/runs/cross_model/sonnet_explicit.jsonl \\
        --explicit opus=data/runs/cross_model/opus_explicit.jsonl \\
        --implicit haiku=data/runs/cross_model/haiku_implicit.jsonl \\
        --implicit sonnet=data/runs/cross_model/sonnet_implicit.jsonl \\
        --implicit opus=data/runs/cross_model/opus_implicit.jsonl \\
        --output reports/cross_model.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from paratext.analysis.metrics import (
    aggregate_explicit,
    aggregate_implicit,
    comparison_table_with_ci,
)
from paratext.schemas import ALL_VARIANT_CLASSES

app = typer.Typer(add_completion=False)


def _df_to_md(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_No data._"
    try:
        return df.to_markdown()
    except ImportError:
        return "```\n" + df.to_string() + "\n```"


def _parse_kv(items: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(f"expected MODEL=PATH, got: {item}")
        name, _, path = item.partition("=")
        out[name] = Path(path)
    return out


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _cross_model_pivot(
    per_model_paired: dict[str, pd.DataFrame],
    field: str,
) -> pd.DataFrame:
    """Build a (variant_class x model) wide table of formatted delta cells
    for a single inference field (e.g. fatigue).
    """
    cells: dict[str, dict[str, str]] = {}
    for model, paired in per_model_paired.items():
        if paired.empty:
            continue
        wide = comparison_table_with_ci(paired, (field,))
        if wide.empty or field not in wide.columns:
            continue
        for vc, cell in wide[field].items():
            cells.setdefault(vc, {})[model] = cell
    if not cells:
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(cells, orient="index")
    # Order rows in canonical variant-class order; columns in user-supplied model order
    df = df.reindex([c for c in ALL_VARIANT_CLASSES if c in df.index])
    df = df[[m for m in per_model_paired if m in df.columns]]
    df.index.name = "variant_class"
    return df


@app.command()
def main(
    explicit: list[str] = typer.Option(
        [], "--explicit", help="MODEL=PATH for an explicit-state JSONL (repeatable)."
    ),
    implicit: list[str] = typer.Option(
        [], "--implicit", help="MODEL=PATH for an implicit-response JSONL (repeatable)."
    ),
    output_path: Path = typer.Option(
        Path("reports/cross_model.md"), "--output", "-o"
    ),
):
    explicit_paths = _parse_kv(explicit)
    implicit_paths = _parse_kv(implicit)
    models = list(dict.fromkeys(list(explicit_paths) + list(implicit_paths)))

    explicit_records = {m: _load(explicit_paths.get(m, Path())) for m in models}
    implicit_records = {m: _load(implicit_paths.get(m, Path())) for m in models}

    per_model_explicit_paired: dict[str, pd.DataFrame] = {}
    per_model_implicit_paired: dict[str, pd.DataFrame] = {}
    for m in models:
        per_model_explicit_paired[m] = aggregate_explicit(explicit_records[m])["paired_deltas"]
        per_model_implicit_paired[m] = aggregate_implicit(implicit_records[m])["paired_deltas"]

    sections: list[str] = []
    sections.append("# paratext · cross-model report\n")
    sections.append(
        "## Research question\n\nDoes the model family read the same paratext "
        "signals the same way? We compare Claude Haiku 4.5, Sonnet 4.6, and "
        "Opus 4.7 head-to-head on the same prompt variants. Cells are "
        "paired deltas vs `polished_neutral` with 95% bootstrap CIs.\n"
    )
    sections.append(
        "## Dataset summary\n\n"
        + "\n".join(
            f"- **{m}** — explicit: {len(explicit_records[m])} records · "
            f"implicit: {len(implicit_records[m])} records"
            for m in models
        )
        + "\n"
    )

    # Headline view: fatigue inference across the family
    sections.append("## Headline · fatigue delta by model\n")
    fatigue_tbl = _cross_model_pivot(per_model_explicit_paired, "fatigue")
    sections.append(_df_to_md(fatigue_tbl) + "\n")

    sections.append("## Headline · rushed_or_mobile delta by model\n")
    sections.append(
        _df_to_md(_cross_model_pivot(per_model_explicit_paired, "rushed_or_mobile"))
        + "\n"
    )

    sections.append("## Headline · low_bandwidth delta by model\n")
    sections.append(
        _df_to_md(_cross_model_pivot(per_model_explicit_paired, "low_bandwidth"))
        + "\n"
    )

    sections.append("## Headline · confidence delta by model\n")
    sections.append(
        _df_to_md(_cross_model_pivot(per_model_explicit_paired, "confidence"))
        + "\n"
    )

    sections.append("## Implicit · num_words delta by model\n")
    sections.append(
        _df_to_md(_cross_model_pivot(per_model_implicit_paired, "num_words")) + "\n"
    )

    sections.append("## Implicit · explicitly_labels_user_state delta by model\n")
    sections.append(
        _df_to_md(
            _cross_model_pivot(
                per_model_implicit_paired, "explicitly_labels_user_state"
            )
        )
        + "\n"
    )

    sections.append("## Implicit · contains_safety_warning delta by model\n")
    sections.append(
        _df_to_md(
            _cross_model_pivot(per_model_implicit_paired, "contains_safety_warning")
        )
        + "\n"
    )

    sections.append(
        "## How to read this report\n\n"
        "- Each cell is the **mean delta vs `polished_neutral`** for that "
        "model on that variant class, followed by a 95% percentile bootstrap "
        "CI in brackets. A CI excluding 0 is the rough significance bar.\n"
        "- **Sensitivity:** how big is the fatigue_coded delta? Larger = "
        "the model reacts more strongly to fatigue cues.\n"
        "- **Specificity:** is the `fatigue_coded` delta larger than the "
        "`random_typo_control` delta? If they look the same, the model is "
        "responding to noise rather than cues. The decoupling experiment on "
        "Opus 4.7 suggested both contribute independently.\n"
        "- **Calibration:** look at the `cue_only` row — that's contextual "
        "fatigue cues with NO typos. A well-calibrated model should still "
        "register some fatigue (the cues are real) but less than full "
        "fatigue_coded.\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(sections))
    typer.echo(f"Wrote {output_path}")


if __name__ == "__main__":
    app()
