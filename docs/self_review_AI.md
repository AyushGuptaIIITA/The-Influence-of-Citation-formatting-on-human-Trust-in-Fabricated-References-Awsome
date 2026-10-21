# AI-generated critical review of the draft (Prompt 16 analogue)

This is the AI assistant reviewing its own draft. It is **not** a peer review and not an independent opinion; treat it as a checklist.

## MAJOR
1. **Construct validity.** Fabrications are rule-generated; conclusions about "fabricated references" are really about the generator. *Remedy:* run the same verifiers on real LLM-generated references checked against a live database.
2. **H1, H1b, H4 are near-tautologies** of the design (format-faithful by construction; a deleted record cannot match). *Remedy:* present them as pipeline sanity checks (the paper does); do not cite as findings.
3. **Corpus mismatch.** Humanities books 1657-2000 without DOIs vs the review's modern journal references with DOIs. *Remedy:* repeat on a DOI-bearing corpus.
4. **Ground truth.** "Real" = in the index; unverified. *Remedy:* spot-check a random sample at source.
5. **Post-hoc explanation** (threshold cliff) rests on 5 seeds. *Remedy:* more seeds and a controlled manipulation of the genuine-noise tail.

## MINOR
6. V1 realised FPR 0.085 vs target 0.05 (calibration). 7. V2 gives partial credit to different venues. 8. No significance tests (by design; n=5).
9. Smoke seed was seen before decision rules were written (disclosed). 10. Defects D1/D2 found after the first run (disclosed; fixed; reported).
11. IEEEtran source not compiled locally. 12. "Pathway B" and "gate" terminology is course-specific.

## Claims checked against evidence
Abstract and results numbers are generated from `results/` by `scripts/make_paper_numbers.py`; related-work numbers are from the verified sources in `research_decisions.md`.
