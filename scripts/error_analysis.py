"""EXPLORATORY (post-hoc, not pre-registered) error analysis of V2 at rho_f=0.05, coverage 1.0.
Regenerates the frozen-protocol candidates deterministically for seeds 0-4."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd, yaml
from src.data import load_corpus
from src.verifiers import Index, title_sim
from src.generate import generate_candidates, render_reference, base_from_record
from src.experiment import fold_assignment, make_title_sim_fn

cfg = yaml.safe_load(open("configs/protocol.yaml"))
rec, _, _ = load_corpus(os.environ.get("FRANKENSTEIN_BIB")); idx = Index(rec)
out = {"per_seed": {}}
fp_rows, fn_rows = [], []
for seed in cfg["seeds"]:
    c = generate_candidates(rec, seed, 0.05, cfg["rho_g"], make_title_sim_fn(idx))
    sc = idx.score(c); c["v2"] = sc.v2_full.values; c["best_rid"] = sc.best_rid.values
    folds = fold_assignment(c.group.values, cfg["n_splits"], seed)
    taus, flag = [], np.zeros(len(c), bool)
    for k in range(cfg["n_splits"]):
        tr, te = folds != k, folds == k
        tau = np.quantile(c.v2[tr & (c.label == 0)], cfg["fpr_target"]); taus.append(float(tau))
        flag[te] = c.v2.values[te] < tau
    c["flag"] = flag
    g = c[c.label == 0]
    out["per_seed"][seed] = {"tau_per_fold": [round(t, 3) for t in taus],
                             "frac_genuine_v2_lt_0.80": round(float((g.v2 < 0.80).mean()), 4),
                             "frac_genuine_v2_lt_0.90": round(float((g.v2 < 0.90).mean()), 4),
                             "recall_F3": round(float(c[(c.ftype == "F3")].flag.mean()), 3)}
    # classify genuine false positives by apparent cause
    for _, r in c[(c.label == 0) & c.flag].iterrows():
        true = rec.loc[rec.rid == r.src].iloc[0]
        au = r.authors
        cause = []
        if len(au) == 1 and au[0][1].lower() == "al": cause.append("authors_bare_et_al")
        elif any(la[:1].islower() for _, la in au): cause.append("authors_lowercased")
        if not (str(r.year).isdigit() and len(str(r.year)) == 4): cause.append("year_malformed")
        if title_sim(r.title, true["title"]) < 0.8: cause.append("title_altered")
        fp_rows.append({"seed": seed, "cause": "+".join(cause) or "other/field_combination"})
    # false negatives for V2 within F3
    for _, r in c[(c.ftype == "F3") & (~c.flag)].iterrows():
        true = rec.loc[rec.rid == r.src].iloc[0]
        fn_rows.append({"seed": seed, "subtype": r.subtype, "v2_score": round(float(r.v2), 3),
                        "candidate": render_reference(r.to_dict()),
                        "true_record": render_reference(base_from_record(true))})
FP = pd.DataFrame(fp_rows); FN = pd.DataFrame(fn_rows)
out["fp_cause_counts"] = FP.cause.value_counts().to_dict()
out["fn_by_subtype"] = FN.subtype.value_counts().to_dict()
FP.to_csv("results/false_positive_causes.csv", index=False)
FN[FN.seed == 0].sample(12, random_state=0).sort_values("subtype").to_csv("results/examples_false_negatives_seed0.csv", index=False)
json.dump(out, open("results/error_analysis.json", "w"), indent=2)
print(json.dumps(out, indent=1))
