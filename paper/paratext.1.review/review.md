# Review: paratext.1

**Reviewer:** Claude (automated paper review)
**Date:** 2026-05-13
**Paper reviewed:** `paper/paratext.1/paper.tex`

---

## Overall Assessment: NEEDS WORK (but the bones are good)

**Score: 27/40**

| Dimension | Score | Key Issue |
|-----------|-------|-----------|
| Technical Soundness | 4/5 | Mostly solid; one factual error on failure count, one method claim that contradicts the actual code |
| Novelty & Contribution | 4/5 | Decoupling design is genuinely novel; specificity-inversion is the publishable finding |
| Experimental Rigor | 3/5 | n=48 with single (model, base_id, class) cell — bootstrap captures between-prompt only, not sampling variance |
| Clarity & Writing | 4/5 | Reads well; some interpretive claims overreach what the data show |
| Related Work Coverage | 2/5 | Major omissions: sycophancy literature (Anthropic's own!), confidence calibration (Kadavath), inverse scaling, recent linguistic-divergence work |
| Figures & Tables | 4/5 | Four figures all generated from real data, captions adequate; legend placement obscures bars in fig 4 |
| Reproducibility | 4/5 | Code/data linked, seeds described; thinking-mode-per-model variation is a hidden confound |
| Presentation & Structure | 2/5 | Title overclaims ("calibration" is not measured statistically); abstract anecdote may belong in blog not preprint |

---

## Critical Issues (must fix)

### 1. Factual error: failure count and rate (Dim: Technical Soundness)

- **Problem:** Section 3.3 says *"We observed 5 silent failures (0.19%) attributable to transient API errors"*. The actual count is **19 silent failures (0.73%)** — 2 in sonnet_explicit, 8 in sonnet_implicit, 4 in opus_explicit, 5 in opus_implicit, 0 in either Haiku run. Total successful records: 2,573 / 2,592.
- **Impact:** This is the only quantitative claim in the paper that is wrong. Reviewers will catch it.
- **Recommendation:** Fix the number; consider acknowledging the asymmetry (Sonnet/Opus failed; Haiku didn't).

### 2. Method-section misstatement on temperature (Dim: Technical Soundness)

- **Problem:** Section 3.3 says *"Temperature is dropped on Opus 4.7 (the API rejects sampling parameters under adaptive thinking) and held at 0.2 / 0.7 (explicit / implicit) on the others."* But the actual adapter code (`anthropic_provider.py:144-146`) strips `temperature` whenever `thinking=True`, regardless of model. Since the entire sweep ran with `--thinking` on, **temperature was not set on any of the three models.**
- **Impact:** Reproducibility claim is wrong. Anyone trying to replicate using temperature 0.2/0.7 with thinking will get different behavior than what we ran.
- **Recommendation:** Either (a) correct the method section to say "no sampling parameters were passed under adaptive thinking on any model," or (b) re-run with explicit temperatures — but option (a) matches what we actually did.

### 3. Major missing related work (Dim: Related Work Coverage)

The paper is conspicuously light on directly-relevant prior work. The following are **must-cite**, in priority order:

- **Sharma et al., "Towards Understanding Sycophancy in Language Models," ICLR 2024** (arXiv:2310.13548). This is Anthropic's own work showing that RLHF models match user views/affect. Our "Opus +0.108 confidence under rudeness" finding is plausibly a sycophancy phenomenon and the paper does not even mention sycophancy. This omission is hard to defend.
- **Kadavath et al., "Language Models (Mostly) Know What They Know,"** 2022. Canonical reference for self-reported confidence in LLMs. Our confidence analysis cites no calibration literature at all.
- **McKenzie et al., "Inverse Scaling: When Bigger Isn't Better,"** TMLR 2023. The specificity inversion is exactly the kind of finding inverse-scaling work cares about. We should position our result against theirs.
- **"Mind the Gap: Linguistic Divergence and Adaptation Strategies"** (arXiv:2510.02645, 2025). Recent work showing humans write more terse/degraded/less polite text to LLMs than to humans — this is the same phenomenon as our cue classes, from the user side. Strong adjacency.
- **Strachan et al., "Evaluating large language models in theory of mind tasks,"** PNAS 2024. We cite a 2019 ToMi paper but ignore the much more recent and relevant work.

### 4. Title misrepresents the work (Dim: Presentation & Structure)

- **Problem:** Subtitle is "Sensitivity, Specificity, and **Calibration** of Paratext Inference." We do not measure calibration in the statistical sense (alignment of self-reported confidence with actual accuracy). We measure self-reported confidence shifts. These are different things — the calibration literature has a precise meaning that we are not delivering on.
- **Impact:** Misleads readers who come for a calibration paper.
- **Recommendation:** Replace "Calibration" with something we actually measured. Suggested: *"Sensitivity, Specificity, and Self-Reported Confidence in Paratext Inference Across the Claude 4 Family,"* or — more honestly — drop the third axis and run a real calibration probe in v2.

---

## Important Issues (should fix)

### 5. Single observation per (model, base_id, class) (Dim: Experimental Rigor)

- The bootstrap CIs estimate between-prompt variance with n=48. They do **not** estimate within-prompt sampling variance — each (model, base_id, class) cell is a single API call. With temperature stripped under thinking, we don't know how reproducible any individual cell is. A 3-resample-per-cell pilot on a small subset would let us decompose between- vs within-prompt variance and either tighten the CIs or widen them honestly.

### 6. Confidence-asymmetry interpretation is speculative (Dim: Technical Soundness)

- Section 6.2 offers two readings ("assertiveness compensation" vs "display, not belief") and admits we can't distinguish them. Good. But the abstract/intro frame this as a "Opus alone becomes more confident" finding without that caveat. The honest framing is: *"Opus's self-reported confidence rises under rude framing — whether this reflects genuine epistemic shift or stylistic mirroring is unresolved by this study."* Tighten the abstract.

### 7. Thinking-mode confound across models (Dim: Reproducibility)

- Opus 4.7 ran with `display: "omitted"` adaptive thinking (no visible thinking content). Sonnet 4.6 ran with adaptive thinking and visible thinking blocks. Haiku 4.5 ran with **manual** thinking, budget 5000 tokens. These are not equivalent settings — a Sonnet response that shows thinking spends output tokens differently than an Opus response that doesn't. The cross-model comparison is partly contaminated by this.
- **Recommendation:** Either acknowledge this in the methods (cheap), or re-run a small probe with thinking off on all three models to confirm direction holds (more work, more defensible).

### 8. Implicit-classifier crudeness undersold (Dim: Experimental Rigor)

- The "zero psychoanalysis" finding is striking — but it depends on a regex that detects literal phrases like "you seem tired." A model could express the same content as "I'll keep this short since you're clearly working through something tonight" and the classifier would miss it. The paper mentions this in Limitations but the headline claim ("zero psychoanalysis across the family") would mislead a reader who skims.

### 9. System-prompt instruction is doing real work (Dim: Technical Soundness)

- The implicit-response system prompt explicitly says *"do not psychoanalyze the user or label their emotional state."* The "zero psychoanalysis" finding then partly tests instruction-following, not natural model behavior. A condition without that instruction would be a useful baseline.

### 10. "rude_frustrated" conflates two states (Dim: Experimental Rigor)

- Rudeness and frustration are not the same construct. ALL CAPS and imperatives can signal urgency without frustration; expressed frustration doesn't require rudeness. The variant class bundles them. This is fine for a first paper, but the paper should either rename the variant ("rude") or note the conflation.

### 11. Bibliography needs explicit verification (Dim: Related Work Coverage)

- The 9 references are plausible-looking but were seeded from general field knowledge, not from a real search. Each needs lookup before submission. In particular, verify Salinas & Morstatter 2024 venue, Salemi et al. 2024 year (LaMP appeared in 2023?), and Herring 2013 chapter title.

---

## Suggestions (nice to have)

- **Figure 4 legend placement** ("lower left") sits on top of the largest negative bars; move to "upper right" or shrink legend to fit margin.
- **Add a per-domain breakdown plot** for the safety-warning finding even before doing a fresh run — splitting the existing data is free and would already de-risk the headline.
- **The personal-anecdote opening** ("the first author noticed something") is charming for the blog version but reads as informal for a preprint. Consider keeping it in the blog and replacing the abstract opener with the punchy version of the headline finding.
- **Add a results-summary table** at the start of Section 5 — a single 3-row × 3-column matrix of (Haiku, Sonnet, Opus) × (sensitivity, specificity gap, confidence-under-rude) would give the reader the headline at a glance.
- **The cost figure ($30)** is genuinely useful for reproducibility — keep it but consider adding "wall time ~70 minutes at concurrency=8" alongside.
- **Mention the silent failure asymmetry as data** — Haiku had zero failures; Sonnet/Opus dropped 0.5–2% of calls. That's not just a number, it's a small finding about API reliability under load.

---

## Missing Related Work (formal citations)

- **Sharma et al., 2023** — *Towards Understanding Sycophancy in Language Models.* arXiv:2310.13548; ICLR 2024.
  - Relevance: Direct precedent for the Opus-confidence-under-rudeness finding. Sycophancy is Anthropic's own framing of "model adapts output to user affect." Cannot omit.
  - Recommendation: cite in §6.2 (confidence asymmetry); discuss in §7 (Discussion).

- **Kadavath et al., 2022** — *Language Models (Mostly) Know What They Know.* arXiv:2207.05221.
  - Relevance: Canonical work on LLMs' self-reported confidence. We claim to study "confidence" without engaging this literature.
  - Recommendation: cite in §6.2; reframe our confidence work as building on Kadavath's "verbalized confidence" formulation.

- **McKenzie et al., 2023** — *Inverse Scaling: When Bigger Isn't Better.* TMLR.
  - Relevance: Our specificity inversion is an inverse-scaling finding by another name.
  - Recommendation: cite in §5; position our result inside the inverse-scaling literature.

- **arXiv:2510.02645, 2025** — *Mind the Gap: Linguistic Divergence and Adaptation Strategies in Human-LLM Communication.*
  - Relevance: Documents that humans write differently to LLMs than to humans (terser, less polite, more grammatical errors). This is the user side of the same phenomenon we study from the model side.
  - Recommendation: cite in §1 (Introduction) and §2 (Background); strong framing aid.

- **Strachan et al., 2024** — *Evaluating large language models in theory of mind tasks.* PNAS.
  - Relevance: Modern, high-profile theory-of-mind work in LLMs. Our 2019 ToM citation is dated.
  - Recommendation: replace or supplement Le et al. 2019 with this in §2.

- **Lin, Hilton, Evans, 2022** — *Teaching models to express their uncertainty in words.* TMLR.
  - Relevance: The verbalized-confidence framework that our `confidence` field implicitly inhabits. Worth a sentence.
  - Recommendation: cite alongside Kadavath in §6.2.

---

## Verified Numerical Claims (spot-check passed)

I re-ran every numerical claim against `data/runs/cross_model/*.jsonl`. All except the failure count match the data:

| Claim | Paper | Data | Match |
|---|---|---|---|
| fatigue_coded Δ Haiku/Sonnet/Opus | +0.28 / +0.37 / +0.34 | +0.277 / +0.369 / +0.336 | ✓ |
| Opus confidence Δ rude_frustrated | +0.108 [0.090, 0.127] | exact match | ✓ |
| Specificity (Haiku cue_only vs typo) | +0.294 vs +0.167 | exact match | ✓ |
| Sonnet cue_only vs random_typo | +0.330 vs +0.328 | exact match | ✓ |
| Opus cue_only vs random_typo | +0.329 vs +0.319 | exact match | ✓ |
| Opus safety Δ rude_frustrated | -0.128 [-0.234, -0.021] | exact match | ✓ |
| num_words Δ rude_frustrated | -64 / -80 / -115 | -63.9 / -80.4 / -115.2 | ✓ (rounding fine) |
| explicitly_labels_user_state Δ | 0.000 every cell | confirmed 0/24 cells | ✓ |
| Total cost | ~$30 | $29.03 | ✓ |
| Failure count | 5 (0.19%) | **19 (0.73%)** | ✗ |

---

## Next Step

Run `/pub-revise paratext.1` to create version 2 incorporating this review.

**Suggested priority order for v2 revisions:**
1. Fix factual error on failure count (5 min)
2. Fix method-section temperature claim (5 min)
3. Add the four critical missing references (sycophancy, calibration, inverse-scaling, linguistic-divergence) and integrate them into §2 and §6 (60–90 min)
4. Retitle to remove "calibration" or run a real calibration probe (decision required)
5. Tighten abstract to flag confidence-asymmetry interpretive uncertainty (10 min)
6. Add per-domain breakdown for safety-warning finding (free — uses existing data)
7. Move figure 4 legend, fix the overfull hbox warning (5 min)

A v2 that addresses items 1–3, 5, 6 would jump from "NEEDS WORK" to "STRONG" without any new experiments.
