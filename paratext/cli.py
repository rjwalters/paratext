"""Typer-based CLI for paratext.

Subcommands:
- generate-variants  Generate prompt variants from a seed YAML.
- run-explicit       Run the explicit latent-state experiment.
- run-implicit       Run the implicit behavioral-adaptation experiment.
- analyze            Generate a Markdown report from explicit+implicit JSONL runs.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import typer
from rich.console import Console

from .dataset import (
    append_run_record,
    load_seed_prompts,
    read_run_records,
    read_variants_jsonl,
    write_variants_jsonl,
)
from .experiments import explicit_state, implicit_response
from .providers import get_provider, parse_model_spec
from .schemas import PromptVariant
from .variants import generate_all_variants

app = typer.Typer(add_completion=False, no_args_is_help=True, help="paratext CLI")
console = Console()


@app.command("generate-variants")
def generate_variants_cmd(
    input_path: Path = typer.Option(
        Path("data/seed_prompts.yaml"), "--input", "-i", help="Seed prompts YAML."
    ),
    output_path: Path = typer.Option(
        Path("data/variants/variants.jsonl"), "--output", "-o", help="Output JSONL."
    ),
    seed: int = typer.Option(0, "--seed", help="Seed for deterministic transformations."),
):
    """Generate the MVP cue-class variants for every seed prompt."""
    prompts = load_seed_prompts(input_path)
    variants = generate_all_variants(prompts, run_seed=seed)
    n = write_variants_jsonl(variants, output_path)
    console.print(
        f"[green]Wrote[/green] {n} variants from {len(prompts)} prompts -> {output_path}"
    )


def _take(it: Iterable[PromptVariant], limit: int) -> list[PromptVariant]:
    if limit and limit > 0:
        out = []
        for v in it:
            out.append(v)
            if len(out) >= limit:
                break
        return out
    return list(it)


@app.command("run-explicit")
def run_explicit_cmd(
    variants_path: Path = typer.Option(
        Path("data/variants/variants.jsonl"), "--variants", "-v"
    ),
    model: str = typer.Option(..., "--model", "-m", help="Provider/model spec, e.g. mock/echo"),
    output_path: Path = typer.Option(
        Path("data/runs/explicit.jsonl"), "--output", "-o"
    ),
    limit: int = typer.Option(0, "--limit", help="Limit variants processed (0 = all)."),
    temperature: float = typer.Option(0.2, "--temperature"),
    seed: int = typer.Option(0, "--seed"),
):
    """Run the explicit latent-state experiment."""
    scheme, model_id = parse_model_spec(model)
    provider = get_provider(scheme)
    variants = _take(read_variants_jsonl(variants_path), limit)
    if output_path.exists():
        output_path.unlink()
    n = 0
    for record in explicit_state.run(
        variants, provider=provider, model=model_id, temperature=temperature, seed=seed
    ):
        append_run_record(record.model_dump_json(), output_path)
        n += 1
    console.print(
        f"[green]Explicit-state run complete:[/green] {n} records -> {output_path}"
    )


@app.command("run-implicit")
def run_implicit_cmd(
    variants_path: Path = typer.Option(
        Path("data/variants/variants.jsonl"), "--variants", "-v"
    ),
    model: str = typer.Option(..., "--model", "-m"),
    output_path: Path = typer.Option(
        Path("data/runs/implicit.jsonl"), "--output", "-o"
    ),
    limit: int = typer.Option(0, "--limit"),
    temperature: float = typer.Option(0.7, "--temperature"),
    seed: int = typer.Option(0, "--seed"),
):
    """Run the implicit behavioral-adaptation experiment."""
    scheme, model_id = parse_model_spec(model)
    provider = get_provider(scheme)
    variants = _take(read_variants_jsonl(variants_path), limit)
    if output_path.exists():
        output_path.unlink()
    n = 0
    for record in implicit_response.run(
        variants, provider=provider, model=model_id, temperature=temperature, seed=seed
    ):
        append_run_record(record.model_dump_json(), output_path)
        n += 1
    console.print(
        f"[green]Implicit-response run complete:[/green] {n} records -> {output_path}"
    )


@app.command("analyze")
def analyze_cmd(
    explicit_path: Path = typer.Option(
        Path("data/runs/explicit.jsonl"), "--explicit"
    ),
    implicit_path: Path = typer.Option(
        Path("data/runs/implicit.jsonl"), "--implicit"
    ),
    output_path: Path = typer.Option(
        Path("reports/mvp_report.md"), "--output", "-o"
    ),
):
    """Aggregate runs and write a Markdown report."""
    from .analysis.report import write_report

    explicit_records = list(read_run_records(explicit_path)) if explicit_path.exists() else []
    implicit_records = list(read_run_records(implicit_path)) if implicit_path.exists() else []
    out = write_report(explicit_records, implicit_records, output_path)
    console.print(f"[green]Report written:[/green] {out}")


@app.command("show-variant")
def show_variant_cmd(
    variant_id: str = typer.Argument(..., help="Variant id, e.g. coding_001__fatigue_coded__v1"),
    variants_path: Path = typer.Option(
        Path("data/variants/variants.jsonl"), "--variants", "-v"
    ),
):
    """Print one variant by id (useful for spot-checking)."""
    for v in read_variants_jsonl(variants_path):
        if v.id == variant_id:
            console.print_json(json.dumps(v.model_dump()))
            return
    raise typer.BadParameter(f"variant id not found: {variant_id}")


if __name__ == "__main__":
    app()
