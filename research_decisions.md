# research_decisions.md  - decisions, evidence ledger, next actions

Labels: **VERIFIED** (checked from a source page retrieved in this project, or by executing code) ·
**INFERRED** (plausible, not checked at source) · **UNKNOWN** (not checked).

## 1. Evidence ledger (literature)
| ID | Claim used | Source | Label | How checked |
|----|-----------|--------|-------|-------------|
| L1 | 636 citations in 84 ChatGPT-written reviews; 55% (GPT-3.5) / 18% (GPT-4) entirely fabricated; Sci. Rep. 13:14045 (2023) | Walters & Wilder | VERIFIED | PMC article page (PMC10484980) + DOAJ record |
| L2 | Eight chatbots; 26.5% fully accurate; ~40% flawed or fabricated; arXiv:2505.18059; journal version J. Data Inf. Sci. 11(2):342-354 (2026) | Cabezas-Clavijo & Sidorenko-Bautista | VERIFIED (arXiv abstract); journal pages from a university repository page only -> INFERRED | arXiv abstract page; repository page |
| L3 | 220,564 prompts, 2x2 design, 7 LLMs, 35-77% hallucination (general knowledge), +3 to >22 pp; arXiv:2606.13104; full author names | Khurana, Ramana RN, Kumar | VERIFIED (abstract). Conference status (ICML/NeurIPS 2026 listings seen in search) -> UNKNOWN | arXiv + mirror abstract pages |
| L4 | >1,000 court filings with AI-fabricated citations, growing yearly; arXiv:2606.21155; first author is **Patty** Liu | Liu, Stammbach, Henderson | VERIFIED (abstract) | arXiv + mirror pages |
| L5 | Searching online to check a false article raised belief; Nature 625(7995):548-**556** | Aslett et al. | VERIFIED | PMC10794132 + RePEc. NOTE: the earlier AI-generated T23 `references.bib` said 548-554 = WRONG |
| L6 | HALLMARK: 2,526 BibTeX entries, 14 hallucination types, 3 tiers; FPR decides whether flags are mostly true catches; arXiv:2607.18360 (Reizinger, Brendel) | HALLMARK | VERIFIED | full PDF fetched and read |
| L7 | CiteTracer: 12-code taxonomy, 2,450-citation synthetic benchmark, multi-agent detector; arXiv:2605.08583 (Li, Lin, Ma) | CiteTracer | VERIFIED at abstract level only | search/abstract page |
| L8 | Alkaissi & McFarlane 2023; McCabe & Castel 2008; Michael et al. 2013; Metzger & Flanagin 2013; Eika & Sandnes 2022; Srba et al. 2024 | carried from the review | **UNKNOWN** (not re-verified in this lab; not relied on for any claim in the paper) | - |
| L9 | Enago / Editage / StrongMocha blog pages | carried from the review | UNKNOWN; non-scholarly; not cited in the paper | - |
| L10 | scikit-learn citation (JMLR 12:2825-2830, 2011) | standard reference | INFERRED (metadata from memory) | - |

## 2. Evidence ledger (empirical)
| ID | Claim | Label | Evidence |
|----|-------|-------|----------|
| E1 | Corpus: 577 entries parsed, 468 usable (294 books, 93 articles, 81 other), years 1657-2000, SHA-256 64ec9db5...a26c1 | VERIFIED | `results/logs/env_check.log` |
| E2 | Entries in the corpus are real works | INFERRED | personal library; not independently checked |
| E3 | All reported numbers | VERIFIED | `results/results_main.csv` (sha256 e322aeec...06e9, reproduced bit-for-bit) |
| E4 | Threshold-instability explanation for variable V2 F3 recall | INFERRED | post hoc, 5 seeds |
| E5 | Behaviour on real LLM-generated fabrications | **UNKNOWN** | not tested |
| E6 | Behaviour on DOI-bearing modern corpora / live Crossref | **UNKNOWN** | not tested |
| E7 | Anything about human readers | **UNKNOWN** | not tested |

## 3. Decision log
| # | Decision | Reason | Evidence |
|---|----------|--------|----------|
| D-01 | Stay in the citation-verification area of the review; Pathway B (controlled comparison) | Review §4.1/§5.5/§6.4 name existence-vs-consistency and mitigation limits as open | review text |
| D-02 | Use `frankenstein.bib` as closed-world index | Only real multi-hundred-entry bibliography available offline (no network, no LLM) | filesystem search |
| D-03 | **Make no novelty claim** | HALLMARK and CiteTracer already benchmark citation verifiers | L6, L7 |
| D-04 | Simulate fabrications by rules (G, F1, F2, F3) with identical benign noise for all classes | No LLM access; presentation style must carry no label | `src/generate.py` |
| D-05 | Operating point = 5% FPR threshold from training folds only | Avoid test-set tuning; deployable framing | `src/experiment.py` |
| D-06 | Group folds by source record | Variants of one record must not straddle train/test | `tests` + validation |
| D-07 | V2 weights fixed a priori (0.4/0.3/0.1/0.1/0.1), not tuned | Avoid tuning on results | `configs/protocol.yaml` |
| D-08 | Freeze protocol + hash before reported runs; smoke seed 999 never reported | Pre-specification | `docs/protocol_freeze.txt` |
| D-09 | Disclose that smoke seed was seen before rules were written | Honesty | `docs/hypotheses_and_freeze.md` |
| D-10 | Fix defects D1 (parser) and D2 (F3 label noise), archive first run, re-run, report both | Found by reading examples; tests had passed | `results/archive_v1_pre_fix/` |
| D-11 | Paper in IEEEtran (`main.tex`) with a stand-in `preview.tex` sharing `body.tex` | IEEEtran not installed locally | `paper/` |
| D-12 | Reuse review Fig. 1 and Table 1, correcting the Khurana row's description | Table called a model hallucination rate an "error rate" | paper Table I |
| D-13 | Do not redistribute the corpus file | No licence stated in file | `data/README.md` |