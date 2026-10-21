"""Baseline validation (gate G2). Uses the non-reported smoke seed and clean (noise-free) probes.
Writes results/baseline_validation.json."""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd, yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.data import load_corpus
from src.features import feature_matrix
from src.generate import base_from_record, generate_candidates
from src.verifiers import Index, WEIGHTS
from src.experiment import fold_assignment, make_title_sim_fn

cfg = yaml.safe_load(open("configs/protocol.yaml"))
SEED = cfg["smoke_seed"]
rec, path, sha = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
idx = Index(rec)
out = {"corpus_sha256": sha, "n_records": int(len(rec)), "seed_used": SEED}

# 1. self-match: an exact copy of every indexed record must score ~1 under V2 and V3
probes = pd.DataFrame([{**base_from_record(r), "cid": i} for i, (_, r) in enumerate(rec.iterrows())])
sc = idx.score(probes)
out["self_match"] = {"v2_min": float(sc.v2_full.min()), "v3_min": float(sc.v3_title.min()),
                     "frac_best_rid_correct": float((sc.best_rid.values == rec.rid.values).mean())}

# 2. single-field perturbation sensitivity on clean probes: score drop must track the weights
rng = np.random.default_rng(SEED)
sub = probes.sample(300, random_state=SEED).reset_index(drop=True)
def drop_for(mod):
    p = sub.copy()
    p = pd.DataFrame([mod(r) for r in p.to_dict("records")])
    p["cid"] = range(len(p))
    s = idx.score(p)
    return float((1.0 - s.v2_full).mean())
def year(r): r = dict(r); r["year"] = str(int(r["year"]) + 3); return r
def auth(r): r = dict(r); r["authors"] = [("X", "Zzyzx")] + list(r["authors"][1:]); return r
def venue(r): r = dict(r); r["venue"] = "Journal of Nothing Particular"; r["publisher"] = "Acme Press" if r["publisher"] else ""; return r
out["single_field_mean_score_drop_V2"] = {"year": drop_for(year), "first_author": drop_for(auth), "venue_or_publisher": drop_for(venue)}
out["weights"] = WEIGHTS

# 3. determinism
a = generate_candidates(rec, SEED, 0.05).astype(str)
b = generate_candidates(rec, SEED, 0.05).astype(str)
out["determinism_hash_equal"] = hashlib.sha256(a.to_csv().encode()).hexdigest() == hashlib.sha256(b.to_csv().encode()).hexdigest()

# 4. label-permutation control for V1 (format classifier): AUROC must be ~0.5
c = generate_candidates(rec, SEED, 0.05, cfg["rho_g"], make_title_sim_fn(idx))
X, y = feature_matrix(c), c.label.values
folds = fold_assignment(c.group.values, cfg["n_splits"], SEED)
def cv_auc(labels):
    s = []
    for k in range(cfg["n_splits"]):
        tr, te = folds != k, folds == k
        m = make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000)).fit(X[tr], labels[tr])
        s.append(roc_auc_score(labels[te], m.predict_proba(X[te])[:, 1]))
    return float(np.mean(s))
perm = [cv_auc(np.random.default_rng(i).permutation(y)) for i in range(5)]
out["v1_label_permutation_auroc"] = {"mean": float(np.mean(perm)), "min": float(np.min(perm)), "max": float(np.max(perm))}

# 5. leakage assertion
out["fold_group_overlap"] = int(sum(len(set(c.group[folds == k]) & set(c.group[folds != k])) for k in range(5)))

# 6. genuine-score distribution (noise + malformation only)
g = c[c.label == 0]
sg = idx.score(g)
out["genuine_v2_quantiles"] = {q: float(sg.v2_full.quantile(q)) for q in (0.01, 0.05, 0.25, 0.5)}
json.dump(out, open("results/baseline_validation.json", "w"), indent=2)
print(json.dumps(out, indent=2))
