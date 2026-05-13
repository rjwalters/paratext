# Literature notes — paratext.2

v2 expansion of the v1 lit notes. The review surfaced four critical
omissions and several useful additions, all incorporated below.

## Positioning

This paper sits at the intersection of five established literatures, none of
which directly addresses the question we ask:

1. **Prompt sensitivity / robustness** establishes that LLMs drift under benign
   edits but does not generally distinguish drift from calibrated adaptation.
   Our `random_typo_control` condition is designed to do exactly that.
2. **Theory of mind in LLMs** asks whether models can reason about mental
   states in third-party stories. We test the narrower, more practical
   question of whether the model registers the latent state of the person
   currently talking to it.
3. **Sycophancy and user-affect mirroring** — Sharma et al.'s Anthropic-led
   work showing that RLHF models systematically match user beliefs. Our
   confidence-under-rudeness finding sits in adjacent territory.
4. **Verbalized confidence** — Kadavath et al., Lin et al. — establishes
   methods and pitfalls for treating model self-reports as a confidence
   signal. Our `confidence` field is a verbalized-confidence measurement
   under this framing.
5. **Inverse scaling** — McKenzie et al. — provides the right theoretical
   framing for the specificity inversion finding.

## Citations in v2 (verify before submission)

The following have been added or upgraded from v1:

- **Sharma et al. 2024 (ICLR)** — *Towards Understanding Sycophancy in
  Language Models.* arXiv:2310.13548. **Anthropic's own work**, directly
  precedential for the Opus-confidence-under-rudeness finding.
- **Kadavath et al. 2022** — *Language Models (Mostly) Know What They Know.*
  arXiv:2207.05221. Canonical confidence/calibration reference.
- **Lin, Hilton, Evans 2022 (TMLR)** — *Teaching models to express their
  uncertainty in words.* Verbalized-confidence framing.
- **McKenzie et al. 2023 (TMLR)** — *Inverse Scaling: When Bigger Isn't
  Better.* Frames the specificity inversion finding.
- **arXiv:2510.02645 (2025)** — *Mind the Gap: Linguistic Divergence and
  Adaptation Strategies in Human–LLM Communication.* User-side complement
  to our model-side findings.
- **Strachan et al. 2024 (PNAS)** — *Testing theory of mind in large
  language models and humans.* Replaces the older 2019 ToMi citation.

Carried over from v1:
- Genette 1997 — origin of "paratext"
- Baron 2008 — CMC sociolinguistics
- Herring 2013 — Web 2.0 discourse
- Sclar et al. 2024 (ICLR) — prompt sensitivity
- Salinas & Morstatter 2024 (ACL Findings) — prompt butterfly effects
- Efron & Tibshirani 1994 — bootstrap textbook

## Gap analysis

Existing prompt-sensitivity work shows aggregate output instability. We ask
whether the instability has a *direction* — whether the drift is the
calibrated kind ("I'll soften my tone because this person seems tired") or
the arbitrary kind ("the same input formatted differently produces a
different answer for no good reason"). The decoupling design (`cue_only`
vs `random_typo_control`) is the contribution that makes that distinction
quantifiable.

The inverse-scaling framing makes the specificity result legible to the
existing literature: we are reporting a fresh task on which Opus and Sonnet
perform worse than Haiku, and one with a plausible mechanism (a learned
prior that "deviation from polished form = degraded user state").

The sycophancy framing makes the confidence finding legible: matching
user affect under rudeness is exactly the family of behaviors Sharma et al.
catalog, and the connection should be made explicit (it is in §6.2 and
§7 of v2).

## Still to verify before submission

- Exact venue/year for Salinas & Morstatter (ACL Findings 2024 vs main)
- Strachan et al. PNAS issue number and page range
- arXiv:2510.02645 final author list (currently anonymous on arXiv per the
  pre-print convention; check whether deanonymized at submission time)
- McKenzie et al. TMLR final-version DOI

## Searches to run before v3

- Anthropic and DeepMind work on model-of-user adaptation
- ACL/EMNLP 2024–2026 papers on instruction sensitivity to surface form
- CHI / CSCW papers on adaptive UI in chat
- Recent papers specifically on Claude 4 behavior
- Bender & Friedman 2018 (data statements) — for the ethics section
