"""Create all result figures from saved CSVs (no numbers typed by hand)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "font.family": "serif", "pdf.fonttype": 42})
A = pd.read_csv("results/summary_by_condition.csv")
OUT = "results/figures"; os.makedirs(OUT, exist_ok=True)
LAB = {"V0_random": "V0 random", "R1_wellformed_rule": "R1 well-formed rule", "V1_format_LR": "V1 format-only LR",
       "V3_title_only": "V3 title-only lookup", "V2_full_field": "V2 full-field check"}
COL = {"V0_random": "#999999", "R1_wellformed_rule": "#d95f02", "V1_format_LR": "#e6ab02", "V3_title_only": "#1b9e77", "V2_full_field": "#7570b3"}
def g(v, m, ft, rho=0.05, cov=1.0):
    r = A[(A.verifier == v) & (A.metric == m) & (A.ftype == ft) & np.isclose(A.rho_f, rho) & np.isclose(A.coverage, cov)].iloc[0]
    return r["mean"], r["std"]
def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight"); fig.savefig(f"{OUT}/{name}.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# Fig: recall by fabrication family
fig, ax = plt.subplots(figsize=(3.45, 2.5))
fams = ["F1", "F2", "F3"]; names = ["F1 invented", "F2 chimeric", "F3 perturbed"]
vs = ["R1_wellformed_rule", "V1_format_LR", "V3_title_only", "V2_full_field"]
w = 0.2
for i, v in enumerate(vs):
    mu = [g(v, "recall", f)[0] for f in fams]; sd = [g(v, "recall", f)[1] for f in fams]
    ax.bar(np.arange(3) + (i - 1.5) * w, mu, w, yerr=sd, color=COL[v], label=LAB[v], capsize=1.5, error_kw={"lw": .6})
ax.axhline(0.05, color="k", lw=.5, ls=":"); ax.set_xticks(range(3)); ax.set_xticklabels(names)
ax.set_ylabel("Recall of defective refs"); ax.set_ylim(0, 1.38); ax.set_yticks([0,.2,.4,.6,.8,1.0]); ax.legend(loc="upper center", ncol=2, frameon=False, fontsize=6)
save(fig, "fig_recall_by_family")

# Fig: fidelity sweep
fig, ax = plt.subplots(figsize=(3.45, 2.4))
rhos = [0.05, 0.25, 0.5]
for v in ["R1_wellformed_rule", "V1_format_LR", "V3_title_only", "V2_full_field"]:
    mu = [g(v, "auroc", "ALL", r)[0] for r in rhos]; sd = [g(v, "auroc", "ALL", r)[1] for r in rhos]
    ax.errorbar(rhos, mu, yerr=sd, marker="o", ms=3, lw=1, color=COL[v], label=LAB[v], capsize=1.5)
ax.axhline(0.5, color="k", lw=.5, ls=":"); ax.set_xlabel(r"Fabricator malformation rate $\rho_f$ (genuine = 0.05)")
ax.set_ylabel("AUROC (defective vs genuine)"); ax.set_ylim(0.4, 1.02); ax.legend(frameon=False, fontsize=6, loc="lower right")
save(fig, "fig_fidelity_sweep")

# Fig: coverage sweep (FPR and PPV)
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.3))
cov = [1.0, 0.9, 0.75, 0.5, 0.25]
for v in ["V3_title_only", "V2_full_field"]:
    mu = [g(v, "fpr", "G", 0.05, c)[0] for c in cov]; sd = [g(v, "fpr", "G", 0.05, c)[1] for c in cov]
    axs[0].errorbar(cov, mu, yerr=sd, marker="o", ms=3, lw=1, color=COL[v], label=LAB[v], capsize=1.5)
cc = np.linspace(0.25, 1, 50); axs[0].plot(cc, (1 - cc) + 0.05 * cc, "k--", lw=.7, label=r"$(1-c)+0.05c$ (H4 prediction)")
axs[0].set_xlabel("Index coverage $c$"); axs[0].set_ylabel("False-positive rate on genuine refs"); axs[0].invert_xaxis(); axs[0].legend(frameon=False, fontsize=6)
for v in ["V3_title_only", "V2_full_field"]:
    mu = [g(v, "ppv_at_prevalence", "ALL", 0.05, c)[0] for c in cov]
    axs[1].plot(cov, mu, marker="o", ms=3, lw=1, color=COL[v], label=LAB[v])
axs[1].set_xlabel("Index coverage $c$"); axs[1].set_ylabel("PPV at 2% assumed prevalence"); axs[1].invert_xaxis(); axs[1].set_ylim(0, 0.4); axs[1].legend(frameon=False, fontsize=6)
save(fig, "fig_coverage_sweep")

# Fig: V2 score distributions (seed 0)
P = pd.read_csv("results/predictions_seed0_rho0.05.csv")
fig, ax = plt.subplots(figsize=(3.45, 2.5))
bins = np.linspace(0, 1, 41)
for ft, c, lab in [("G", "#444444", "genuine"), ("F3", "#d95f02", "F3 perturbed"), ("F2", "#1b9e77", "F2 chimeric"), ("F1", "#7570b3", "F1 invented")]:
    ax.hist(P[P.ftype == ft].v2_full, bins=bins, histtype="step", lw=1.2, color=c, label=lab, density=False)
ax.set_xlabel("V2 consistency score (seed 0)"); ax.set_ylabel("candidates"); ax.legend(frameon=False, fontsize=6, loc="upper center")
save(fig, "fig_v2_score_distributions")

# Fig: threshold vs F3 recall per seed
E = json.load(open("results/error_analysis.json"))["per_seed"]
fig, ax = plt.subplots(figsize=(3.45, 2.3))
for s, d in E.items():
    ax.scatter([np.mean(d["tau_per_fold"])], [d["recall_F3"]], s=22, color="#7570b3"); ax.annotate(f"seed {s}", (np.mean(d["tau_per_fold"]), d["recall_F3"]), fontsize=6, xytext=(-4, 5 if s != "3" else -9), textcoords="offset points", ha="right" if s in ("2","3") else "left")
ax.set_xlabel(r"mean learned threshold $\tau$ (V2)"); ax.set_ylabel("V2 recall on F3"); ax.margins(x=0.08, y=0.12)
save(fig, "fig_tau_vs_f3")
print("figures:", sorted(os.listdir(OUT)))
