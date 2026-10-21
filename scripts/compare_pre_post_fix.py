"""Quantify the effect of defects D1/D2: archived first run vs corrected re-run (same seeds, same rules)."""
import numpy as np, pandas as pd
def load(p):
    A = pd.read_csv(p)
    return A.set_index(["verifier","metric","ftype","rho_f","coverage"])["mean"]
old = load("results/archive_v1_pre_fix/summary_by_condition.csv"); new = load("results/summary_by_condition.csv")
rows = []
for v in ["R1_wellformed_rule","V1_format_LR","V3_title_only","V2_full_field"]:
    for m, ft, nm in [("auroc","ALL","AUROC"),("recall","ALL","Recall"),("recall","F3","Recall F3"),("fpr","G","FPR")]:
        k = (v, m, ft, 0.05, 1.0)
        rows.append({"verifier": v, "metric": nm, "pre_fix": old[k], "post_fix": new[k], "delta": new[k]-old[k]})
D = pd.DataFrame(rows); D.to_csv("results/pre_post_fix_comparison.csv", index=False)
print(D.round(3).to_string(index=False)); print("max |delta| over listed metrics:", round(D.delta.abs().max(),3))
