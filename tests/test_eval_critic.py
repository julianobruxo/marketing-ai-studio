"""Pontuação da avaliação do Critic: determinística e sem modelo (ADR-21)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import eval_critic  # noqa: E402

CASES = json.loads((REPO_ROOT / "tests/critic/cases.json").read_text(encoding="utf-8"))
REJECT = {"id": "A", "expected": {"verdict": "reject", "target": "the bad line"}}
PASS = {"id": "B", "expected": {"verdict": "pass", "keep": "the good line"}}


def gate(status, quote=""):
    return {"gate": "quality", "status": status, "evidence": [{"quote": quote}] if quote else []}


class CasesTest(unittest.TestCase):
    def test_ids_are_unique(self):
        ids = [case["id"] for case in CASES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_cases_are_synthetic(self):
        text = json.dumps(CASES, ensure_ascii=False).casefold()
        for private in ("zazmic", "anna", "alina", "haiokha", "yann"):
            self.assertNotIn(private, text)

    def test_every_case_declares_a_verdict_and_every_target_is_in_the_text(self):
        for case in CASES:
            expected = case["expected"]
            self.assertIn(expected["verdict"], ("pass", "reject"))
            for key in ("target", "keep"):
                if expected.get(key):
                    self.assertIn(expected[key], case["candidate"], case["id"])

    def test_pack_is_blind(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_critic.pack(CASES, Path(tmp))
            text = (Path(tmp) / "cases.json").read_text(encoding="utf-8")
            self.assertNotIn('"expected"', text)
            self.assertTrue((Path(tmp) / "contract.md").is_file())


class ScoreTest(unittest.TestCase):
    def test_outcome_accepts_both_verdict_shapes(self):
        self.assertEqual(eval_critic.outcome([gate("FAIL")]), "reject")
        self.assertEqual(eval_critic.outcome({"gates": [gate("PASS"), gate("N/A")]}), "pass")
        self.assertEqual(eval_critic.outcome({"gates": [gate("UNVERIFIED")]}), "reject")

    def test_right_verdict_on_the_wrong_line_does_not_hit_the_target(self):
        row = eval_critic.score_case(REJECT, [gate("FAIL", "another line")])
        self.assertTrue(row["verdict_ok"])
        self.assertFalse(row["target_ok"])

    def test_keep_is_scored(self):
        verdict = {"gates": [gate("PASS")], "keep": ["the good line"]}
        self.assertTrue(eval_critic.score_case(PASS, verdict)["keep_ok"])
        self.assertFalse(eval_critic.score_case(PASS, [gate("PASS")])["keep_ok"])

    def test_summary_counts_false_fails_and_missing_verdicts(self):
        result = eval_critic.score([REJECT, PASS], {"B": [gate("FAIL", "x")]})
        self.assertEqual(result["caught"], {"ok": 0, "total": 1})
        self.assertEqual(result["false_fail"], {"bad": 1, "total": 1})


if __name__ == "__main__":
    unittest.main()
