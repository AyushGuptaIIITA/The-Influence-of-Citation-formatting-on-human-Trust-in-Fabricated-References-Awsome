# Hypotheses, decision rules and protocol freeze

**Honesty note on blindness.** A development smoke run on the *non-reported* seed 999 was inspected
before these decision rules were written (it showed V1 near chance, V2 high, V3 intermediate).
The thresholds below are therefore *informed expectations*, not blind predictions. The reported seeds
0-4 had **not** been run when this file was frozen (see `protocol_freeze.txt` for the hash and time).

Primary metric: out-of-fold **recall of defective references at FPR = 5%** on genuine references.
Secondary: AUROC (mean over folds), per-family recall, PPV at 2% assumed prevalence.
All statements are about *this simulation*, not about LLM-generated citations.

| ID | Hypothesis | Decision rule (mean over seeds 0-4) | Contradicted if |
|----|-----------|--------------------------------------|-----------------|
| H1 | With a format-faithful fabricator (rho_f = rho_g = 0.05), format-only features cannot separate defective from genuine references. | V1 AUROC(ALL) in [0.45, 0.60] | V1 AUROC > 0.60 |
| H1b | Format signal appears only when the fabricator is sloppy. | V1 AUROC(rho_f=0.50) - V1 AUROC(rho_f=0.05) >= 0.15 | difference < 0.15 |
| H2 | Full-field database consistency (V2) detects most defective references when the index is complete. | V2 recall(ALL) >= 0.85 at FPR 5%, coverage 1.0, rho_f = 0.05 | recall < 0.85 |
| H3 | Title-only existence checking (V3) is blind to chimeric titles and non-title perturbations. | V3 recall <= 0.20 on F2 and on each of F3:year, F3:author, F3:venue, F3:locator | any of these > 0.20 |
| H4 | With the full-coverage threshold held fixed, false-positive rate on genuine references rises roughly as (1 - c) + 0.05c as index coverage c falls. | |FPR(V2, c) - [(1-c) + 0.05c]| <= 0.05 for every c in {0.9, 0.75, 0.5, 0.25} | any deviation > 0.05 |
| E1 | (Exploratory, no direction fixed) Which F3 subtypes does V2 miss most? | descriptive | - |

Deeper analyses fixed in advance: (i) per-family and per-F3-subtype recall (error analysis);
(ii) index-coverage sweep (sensitivity); (iii) fabricator format-fidelity sweep (robustness).
Seeds: 0,1,2,3,4. No test-set tuning: the only fitted/tuned quantities (V1 weights, all thresholds)
come from training folds. No significance tests are claimed (5 seeds; report mean +/- SD).

Protocol deviations after freezing must be appended below with date and reason.

## Protocol deviations
(none at time of freezing)

### D1 (after first run) - LaTeX accent regex bug
*Found:* while reading qualitative false-negative examples (post-hoc), titles such as "Narrative of ookMoran" revealed that the
accent regex treated the macro `\book{..}` as accent `\b` + letter `o`. 83 occurrences; 53/468 record titles affected. A second latent
defect in the same function (non-breaking `~` converted before the `\~n` accent) was fixed at the same time.
*Fix:* letter accents (`\u \v \H \c \k \r \b`) now require whitespace or a brace; accents are processed before `~`.
*Why not caught earlier:* all 9 original unit tests passed; none exercised custom macros.

### D2 (after first run) - label noise in F3
*Found:* the same examples showed F3 candidates with V2 score 1.000 - the altered field (e.g. publisher, year) had been erased by
later benign noise/malformation, so ~3.4% of F3 candidates (16/468 at seed 0) were indistinguishable from the genuine record.
*Fix:* F3 perturbations are applied AFTER noise and malformation, only to a field that is still present and well-formed.
*Effect on protocol:* decision rules, seeds, thresholds and all verifiers are unchanged; only the generator (D2) and the corpus text (D1) changed.

**Handling:** first-run results archived in `results/archive_v1_pre_fix/` (not for citation); all five seeds re-run with the fixed code;
the same frozen decision rules were applied to the re-run; regression tests added. The paper reports the re-run and states the pre-fix
numbers in its limitations. Because the defects were found by inspecting results, the re-run is NOT blind to the first-run outcome.
