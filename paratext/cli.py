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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

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


def _run_parallel(
    variants: list[PromptVariant],
    runner_one,
    new_run_id,
    *,
    provider,
    model_id: str,
    output_path: Path,
    temperature: float,
    seed: int,
    thinking: bool,
    concurrency: int,
    label: str,
) -> int:
    """Drive `runner_one(variant, provider, model_id, run_id, ...)` over a
    thread pool, appending each result to `output_path` as it finishes.

    All workers share one `run_id` so the JSONL is self-consistent. We append
    in the main thread (one writer) to avoid file-lock contention.
    """
    if output_path.exists():
        output_path.unlink()
    rid = new_run_id(model_id)
    n = 0
    errors: list[tuple[str, Exception]] = []
    with Progress(transient=True) as progress:
        task = progress.add_task(f"[cyan]{label}", total=len(variants))
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            futures = {
                pool.submit(
                    runner_one,
                    v,
                    provider,
                    model_id,
                    rid,
                    temperature,
                    seed,
                    thinking,
                ): v
                for v in variants
            }
            for fut in as_completed(futures):
                v = futures[fut]
                try:
                    record = fut.result()
                    append_run_record(record.model_dump_json(), output_path)
                    n += 1
                except Exception as e:  # noqa: BLE001 — surface and continue
                    errors.append((v.id, e))
                progress.update(task, advance=1)
    if errors:
        console.print(f"[yellow]{len(errors)} variants failed:[/yellow]")
        for vid, e in errors[:10]:
            console.print(f"  {vid}: {type(e).__name__}: {e}")
        if len(errors) > 10:
            console.print(f"  ... and {len(errors) - 10} more")
    return n


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
    thinking: bool = typer.Option(False, "--thinking/--no-thinking", help="Enable adaptive thinking."),
    concurrency: int = typer.Option(1, "--concurrency", "-c", help="Parallel in-flight requests."),
):
    """Run the explicit latent-state experiment."""
    scheme, model_id = parse_model_spec(model)
    provider = get_provider(scheme)
    variants = _take(read_variants_jsonl(variants_path), limit)
    n = _run_parallel(
        variants,
        explicit_state.run_one,
        explicit_state.new_run_id,
        provider=provider,
        model_id=model_id,
        output_path=output_path,
        temperature=temperature,
        seed=seed,
        thinking=thinking,
        concurrency=concurrency,
        label=f"explicit · {model_id}",
    )
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
    thinking: bool = typer.Option(False, "--thinking/--no-thinking"),
    concurrency: int = typer.Option(1, "--concurrency", "-c"),
):
    """Run the implicit behavioral-adaptation experiment."""
    scheme, model_id = parse_model_spec(model)
    provider = get_provider(scheme)
    variants = _take(read_variants_jsonl(variants_path), limit)
    n = _run_parallel(
        variants,
        implicit_response.run_one,
        implicit_response.new_run_id,
        provider=provider,
        model_id=model_id,
        output_path=output_path,
        temperature=temperature,
        seed=seed,
        thinking=thinking,
        concurrency=concurrency,
        label=f"implicit · {model_id}",
    )
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
