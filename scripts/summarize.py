"""Aggregate results over seeds and evaluate the frozen decision rules (docs/hypotheses_and_freeze.md)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd

df = pd.read_csv("results/results_main.csv")
def agg(d):
    g = d.groupby(["verifier", "metric", "ftype", "rho_f", "coverage"])["value"].agg(["mean", "std", "count"]).reset_index()
    g["std"] = g["std"].fillna(0.0)
    return g
A = agg(df); A.to_csv("results/summary_by_condition.csv", index=False)
def get(v, m, ft, rho=0.05, cov=1.0):
    r = A[(A.verifier == v) & (A.metric == m) & (A.ftype == ft) & np.isclose(A.rho_f, rho) & np.isclose(A.coverage, cov)]
    return float(r["mean"].iloc[0]), float(r["std"].iloc[0])

out = []
v1_05 = get("V1_format_LR", "auroc", "ALL", 0.05)[0]; v1_50 = get("V1_format_LR", "auroc", "ALL", 0.50)[0]
out.append(("H1", f"V1 AUROC at rho_f=0.05 = {v1_05:.3f} (rule: in [0.45,0.60])", 0.45 <= v1_05 <= 0.60))
out.append(("H1b", f"V1 AUROC rho_f 0.50 - 0.05 = {v1_50 - v1_05:+.3f} (rule: >=0.15)", (v1_50 - v1_05) >= 0.15))
v2r = get("V2_full_field", "recall", "ALL")[0]
out.append(("H2", f"V2 recall(ALL) at FPR5% = {v2r:.3f} (rule: >=0.85)", v2r >= 0.85))
h3 = {ft: get("V3_title_only", "recall", ft)[0] for ft in ["F2", "F3:year", "F3:author", "F3:venue", "F3:locator"]}
out.append(("H3", "V3 recall " + ", ".join(f"{k}={v:.3f}" for k, v in h3.items()) + " (rule: all <=0.20)", all(v <= 0.20 for v in h3.values())))
dev = {}
for c in [0.9, 0.75, 0.5, 0.25]:
    f = get("V2_full_field", "fpr", "G", 0.05, c)[0]
    dev[c] = (f, (1 - c) + 0.05 * c)
out.append(("H4", "V2 FPR(obs vs pred) " + ", ".join(f"c={c}: {o:.3f} vs {p:.3f}" for c, (o, p) in dev.items()) + " (rule: |diff|<=0.05)",
            all(abs(o - p) <= 0.05 for o, p in dev.values())))
res = pd.DataFrame(out, columns=["id", "observation", "supported"])
res.to_csv("results/hypothesis_outcomes.csv", index=False)
print(res.to_string(index=False))

pd.set_option("display.width", 220)
print("\n=== MAIN TABLE (rho_f=0.05, coverage=1.0): mean +/- sd over 5 seeds ===")
rows = []
for v in ["V0_random", "R1_wellformed_rule", "V1_format_LR", "V3_title_only", "V2_full_field"]:
    r = {"verifier": v}
    for m, ft, name in [("auroc", "ALL", "AUROC"), ("fpr", "G", "FPR"), ("recall", "ALL", "Recall"),
                        ("recall", "F1", "F1"), ("recall", "F2", "F2"), ("recall", "F3", "F3"), ("ppv_at_prevalence", "ALL", "PPV@2%")]:
        mu, sd = get(v, m, ft); r[name] = f"{mu:.3f}±{sd:.3f}"
    rows.append(r)
T = pd.DataFrame(rows); T.to_csv("results/table_main.csv", index=False); print(T.to_string(index=False))

print("\n=== F3 SUBTYPE RECALL (rho_f=0.05) ===")
sub = sorted({x for x in A.ftype.unique() if x.startswith("F3:")})
S = pd.DataFrame([{"verifier": v, **{s.split(':')[1]: f"{get(v,'recall',s)[0]:.3f}" for s in sub}} for v in ["V1_format_LR", "V3_title_only", "V2_full_field"]])
S.to_csv("results/table_f3_subtypes.csv", index=False); print(S.to_string(index=False))

print("\n=== FIDELITY SWEEP: AUROC(ALL) by rho_f ===")
F = pd.DataFrame([{"verifier": v, **{f"rho_f={r}": f"{get(v,'auroc','ALL',r)[0]:.3f}±{get(v,'auroc','ALL',r)[1]:.3f}" for r in [0.05, 0.25, 0.5]}} for v in ["R1_wellformed_rule", "V1_format_LR", "V3_title_only", "V2_full_field"]])
F.to_csv("results/table_fidelity.csv", index=False); print(F.to_string(index=False))

print("\n=== COVERAGE SWEEP (rho_f=0.05) ===")
C = []
for v in ["V3_title_only", "V2_full_field"]:
    for c in [1.0, 0.9, 0.75, 0.5, 0.25]:
        C.append({"verifier": v, "coverage": c, "FPR": f"{get(v,'fpr','G',0.05,c)[0]:.3f}±{get(v,'fpr','G',0.05,c)[1]:.3f}",
                  "Recall": f"{get(v,'recall','ALL',0.05,c)[0]:.3f}±{get(v,'recall','ALL',0.05,c)[1]:.3f}",
                  "PPV@2%": f"{get(v,'ppv_at_prevalence','ALL',0.05,c)[0]:.3f}"})
C = pd.DataFrame(C); C.to_csv("results/table_coverage.csv", index=False); print(C.to_string(index=False))
