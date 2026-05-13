#!/usr/bin/env python3
"""Run both experiments (explicit + implicit) for a given model spec.

Example:
    python scripts/run_experiment.py mock/echo --limit 16
"""

from __future__ import annotations

from pathlib import Path

import typer

from paratext.cli import run_explicit_cmd, run_implicit_cmd

app = typer.Typer(add_completion=False)


@app.command()
def main(
    model: str = typer.Argument(..., help="Provider/model spec, e.g. mock/echo"),
    variants_path: Path = typer.Option(
        Path("data/variants/variants.jsonl"), "--variants"
    ),
    explicit_out: Path = typer.Option(Path("data/runs/explicit.jsonl"), "--explicit-out"),
    implicit_out: Path = typer.Option(Path("data/runs/implicit.jsonl"), "--implicit-out"),
    limit: int = typer.Option(0, "--limit"),
):
    run_explicit_cmd(
        variants_path=variants_path,
        model=model,
        output_path=explicit_out,
        limit=limit,
    )
    run_implicit_cmd(
        variants_path=variants_path,
        model=model,
        output_path=implicit_out,
        limit=limit,
    )


if __name__ == "__main__":
    app()
