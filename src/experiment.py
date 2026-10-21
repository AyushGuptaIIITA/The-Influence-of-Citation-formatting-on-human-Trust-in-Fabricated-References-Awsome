"""Experiment engine (frozen protocol lives in configs/protocol.yaml)."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from .features import feature_matrix, rule_wellformed
from .generate import generate_candidates
from .verifiers import Index, title_sim

VERIFIERS = ["V0_random", "R1_wellformed_rule", "V1_format_LR", "V3_title_only", "V2_full_field"]


def make_title_sim_fn(index: Index):
    """Used by the F1 generator to avoid inventing a title that is (nearly)
    identical to an indexed one."""
    def fn(title: str) -> float:
        S = index.sim_matrix([title])[0]
        top = np.argsort(-S)[:3]
        return max(title_sim(title, index.rows[int(j)]["title"]) for j in top)
    return fn


def fold_assignment(groups: np.ndarray, n_splits: int, seed: int) -> np.ndarray:
    """Seeded, group-wise fold ids: every candidate of one group shares a fold."""
    rng = np.random.default_rng(10_000 + seed)
    ug = np.unique(groups)
    perm = rng.permutation(len(ug))
    gfold = {g: int(perm[i] % n_splits) for i, g in enumerate(ug)}
    return np.array([gfold[g] for g in groups])


def _tau_low(train_scores_genuine: np.ndarray, fpr: float) -> float:
    """Flag if score < tau, with tau the fpr-quantile of genuine training scores."""
    return float(np.quantile(train_scores_genuine, fpr))


def _tau_high(train_scores_genuine: np.ndarray, fpr: float) -> float:
    """Flag if score > tau, with tau the (1-fpr)-quantile of genuine training scores."""
    return float(np.quantile(train_scores_genuine, 1.0 - fpr))


def _rows_from_flags(base: dict, df: pd.DataFrame, flags: np.ndarray, verifier: str,
                     extra: Optional[dict] = None, prevalence: float = 0.02) -> List[dict]:
    extra = extra or {}
    rows = []
    y = df["label"].values
    g = df["ftype"].values
    sub = df["subtype"].values
    gen = (y == 0)
    fpr = float(flags[gen].mean()) if gen.any() else np.nan
    rows.append({**base, **extra, "verifier": verifier, "metric": "fpr", "ftype": "G",
                 "value": fpr, "n": int(gen.sum())})
    defect = (y == 1)
    rec_all = float(flags[defect].mean())
    rows.append({**base, **extra, "verifier": verifier, "metric": "recall", "ftype": "ALL",
                 "value": rec_all, "n": int(defect.sum())})
    for ft in ("F1", "F2", "F3"):
        m = (g == ft)
        rows.append({**base, **extra, "verifier": verifier, "metric": "recall", "ftype": ft,
                     "value": float(flags[m].mean()), "n": int(m.sum())})
    for s in sorted(set(sub[g == "F3"])):
        m = (g == "F3") & (sub == s)
        rows.append({**base, **extra, "verifier": verifier, "metric": "recall",
                     "ftype": f"F3:{s}", "value": float(flags[m].mean()), "n": int(m.sum())})
    denom = rec_all * prevalence + fpr * (1 - prevalence)
    rows.append({**base, **extra, "verifier": verifier, "metric": "ppv_at_prevalence",
                 "ftype": "ALL", "value": (rec_all * prevalence / denom) if denom > 0 else np.nan,
                 "n": int(len(df))})
    return rows


def run_condition(rec: pd.DataFrame, index: Index, cfg: dict, seed: int, rho_f: float,
                  coverages: List[float], save_predictions: bool = False):
    """One (seed, rho_f) condition. Returns (rows, predictions_df_or_None)."""
    n_splits = cfg["n_splits"]
    fpr_t = cfg["fpr_target"]
    cands = generate_candidates(rec, seed, rho_f, cfg["rho_g"], make_title_sim_fn(index))
    y = cands["label"].values
    X = feature_matrix(cands)
    wf = rule_wellformed(cands)
    folds = fold_assignment(cands["group"].values, n_splits, seed)
    assert all(set(cands.loc[folds == k, "group"]).isdisjoint(set(cands.loc[folds != k, "group"]))
               for k in range(n_splits)), "group leakage between folds"

    S = index.sim_matrix(list(cands["title"]))
    all_rids = set(int(r) for r in rec["rid"])
    sc_full = index.score(cands, None, S)
    rng = np.random.default_rng(20_000 + seed)
    v0 = rng.random(len(cands))

    flags = {v: np.zeros(len(cands), dtype=bool) for v in VERIFIERS}
    defect_score = {v: np.zeros(len(cands)) for v in VERIFIERS}
    taus = {}
    aucs = {v: [] for v in VERIFIERS}
    for k in range(n_splits):
        tr, te = np.where(folds != k)[0], np.where(folds == k)[0]
        gtr = tr[y[tr] == 0]
        # V0 random
        t0 = _tau_high(v0[gtr], fpr_t)
        flags["V0_random"][te] = v0[te] > t0
        defect_score["V0_random"][te] = v0[te]
        # R1 rule (no tuning)
        flags["R1_wellformed_rule"][te] = ~wf[te]
        defect_score["R1_wellformed_rule"][te] = (~wf[te]).astype(float)
        # V1 logistic regression on format features
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced",
                                                                 max_iter=2000, random_state=seed))
        clf.fit(X[tr], y[tr])
        p_tr, p_te = clf.predict_proba(X[tr])[:, 1], clf.predict_proba(X[te])[:, 1]
        t1 = _tau_high(p_tr[y[tr] == 0], fpr_t)
        flags["V1_format_LR"][te] = p_te > t1
        defect_score["V1_format_LR"][te] = p_te
        # V3 / V2 (similarity scores: low = defective)
        for name, col in (("V3_title_only", "v3_title"), ("V2_full_field", "v2_full")):
            s = sc_full[col].values
            t = _tau_low(s[gtr], fpr_t)
            taus[(name, k)] = t
            flags[name][te] = s[te] < t
            defect_score[name][te] = 1.0 - s[te]
        for v in VERIFIERS:
            if len(set(y[te])) == 2:
                aucs[v].append(roc_auc_score(y[te], defect_score[v][te]))

    rows: List[dict] = []
    base = {"seed": seed, "rho_f": rho_f, "coverage": 1.0}
    for v in VERIFIERS:
        rows += _rows_from_flags(base, cands, flags[v], v, prevalence=cfg["prevalence"])
        rows.append({**base, "verifier": v, "metric": "auroc", "ftype": "ALL",
                     "value": float(np.mean(aucs[v])), "n": int(len(cands))})
        # AUROC per fabrication family (genuine vs that family), pooled out-of-fold
        for ft in ("F1", "F2", "F3"):
            m = (cands["ftype"].values == "G") | (cands["ftype"].values == ft)
            rows.append({**base, "verifier": v, "metric": "auroc", "ftype": ft,
                         "value": float(roc_auc_score(y[m], defect_score[v][m])), "n": int(m.sum())})

    # --- coverage sweep (only V2 / V3 depend on the index); tau fixed from full coverage
    for c in coverages:
        if c >= 1.0:
            continue
        rng_c = np.random.default_rng(30_000 + seed + int(c * 1000))
        keep = set(int(r) for r in rng_c.choice(sorted(all_rids), size=int(round(c * len(all_rids))),
                                                replace=False))
        sc_c = index.score(cands, keep, S)
        for name, col in (("V3_title_only", "v3_title"), ("V2_full_field", "v2_full")):
            fl = np.zeros(len(cands), dtype=bool)
            for k in range(n_splits):
                te = np.where(folds == k)[0]
                fl[te] = sc_c[col].values[te] < taus[(name, k)]
            b2 = {"seed": seed, "rho_f": rho_f, "coverage": c}
            rows += _rows_from_flags(b2, cands, fl, name, prevalence=cfg["prevalence"])
            # diagnostic: share of flagged genuine whose true record was removed
            gen_flag = fl & (y == 0)
            removed = np.array([int(r) not in keep for r in cands["src"].values])
            rows.append({**b2, "verifier": name, "metric": "flagged_genuine_with_removed_record",
                         "ftype": "G", "value": float((gen_flag & removed).sum() / max(1, gen_flag.sum())),
                         "n": int(gen_flag.sum())})

    pred = None
    if save_predictions:
        pred = cands.drop(columns=["authors"]).copy()
        pred["authors"] = [", ".join(f"{fi} {la}".strip() for fi, la in a) for a in cands["authors"]]
        pred["fold"] = folds
        for v in VERIFIERS:
            pred[f"flag_{v}"] = flags[v]
        pred["v3_title"] = sc_full["v3_title"].values
        pred["v2_full"] = sc_full["v2_full"].values
        pred["best_rid"] = sc_full["best_rid"].values
    return rows, pred
