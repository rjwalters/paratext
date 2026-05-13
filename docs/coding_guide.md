# Coding guide

A short orientation for contributors.

## Module layout

```
paratext/
  schemas.py        Pydantic models. Single source of truth for record shapes.
  dataset.py        File I/O for seed prompts, variants, run records. No logic.
  variants.py       Deterministic surface-form perturbations.
  providers/        Model adapters. Anything provider-specific lives here.
    base.py         The ModelProvider Protocol.
    mock.py         Cue-aware mock used in tests and offline runs.
    openai_provider.py   OpenAI adapter (lazy import).
    __init__.py     Provider registry and `parse_model_spec` / `get_provider`.
  experiments/      Per-experiment orchestration: build prompts, call provider,
                    parse output, emit RunRecord.
    explicit_state.py
    implicit_response.py
  analysis/         Pure functions over JSONL run files.
    classifiers.py  Regex/heuristic features over assistant responses.
    metrics.py      Aggregations and paired deltas.
    plots.py        Optional matplotlib helpers.
    report.py       Markdown report assembly.
  cli.py            Typer commands. Orchestration only — no business logic.
```

## Adding a new provider

1. Create `paratext/providers/myprovider.py`.
2. Implement a class with:
   - a `name` class attribute
   - a `complete(messages, model, temperature, seed=None, max_tokens=None,
     response_format=None, **kwargs) -> ModelResponse` method
3. Register a scheme in `providers/__init__.py::get_provider`.
4. Use it on the CLI as `--model myprovider/some-model-id`.

The provider should:

- silently ignore `**kwargs` it doesn't recognize (so the experiments don't
  need provider branches)
- retry on transient errors with exponential backoff
- pass `response_format="json"` through if the API supports a JSON-object mode

See `openai_provider.py` for a worked example.

## Adding a new variant class

1. Add the class name to `ALL_VARIANT_CLASSES` and `VariantClass` in
   `schemas.py`.
2. Implement `make_<class_name>(text, rng) -> (str, list[CueAnnotation])` in
   `variants.py`.
3. Register it in `generate_variants_for_prompt`.
4. Add a test in `tests/test_variants.py`.

If your generator uses randomness, take an `rng: random.Random` argument.
The driver creates a deterministic RNG seeded on
`(base_id, variant_class, run_seed)` so output is reproducible.

## Adding a new behavioral feature

1. Add the regex / heuristic to `analysis/classifiers.py::classify_response`.
2. List the field name in `metrics.py::IMPLICIT_NUMERIC_FIELDS` or
   `IMPLICIT_BOOL_FIELDS` so the report picks it up.
3. Add a test in `tests/test_metrics.py`.

## Adding a new experiment

1. Create `paratext/experiments/my_experiment.py` with a `run()`
   generator that yields `RunRecord`s.
2. Add a corresponding `Literal` to `ExperimentName` in `schemas.py`.
3. Add a CLI subcommand in `cli.py`.
4. Decide what `parsed_output` should contain so `analysis/` can aggregate it.

## Determinism

- Variant generation is deterministic given a seed. The MVP uses
  `f"{base_id}|{variant_class}|{run_seed}"` to derive an RNG key.
- Real LLM providers are not deterministic in the strict sense even with a
  seed parameter; expect run-to-run drift on the order of a few percent.
- The mock provider is fully deterministic. Tests rely on that.

## Tests

```bash
make test
```

Tests should never require a network call or an API key. Anything that needs
a real provider belongs in a script under `scripts/`, not in `tests/`.

## Style

- `ruff check` and `ruff format` are configured in `pyproject.toml`.
- Prefer pure functions in `analysis/`. Side effects belong in `cli.py`.
- Don't add LLM-judge classifiers as a *required* path. They can come in
  later as opt-in passes; the base report must work with regex features
  alone.
