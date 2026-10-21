# Data

**No raw data is committed.** The evaluation corpus is `frankenstein.bib`, a personal bibliography (577 BibTeX entries,
468 usable after filtering) distributed with TeX Live inside the `frankenstein` bundle by Matt Swift
(Debian/Ubuntu package `texlive-latex-extra`; confirmed in the build environment with `dpkg -S`).
The file states no licence of its own, and the bundle's style files carry "Copyright 1995-2001 Matt Swift", so the
file is **not redistributed** here.

Expected SHA-256 of the file used for every reported result:
`64ec9db5903046268e533ab623455a70a58f7ebea14e34350e827e99deba26c1`

How to obtain it:
- TeX Live / Debian / Ubuntu: `sudo apt install texlive-latex-extra`, then `kpsewhich -format=bib frankenstein.bib`.
- Otherwise place the file anywhere and run with `FRANKENSTEIN_BIB=/path/to/frankenstein.bib`.
- If your copy has a different SHA-256, numbers may differ slightly. Re-run `scripts/env_check.py` to see the hash.

What the corpus is (and is not): a single researcher's library, mostly humanities books (1657-2000), no DOIs.
"Real" in this project means "an entry in this file"; entries were **not** independently verified (INFERRED).
