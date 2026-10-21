"""Turn a BibTeX file into a clean table of citable records.

A record is kept only if it has >=1 author, a title and a 4-digit year, so a
verifier has something to verify. Duplicate (title, first-author) pairs are
dropped so that "which indexed record does this match?" is unambiguous.
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Tuple

import pandas as pd

from .bibparse import latex_to_text, parse_bib

KEEP_TYPES = {"article", "book", "incollection", "inbook", "inproceedings"}
_PARTICLES = {"von", "van", "de", "der", "den", "du", "da", "di", "la", "le",
              "del", "della", "dos", "das", "ten", "ter", "al", "bin", "ibn"}


def split_authors(raw: str) -> List[str]:
    """Split a BibTeX author field on top-level ' and '."""
    out, depth, cur = [], 0, []
    toks = re.split(r"(\s+and\s+)", raw)
    buf = ""
    for t in toks:
        if re.fullmatch(r"\s+and\s+", t) and buf.count("{") == buf.count("}"):
            out.append(buf)
            buf = ""
        else:
            buf += t
    if buf.strip():
        out.append(buf)
    return [a.strip() for a in out if a.strip()]


def parse_name(raw: str) -> Tuple[str, str]:
    """Return (first, last) in plain ASCII."""
    raw = raw.strip()
    if "," in raw and not raw.startswith("{"):
        last, _, first = raw.partition(",")
        return latex_to_text(first.strip()), latex_to_text(last.strip())
    plain = latex_to_text(raw)
    toks = plain.split()
    if len(toks) <= 1:
        return "", plain
    i = len(toks) - 1
    while i > 1 and toks[i - 1].lower() in _PARTICLES:
        i -= 1
    return " ".join(toks[:i]), " ".join(toks[i:])


def _clean_pages(p: str) -> str:
    p = latex_to_text(p)
    return p.replace(" ", "")


def load_records(bib_path: str, source_tag: str) -> pd.DataFrame:
    with open(bib_path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    entries = parse_bib(text)
    by_key = {e["key"]: e for e in entries}
    rows = []
    for e in entries:
        f = dict(e["fields"])
        if e["type"] not in KEEP_TYPES:
            continue
        # resolve crossref: child inherits missing fields from parent
        cr = f.get("crossref")
        if cr and cr in by_key:
            parent = by_key[cr]["fields"]
            for k, v in parent.items():
                if k == "title":
                    f.setdefault("booktitle", v)
                else:
                    f.setdefault(k, v)
        raw_auth = f.get("author", "")
        if not raw_auth:
            continue
        title = latex_to_text(f.get("title", ""))
        ym = re.search(r"\b(1[4-9]\d\d|20[0-2]\d)\b", f.get("year", ""))
        if not title or not ym:
            continue
        authors = [parse_name(a) for a in split_authors(raw_auth)]
        authors = [(fi, la) for fi, la in authors if la]
        if not authors:
            continue
        et = e["type"]
        venue = ""
        if et == "article":
            venue = latex_to_text(f.get("journal", ""))
        elif et in ("incollection", "inbook", "inproceedings"):
            venue = latex_to_text(f.get("booktitle", ""))
        publisher = latex_to_text(f.get("publisher", ""))
        if et == "article" and not venue:
            continue  # an article with no journal is not verifiable
        rows.append({
            "key": e["key"], "etype": et,
            "authors": authors, "title": title, "year": int(ym.group(1)),
            "venue": venue, "publisher": publisher,
            "address": latex_to_text(f.get("address", "")),
            "volume": latex_to_text(f.get("volume", "")),
            "number": latex_to_text(f.get("number", "")),
            "pages": _clean_pages(f.get("pages", "")),
            "source": source_tag,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # drop duplicates by (normalised title, first-author last name)
    df["_t"] = df["title"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    df["_a"] = df["authors"].apply(lambda a: a[0][1].lower())
    df = df.drop_duplicates(subset=["_t", "_a"]).drop(columns=["_t", "_a"])
    # also drop records whose normalised title is identical (ambiguous matching)
    df["_t"] = df["title"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
    df = df.drop_duplicates(subset=["_t"], keep="first").drop(columns=["_t"])
    df = df[df["title"].str.len() >= 8].reset_index(drop=True)
    df.insert(0, "rid", range(len(df)))
    return df


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()
