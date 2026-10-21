import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from src.bibparse import parse_bib, latex_to_text
from src.data import load_corpus
from src.generate import generate_candidates, base_from_record
from src.verifiers import Index, title_sim
from src.experiment import fold_assignment, _rows_from_flags, make_title_sim_fn

REC, _, _ = load_corpus(os.environ.get("FRANKENSTEIN_BIB"))
INDEX = Index(REC)


class TestParser(unittest.TestCase):
    def test_macros_concat_braces(self):
        s = '@string{up = "University Press"}\n@book{k1, author = {Smith, John and Ann {van der} Berg}, ' \
            'title = {A {B}ook}, publisher = "Oxford " # up, year = 1999}'
        e = parse_bib(s)[0]
        self.assertEqual(e["fields"]["publisher"], "Oxford University Press")
        self.assertEqual(e["fields"]["year"], "1999")
        self.assertIn("{van der}", e["fields"]["author"])

    def test_latex_accents(self):
        self.assertEqual(latex_to_text(r"Gr{\'e}goire M{\"u}ller \& co"), "Gregoire Muller & co")


class TestRegressionD1D2(unittest.TestCase):
    """Regression tests for defects found AFTER the first frozen run (see docs/hypotheses_and_freeze.md)."""
    def test_D1_book_macro_not_an_accent(self):
        self.assertEqual(latex_to_text(r"the Narrative of \book{Molloy}"), "the Narrative of Molloy")
        self.assertEqual(latex_to_text(r"\v{S}koda \c{C}elik"), "Skoda Celik")
        self.assertEqual(latex_to_text(r"Se\~nor"), "Senor")

    def test_D1_no_artifact_titles_in_corpus(self):
        self.assertEqual(int(REC.title.str.contains(r"ook[A-Z]").sum()), 0)

    def test_D2_every_F3_candidate_is_visibly_defective(self):
        for rho in (0.05, 0.5):
            c = generate_candidates(REC, 999, rho)
            f3 = c[c.ftype == "F3"]
            sc = INDEX.score(f3)
            self.assertEqual(int((sc["v2_full"] >= 0.9999).sum()), 0)


class TestGeneration(unittest.TestCase):
    def test_counts_and_labels(self):
        c = generate_candidates(REC, 999, 0.05)
        self.assertEqual(len(c), 4 * len(REC))
        self.assertEqual(c.groupby("ftype").size().to_dict(), {"F1": len(REC), "F2": len(REC), "F3": len(REC), "G": len(REC)})
        self.assertTrue(((c["ftype"] == "G") == (c["label"] == 0)).all())

    def test_determinism(self):
        a = generate_candidates(REC.head(80), 999, 0.25)
        b = generate_candidates(REC.head(80), 999, 0.25)
        self.assertTrue(a.astype(str).equals(b.astype(str)))

    def test_group_folds_disjoint(self):
        c = generate_candidates(REC, 999, 0.05)
        f = fold_assignment(c["group"].values, 5, 999)
        for k in range(5):
            self.assertTrue(set(c.loc[f == k, "group"]).isdisjoint(set(c.loc[f != k, "group"])))

    def test_invented_titles_not_copies(self):
        fn = make_title_sim_fn(INDEX)
        c = generate_candidates(REC.head(150), 999, 0.05, title_sim_fn=fn)
        t = c[c.ftype == "F1"].head(60)
        sims = [fn(x) for x in t["title"]]
        self.assertGreaterEqual(np.mean(np.array(sims) < 0.9), 0.95)


class TestVerifiers(unittest.TestCase):
    def test_exact_copy_self_match(self):
        sub = REC.sample(80, random_state=0)
        rows = [{**base_from_record(r), "cid": i} for i, (_, r) in enumerate(sub.iterrows())]
        sc = INDEX.score(pd.DataFrame(rows))
        self.assertGreaterEqual(sc["v2_full"].min(), 0.999)
        self.assertGreaterEqual(sc["v3_title"].min(), 0.999)

    def test_title_sim_properties(self):
        self.assertAlmostEqual(title_sim("The Syntax of Violence", "the syntax of violence"), 1.0)
        self.assertLess(title_sim("The Syntax of Violence", "Desert Solitaire"), 0.5)


class TestMetrics(unittest.TestCase):
    def test_rows_known_values(self):
        df = pd.DataFrame({"label": [0, 0, 0, 0, 1, 1, 1, 1],
                           "ftype": ["G"] * 4 + ["F1", "F1", "F2", "F3"],
                           "subtype": [""] * 7 + ["year"]})
        flags = np.array([1, 0, 0, 0, 1, 1, 0, 1], dtype=bool)
        rows = {(r["metric"], r["ftype"]): r["value"] for r in _rows_from_flags({}, df, flags, "x")}
        self.assertAlmostEqual(rows[("fpr", "G")], 0.25)
        self.assertAlmostEqual(rows[("recall", "ALL")], 0.75)
        self.assertAlmostEqual(rows[("recall", "F1")], 1.0)
        self.assertAlmostEqual(rows[("recall", "F2")], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
