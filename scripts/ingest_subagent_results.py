#!/usr/bin/env python3
"""Ingest subagent outputs into RunRecords and append to JSONL.

Designed for the subagent-as-provider workflow: when paratext experiments are
driven from a Claude Code session via the Agent tool (rather than through a
real provider adapter), this script converts captured agent responses into
the same RunRecord JSONL format the analyzer consumes.

Input format (stdin or --in): a JSON list of objects with keys:
  - variant_id   (matches an id in the variants.jsonl)
  - experiment   ("explicit_state" | "implicit_response")
  - raw_output   (the assistant's response text)

The script looks up variant metadata from --variants and writes RunRecords
to --explicit-out / --implicit-out, splitting by experiment.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from paratext.analysis.classifiers import classify_response
from paratext.dataset import append_run_record, read_variants_jsonl
from paratext.experiments.explicit_state import _parse_inference
from paratext.schemas import RunRecord


def _run_id(model: str, experiment: str) -> str:
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}_{model.replace('/', '_')}_{experiment}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="data/variants/pilot.jsonl")
    ap.add_argument("--in", dest="in_path", default="-",
                    help="Input JSON list path, or '-' for stdin.")
    ap.add_argument("--explicit-out", default="data/runs/explicit_pilot.jsonl")
    ap.add_argument("--implicit-out", default="data/runs/implicit_pilot.jsonl")
    ap.add_argument("--model", default="subagent/claude-opus-4-7")
    args = ap.parse_args()

    variants_by_id = {v.id: v for v in read_variants_jsonl(args.variants)}

    if args.in_path == "-":
        items = json.loads(sys.stdin.read())
    else:
        items = json.loads(Path(args.in_path).read_text())

    counts = {"explicit_state": 0, "implicit_response": 0, "missing": 0}
    for item in items:
        vid = item["variant_id"]
        experiment = item["experiment"]
        raw = item["raw_output"]
        v = variants_by_id.get(vid)
        if v is None:
            counts["missing"] += 1
            print(f"warning: variant {vid!r} not found in {args.variants}",
                  file=sys.stderr)
            continue

        if experiment == "explicit_state":
            parsed = _parse_inference(raw)
            out_path = args.explicit_out
        elif experiment == "implicit_response":
            parsed = classify_response(raw)
            out_path = args.implicit_out
        else:
            raise SystemExit(f"unknown experiment: {experiment!r}")

        record = RunRecord(
            run_id=_run_id(args.model, experiment),
            model=args.model,
            experiment=experiment,
            prompt_variant_id=v.id,
            base_id=v.base_id,
            variant_class=v.variant_class,
            domain=v.domain,
            input_text=v.text,
            raw_output=raw,
            parsed_output=parsed,
            provider_metadata={"source": "subagent"},
        )
        append_run_record(record.model_dump_json(), out_path)
        counts[experiment] += 1

    print(json.dumps(counts), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
