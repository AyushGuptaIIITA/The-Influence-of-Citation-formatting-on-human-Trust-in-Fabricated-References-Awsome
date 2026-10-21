"""Database-grounded verifiers over a closed-world index of records.

V3  title-only existence : best title similarity among retrieved index records.
V2  full-field check     : best weighted multi-field consistency among the same
                           retrieved records (title, authors, year, venue/publisher,
                           volume/pages).

Both return a score in [0, 1]; HIGH = looks genuine. A reference is flagged as
defective when its score falls BELOW a threshold chosen on training folds.

This is a simplified stand-in for "cross-check against a bibliographic
database". It is NOT a reproduction of RefChecker, bibtex-updater, or any
published tool, and makes no claim about their performance.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .bibparse import latex_to_text

WEIGHTS = {"title": 0.40, "authors": 0.30, "year": 0.10, "venue_pub": 0.10, "locator": 0.10}
TOPK = 5


def norm(s: str) -> str:
    s = latex_to_text(s).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_sim(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b, autojunk=False).ratio()
    ta, tb = set(a.split()), set(b.split())
    dice = 2 * len(ta & tb) / (len(ta) + len(tb)) if (ta or tb) else 0.0
    m = min(len(ta), len(tb))
    contain = len(ta & tb) / m if m >= 2 else 0.0
    return max(ratio, dice, 0.95 * contain)


def _last_names(authors: List[Tuple[str, str]]) -> List[str]:
    return [norm(la) for _, la in authors if norm(la)]


def author_sim(ca: List[Tuple[str, str]], ra: List[Tuple[str, str]]) -> float:
    cl, rl = _last_names(ca), _last_names(ra)
    if not cl or not rl:
        return 0.0
    used = set()
    matched = 0
    for c in cl:
        for k, r in enumerate(rl):
            if k in used:
                continue
            if c == r or SequenceMatcher(None, c, r).ratio() >= 0.85:
                used.add(k)
                matched += 1
                break
    return matched / (len(cl) + len(rl) - matched)


def _str_sim(c: str, r: str) -> Optional[float]:
    c, r = norm(c), norm(r)
    if not c or not r:
        return None
    if c in r or r in c:
        return 0.95 if c != r else 1.0
    return SequenceMatcher(None, c, r).ratio()


def field_components(c: dict, r: dict) -> Dict[str, Optional[float]]:
    comp: Dict[str, Optional[float]] = {}
    comp["title"] = title_sim(c["title"], r["title"])
    comp["authors"] = author_sim(c["authors"], r["authors"])
    y = str(c["year"])
    comp["year"] = (1.0 if y == str(r["year"]) else 0.0) if re.fullmatch(r"\d{4}", y) else None
    vp = [s for s in (_str_sim(c["venue"], r["venue"]), _str_sim(c["publisher"], r["publisher"]))
          if s is not None]
    comp["venue_pub"] = float(np.mean(vp)) if vp else None
    loc = []
    if c["volume"] and r["volume"]:
        loc.append(1.0 if norm(c["volume"]) == norm(r["volume"]) else 0.0)
    if c["pages"] and r["pages"]:
        loc.append(1.0 if c["pages"].replace(" ", "") == r["pages"].replace(" ", "") else 0.0)
    comp["locator"] = float(np.mean(loc)) if loc else None
    return comp


def combined(comp: Dict[str, Optional[float]]) -> float:
    num = den = 0.0
    for k, w in WEIGHTS.items():
        if comp.get(k) is not None:
            num += w * comp[k]
            den += w
    return num / den if den else 0.0


class Index:
    """Closed-world reference index with title-TF-IDF retrieval."""

    def __init__(self, rec: pd.DataFrame):
        self.rec = rec.reset_index(drop=True)
        self.rows = self.rec.to_dict("records")
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), lowercase=True,
                                   sublinear_tf=True)
        self.M = self.vec.fit_transform([norm(t) for t in self.rec["title"]])
        self.rid_to_pos = {int(r): i for i, r in enumerate(self.rec["rid"])}

    def sim_matrix(self, cand_titles: List[str]) -> np.ndarray:
        X = self.vec.transform([norm(t) for t in cand_titles])
        return (X @ self.M.T).toarray()

    def score(self, cands: pd.DataFrame, keep_rids: Optional[set] = None,
              S: Optional[np.ndarray] = None) -> pd.DataFrame:
        """Return DataFrame(cid, v3_title, v2_full, best_rid) for every candidate.

        keep_rids restricts the index (simulating an incomplete database).
        """
        if S is None:
            S = self.sim_matrix(list(cands["title"]))
        mask = np.ones(len(self.rows), dtype=bool)
        if keep_rids is not None:
            mask = np.array([int(r["rid"]) in keep_rids for r in self.rows])
        S = np.where(mask[None, :], S, -1.0)
        out = []
        for i, c in enumerate(cands.to_dict("records")):
            if not mask.any():
                out.append((c["cid"], 0.0, 0.0, -1))
                continue
            k = min(TOPK, int(mask.sum()))
            top = np.argpartition(-S[i], k - 1)[:k]
            best_t, best_f, best_rid = 0.0, 0.0, -1
            for j in top:
                r = self.rows[int(j)]
                comp = field_components(c, r)
                t = comp["title"]
                f = combined(comp)
                if t > best_t:
                    best_t = t
                if f > best_f:
                    best_f, best_rid = f, int(r["rid"])
            out.append((c["cid"], best_t, best_f, best_rid))
        return pd.DataFrame(out, columns=["cid", "v3_title", "v2_full", "best_rid"])
