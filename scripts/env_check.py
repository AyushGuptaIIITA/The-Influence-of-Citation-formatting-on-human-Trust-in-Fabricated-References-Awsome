"""Environment test (Prompt 08 analogue). Prints actual versions and a tiny end-to-end check."""
import os, platform, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy, pandas, scipy, sklearn, matplotlib, yaml
from src.data import load_corpus
print("python", sys.version.split()[0], "|", platform.platform())
for m in (numpy, pandas, scipy, sklearn, matplotlib, yaml):
    print(f"{m.__name__:12s} {m.__version__}")
print("cpu_count", os.cpu_count())
rec, path, sha = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
print("corpus path:", path); print("sha256:", sha); print("records:", len(rec))
assert len(rec) > 300, "corpus unexpectedly small"
print("ENV OK")
