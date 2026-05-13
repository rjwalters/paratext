#!/usr/bin/env bash
# Run all six (model x experiment) sweeps sequentially, plus the cross-model report.
# Idempotent: skips a run if its output JSONL already has the expected 432 records.
#
# Usage:
#   bash scripts/run_cross_model_sweep.sh

set -euo pipefail
cd "$(dirname "$0")/.."

# Load .env so ANTHROPIC_API_KEY is available regardless of caller env.
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not set (expected in .env)}"

VARIANTS=data/variants/cross_model_full.jsonl
OUT=data/runs/cross_model
EXPECTED=432
CONC=8
mkdir -p "$OUT"

run_once () {
    local kind=$1   # explicit | implicit
    local alias=$2  # haiku | sonnet | opus
    local model=$3  # anthropic/claude-*
    local out="$OUT/${alias}_${kind}.jsonl"
    if [ -f "$out" ] && [ "$(wc -l < "$out")" -ge "$EXPECTED" ]; then
        echo "[skip] $alias $kind already complete ($(wc -l < "$out") records)"
        return
    fi
    echo "[run]  $alias $kind ($model) -> $out"
    local cmd="run-${kind}"
    .venv/bin/python -m paratext.cli "$cmd" \
        --variants "$VARIANTS" \
        --model "$model" \
        --output "$out" \
        --thinking \
        --concurrency "$CONC"
}

# Order: cheapest first so failures surface early.
run_once explicit haiku  anthropic/claude-haiku-4-5
run_once implicit haiku  anthropic/claude-haiku-4-5
run_once explicit sonnet anthropic/claude-sonnet-4-6
run_once implicit sonnet anthropic/claude-sonnet-4-6
run_once explicit opus   anthropic/claude-opus-4-7
run_once implicit opus   anthropic/claude-opus-4-7

echo "=== generating cross-model report ==="
.venv/bin/python scripts/cross_model_report.py \
    --explicit haiku="$OUT/haiku_explicit.jsonl" \
    --explicit sonnet="$OUT/sonnet_explicit.jsonl" \
    --explicit opus="$OUT/opus_explicit.jsonl" \
    --implicit haiku="$OUT/haiku_implicit.jsonl" \
    --implicit sonnet="$OUT/sonnet_implicit.jsonl" \
    --implicit opus="$OUT/opus_implicit.jsonl" \
    --output reports/cross_model.md

echo "=== done ==="
