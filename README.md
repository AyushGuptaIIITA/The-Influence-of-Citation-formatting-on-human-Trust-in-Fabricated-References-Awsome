# AITR Lab 02 - Format-only vs title-only vs full-field citation verification (controlled simulation)

**Author:** Ayush Gupta (MSE2026011), IIIT Prayagraj. **Course:** AI Tools for Research (post-mid-sem implementation paper).
**Continues:** the author's review *The Influence of Citation Formatting on Human Trust in Fabricated References*.

## Question
When fabricated references are format-faithful, (RQ1) how well can format-only signals separate them from genuine ones; (RQ2) what do title-only
and full-field database checks each detect and miss per fabrication family; (RQ3) how do they degrade when the reference index is incomplete?
**No novelty is claimed** (HALLMARK and CiteTracer exist). Fabrications are **rule-generated, not LLM output**; nothing is claimed about human trust.

## Headline results (mean over 5 seeds; format-faithful fabricator, complete index; FPR target 5%)
| Verifier | AUROC | FPR | Recall |
|---|---|---|---|
| V0 random | 0.508 | 0.051 | 0.050 |
| R1 well-formed rule | 0.497 | 0.228 | 0.223 |
| V1 format-only LR | 0.504 | 0.085 | 0.089 |
| V3 title-only lookup | 0.693 | 0.038 | 0.406 (0.95 invented, 0.04 chimeric) |
| V2 full-field check | 0.985 | 0.052 | 0.918 (F3 perturbed-real 0.756, range 0.425-0.906 over seeds) |

At 50% index coverage V2's FPR is 0.526 and PPV at 2% assumed prevalence is 0.036. All five frozen decision rules were met, but H1, H1b and H4 are near-consequences of the design (paper Sec. VII).
Two defects (D1 parser, D2 label noise) were found after the first run and fixed; see `docs/hypotheses_and_freeze.md` and `results/archive_v1_pre_fix/`.

## Layout
```
README.md  requirements.txt  research_decisions.md  research_brief_G1.md  baseline_validation.md  ai_assistance_log.md
configs/protocol.yaml        frozen settings (hash in docs/protocol_freeze.txt)
data/README.md               how to obtain the corpus (not redistributed)
src/                         bibparse, corpus, generate, features, verifiers, experiment, data
scripts/                     env_check, validate_baselines, run_experiments, summarize, error_analysis, compare_pre_post_fix, make_figures, make_paper_numbers, reproduce_all.sh
tests/test_pipeline.py       12 unit/regression tests
results/                     results_main.csv, summaries, tables, figures/, logs/, archive_v1_pre_fix/
paper/                       main.tex (IEEEtran), body.tex, preview.tex (stand-in), references.bib, numbers.tex, tab_*.tex, figures/, preview.pdf
docs/                        hypotheses_and_freeze.md, protocol_freeze.txt, self_review_AI.md, DEMO_5min.md, devnotes_raw.txt
```

## Reproduce (Python 3.12.3; one CPU core)
```bash
pip install -r requirements.txt                 # [TESTED with the pinned versions]
sudo apt install texlive-latex-extra            # provides frankenstein.bib; or set FRANKENSTEIN_BIB=/path (see data/README.md)
bash scripts/reproduce_all.sh                   # [TESTED] ~4 min; regenerates all results, figures and paper/preview.pdf
sha256sum results/results_main.csv              # [TESTED] expect e322aeec00da83dac07d72db4b27b249cac72a0f87f005b9f25194b3e48b06e9
python3 -m unittest tests.test_pipeline         # [TESTED] 12 tests
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main   # [TEST REQUIRED] needs IEEEtran (e.g. Overleaf); only preview.tex was compiled here
```
Individual steps: `python3 scripts/run_experiments.py` (~2 min), `python3 scripts/summarize.py`, `python3 scripts/make_figures.py`.

## Minimum reproduction checklist (for a second student)
- [ ] Corpus SHA-256 matches `data/README.md`. - [ ] `env_check.py` prints `ENV OK`. - [ ] 12 tests pass.
- [ ] `results_main.csv` hash matches. - [ ] `results/table_main.csv` matches the table above. - [ ] `paper/preview.pdf` builds.

## Limitations (short)
Simulated fabrications; closed-world index; humanities books 1657-2000 without DOIs; entries assumed real; 5 seeds, no significance tests; V2/V3 are not published tools. Full list: paper Sec. IX.

## Credits, licence, AI disclosure
Corpus: Matt Swift's `frankenstein` bundle (TeX Live). Libraries: NumPy, pandas, SciPy, scikit-learn, Matplotlib, PyYAML.
AI assistance (Claude, Anthropic) was used for planning, code, debugging, analysis and drafting; see `ai_assistance_log.md`.
Code licence: **[STUDENT: choose a licence before publishing]**. No secrets, API keys or restricted data are in this repository.

## Cite
Gupta, A. (2026). *How Far Can a Reference Be Judged by Its Format?* Course paper, IIIT Prayagraj.
