"""Run the frozen protocol. Usage: python scripts/run_experiments.py"""
import os, sys, time, json, yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from src.data import load_corpus
from src.verifiers import Index
from src.experiment import run_condition
from src.generate import render_reference

cfg = yaml.safe_load(open("configs/protocol.yaml"))
rec, path, sha = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
idx = Index(rec)
rows, t0 = [], time.time()
for seed in cfg["seeds"]:
    for rho_f in cfg["rho_f_levels"]:
        cov = cfg["coverage_levels"] if rho_f == cfg["rho_g"] else [1.0]
        save = (seed == cfg["seeds"][0] and rho_f == cfg["rho_g"])
        r, pred = run_condition(rec, idx, cfg, seed, rho_f, cov, save_predictions=save)
        rows += r
        if pred is not None:
            pred.to_csv("results/predictions_seed0_rho0.05.csv", index=False)
        print(f"seed={seed} rho_f={rho_f} done  t={time.time()-t0:.0f}s", flush=True)
df = pd.DataFrame(rows)
df.to_csv("results/results_main.csv", index=False)
json.dump({"corpus_sha256": sha, "n_records": int(len(rec)), "seeds": cfg["seeds"],
           "elapsed_s": round(time.time() - t0, 1), "rows": int(len(df))},
          open("results/run_manifest.json", "w"), indent=2)
print("wrote results/results_main.csv", len(df), "rows")
