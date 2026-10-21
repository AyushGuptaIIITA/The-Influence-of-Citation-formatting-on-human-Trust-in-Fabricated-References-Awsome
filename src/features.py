"""Format-only comparators (a proxy for 'judging a reference by how it looks').

These use ONLY structural properties of the reference string. They never see
the index and never use lexical content of the title, so they cannot memorise
which works exist. That is the point of the comparison.
"""
from __future__ import annotations

import re
from typing import List

import numpy as np
import pandas as pd

ETYPES = ["article", "book", "incollection", "inbook", "inproceedings"]
_PAGES_OK = re.compile(r"^\d+(-\d+)?$|^[ivxlcdm]+(-[ivxlcdm]+)?$", re.I)
FEATURE_NAMES: List[str] = (
    ["n_auth", "frac_with_first", "frac_initials", "any_lower_last", "bare_etal",
     "has_year", "year_valid", "title_ntok", "title_nchar", "title_allcaps",
     "title_ellipsis", "title_upper_start", "has_venue", "venue_len", "venue_allcaps",
     "has_publisher", "has_address", "has_volume", "volume_numeric", "has_number",
     "has_pages", "pages_valid", "pages_span", "n_fields"]
    + [f"etype_{e}" for e in ETYPES]
)


def _row_features(c) -> List[float]:
    au = c["authors"]
    n_auth = len(au)
    with_first = [bool(fi) for fi, _ in au]
    initials = [bool(fi) and re.fullmatch(r"(?:[A-Za-z]\.\s?)+", fi.strip()) is not None for fi, _ in au]
    lower_last = any(la[:1].islower() for _, la in au)
    bare_etal = len(au) == 1 and au[0][1].lower() in ("al", "et al", "et al.")
    year = str(c["year"])
    year_valid = bool(re.fullmatch(r"(1[4-9]\d\d|20[0-2]\d)", year))
    title = c["title"]
    letters = [ch for ch in title if ch.isalpha()]
    allcaps = bool(letters) and all(ch.isupper() for ch in letters) and len(letters) > 3
    venue, pub = c["venue"], c["publisher"]
    pages = c["pages"]
    pages_valid = bool(pages) and bool(_PAGES_OK.match(pages))
    span = 0.0
    if pages_valid and "-" in pages and pages.replace("-", "").isdigit():
        a, b = pages.split("-")[:2]
        span = float(abs(int(b) - int(a)))
    fields = [bool(venue), bool(pub), bool(c["address"]), bool(c["volume"]),
              bool(c["number"]), bool(pages)]
    return [
        n_auth, float(np.mean(with_first)), float(np.mean(initials)), float(lower_last),
        float(bare_etal), float(bool(year)), float(year_valid), len(title.split()),
        len(title), float(allcaps), float(title.endswith("...")), float(title[:1].isupper()),
        float(bool(venue)), len(venue), float(venue.isupper() and len(venue) > 3),
        float(bool(pub)), float(bool(c["address"])), float(bool(c["volume"])),
        float(c["volume"].isdigit()), float(bool(c["number"])), float(bool(pages)),
        float(pages_valid), span, float(sum(fields)),
    ] + [float(c["etype"] == e) for e in ETYPES]


def feature_matrix(df: pd.DataFrame) -> np.ndarray:
    return np.array([_row_features(r) for r in df.to_dict("records")], dtype=float)


def rule_wellformed(df: pd.DataFrame) -> np.ndarray:
    """R1: accept (return True) iff the reference looks well-formed.
    A deliberately naive 'does it look like a proper reference?' check."""
    ok = []
    for c in df.to_dict("records"):
        f = dict(zip(FEATURE_NAMES, _row_features(c)))
        good = (f["year_valid"] == 1 and f["bare_etal"] == 0 and f["any_lower_last"] == 0
                and f["title_allcaps"] == 0 and f["title_ellipsis"] == 0
                and (f["has_venue"] == 1 or f["has_publisher"] == 1)
                and (f["has_pages"] == 0 or f["pages_valid"] == 1)
                and (f["has_volume"] == 0 or f["volume_numeric"] == 1))
        ok.append(good)
    return np.array(ok)
