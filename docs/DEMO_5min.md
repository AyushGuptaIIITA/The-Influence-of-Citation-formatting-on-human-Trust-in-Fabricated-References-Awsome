# 5-minute demonstration script (practise this; do not read it)

| Time | Show | Say |
|------|------|-----|
| 0:00 | `research_brief_G1.md` | The review claims format can't separate format-faithful fabrications and existence checks can't judge consistency. I turned that into three questions. No novelty claim: HALLMARK/CiteTracer exist. |
| 0:45 | `paper/figures` Fig. 2 pipeline; `src/generate.py` | 468 real records as index; G, F1 invented, F2 chimeric, F3 perturbed; identical benign noise for all classes. |
| 1:45 | `bash scripts/reproduce_all.sh` (start it; or show `results/logs`) | Frozen protocol, 5 seeds, grouped folds, threshold from training folds. SHA-256 of results is reproducible. |
| 2:30 | `results/table_main.csv`, Fig. recall-by-family | Format-only at chance; title-only 0.95 on invented but 0.04 on chimeric; full-field 0.92 recall at 5% FPR. |
| 3:30 | Fig. coverage sweep | FPR follows 1-c; PPV at 2% prevalence falls to 0.04 at half coverage. |
| 4:15 | `docs/hypotheses_and_freeze.md` (D1, D2) | I found two bugs after the first run by reading examples; tests had passed. Re-ran, reported both. |
| 4:45 | Limitations | Simulation, closed world, humanities corpus. |

Be ready for the viva: explain `generate_candidates`, why groups share a fold, how the 5% FPR threshold is chosen, why H4 is nearly tautological, and rerun `python scripts/run_experiments.py`.
