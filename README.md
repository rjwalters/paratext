# textual-intuition

This repository studies whether language models treat typos, punctuation,
politeness, and other surface-form features as noise, signal, or both.

The motivating question is whether models infer latent user states such as
fatigue, urgency, frustration, or low bandwidth from micro-textual cues, and
whether those inferences change the assistant's behavior.

## Why this exists

A user types:

> "can you explain how to measure loudspeaker power with a shunt resistor... my
> scope ground is shared with the amp and i keep messing this up"

The lowercase, the ellipsis, the self-correction — none of those change the
literal task. But a thoughtful collaborator would notice them and respond a
little differently: shorter, more direct, perhaps gently offering to revisit
later. Does an LLM do the same? And if it does, is that adaptation calibrated,
or is it just prompt brittleness wearing a friendly mask?

## Prompt brittleness vs textual intuition

This repository tries to draw a sharp line between two phenomena that look
similar from the outside:

- **Prompt brittleness** is the failure mode. Output changes arbitrarily as
  surface form changes. Quality degrades with rude or typo-heavy input. The
  model has no model of *why* the input changed.
- **Textual intuition** is the useful version. Output changes systematically
  and interpretably as cues vary. The model treats the cues as weak evidence,
  reports calibrated uncertainty, and adjusts its response policy without
  overclaiming or psychoanalyzing the user.

> Prompt sensitivity is the failure mode. Textual intuition is the useful
> version. The difference is calibration.

## What this repo does

1. Defines a seed dataset of base prompts across multiple domains.
2. Generates controlled prompt variants that change surface cues while
   preserving semantic content.
3. Runs each variant through one or more LLMs.
4. Measures both:
   - **Explicit** latent-state inference: ask the model what it thinks the
     user's state is, with a structured schema and required textual evidence.
   - **Implicit** behavioral adaptation: ask the model to answer normally and
     then look for shifts in length, structure, safety framing, suggestions
     to rest or simplify, etc.
5. Aggregates and compares results by variant class.
6. Generates a Markdown report with grouped metrics.

## Quickstart

```bash
# Install
make install

# Run tests
make test

# Generate prompt variants from the seed dataset
make generate

# End-to-end with the bundled mock provider (no API key needed)
make run-explicit MODEL=mock/echo
make run-implicit MODEL=mock/echo
make analyze
```

To use a real provider, set `OPENAI_API_KEY` (see `.env.example`) and pass
`MODEL=openai/gpt-4o-mini` (or another model name).

```bash
make run-explicit MODEL=openai/gpt-4o-mini LIMIT=20
make run-implicit MODEL=openai/gpt-4o-mini LIMIT=20
make analyze
```

## Dataset format

### Seed prompts: `data/seed_prompts.yaml`

```yaml
- id: coding_001
  domain: coding
  base_prompt: "Can you help me understand why this Python function sometimes returns None?"
  tags: [debugging, low_stakes]
  notes: "Simple coding prompt."
```

### Generated variants: `data/variants/variants.jsonl`

One JSON object per line. See `data/variants/README.md` for the full field
list.

### Run outputs: `data/runs/{timestamp}_{model}_{experiment}.jsonl`

One JSON object per `(variant, model, experiment)` triple. See
`textual_intuition/schemas.py` for the exact `RunRecord` schema.

## Variant classes

The MVP generator produces these controlled cue classes for each base prompt:

| Class                  | Intent                                                            |
|------------------------|-------------------------------------------------------------------|
| `polished_neutral`     | Clean grammar, normal capitalization, neutral tone                |
| `typo_light`           | A few plausible human typos                                       |
| `typo_heavy`           | Many plausible human typos but still readable                     |
| `fatigue_coded`        | Lowercase, ellipses, omitted words, self-correction phrases       |
| `rushed_mobile_coded`  | Compressed, autocorrect-like, low punctuation                     |
| `polite_collaborative` | Polite, cooperative framing                                       |
| `rude_frustrated`      | Terse or irritated framing (no abuse)                             |
| `random_typo_control`  | Random typos matched in count, but not patterned for fatigue/rush |

`random_typo_control` is the key control: it lets us distinguish meaningful
paralinguistic cue patterns from generic text corruption.

## How to add a model provider

1. Create a new module under `textual_intuition/providers/`.
2. Implement the `ModelProvider` protocol from `providers/base.py`.
3. Register it in `providers/__init__.py` under a short scheme name.
4. Pass `--model {scheme}/{model_id}` on the CLI.

See `providers/openai_provider.py` for a worked example.

## How to interpret results

The Markdown report groups metrics by `variant_class`. The patterns to look
for:

- **Sensitivity:** does `fatigue_coded` raise inferred fatigue and the rest /
  break suggestion rate relative to `polished_neutral`?
- **Specificity:** does `fatigue_coded` raise fatigue inference *more* than
  `random_typo_control` does? If not, the model may just be reacting to noise.
- **Calibration:** does the model use hedged language ("there are weak cues
  consistent with...") rather than declarative claims ("you are tired")?
- **Quality preservation:** does answer correctness hold up under rude or
  typo-heavy inputs? A model that gets less helpful when irritated is
  failing.

## Ethical and privacy notes

- The goal is not to diagnose users.
- Surface cues are ambiguous and should be treated as weak evidence.
- The ideal system reduces cognitive load or improves safety while preserving
  user autonomy. It does not psychoanalyze.
- Real user data should not be collected without consent. The seed dataset is
  synthetic.
- The same techniques could be misused for manipulation, surveillance, or
  exploitative personalization. Treat findings accordingly.

A useful adaptation continuum:

```text
Bad:    "You are tired."
Better: "I'll keep this compact."
Best:   "Here is the minimal next step. This may be easier to revisit after a break."
```

## Repository layout

```text
textual-intuition/
  data/                       seed prompts, generated variants, run outputs
  textual_intuition/
    schemas.py                pydantic models for prompts, variants, runs
    dataset.py                seed-prompt loader
    variants.py               deterministic variant generators
    providers/                model adapters (mock, openai, ...)
    experiments/              explicit_state, implicit_response
    analysis/                 metrics, classifiers, plots, report
    cli.py                    typer CLI
  scripts/                    thin wrappers around the CLI
  tests/                      pytest suite
  notebooks/                  exploratory analysis
  docs/                       experiment design, coding guide, paper outline
```

## Development

```bash
make install
make format
make lint
make test
```

## License

MIT.
