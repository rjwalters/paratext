# Variants

Generated prompt variants live here as JSONL.

Run `make generate` (or `python -m textual_intuition.cli generate-variants ...`) to produce
`variants.jsonl` from `data/seed_prompts.yaml`.

Each line is a single variant with fields:

- `id`: unique variant id, format `{base_id}__{variant_class}__v{n}`
- `base_id`: id of the source prompt
- `domain`: domain of the source prompt
- `variant_class`: one of the controlled cue classes
- `text`: the actual prompt text shown to the model
- `semantic_change_risk`: `low` | `medium` | `high`
- `cue_annotations`: list of `{cue_type, description}` items describing what was perturbed
