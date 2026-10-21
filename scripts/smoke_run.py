"""Development smoke run on the NON-REPORTED seed. Output is never used in the paper."""
import os, sys, time, yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from src.data import load_corpus
from src.verifiers import Index
from src.experiment import run_condition
cfg = yaml.safe_load(open("configs/protocol.yaml"))
rec, _, _ = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
idx = Index(rec)
t = time.time()
rows, _ = run_condition(rec, idx, cfg, cfg["smoke_seed"], 0.05, [1.0, 0.5])
print(f"elapsed {time.time()-t:.1f}s, rows {len(rows)}")
df = pd.DataFrame(rows)
piv = df[(df.coverage == 1.0) & df.metric.isin(["auroc", "fpr", "recall"]) & df.ftype.isin(["ALL", "G"])]
print(piv.pivot_table(index="verifier", columns=["metric", "ftype"], values="value").round(3).to_string())
