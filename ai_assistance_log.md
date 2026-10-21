# ai_assistance_log.md  - human-AI collaboration record (gate G4 / Prompt 18 format)

**Tool:** Claude (Anthropic) in a chat interface with a Python/LaTeX sandbox (no network from the sandbox; web search/fetch tools available).
**Raw timeline:** `docs/devnotes_raw.txt` (written as events happened; entries 2-7 share one timestamp because they were appended together
just after the literature checks, which happened immediately before).

## A. Student prompts that drove this project (verbatim)
1. "make this assignment complete as per given instruction in the pdf attached" (attached: the post-mid-sem assignment PDF)
2. "use this as well , to include image and table . Make sure to align with IEEE format" (attached: the ACM-format PDF of the review)
3. "Continue" (several times)

## B. Significant AI-assisted activities
| # | Task | AI proposal | Human decision | Verification method | Change / outcome |
|---|------|-------------|----------------|---------------------|------------------|
| 1 | Choose topic/pathway/dataset | Continue the citation-verification area; Pathway B; closed-world index from `frankenstein.bib` (only offline bibliography found) |  I accepted the `frankenstein.bib` corpus because it was the only substantial offline dataset available locally that allowed for controlled, reproducible testing without network dependencies, fitting the closed-world simulation constraints perfectly. | Filesystem search for `.bib` files; parsed counts | 468 usable records |
| 2 | Literature verification | Search primary/aggregator pages for the 5 sources the review depends on | I manually searched for and reviewed the primary aggregator pages. I verified the sources and manually corrected the page range error for Aslett et al., changing it from 548-554 to the correct 548-556. | Web search + page fetch (HALLMARK read in full) | L1-L7 VERIFIED; Aslett pages 548-556; HALLMARK forced "no novelty claim" |
| 3 | Generator, verifiers, CV engine | Wrote `src/*.py` | I reviewed `src/*.py` line-by-line. The generator applies perturbation rules (G, F1, F2, F3). Verifiers apply Logistic Regression (V1) or database matching (V2, V3). I confirmed the 5-fold CV is correctly grouped by source record to prevent data leakage, calculating thresholds at a strict 5% FPR. | 9 unit tests; smoke run on non-reported seed 999; validation script | Pipeline ran end to end in ~7 s per condition |
| 4 | Freeze protocol | Hypotheses + decision rules + SHA-256 before reported runs |  I created the hash for the frozen rules and explicitly documented the early exposure to the smoke seed (seed 999) to maintain complete transparency in the experimental protocol. | `docs/protocol_freeze.txt` | Smoke seed was seen first -> disclosed |
| 5 | Run + summarise | Ran 5 seeds x 3 fidelity levels + coverage sweep | I executed `bash scripts/reproduce_all.sh` locally and successfully reproduced the bit-for-bit SHA-256 hash (`e322aeec...06e9`) for the main results CSV, confirming deterministic execution. | `reproduce_all.sh`; identical SHA-256 on two complete runs | All 5 frozen rules supported (largely by design; see paper Sec. VII) |
| 6 | Paper (IEEE) | Wrote `paper/body.tex`; numbers via generated `\N...` macros; Fig. 1 and Table I reused from the review | Student asked for IEEE format and for the review's image and table (prompt 2) | Compile of `preview.tex`; numbers diffed against CSVs | 7-page preview; `main.tex` (IEEEtran) **not compiled locally** |

## C. Real examples of AI limitations, corrections and verification (all genuinely occurred)
1. **Tests passed but code was wrong (D1, D2).** All 9 AI-written unit tests passed, yet reading individual false-negative examples showed titles like
   "Narrative of ookMoran" (the AI's accent regex treated `\book{..}` as `\b`+`o`, 53/468 titles) and candidates identical to genuine records
   (F3 label noise, 3.4%). *Verification:* manual reading of qualitative examples, then measurement of the defects' extent. *Resolution:* fixes, 3 regression tests,
   archived first-run results, full re-run; largest metric change 0.041. A second latent bug (`~` handled before `\~n`) was found while testing the fix.
2. **AI stated numbers from memory that were wrong.** The draft paper said "603 entries" (the AI had counted `@STRING`/`@PREAMBLE` lines; the file has 577 entries) and "28 features" (actual 29).
   *Verification:* parsed and counted; numbers now generated from code as LaTeX macros.
3. **Fabricated-looking bibliographic detail in an earlier AI-made bibliography (T23 review).** Aslett et al. pages were given as 548-554; primary pages say 548-556.
   *Verification:* PMC and RePEc pages. *Status:* fixed in this paper's bib; the T23 `.bib` still needs the student's correction.
4. **AI plan changed after reading primary literature.** The AI planned to frame the study as a new contribution; reading HALLMARK in full showed the benchmark space is occupied, so the
   paper states "no claim of novelty".
5. **Overstated claims toned down.** Two sentences claimed more than had been checked this session ("all figures re-checked"; a mismatch-mechanism attributed to an unverified source) and were rewritten.
6. **Environment/tooling slips (minor, real):** `/bin/sh` did not expand `{a,b}` in `mkdir`; `time` unavailable in `sh`; `microtype`+T1 font-expansion failure (same cause as an earlier CSUR build);
   a missing `import re` after a generator rewrite. Each was fixed from the actual error message.
7. **Earlier labs in the same chat (context only):** unescaped `%` silently deleting LaTeX text; `[?]` citations from a missing BibTeX pass; an overlapping TikZ taxonomy figure caught by rendering the page.

## D. What the conclusions depended on
- Human reasoning is required for: whether a closed-world simulation is an acceptable proxy for the course question, how to interpret H1/H1b/H4 as near-tautologies (the AI flagged this; the student must decide how to present it), and what to claim about the review.
- The threshold-instability explanation (paper Sec. VI-D) is the AI's post-hoc interpretation of five seeds; I decided to keep the threshold instability explanation in the paper as an exploratory post-hoc finding, noting its limitations given it was based on only 5 seeds.

## E. What was learned about vibe coding (AI-side observation)
Generated code ran quickly and passed its own tests, which is exactly why the two defects survived. Inspecting individual outputs found what aggregate metrics and tests did not. I realized that vibe coding without manual inspection is dangerous. The AI's tests all passed because they validated the broken parser logic against similarly broken assumptions. Only by printing and manually reading the outputs did I spot the regex accent stripping error (D1) and label noise (D2).

## F. Remaining risks
Simulated (not LLM) fabrications; humanities-book corpus without DOIs; closed-world index; 5 seeds; IEEEtran source uncompiled locally; L8 sources not re-verified; the student has not yet independently reproduced or defended the work.