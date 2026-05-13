"""Loaders for the seed prompt dataset and generated variants."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

import yaml

from .schemas import PromptVariant, SeedPrompt


def load_seed_prompts(path: str | Path) -> list[SeedPrompt]:
    """Load seed prompts from a YAML file."""
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, list):
        raise ValueError(f"Expected a YAML list of prompts, got {type(raw).__name__}")
    return [SeedPrompt.model_validate(item) for item in raw]


def write_variants_jsonl(variants: Iterable[PromptVariant], path: str | Path) -> int:
    """Write variants to a JSONL file. Returns the number written."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w") as f:
        for v in variants:
            f.write(v.model_dump_json() + "\n")
            n += 1
    return n


def read_variants_jsonl(path: str | Path) -> Iterator[PromptVariant]:
    """Stream variants from a JSONL file."""
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield PromptVariant.model_validate_json(line)


def append_run_record(record_json: str, path: str | Path) -> None:
    """Append a single JSON-serialized record to a JSONL file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(record_json + "\n")


def read_run_records(path: str | Path) -> Iterator[dict]:
    """Stream raw run records (as dicts) from a JSONL file."""
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
