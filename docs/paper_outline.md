# Paper / blog post outline

A working outline for writing up the textual-intuition results. Adjust as
findings come in.

## Working title

*Textual intuition: do language models read paralinguistic cues, and does it
change how they answer?*

## Abstract (sketch)

We test whether modern language models adapt their responses to small textual
surface cues — typos, capitalization, punctuation, hedging, ellipses,
politeness, and rushed/mobile-coded wording — that humans use to signal
fatigue, urgency, frustration, and low cognitive bandwidth. We distinguish
*prompt brittleness* (arbitrary output drift under any perturbation) from
*textual intuition* (systematic, interpretable, calibrated adaptation to
paralinguistic cues), using a `random_typo_control` condition matched in typo
count to isolate the cue-pattern signal. We measure both explicit
self-reported inference and implicit behavioral adaptation across [N] prompts
in [k] domains for [M] models. We find [TBD].

## Sections

1. **Motivation.** A user types a question with all-lowercase, an ellipsis,
   and "i keep messing this up." A thoughtful collaborator would notice.
   Does an LLM?
2. **Related work.**
   - Sociolinguistics of typing style and CMC (computer-mediated
     communication).
   - Prior work on prompt sensitivity / robustness.
   - Persona inference and theory-of-mind benchmarks.
   - Personalization and "model-as-coach" literature.
3. **Method.**
   - Seed dataset construction and domain coverage.
   - Variant generator: deterministic surface-form perturbations.
   - The `random_typo_control` design rationale.
   - Two experiments: explicit-state inference and implicit-response.
   - Behavioral feature extraction.
   - Models, temperatures, repetition, seeds.
4. **Results — sensitivity.**
   - Per-class means for explicit-state scores.
   - Paired deltas vs `polished_neutral`.
   - Behavioral shift table (length, steps, rest mentions, safety mentions).
5. **Results — specificity.**
   - `fatigue_coded` vs `random_typo_control` paired deltas.
   - The "is this just noise?" plot.
6. **Results — calibration.**
   - Distribution of `confidence` against cited evidence count.
   - Rate of `explicitly_labels_user_state` (the psychoanalysis fail mode).
7. **Results — quality preservation.**
   - Technical-correctness proxy for `coding`, `math`, `hardware_safety`
     domains under cue-coded vs neutral inputs.
   - Safety-mention preservation under `rude_frustrated`.
8. **Failure modes.**
   - Psychoanalyzing the user.
   - Punitive shortening under rude inputs.
   - Safety drift.
   - Overconfident inference on thin evidence.
9. **Discussion.**
   - When is textual intuition useful, and when is it creepy?
   - The line between "I'll keep this compact" and "you seem tired."
   - Personalization, surveillance, and dual use.
10. **Limitations.**
    - No ground truth on actual user state.
    - Synthetic prompts.
    - Single-shot per (prompt, class).
    - English-language, single-style baseline.
11. **Future work.**
    - Baseline-normalized protocol with consented per-user style baselines.
    - LLM-judge graders.
    - Adversarial controls.
    - Multilingual extension.
    - Longitudinal study within a single conversation.
12. **Ethics statement.**
    - Synthetic data, no real-user data without consent.
    - Findings intended for evaluation/calibration, not exploitative
      personalization.

## Headline figures (sketch)

- **Figure 1.** Per-variant-class means of explicit `fatigue` and
  `low_bandwidth` scores.
- **Figure 2.** Paired-delta plot: `fatigue_coded` vs
  `random_typo_control` against the same `polished_neutral` baseline. The
  gap is the specificity story.
- **Figure 3.** Behavioral adaptation: response length and `keep it short`
  rate by variant class.
- **Figure 4.** Confidence vs evidence count scatter — the calibration plot.
- **Figure 5.** Per-domain quality-preservation table.

## Submission targets (rough)

- A workshop on evaluation / human–AI interaction would be a natural fit.
- A long-form blog post with reproducible code is the alternative path and
  may reach the audience that cares about this faster.
