# One-page research brief (gate G1)

| Field | Project information |
|-------|--------------------|
| Review topic and key papers | Citation formatting, fabricated references and trust (student's review). Verified originals: Walters & Wilder 2023 (Sci. Rep. 13:14045); Cabezas-Clavijo & Sidorenko-Bautista (arXiv:2505.18059); Khurana et al. (arXiv:2606.13104); Liu et al. (arXiv:2606.21155); Aslett et al. (Nature 625:548-556); related benchmarks HALLMARK (arXiv:2607.18360) and CiteTracer (arXiv:2605.08583) |
| Research gap | Review claims (i) format inspection cannot discriminate format-faithful fabrications and (ii) existence matching cannot judge consistency (review §2.1, §4.1, §5.5, §6.4). Neither was measured. Source: review text; benchmarks above mix these factors with others. |
| Research question | RQ1: how well do format-only signals separate real from fabricated references when fabrications are format-faithful? RQ2: what do title-only and full-field checks detect/miss per fabrication family? RQ3: how do they degrade with index incompleteness, and what share of flags is correct at realistic prevalence? |
| Study pathway | B: controlled comparative study (no novelty claimed) |
| Dataset or measurement setup | `frankenstein.bib` (TeX Live; 468 usable records, SHA-256 64ec9db5...a26c1; not redistributed). Simulated candidates G/F1/F2/F3; grouped 5-fold CV; seeds 0-4 |
| Baseline/comparators | V0 random; R1 well-formed rule; V1 format-only logistic regression; V3 title-only lookup; V2 full-field consistency (V2/V3 are simple stand-ins, not published tools) |
| Primary metric and control | Out-of-fold recall of defective references at a 5% FPR operating point fixed on training folds; controls: identical benign noise for all classes, rho_f = rho_g null, label-permutation control |
| Computing and risks | 1 CPU core, ~2 min per full run. Risks: simulation != LLM output; closed-world index; humanities corpus; small n of seeds. Fallback: none needed |
| First executable milestone | Done: environment test, corpus parse (468 records), 12 unit tests, validation script, smoke run |
