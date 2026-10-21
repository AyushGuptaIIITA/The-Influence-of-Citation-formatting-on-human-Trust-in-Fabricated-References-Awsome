"""Locate and load the evaluation corpus."""
import subprocess
from typing import Optional, Tuple
import pandas as pd
from .corpus import file_sha256, load_records


def locate_bib(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    out = subprocess.run(["kpsewhich", "-format=bib", "frankenstein.bib"],
                         capture_output=True, text=True).stdout.strip()
    if not out:
        raise FileNotFoundError(
            "frankenstein.bib not found. Install TeX Live 'texlive-latex-extra' or the CTAN "
            "package 'frankenstein', or pass --bib /path/to/frankenstein.bib")
    return out


def load_corpus(explicit: Optional[str] = None) -> Tuple[pd.DataFrame, str, str]:
    path = locate_bib(explicit)
    return load_records(path, "frankenstein.bib"), path, file_sha256(path)
