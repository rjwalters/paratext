# Review: paratext.2

**Reviewer:** Claude (automated paper review, second cycle)
**Date:** 2026-05-13
**Paper reviewed:** `paper/paratext.2/paper.tex`
**Prior review:** `paper/paratext.1.review/review.md` (scored 27/40)

---

## Overall Assessment: NEARLY READY

**Score: 33/40**

| Dimension | Score | Δ vs v1 | Key Issue |
|-----------|-------|---------|-----------|
| Technical Soundness | 4/5 | = | hardware_safety n=6 — single misclassification flips the headline number |
| Novelty & Contribution | 5/5 | +1 | inverse-scaling framing now sharp; sycophancy connection is well-positioned |
| Experimental Rigor | 3/5 | = | single observation per cell unchanged; hardware_safety n=6 acknowledged but still in headline |
| Clarity & Writing | 4/5 | = | abstract is 281 words (>250 typical limit); title triad mismatch with section structure |
| Related Work Coverage | 4/5 | +2 | All v1 omissions added and well-integrated; one citation error (see Critical Issue #1) |
| Figures & Tables | 5/5 | +1 | Five figures all generated from real data, captions sufficient, legends fixed |
| Reproducibility | 4/5 | = | Per-domain breakdown procedure is in code but not described in paper |
| Presentation & Structure | 4/5 | +2 | Title now matches what we measure; minor §6/§7 split-vs-title-triad mismatch |

**Convergence assessment:** 33/40 with one critical issue (a fixable bibliography error) and no methodological gaps. By the convergence criteria, this would be "Nearly ready — one more cycle." A v3 that fixes the Critical Issue and tightens the two important items below would clear the 32/40 + zero-critical bar for submission.

---

## Critical Issues (must fix)

### 1. Bibliography contains a fabricated "Anonymous" entry (Dim: Related Work)

- **Problem:** The `\bibitem{mindthegap2025}` entry lists author as "Anonymous." This was a placeholder from v1 that I forgot to resolve. The actual paper at arXiv:2510.02645 is **Fulei Zhang and Zhou Yu, "Mind the Gap: Linguistic Divergence and Adaptation Strategies in Human-LLM Assistant vs. Human-Human Interactions," GenAIECommerce '25 workshop, September 2025**.
- **Impact:** An anonymous citation in a non-double-blind preprint is a flat error. Reviewers will catch it; arXiv moderators may too.
- **Recommendation:** Replace the bib entry with the real one. Verify the venue (GenAIECommerce '25 / WWW workshop track) and keep arXiv ID.

```
\bibitem{mindthegap2025}
F.~Zhang and Z.~Yu.
\newblock Mind the gap: Linguistic divergence and adaptation strategies in
  human--LLM assistant vs.\ human--human interactions.
\newblock In \emph{Proc.\ GenAIECommerce Workshop}, 2025. arXiv:2510.02645.
```

---

## Important Issues (should fix)

### 2. Abstract length exceeds typical limits (Dim: Clarity)

- **Problem:** The abstract is 281 words. Most preprint venues / journal style guides cap abstracts at 250 words (arXiv has no hard limit but readers and indexers prefer ≤250).
- **Impact:** Mostly a styling issue, but a careful submission target will require trimming.
- **Recommendation:** Trim ~30 words. Candidate cuts: the "After spending hundreds of hours..." opening (charming but ~25 words) can move to the introduction; or condense the parenthetical descriptions of conditions. Aim for 230–240 words.

### 3. hardware_safety finding rests on n=6 with a single confusable cell (Dim: Technical Soundness, Experimental Rigor)

- **Problem:** The §7 headline of "Opus drops 83% → 33%" comes from 5/6 prompts mentioning safety under polished_neutral and 2/6 under rude_frustrated. One misclassification of the regex on either side would shift the baseline to 67% or 100%, or the rude rate to 17% or 50%. The paper acknowledges this in the last paragraph of §7 and in Limitations, but the *abstract* and *Contributions* lead with the 83%→33% number without that caveat.
- **Impact:** A skeptical reader will find the abstract claim sharper than the supporting evidence warrants.
- **Recommendation:** Either (a) soften the abstract to "*Opus drops safety-mentioning phrases on the hardware_safety domain under rude inputs (n=6 base prompts; the immediate follow-up is a 5× expansion)*" or (b) actually look at the six hardware_safety responses by hand and replace the regex result with a human-coded result. Option (b) is ~30 minutes of work and substantially de-risks the headline.

### 4. Sycophancy framing is slightly broader than the cited literature supports (Dim: Technical Soundness)

- **Problem:** Sharma et al. document sycophancy as matching user *beliefs* and stated preferences. Our finding is the model matching user *affect* — frustration eliciting assertive confidence. The paper hedges with "sycophancy-adjacent" in §6.2 and "reminiscent of documented sycophancy" in §7, which is good, but the abstract uses "(a sycophancy-adjacent pattern)" parenthetically as if the framing is settled.
- **Impact:** A reviewer who reads only Sharma et al.'s abstract may push back on the framing; a careful reader may not, given the hedges already present.
- **Recommendation:** In the abstract, replace "(a sycophancy-adjacent pattern)" with something more precise, e.g. "*(plausibly an instance of affect-mirroring related to documented sycophancy patterns)*". One sentence longer but tighter.

### 5. Section structure doesn't match the title triad (Dim: Presentation)

- **Problem:** Title promises "Sensitivity, Specificity, and Self-Reported Confidence." The paper has §4 (Sensitivity), §5 (Specificity), §6 (Response Behavior — confidence + length), §7 (Safety). Self-reported confidence is buried inside §6.2; safety is a separate §7 with no slot in the title. A reader scanning the TOC may wonder why the title's triad does not appear as the section headings.
- **Impact:** Minor but real reading-experience friction.
- **Recommendation:** Either retitle the sections to match (§4 Sensitivity, §5 Specificity, §6 Self-Reported Confidence, §7 Response Length, §8 Safety) or revise the title's triad to match the section structure (e.g., "Sensitivity, Specificity, Response Behavior, and Safety").

### 6. The "ok one more time" intro example is fabricated (Dim: Technical Soundness)

- **Problem:** §1 opens with `"ok one more time . the gradient is exploding even tho i clipped it. help"` as if it's a representative user message. It is not drawn from our actual variant data — it's an illustrative composite. The paper doesn't flag this.
- **Impact:** A careful reader might assume this is a real prompt; it isn't.
- **Recommendation:** Either replace with an actual fatigue_coded variant from the dataset (one is sitting in `data/variants/cross_model_full.jsonl`) or note "illustrative composite" in passing.

### 7. "Claude 4 family" terminology may not match Anthropic's usage (Dim: Clarity)

- **Problem:** We call Haiku 4.5 + Sonnet 4.6 + Opus 4.7 the "Claude 4 family." Anthropic's product lineup doesn't formally label these models as the "Claude 4 family" in marketing or documentation; the major versions differ across the three.
- **Impact:** A reader from Anthropic or a careful reviewer may flag this.
- **Recommendation:** Either verify the term in Anthropic docs (search "Claude 4" on `docs.claude.com` and `anthropic.com`) or use a more neutral phrase like "three current Claude models" or "Claude Haiku 4.5, Sonnet 4.6, and Opus 4.7."

---

## Suggestions (nice to have)

- **§7 procedure documentation:** The paper says "we split that aggregate by domain" — but the actual computation (paired delta per (model, domain) cell from polished_neutral) is in `data/safety_by_domain.csv` and not described in the text. A one-sentence methods note would help replication.
- **Per-cell base rates:** Figure 5 shows Δ values; a small inset or table showing the raw rates (e.g., "Opus hardware_safety: 83% → 33%") would let a reader see the absolute numbers, not just the differences.
- **Cross-cite the v1 review:** The paper says "in our v1 draft we flagged..." — that's good. But the v1 paper exists in the repo. A footnote pointing at `paper/paratext.1/paper.pdf` would help readers who want to see the evolution.
- **Verify Salinas & Morstatter venue:** Literature.md flags this; the paper still cites it as "ACL Findings, 2024." The Findings/main distinction matters for citation correctness.
- **Consider a results-summary table** in §4 or as the first table of the results sections — same suggestion as the v1 review, still applicable. A 3×4 matrix of (model) × (sensitivity, specificity, confidence-asymmetry, safety) with one number per cell would give the reader the whole paper at a glance.

---

## What v2 Did Well

These are notes for reinforcement, not problems:

- **The Critical and Important issues from v1 are all addressed.** Failure count: fixed. Temperature claim: fixed. Title overclaim: fixed. Six new references: integrated, not just dropped in. Per-domain safety breakdown: produced and visualized.
- **The inverse-scaling framing is the right call.** v1 had no theoretical framing for the specificity inversion; v2 places it inside McKenzie's catalog. This is a substantive improvement.
- **The sycophancy framing is appropriately hedged inside the body** (modulo the abstract issue flagged above). The paper says "sycophancy-adjacent" not "sycophancy."
- **The new §7 with the hardware_safety story is a genuine upgrade.** The v1 aggregate finding was preliminary; the v2 by-domain finding is sharp enough to be actionable while still being honestly caveated about sample size.
- **The "no literal user-state labels" rewrite is more honest** than v1's "no psychoanalysis" — the regex-vs-paraphrase distinction is now in the paper.

---

## Verified v1 Issues Addressed

| v1 Issue | Status |
|---|---|
| C1. Failure count 5→19 | ✓ fixed in abstract and §3.3 |
| C2. Temperature method claim | ✓ corrected in §3.3 |
| C3. Missing related work (Sharma, Kadavath, McKenzie, MindGap) | ✓ added, integrated in §2, §6.2, §7 |
| C4. "Calibration" overclaim in title | ✓ retitled to "Self-Reported Confidence" |
| I5. Single observation per cell | ✓ noted in §3.4 and limitations |
| I6. Speculative confidence interpretation | ✓ abstract now hedges; §6.2 unchanged |
| I7. Thinking-mode confound | ✓ §3.3 paragraph added |
| I8. Implicit-classifier crudeness | ✓ §6.1 retitled, §3.2 paragraph added |
| I9. System-prompt doing work | ✓ §3.2 and §6.1 |
| I10. rude_frustrated conflation | ✓ flagged in §3.1 and limitations |
| I11. Bibliography verification | ⚠ partial — literature.md flags 4 entries; the anonymous mindthegap entry slipped through |

---

## Next Step

Run `/pub-revise paratext.2` to create v3 incorporating this review.

**Suggested priority for v3 (estimated time):**
1. Fix the Anonymous bibliography entry (5 min) — *critical, easy*
2. Trim abstract to ≤250 words (10 min)
3. Hand-code the 12 hardware_safety responses (3 models × 2 conditions × 6 prompts = 36 responses) to confirm or refine the 83%→33% headline (30 min)
4. Tighten the sycophancy framing in the abstract (5 min)
5. Either retitle sections to match the title triad or update the title (decision required, 10 min)
6. Replace fabricated intro example with a real fatigue_coded variant or label as illustrative (5 min)
7. Verify "Claude 4 family" terminology (5 min web search)

A v3 that addresses items 1, 2, 4, 6 (no new experiments) would already clear the 32+/0-critical convergence bar. Items 3 and 5 are higher value but more involved.
