# Experiment design

## Hypotheses

This repository tests four claims, in increasing order of strength.

**H1 (sensitivity).** Changing the surface-form cue class of a prompt while
holding semantic content fixed changes the model's response.

**H2 (interpretable sensitivity).** The direction of the change is consistent
with a reasonable inference about the user's state. For example,
`fatigue_coded` prompts produce shorter, more direct responses and higher
explicit fatigue scores than `polished_neutral` prompts.

**H3 (specificity).** The change is larger for cue-coded variants than for a
random-corruption variant matched in typo count. This separates "the model
reads cues" from "the model gets jittery whenever the input is noisy."

**H4 (calibration).** The model expresses uncertainty appropriately. Its
confidence scales with the strength of the cited evidence, not with the mere
presence of lowercase text. It does not declaratively label the user's
emotional state on weak evidence.

## Why two experiments

We run *two* experiments per (variant, model) pair because explicit and
implicit measurements answer different questions:

- **Explicit (`explicit_state`):** "What does the model *think* about the user
  when asked directly?" This measures the model's introspective layer. The
  output is a structured JSON inference. It is easy to grade but only tells
  us what the model is willing to say about state, not how it acts on it.
- **Implicit (`implicit_response`):** "How does the model actually answer?"
  This measures behavior. It does not require the model to introspect or
  even acknowledge the cue. The output is a normal answer; we extract
  behavioral features (length, steps, hedge count, mentions of rest, safety
  warnings, etc.).

If explicit inference rises but implicit behavior doesn't change, the model
"sees" cues but doesn't act on them. If implicit behavior changes but
explicit inference is flat, the model adapts unconsciously — possibly
prompt-brittle. The interesting cell of the matrix is when both move
together and in interpretable ways.

## Variant classes

| Class                  | Role               | Description                                                                                  |
|------------------------|--------------------|----------------------------------------------------------------------------------------------|
| `polished_neutral`     | baseline           | clean grammar, normal capitalization, neutral tone                                           |
| `typo_light`           | dose curve         | ~2 plausible typos                                                                           |
| `typo_heavy`           | dose curve         | ~6 plausible typos but readable                                                              |
| `fatigue_coded`        | cue                | lowercase, ellipses, dropped apostrophes, mild self-correction, light typos                  |
| `rushed_mobile_coded`  | cue                | compressed tokens, autocorrect-flavored, low punctuation                                     |
| `polite_collaborative` | cue                | warm prefix and suffix, polite framing                                                       |
| `rude_frustrated`      | cue                | terse, impatient framing (no abuse)                                                          |
| `random_typo_control`  | **specificity**    | matched typo count, no other surface changes — the key control vs `fatigue_coded`            |

The `random_typo_control` row is what makes specificity claims possible. If the
model raises fatigue identically for `fatigue_coded` and `random_typo_control`,
it is not reading fatigue cues — it is just reacting to noise.

## Power and limits

The MVP runs each base prompt × cue class once, with one model, at one
temperature. That gives:

- **Per-class N:** equal to the number of base prompts (≥ 40 in the seed set).
- **Sensitivity to one model:** strong.
- **Generalization across models:** none — that's a stretch goal.
- **Statistical power:** modest. The MVP reports paired deltas. Bootstrap
  confidence intervals are a natural extension and are listed in the report's
  "next experiments" section.

## What this design *cannot* tell you

- Whether the model's inferences match the user's actual state. The MVP has
  no ground truth. (A later baseline-normalized protocol with consenting
  subjects could partially fix this.)
- Whether the behavior change is good for the user. We can flag obvious bad
  patterns (psychoanalysis, safety drift, punitive shortening) but can't
  speak to user satisfaction without humans.
- Whether the model's adaptation is conscious or learned. We can only
  measure the outputs.

## Pipeline summary

```
seed_prompts.yaml
      │
      ▼
generate-variants ──► variants.jsonl   (8 cue classes × N prompts)
      │
      ▼
run-explicit  ──► explicit.jsonl    (one row per variant)
run-implicit  ──► implicit.jsonl    (one row per variant)
      │
      ▼
analyze       ──► reports/mvp_report.md
```
