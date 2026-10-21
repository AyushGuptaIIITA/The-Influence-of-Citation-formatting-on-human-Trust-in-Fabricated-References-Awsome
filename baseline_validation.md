# baseline_validation.md  (gate G2)

These are **simple heuristic baselines representing mechanisms**, not reproductions of published methods.
V2/V3 are NOT RefChecker, bibtex-updater, HALLMARK's verifiers, or any tool; their code was not available to me and no claim is made about them.

## Checks performed (non-reported smoke seed 999; results in `results/baseline_validation.json`)
| Item | Result | Status |
|------|--------|--------|
| Exact copy of each of 468 records scores 1.0 (V2, V3) and retrieves the right record | min 1.000 / 1.000; 100% correct retrieval | VERIFIED |
| Candidate generation deterministic (same seed -> same hash) | true | VERIFIED |
| Full pipeline reproducible (sha256 of `results_main.csv` identical across two complete runs) | e322aeec...06e9 both times | VERIFIED |
| No train/test group overlap in folds | 0 overlapping groups, asserted at runtime and in tests | VERIFIED |
| V1 learns nothing from shuffled labels | AUROC 0.509 (0.473-0.527, 5 shuffles) | VERIFIED |
| V2 sensitivity: one-field alteration lowers score by about the field's weight | year 0.107 (w 0.10); first author 0.313 (w 0.30); venue/publisher 0.068 (w 0.10) | VERIFIED, venue below weight -> UNCERTAIN (below) |
| Invented titles are not near-copies of indexed ones | >=95% below similarity 0.9 (unit test); generator rejects >=0.9 | VERIFIED |
| Metric direction and per-family recall on a toy example | unit test passes | VERIFIED |

## UNCERTAIN
- **Venue/publisher partial credit:** different venue strings still earn fuzzy credit (0.068 drop vs 0.10 weight), lowering recall on F3:venue. Not corrected; reported as a limitation.
- **V1 calibration:** thresholds set at 5% FPR on training folds give realised test FPR 0.085±0.013. Reported, not corrected.
- **Closed-world matching:** genuine candidates always have an indexed record at full coverage.

## NEEDS CORRECTION -> corrected (deviations after first run)
- **D1** LaTeX accent regex mangled `\book{..}` in 53/468 titles. Fixed; regression tests added.
- **D2** 3.4% of F3 candidates were indistinguishable from the genuine record (label noise). Fixed; regression test added.
- Effect of both fixes: largest change in any listed metric 0.041 (V2 recall on F3 0.796 -> 0.756). See `results/pre_post_fix_comparison.csv`.

## Not done
- No comparison to numbers from any published paper: protocols differ, so no discrepancy analysis is possible.
