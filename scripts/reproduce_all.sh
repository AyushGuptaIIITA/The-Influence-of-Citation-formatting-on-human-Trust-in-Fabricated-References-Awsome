#!/usr/bin/env bash
# Regenerates every reported number, table and figure, then the preview PDF. ~3 minutes on one CPU core.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/env_check.py | tee results/logs/env_check.log
python3 -m unittest tests.test_pipeline 2>&1 | tee results/logs/unit_tests.log
python3 scripts/validate_baselines.py > results/logs/baseline_validation.log
python3 scripts/run_experiments.py   > results/logs/run_experiments.log
python3 scripts/summarize.py         > results/logs/summarize.log
python3 scripts/error_analysis.py    > results/logs/error_analysis.log
python3 scripts/compare_pre_post_fix.py > results/logs/compare_pre_post_fix.log
python3 scripts/make_figures.py      > results/logs/make_figures.log
python3 scripts/make_paper_numbers.py > results/logs/make_paper_numbers.log
cp results/figures/*.pdf paper/figures/
( cd paper && pdflatex -interaction=nonstopmode preview.tex >/dev/null && bibtex preview >/dev/null && \
  pdflatex -interaction=nonstopmode preview.tex >/dev/null && pdflatex -interaction=nonstopmode preview.tex >/dev/null )
sha256sum results/results_main.csv | tee results/logs/results_main.sha256
echo "DONE"
