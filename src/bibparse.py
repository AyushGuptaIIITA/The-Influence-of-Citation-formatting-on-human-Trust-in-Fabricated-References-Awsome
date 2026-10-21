"""Minimal, dependency-free BibTeX parser.

Handles: @string macros, '#' concatenation, {braced} and "quoted" values with
nested braces, @comment/@preamble skipping, and conversion of common LaTeX
accent/escape sequences to plain ASCII for matching.

It is deliberately small. It is NOT a full BibTeX implementation.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

_MONTHS = {m: m for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul",
                           "aug", "sep", "oct", "nov", "dec"]}


def _skip_ws(s: str, i: int) -> int:
    n = len(s)
    while i < n and s[i] in " \t\r\n":
        i += 1
    return i


def _read_braced(s: str, i: int) -> Tuple[str, int]:
    """s[i] == '{'. Return (content without outer braces, index after '}')."""
    depth = 0
    j = i
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\" and j + 1 < n:  # skip escaped char
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces")


def _read_quoted(s: str, i: int) -> Tuple[str, int]:
    """s[i] == '"'. Quotes may contain balanced braces."""
    j = i + 1
    depth = 0
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\" and j + 1 < n:
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == '"' and depth == 0:
            return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unterminated quote")


def _read_value(s: str, i: int, macros: Dict[str, str]) -> Tuple[str, int]:
    parts: List[str] = []
    n = len(s)
    while True:
        i = _skip_ws(s, i)
        if i >= n:
            break
        c = s[i]
        if c == "{":
            v, i = _read_braced(s, i)
            parts.append(v)
        elif c == '"':
            v, i = _read_quoted(s, i)
            parts.append(v)
        else:
            m = re.match(r"[A-Za-z0-9_:\-\.]+", s[i:])
            if not m:
                break
            tok = m.group(0)
            i += len(tok)
            if tok.isdigit():
                parts.append(tok)
            else:
                parts.append(macros.get(tok.lower(), _MONTHS.get(tok.lower(), "")))
        i = _skip_ws(s, i)
        if i < n and s[i] == "#":
            i += 1
            continue
        break
    return "".join(parts), i


def parse_bib(text: str) -> List[dict]:
    """Return a list of dicts: {'type', 'key', 'fields': {name: value}}."""
    macros: Dict[str, str] = {}
    entries: List[dict] = []
    i = 0
    n = len(text)
    while True:
        i = text.find("@", i)
        if i < 0:
            break
        m = re.match(r"@\s*([A-Za-z]+)\s*([{(])", text[i:])
        if not m:
            i += 1
            continue
        etype = m.group(1).lower()
        open_ch = m.group(2)
        close_ch = "}" if open_ch == "{" else ")"
        j = i + m.end()
        if etype in ("comment", "preamble"):
            # skip balanced block
            if open_ch == "{":
                try:
                    _, j = _read_braced(text, j - 1)
                except ValueError:
                    j = i + 1
            i = max(j, i + 1)
            continue
        if etype == "string":
            j = _skip_ws(text, j)
            mm = re.match(r"([A-Za-z0-9_:\-\.]+)\s*=", text[j:])
            if mm:
                name = mm.group(1).lower()
                j += mm.end()
                try:
                    val, j = _read_value(text, j, macros)
                    macros[name] = val
                except ValueError:
                    pass
            i = max(j, i + 1)
            continue
        # regular entry: key, then fields
        j = _skip_ws(text, j)
        mk = re.match(r"([^,\s]+)\s*,", text[j:])
        if not mk:
            i += 1
            continue
        key = mk.group(1)
        j += mk.end()
        fields: Dict[str, str] = {}
        while j < n:
            j = _skip_ws(text, j)
            if j >= n or text[j] == close_ch:
                j += 1
                break
            mf = re.match(r"([A-Za-z0-9_\-:]+)\s*=", text[j:])
            if not mf:
                j += 1
                continue
            fname = mf.group(1).lower()
            j += mf.end()
            try:
                val, j = _read_value(text, j, macros)
            except ValueError:
                break
            fields[fname] = val
            j = _skip_ws(text, j)
            if j < n and text[j] == ",":
                j += 1
        entries.append({"type": etype, "key": key, "fields": fields})
        i = max(j, i + 1)
    return entries


# --------------------------------------------------------------------------
# LaTeX -> plain text
# --------------------------------------------------------------------------
# Symbol accents (\' \` \^ \" \~ \= \.) may be followed directly by a letter. Letter accents
# (\u \v \H \c \k \r \b) are only accents when followed by whitespace or a brace; otherwise
# a command such as \book{..} would be mis-read as the accent \b plus the letter "o" (bug D1).
_ACC_SYM = re.compile(r"""\\['`^"~=.]\s*\{?\\?([A-Za-z])\}?""")
_ACC_LET = re.compile(r"""\\[uvHckrb](?:\s+|\s*\{)\\?([A-Za-z])\}?""")
_SPECIAL = {
    r"\ss": "ss", r"\o": "o", r"\O": "O", r"\aa": "a", r"\AA": "A",
    r"\ae": "ae", r"\AE": "AE", r"\oe": "oe", r"\OE": "OE", r"\l": "l",
    r"\L": "L", r"\i": "i", r"\j": "j",
}


def latex_to_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    s = _ACC_SYM.sub(r"\1", s)
    s = _ACC_LET.sub(r"\1", s)
    s = s.replace("~", " ").replace("--", "-")  # after accents: \~n is an accent, bare ~ is a space
    for k, v in _SPECIAL.items():
        s = re.sub(re.escape(k) + r"(?![A-Za-z])", v, s)
    s = re.sub(r"\\[A-Za-z]+\s*", "", s)  # drop remaining commands, keep args
    s = s.replace("{", "").replace("}", "").replace("\\", "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).strip()
