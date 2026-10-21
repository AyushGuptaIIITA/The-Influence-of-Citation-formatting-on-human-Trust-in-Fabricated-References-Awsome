"""Generate citation candidates for the verification experiment.

Label 0 (genuine)   G  : an indexed record shown with benign presentation noise.
Label 1 (defective) F1 : invented reference (no indexed record behind it).
                    F2 : chimeric - metadata of record A, title of record B.
                    F3 : perturbed real - one (visible) field of an indexed record altered.

SIMULATION CAVEAT (stated again in the paper): these fabrications are produced
by explicit rules, NOT by a language model. They encode mechanisms reported in
the literature (invented works, mismatched fields, wrong years/volumes/pages)
but are not claimed to match the output distribution of any LLM.

Fairness rule: the *same* presentation-noise process is applied to every
candidate type, so presentation style carries no label information. Format
malformation is applied separately at rate rho_g (genuine) and rho_f
(defective); rho_f == rho_g is the "format-faithful fabricator" null condition.
"""
from __future__ import annotations

import re
import string
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

OPTIONAL_DROP = {"address": 0.30, "number": 0.30, "publisher": 0.10,
                 "volume": 0.10, "pages": 0.10}
NOISE = {"initials": 0.50, "subtitle_drop": 0.20, "typo": 0.25, "sentence_case": 0.20}
BASE_MALFORMATION_GENUINE = 0.05


# --------------------------------------------------------------------------
# Pools learned from the corpus (used only to make fabrications plausible)
# --------------------------------------------------------------------------
class Pools:
    def __init__(self, rec: pd.DataFrame):
        self.firsts: List[str] = []
        self.lasts: List[str] = []
        n_auth = []
        for authors in rec["authors"]:
            n_auth.append(len(authors))
            for fi, la in authors:
                if fi:
                    self.firsts.append(fi)
                self.lasts.append(la)
        self.n_auth = np.array(n_auth)
        self.title_tokens: List[List[str]] = [t.split() for t in rec["title"]]
        self.len_title = np.array([len(t) for t in self.title_tokens])
        self.bigram: Dict[str, List[str]] = defaultdict(list)
        self.first_tok: List[str] = []
        for toks in self.title_tokens:
            if not toks:
                continue
            self.first_tok.append(toks[0])
            prev = "<s>"
            for t in toks:
                self.bigram[prev].append(t)
                prev = t
            self.bigram[prev].append("</s>")
        self.vocab = sorted({t for toks in self.title_tokens for t in toks if len(t) >= 4})
        self.venues = {et: sorted(set(g["venue"]) - {""}) for et, g in rec.groupby("etype")}
        self.publishers = sorted(set(rec["publisher"]) - {""})


# --------------------------------------------------------------------------
# Candidate dict helpers
# --------------------------------------------------------------------------
def base_from_record(r: pd.Series) -> dict:
    return {
        "etype": r["etype"], "authors": [tuple(a) for a in r["authors"]],
        "title": r["title"], "year": str(int(r["year"])), "venue": r["venue"],
        "publisher": r["publisher"], "address": r["address"],
        "volume": r["volume"], "number": r["number"], "pages": r["pages"],
    }


def _initials(first: str) -> str:
    parts = [p for p in first.replace(".", " ").split() if p]
    return " ".join(p[0].upper() + "." for p in parts)


def _typo(word: str, rng: np.random.Generator) -> str:
    if len(word) < 5:
        return word
    i = int(rng.integers(1, len(word) - 1))
    k = int(rng.integers(0, 3))
    if k == 0:
        return word[:i] + word[i + 1] + word[i] + word[i + 2:] if i + 1 < len(word) else word
    if k == 1:
        return word[:i] + word[i + 1:]
    return word[:i] + word[i] + word[i:]


def presentation_noise(c: dict, rng: np.random.Generator) -> dict:
    """Benign, label-independent variation in how a reference is typed."""
    c = dict(c)
    if rng.random() < NOISE["initials"]:
        c["authors"] = [(_initials(fi) if fi else "", la) for fi, la in c["authors"]]
    for f, p in OPTIONAL_DROP.items():
        if c.get(f) and rng.random() < p:
            c[f] = ""
    t = c["title"]
    if ":" in t and rng.random() < NOISE["subtitle_drop"]:
        t = t.split(":")[0].strip()
    if rng.random() < NOISE["typo"]:
        words = t.split()
        idx = [i for i, w in enumerate(words) if len(w) >= 5]
        if idx:
            j = int(rng.choice(idx))
            words[j] = _typo(words[j], rng)
            t = " ".join(words)
    if rng.random() < NOISE["sentence_case"] and len(t) > 1:
        t = t[0] + t[1:].lower()
    c["title"] = t
    return c


def malform(c: dict, rng: np.random.Generator, rho: float) -> dict:
    """Format malformation: each field independently with probability rho."""
    c = dict(c)
    if rho <= 0:
        return c
    if rng.random() < rho:
        k = int(rng.integers(0, 3))
        if k == 0:
            c["authors"] = [(fi.lower(), la.lower()) for fi, la in c["authors"]]
        elif k == 1:
            c["authors"] = [("", "al")]  # a bare "et al."
        else:
            c["authors"] = [("", la) for fi, la in c["authors"]]
    if rng.random() < rho:
        c["year"] = ["19??", "n.d.", c["year"][-2:], c["year"] + "a"][int(rng.integers(0, 4))]
    for f in ("venue", "publisher"):
        if c.get(f) and rng.random() < rho:
            k = int(rng.integers(0, 3))
            c[f] = "" if k == 0 else (c[f][:12] if k == 1 else c[f].upper())
    if c.get("pages") and rng.random() < rho:
        c["pages"] = ["pp", "12-", "n.p.", ""][int(rng.integers(0, 4))]
    if c.get("volume") and rng.random() < rho:
        c["volume"] = ["vol.?", ""][int(rng.integers(0, 2))]
    if rng.random() < rho:
        c["title"] = c["title"].upper() if rng.random() < 0.5 else c["title"] + "..."
    return c


# --------------------------------------------------------------------------
# Fabrication families
# --------------------------------------------------------------------------
def _gen_title(pools: Pools, rng: np.random.Generator) -> str:
    L = int(rng.choice(pools.len_title))
    L = max(L, 3)
    toks: List[str] = []
    prev = "<s>"
    for _ in range(L + 6):
        nxt_pool = pools.bigram.get(prev) or pools.first_tok
        nxt = str(rng.choice(nxt_pool))
        if nxt == "</s>":
            if len(toks) >= max(2, L - 2):
                break
            nxt = str(rng.choice(pools.first_tok))
        toks.append(nxt)
        prev = nxt
        if len(toks) >= L:
            break
    return " ".join(toks)


def fabricate_F1(rec: pd.DataFrame, pools: Pools, rng: np.random.Generator,
                 title_sim_fn=None, max_sim: float = 0.9) -> Tuple[dict, int]:
    """Invented reference. Structure (type, venue, publisher, ...) is borrowed
    from a random donor record so the result is format-faithful by design."""
    d = rec.iloc[int(rng.integers(0, len(rec)))]
    na = int(rng.choice(pools.n_auth))
    authors = [(str(rng.choice(pools.firsts)), str(rng.choice(pools.lasts))) for _ in range(na)]
    title = ""
    for _ in range(25):
        title = _gen_title(pools, rng)
        if title_sim_fn is None or title_sim_fn(title) < max_sim:
            break
    year = int(d["year"]) + int(rng.integers(-3, 4))
    c = base_from_record(d)
    c.update({"authors": authors, "title": title, "year": str(year)})
    if d["etype"] == "article":
        vol = d["volume"]
        if vol.isdigit():
            c["volume"] = str(max(1, int(vol) + int(rng.integers(-2, 3))))
        if d["pages"]:
            start = int(rng.integers(1, 400))
            try:
                a, b = d["pages"].split("-")[:2]
                span = max(1, abs(int(b) - int(a)))
            except Exception:
                span = int(rng.integers(5, 40))
            c["pages"] = f"{start}-{start + span}"
    elif d["pages"]:
        start = int(rng.integers(1, 300))
        c["pages"] = f"{start}-{start + int(rng.integers(5, 40))}"
    return c, int(d["rid"])


def fabricate_F2(rec: pd.DataFrame, rng: np.random.Generator, a: pd.Series) -> Tuple[dict, int]:
    """Chimeric: everything from record A except the title, taken from B."""
    pool = rec[rec["rid"] != a["rid"]]
    b = pool.iloc[int(rng.integers(0, len(pool)))]
    c = base_from_record(a)
    c["title"] = b["title"]
    return c, int(b["rid"])


def fabricate_F3(c: dict, a: pd.Series, pools: Pools, rng: np.random.Generator) -> Tuple[dict, str]:
    """Perturbed real: alter exactly ONE field of an (already noised) candidate.

    Fix D2: the perturbation is applied AFTER presentation noise and malformation, and only to a
    field that is still present and well-formed, so the defect is always visible in the candidate.
    (Previously ~3.4% of F3 candidates had the altered field erased by later noise and were
    indistinguishable from the genuine record.)
    """
    c = dict(c)
    opts = []
    if re.fullmatch(r"\d{4}", str(c["year"])):
        opts.append("year")
    if any(la and la.lower() != "al" for _, la in c["authors"]):
        opts.append("author")
    if any(len(w) >= 4 for w in c["title"].split()):
        opts.append("title")
    if (c["venue"] if a["etype"] == "article" else c["publisher"]):
        opts.append("venue")
    if re.fullmatch(r"\d+-\d+", c["pages"] or "") or (c["volume"] or "").isdigit():
        opts.append("locator")
    sub = str(rng.choice(opts)) if opts else "title"
    if sub == "year":
        d = int(rng.integers(1, 6)) * int(rng.choice([-1, 1]))
        c["year"] = str(int(c["year"]) + d)
    elif sub == "author":
        idx = [i for i, (_, la) in enumerate(c["authors"]) if la and la.lower() != "al"]
        i = int(rng.choice(idx))
        fi, la = c["authors"][i]
        new = str(rng.choice(pools.lasts))
        while new.lower() == la.lower():
            new = str(rng.choice(pools.lasts))
        c["authors"][i] = (fi, new)
    elif sub == "title":
        words = c["title"].split()
        idx = [i for i, w in enumerate(words) if len(w) >= 4]
        j = int(rng.choice(idx)) if idx else 0
        new = str(rng.choice(pools.vocab))
        while new.lower() == words[j].lower():
            new = str(rng.choice(pools.vocab))
        words[j] = new
        c["title"] = " ".join(words)
    elif sub == "venue":
        if a["etype"] == "article":
            cand = [v for v in pools.venues.get("article", []) if v != a["venue"] and v != c["venue"]]
            c["venue"] = str(rng.choice(cand))
        else:
            cand = [p_ for p_ in pools.publishers if p_ != a["publisher"] and p_ != c["publisher"]]
            c["publisher"] = str(rng.choice(cand))
    elif sub == "locator":
        if re.fullmatch(r"\d+-\d+", c["pages"] or ""):
            x, y = c["pages"].split("-")
            sh = int(rng.integers(1, 31))
            c["pages"] = f"{int(x) + sh}-{int(y) + sh}"
        if (c["volume"] or "").isdigit() and (a["etype"] == "article" or not re.fullmatch(r"\d+-\d+", c["pages"] or "")):
            c["volume"] = str(int(c["volume"]) + 1)
    return c, sub


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def generate_candidates(rec: pd.DataFrame, seed: int, rho_f: float,
                        rho_g: float = BASE_MALFORMATION_GENUINE,
                        title_sim_fn=None) -> pd.DataFrame:
    """One G, F1, F2 and F3 candidate per indexed record (deterministic)."""
    rng = np.random.default_rng(seed)
    pools = Pools(rec)
    rows = []
    for _, a in rec.iterrows():
        rid = int(a["rid"])
        # --- genuine
        g = malform(presentation_noise(base_from_record(a), rng), rng, rho_g)
        rows.append({**g, "label": 0, "ftype": "G", "subtype": "", "group": rid, "src": rid})
        # --- F1 invented (group = donor so structure-sharing candidates stay together)
        f1, donor = fabricate_F1(rec, pools, rng, title_sim_fn)
        f1 = malform(presentation_noise(f1, rng), rng, rho_f)
        rows.append({**f1, "label": 1, "ftype": "F1", "subtype": "", "group": rid, "src": donor})
        # --- F2 chimeric
        f2, b = fabricate_F2(rec, rng, a)
        f2 = malform(presentation_noise(f2, rng), rng, rho_f)
        rows.append({**f2, "label": 1, "ftype": "F2", "subtype": "", "group": rid, "src": rid})
        # --- F3 perturbed real (D2 fix: perturb AFTER noise + malformation so the defect is visible)
        f3_base = malform(presentation_noise(base_from_record(a), rng), rng, rho_f)
        f3, sub = fabricate_F3(f3_base, a, pools, rng)
        rows.append({**f3, "label": 1, "ftype": "F3", "subtype": sub, "group": rid, "src": rid})
    df = pd.DataFrame(rows)
    df.insert(0, "cid", range(len(df)))
    df["seed"] = seed
    df["rho_f"] = rho_f
    return df


def render_reference(c: dict) -> str:
    """Human-readable APA-like string, for qualitative examples only."""
    au = ", ".join((f"{la}, {fi}".strip(", ") if fi else la) for fi, la in c["authors"])
    parts = [f"{au} ({c['year']}). {c['title']}."]
    if c.get("venue"):
        v = c["venue"]
        loc = ""
        if c.get("volume"):
            loc += f", {c['volume']}"
            if c.get("number"):
                loc += f"({c['number']})"
        if c.get("pages"):
            loc += f", {c['pages']}"
        parts.append(f"{v}{loc}.")
    elif c.get("publisher"):
        parts.append(f"{c.get('address') + ': ' if c.get('address') else ''}{c['publisher']}.")
    return " ".join(parts)
