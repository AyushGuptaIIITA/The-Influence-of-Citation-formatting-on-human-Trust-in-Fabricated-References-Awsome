"""Emit paper/numbers.tex (macros) and LaTeX tables from saved result files. No hand-typed results."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
A = pd.read_csv("results/summary_by_condition.csv")
def g(v, m, ft, rho=0.05, cov=1.0):
    r = A[(A.verifier == v) & (A.metric == m) & (A.ftype == ft)
          & np.isclose(A.rho_f, rho) & np.isclose(A.coverage, cov)].iloc[0]
    return float(r["mean"]), float(r["std"])
def f3(x, d=3): return f"{x:.{d}f}"
def pm(v, m, ft, rho=0.05, cov=1.0, d=3):
    mu, sd = g(v, m, ft, rho, cov); return f"{mu:.{d}f}$\\pm${sd:.{d}f}"
M = {}
EA = json.load(open("results/error_analysis.json"))
fp = pd.read_csv("results/false_positive_causes.csv")
M["nFPtotal"] = len(fp)
M["FPetal"] = int(fp.cause.str.contains("authors_bare_et_al").sum())
M["FPtitle"] = int(fp.cause.str.contains("title_altered").sum())
M["FPother"] = int((fp.cause == "other/field_combination").sum())
M["FPyear"] = int(fp.cause.str.contains("year_malformed").sum())
M["FPetalPct"] = round(100 * M["FPetal"] / M["nFPtotal"])
M["FPtitlePct"] = round(100 * M["FPtitle"] / M["nFPtotal"])
M["FPotherPct"] = round(100 * M["FPother"] / M["nFPtotal"])
ps = EA["per_seed"]
taus = [np.mean(d["tau_per_fold"]) for d in ps.values()]
M["tauMin"] = f3(min(taus)); M["tauMax"] = f3(max(taus))
M["degMin"] = f3(100 * min(d["frac_genuine_v2_lt_0.90"] for d in ps.values()), 1)
M["degMax"] = f3(100 * max(d["frac_genuine_v2_lt_0.90"] for d in ps.values()), 1)
M["fthreeMin"] = f3(min(d["recall_F3"] for d in ps.values())); M["fthreeMax"] = f3(max(d["recall_F3"] for d in ps.values()))
for tag, v in [("VtwoR", "V2_full_field"), ("VthreeR", "V3_title_only"), ("VoneR", "V1_format_LR"), ("Rone", "R1_wellformed_rule")]:
    M[tag + "Auroc"] = pm(v, "auroc", "ALL"); M[tag + "Fpr"] = pm(v, "fpr", "G"); M[tag + "Rec"] = pm(v, "recall", "ALL")
M["VtwoPpv"] = f3(g("V2_full_field", "ppv_at_prevalence", "ALL")[0]); M["VthreePpv"] = f3(g("V3_title_only", "ppv_at_prevalence", "ALL")[0])
for c, tag in [(0.5, "Half"), (0.25, "Quarter"), (0.9, "Ninety")]:
    M["VtwoFpr" + tag] = f3(g("V2_full_field", "fpr", "G", 0.05, c)[0]); M["VtwoPpv" + tag] = f3(g("V2_full_field", "ppv_at_prevalence", "ALL", 0.05, c)[0])
    M["VtwoRec" + tag] = f3(g("V2_full_field", "recall", "ALL", 0.05, c)[0])
M["VoneAurocHigh"] = f3(g("V1_format_LR", "auroc", "ALL", 0.50)[0]); M["VoneAurocMid"] = f3(g("V1_format_LR", "auroc", "ALL", 0.25)[0])
M["RoneAurocHigh"] = f3(g("R1_wellformed_rule", "auroc", "ALL", 0.50)[0])
M["VtwoAurocHigh"] = f3(g("V2_full_field", "auroc", "ALL", 0.50)[0])
for ft in ["title", "venue", "locator", "year", "author"]:
    M["VtwoSub" + ft.capitalize()] = f3(g("V2_full_field", "recall", f"F3:{ft}")[0])
    M["VthreeSub" + ft.capitalize()] = f3(g("V3_title_only", "recall", f"F3:{ft}")[0])

from src.bibparse import parse_bib
from src.data import load_corpus
from src.features import FEATURE_NAMES
_rec, _path, _sha = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
_raw = parse_bib(open(_path, encoding="utf-8", errors="replace").read())
M["nRaw"] = len(_raw); M["nKept"] = len(_rec)
M["nBook"] = int((_rec.etype == "book").sum()); M["nArticle"] = int((_rec.etype == "article").sum())
M["nOther"] = int((~_rec.etype.isin(["book", "article"])).sum())
M["yearMin"] = int(_rec.year.min()); M["yearMax"] = int(_rec.year.max()); M["nFeat"] = len(FEATURE_NAMES)

# ---- extra macros: family recalls, validation, F3 score range, pre/post-fix
for tag, v, ft in [("VthreeFone","V3_title_only","F1"),("VthreeFtwo","V3_title_only","F2"),("VtwoFone","V2_full_field","F1"),
                   ("VtwoFtwo","V2_full_field","F2"),("VtwoFthree","V2_full_field","F3")]:
    M[tag] = f3(g(v, "recall", ft)[0], 2) if tag != "VtwoFthree" else f3(g(v, "recall", ft)[0], 3)
M["VtwoFthreeSD"] = f3(g("V2_full_field", "recall", "F3")[1], 3)
BV = json.load(open("results/baseline_validation.json"))
M["valPermMean"] = f3(BV["v1_label_permutation_auroc"]["mean"]); M["valPermMin"] = f3(BV["v1_label_permutation_auroc"]["min"]); M["valPermMax"] = f3(BV["v1_label_permutation_auroc"]["max"])
M["valDropYear"] = f3(BV["single_field_mean_score_drop_V2"]["year"]); M["valDropAuthor"] = f3(BV["single_field_mean_score_drop_V2"]["first_author"]); M["valDropVenue"] = f3(BV["single_field_mean_score_drop_V2"]["venue_or_publisher"])
_p = pd.read_csv("results/predictions_seed0_rho0.05.csv"); _q = _p[(_p.ftype == "F3") & (_p.subtype != "author")].v2_full
M["fThreeLo"] = f3(_q.quantile(0.25), 2); M["fThreeHi"] = f3(_q.quantile(0.75), 2)
_a = _p[(_p.ftype == "F3") & (_p.subtype == "author")].v2_full; M["fThreeAuthMed"] = f3(_a.median(), 2)
_mins = min(ps.items(), key=lambda kv: kv[1]["recall_F3"]); M["degAtMinRecall"] = f3(100 * _mins[1]["frac_genuine_v2_lt_0.90"], 1); M["seedMinRecall"] = _mins[0]
_hi = [d for k, d in ps.items() if k != _mins[0]]; M["degOthersMax"] = f3(100 * max(d["frac_genuine_v2_lt_0.90"] for d in _hi), 1)
M["recOthersMin"] = f3(min(d["recall_F3"] for d in _hi))
PP = pd.read_csv("results/pre_post_fix_comparison.csv")
M["preVtwoFthree"] = f3(PP[(PP.verifier == "V2_full_field") & (PP.metric == "Recall F3")].pre_fix.iloc[0])
M["preVtwoRec"] = f3(PP[(PP.verifier == "V2_full_field") & (PP.metric == "Recall")].pre_fix.iloc[0])
M["maxDeltaFix"] = f3(PP.delta.abs().max())
T = ["\\begin{tabular}{@{}llccc@{}}", "\\toprule", "Verifier & Metric & Pre-fix & Post-fix & $\\Delta$ \\\\", "\\midrule"]
nm2 = {"R1_wellformed_rule": "R1", "V1_format_LR": "V1", "V3_title_only": "V3", "V2_full_field": "V2"}
for _, r in PP[PP.metric.isin(["AUROC", "Recall", "Recall F3"])].iterrows():
    T.append(f"{nm2[r.verifier]} & {r.metric} & {r.pre_fix:.3f} & {r.post_fix:.3f} & {r.delta:+.3f} \\\\")
T += ["\\bottomrule", "\\end{tabular}"]
open("paper/tab_prepost.tex", "w").write("\n".join(T))
with open("paper/numbers.tex", "w") as fh:
    for k, v in M.items():
        fh.write(f"\\newcommand{{\\N{k}}}{{{v}}}\n")
# ---- Table: main comparison
names = {"V0_random": "V0 random", "R1_wellformed_rule": "R1 well-formed rule", "V1_format_LR": "V1 format-only LR",
         "V3_title_only": "V3 title-only lookup", "V2_full_field": "V2 full-field check"}
T = ["\\begin{tabular}{@{}lccccccc@{}}", "\\toprule",
     "Verifier & AUROC & FPR & Recall & R-F1 & R-F2 & R-F3 & PPV@2\\% \\\\", "\\midrule"]
for v, nm in names.items():
    T.append(f"{nm} & {pm(v,'auroc','ALL')} & {pm(v,'fpr','G')} & {pm(v,'recall','ALL')} & {pm(v,'recall','F1',d=2)} & {pm(v,'recall','F2',d=2)} & {pm(v,'recall','F3',d=2)} & {g(v,'ppv_at_prevalence','ALL')[0]:.3f} \\\\")
T += ["\\bottomrule", "\\end{tabular}"]
open("paper/tab_main.tex", "w").write("\n".join(T))
# ---- Table: F3 subtype recall
T = ["\\begin{tabular}{@{}lccccc@{}}", "\\toprule", "Verifier & author & year & title & venue/publ. & vol./pages \\\\", "\\midrule"]
for v in ["V1_format_LR", "V3_title_only", "V2_full_field"]:
    T.append(f"{names[v]} & " + " & ".join(f"{g(v,'recall','F3:'+s)[0]:.3f}" for s in ["author", "year", "title", "venue", "locator"]) + " \\\\")
T += ["\\bottomrule", "\\end{tabular}"]
open("paper/tab_f3.tex", "w").write("\n".join(T))
# ---- Table: hypotheses
H = pd.read_csv("results/hypothesis_outcomes.csv")
rule = {"H1": "V1 AUROC at $\\rho_f{=}0.05$ in [0.45, 0.60]", "H1b": "V1 AUROC rise (0.05$\\to$0.50) $\\geq$ 0.15",
        "H2": "V2 recall $\\geq$ 0.85 (FPR 5\\%, $c{=}1$)", "H3": "V3 recall $\\leq$ 0.20 on F2 and F3 non-title subtypes",
        "H4": "$|$FPR$-[(1{-}c){+}0.05c]|\\leq 0.05$ for all $c$"}
obs = {"H1": f"{g('V1_format_LR','auroc','ALL')[0]:.3f}",
       "H1b": f"{g('V1_format_LR','auroc','ALL',0.5)[0]-g('V1_format_LR','auroc','ALL')[0]:+.3f}",
       "H2": f"{g('V2_full_field','recall','ALL')[0]:.3f}",
       "H3": f"max {max(g('V3_title_only','recall',x)[0] for x in ['F2','F3:year','F3:author','F3:venue','F3:locator']):.3f}",
       "H4": f"max dev {max(abs(g('V2_full_field','fpr','G',0.05,c)[0]-((1-c)+0.05*c)) for c in [0.9,0.75,0.5,0.25]):.3f}"}
T = ["\\begin{tabular}{@{}llcc@{}}", "\\toprule", "ID & Frozen decision rule & Observed & Outcome \\\\", "\\midrule"]
for _, r in H.iterrows():
    T.append(f"{r['id']} & {rule[r['id']]} & {obs[r['id']]} & {'supported' if r['supported'] else 'contradicted'} \\\\")
T += ["\\bottomrule", "\\end{tabular}"]
open("paper/tab_hyp.tex", "w").write("\n".join(T))
print(open("paper/numbers.tex").read()[:1500]); print("tables written")
