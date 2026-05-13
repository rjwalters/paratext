# Literature notes — paratext.1

Lightweight v1 notes. For v2 we should do a proper search before submission.

## Positioning

This paper sits at the intersection of three established literatures, none of which
directly addresses the question we ask:

1. **Prompt sensitivity / robustness** establishes that LLMs drift under benign edits
   but does not distinguish drift from calibrated adaptation. Our `random_typo_control`
   condition is designed to do exactly that.
2. **Theory-of-mind and persona inference benchmarks** test whether models can reason
   about mental states in third-party stories. We test something narrower: whether the
   model registers the latent state of the person it is currently talking to.
3. **Personalization** research generally assumes an explicit user profile. We test
   zero-shot, single-message paratext reading.

## Citations seeded in v1 (verify before submission)

- Genette 1997 — origin of the term "paratext"
- Baron 2008 — CMC sociolinguistics
- Herring 2013 — discourse on the modern web
- Sclar et al. 2024 (ICLR) — prompt sensitivity quantification
- Salinas & Morstatter 2024 (ACL Findings) — butterfly effect of prompt changes
- Le et al. 2019 (EMNLP) — ToMi benchmark
- Sap et al. 2019 (EMNLP) — SocialIQA
- Salemi et al. 2024 (ACL) — LaMP personalization
- Efron & Tibshirani 1994 — bootstrap textbook

## Gap analysis

Existing prompt-sensitivity work shows aggregate output instability. We are
asking whether the instability has a *direction* — whether the drift is the
calibrated kind ("I'll soften my tone because this person seems tired") or
the arbitrary kind ("the same input formatted differently produces a
different answer for no good reason").

The decoupling design (`cue_only` vs `random_typo_control`) is the
contribution that makes that distinction quantifiable.

## Searches to run before v2

- Anthropic and DeepMind work on model-of-user adaptation
- ACL/EMNLP 2024–2026 papers on instruction sensitivity to surface form
- CHI / CSCW papers on adaptive UI in chat
- Work on confidence calibration under adversarial prompts
- Recent papers specifically on Claude 4 behavior
