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
            self.assertEqual(len(json.loads((Path(tmp) / "manifest.json").read_text())["contract_sha256"]), 64)

    def test_pack_does_not_expose_human_feedback_or_annotations(self):
        private = [{
            "id": "D01", "intent": "article", "brief": "Independent review",
            "candidate": "Full original document. It has two paragraphs.",
            "source_comment": "This writing is terrible", "reviewer": "PRIVATE PERSON",
            "adjudication": {"diagnosis": "aligned"},
            "expected": {"issues": [{"id": "c1", "source_comment": "Fix this"}]},
            "research_notes": ["A fact from an ordinary source"]
        }]
        with tempfile.TemporaryDirectory() as tmp:
            eval_critic.pack(private, Path(tmp))
            blind = json.loads((Path(tmp) / "cases.json").read_text(encoding="utf-8"))
            self.assertEqual(blind[0]["candidate"], private[0]["candidate"])
            self.assertEqual(blind[0]["research_notes"], private[0]["research_notes"])
            for forbidden in ("source_comment", "reviewer", "adjudication", "expected"):
                self.assertNotIn(forbidden, blind[0])
            packet = (Path(tmp) / "cases.json").read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE PERSON", packet)
            self.assertNotIn("Fix this", packet)

    def test_blind_revision_pack_preserves_only_review_relevant_change_metadata(self):
        old_line = "A concrete example that supported the original angle."
        case = {
            "id": "REV01", "intent": "social-post", "candidate": "Rewritten post.",
            "previous_candidate": old_line, "keep": [old_line],
            "selected_approach": "Explain the audience decision instead of describing examples.",
            "keep_exceptions": [{
                "original_line": old_line, "action": "removed", "reason": "approach",
                "explanation": "The old example is unrelated to the decision now developed."
            }],
            "strategist_private_reasoning": "SHOULD NOT LEAK",
            "writer_process_notes": "SHOULD NOT LEAK",
            "source_comment": "PRIVATE HUMAN FEEDBACK",
            "expected": {"verdict": "pass"}
        }
        with tempfile.TemporaryDirectory() as tmp:
            eval_critic.pack([case], Path(tmp))
            packed = json.loads((Path(tmp) / "cases.json").read_text(encoding="utf-8"))[0]
            self.assertEqual(packed["selected_approach"], case["selected_approach"])
            self.assertEqual(packed["keep_exceptions"], case["keep_exceptions"])
            self.assertEqual(packed["previous_candidate"], old_line)
            self.assertEqual(packed["keep"], [old_line])
            self.assertNotIn("expected", packed)
            self.assertNotIn("source_comment", packed)
            self.assertNotIn("strategist_private_reasoning", packed)
            self.assertNotIn("writer_process_notes", packed)

    def test_keep_exceptions_reject_unprotected_or_unsupported_changes(self):
        old_line = "Good sentence."
        valid = {
            "id": "REV02", "candidate": "Other text.", "keep": [old_line],
            "selected_approach": "Focus on a different audience decision.",
            "keep_exceptions": [{
                "original_line": old_line, "action": "removed",
                "reason": "approach", "explanation": "Conflicts with the new central topic."
            }]
        }
        eval_critic.validate_keep_exceptions(valid)
        invalids = [
            {**valid, "selected_approach": ""},
            {**valid, "keep_exceptions": [{**valid["keep_exceptions"][0], "original_line": "Not protected"}]},
            {**valid, "keep_exceptions": [{**valid["keep_exceptions"][0], "explanation": "  "}]},
            {**valid, "keep_exceptions": [{**valid["keep_exceptions"][0], "reason": "preference"}]},
            {**valid, "keep_exceptions": [{**valid["keep_exceptions"][0], "action": "ignored"}]},
            {**valid, "keep_exceptions": valid["keep_exceptions"] * 2},
        ]
        for index, item in enumerate(invalids):
            with self.subTest(index=index), self.assertRaises(ValueError):
                eval_critic.validate_keep_exceptions(item)

    def test_no_change_does_not_require_approach_summary(self):
        eval_critic.validate_keep_exceptions({
            "id": "REV03", "keep": ["Sentence retained."], "keep_exceptions": []
        })

    def test_blind_pack_includes_exact_role_specific_critic_skills(self):
        import hashlib
        fixture = {
            "id": "COREY-SOCIAL", "intent": "social-post", "brief": "LinkedIn caption",
            "candidate": "An original social post.", "expected": {"verdict": "pass"},
            "source_comment": "PRIVATE REVIEWER FEEDBACK",
        }
        with tempfile.TemporaryDirectory() as tmp:
            eval_critic.pack([fixture], Path(tmp))
            entry = json.loads((Path(tmp) / "cases.json").read_text(encoding="utf-8"))[0]
            self.assertEqual([ref["name"] for ref in entry["skill_manifest"]],
                             ["corey/social", "corey/copy-editing"])
            self.assertEqual(len(entry["skill_context"]), 2)
            self.assertNotIn("source_comment", entry)
            self.assertNotIn("expected", entry)
            for ref, pack in zip(entry["skill_manifest"], entry["skill_context"]):
                source = REPO_ROOT / ref["path"]
                lines = source.read_text(encoding="utf-8").splitlines()
                self.assertEqual(ref["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(pack["sha256"], ref["sha256"])
                for section in pack["sections"]:
                    self.assertEqual(section["excerpt"],
                                     "\n".join(lines[section["start_line"] - 1:section["end_line"]]))
                    self.assertTrue(section["excerpt"].startswith(section["heading"]))

    def test_deerflow_is_included_in_newsletter_critic_blind_pack(self):
        refs, text = eval_critic.critic_skills_for_case({"id": "B", "intent": "newsletter"})
        self.assertEqual([x["name"] for x in refs],
                         ["bytedance/newsletter-generation", "corey/copy-editing"])
        self.assertIn("## Newsletter Workflow", text[0]["sections"][1]["excerpt"])
        self.assertFalse(any(x["name"] == "bytedance/deep-research" for x in refs))

    def test_explicit_blind_skill_context_must_match_hash_and_path(self):
        item = {"id": "X", "intent": "social-post", "candidate": "Some copy",
                "skill_manifest": [{"path": "compiled/corey/social.md", "sha256": "correct"}],
                "skill_context": [{"path": "compiled/corey/social.md", "sha256": "wrong"}]}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                eval_critic.pack([item], Path(tmp))

    def test_pack_rejects_duplicate_case_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                eval_critic.pack([{"id": "D"}, {"id": "D"}], Path(tmp))


class ScoreTest(unittest.TestCase):
    def test_outcome_accepts_both_verdict_shapes(self):
        self.assertEqual(eval_critic.outcome([gate("FAIL")]), "reject")
        self.assertEqual(eval_critic.outcome({"gates": [gate("PASS"), gate("N/A")]}), "pass")
        self.assertEqual(eval_critic.outcome({"gates": [gate("UNVERIFIED")]}), "reject")

    def test_right_verdict_on_the_wrong_line_does_not_hit_the_target(self):
        row = eval_critic.score_case(REJECT, [gate("FAIL", "another line")])
        self.assertTrue(row["verdict_ok"])
        self.assertFalse(row["target_ok"])

    def test_a_tiny_quote_gets_no_credit_for_the_target(self):
        self.assertFalse(eval_critic.overlaps("the whole bad sentence here", "bad"))
        self.assertTrue(eval_critic.overlaps("the whole bad sentence", "the whole bad"))
        self.assertTrue(eval_critic.overlaps("bad", "a very bad line"))

    def test_target_equal_to_the_whole_candidate_is_not_scored(self):
        case = {"id": "A", "candidate": "all of it", "expected": {"verdict": "reject", "target": "all of it"}}
        self.assertNotIn("target_ok", eval_critic.score_case(case, [gate("FAIL", "all")]))

    def test_keep_is_scored(self):
        verdict = {"gates": [gate("PASS")], "keep": ["the good line"]}
        self.assertTrue(eval_critic.score_case(PASS, verdict)["keep_ok"])
        self.assertFalse(eval_critic.score_case(PASS, [gate("PASS")])["keep_ok"])

    def test_material_finding_is_flagged_but_is_not_a_reject(self):
        verdict = {"decision": "IMPROVE", "gates": [gate("PASS")]}
        self.assertEqual(eval_critic.outcome(verdict), "pass")
        self.assertTrue(eval_critic.flagged(verdict))
        self.assertFalse(eval_critic.flagged({"decision": "KEEP AS IS", "gates": [gate("PASS")]}))

    def test_diagnosis_comes_from_the_label_not_from_any_finding(self):
        case = {"id": "A", "expected": {"verdict": "reject", "severity": "blocking"}}
        verdict = {"gates": [{"gate": "voice", "status": "PASS",
                              "evidence": [{"quote": "x", "severity": "material"}]}]}
        wrong = eval_critic.score_case(case, verdict, {"match": None, "category": False, "diagnosis": "different"})
        self.assertFalse(wrong["category_ok"])
        self.assertEqual(wrong["diagnosis"], "none")
        right = eval_critic.score_case(case, verdict, {"match": 0, "category": True, "diagnosis": "aligned"})
        self.assertTrue(right["category_ok"])
        self.assertFalse(right["severity_ok"])

    def test_fact_objection_to_approved_text_is_not_a_false_fail(self):
        facts = {"gates": [{"gate": "facts", "status": "FAIL", "evidence": []}]}
        result = eval_critic.score([PASS], {"B": facts})
        self.assertEqual(result["false_fail"]["bad"], 0)
        self.assertEqual(result["fact_dissent"]["bad"], 1)

    def test_summary_counts_false_fails_and_missing_verdicts(self):
        result = eval_critic.score([REJECT, PASS], {"B": [gate("FAIL", "x")]})
        self.assertEqual(result["caught"], {"ok": 0, "total": 1})
        self.assertEqual(result["false_fail"], {"bad": 1, "total": 1})

    def test_cases_that_need_context_are_reported_apart(self):
        case = {"id": "C", "expected": {"verdict": "reject", "needs_context": True}}
        result = eval_critic.score([REJECT, case], {})
        self.assertEqual(result["without_context_cases"]["caught"]["total"], 1)



class DocumentScoreTest(unittest.TestCase):
    def setUp(self):
        self.case = {
            "id": "D01", "candidate": "A complete synthetic editorial article.",
            "expected": {"issues": [
                {"id": "p1", "kind": "problem", "source_comment": "No causal connection"},
                {"id": "p2", "kind": "problem", "source_comment": "Heading not answered"},
                {"id": "ok", "kind": "praise", "source_comment": "Keep the strong CTA"},
            ]}
        }
        self.verdict = {
            "decision": "REVISE", "gates": [
                {"gate": "editorial", "status": "FAIL", "evidence": [
                    {"quote": "First line", "severity": "blocking", "issue": "Missing argument"},
                    {"quote": "Second line", "severity": "material", "issue": "Unclear wording"},
                    {"quote": "Third line", "severity": "material", "issue": "Other observation"}
                ]}
            ]
        }
        self.adjudication = {"matches": [
            {"issue_id": "p1", "finding_index": 0, "diagnosis": "aligned",
             "category_ok": True, "severity_ok": True},
            {"issue_id": "p2", "finding_index": None, "diagnosis": "missed"},
        ]}

    def test_each_human_issue_is_scored_separately(self):
        row = eval_critic.score_document_case(self.case, self.verdict, self.adjudication)
        self.assertEqual(row["expected_issues"], 2)
        self.assertEqual(row["aligned"], 1)
        self.assertEqual(row["missed"], 1)
        self.assertEqual(row["unmatched_findings"], 2)
        self.assertTrue(row["document_rejected"])

    def test_aggregates_without_claiming_unmatched_findings_are_false_positives(self):
        result = eval_critic.score_documents([self.case], {"D01": self.verdict},
                                               {"D01": self.adjudication})
        self.assertEqual(result["totals"]["aligned"], 1)
        self.assertEqual(result["totals"]["unmatched_findings"], 2)
        self.assertEqual(result["totals"]["documents"], 1)

    def test_explicit_human_judgment_is_required(self):
        with self.assertRaises(ValueError):
            eval_critic.score_documents([self.case], {"D01": self.verdict}, {})
        with self.assertRaises(ValueError):
            eval_critic.score_document_case(self.case, self.verdict, {"matches": []})

    def test_rejects_mapping_two_issues_to_one_finding(self):
        bad = {"matches": [
            {"issue_id": "p1", "finding_index": 0, "diagnosis": "aligned",
             "category_ok": True, "severity_ok": True},
            {"issue_id": "p2", "finding_index": 0, "diagnosis": "partial",
             "category_ok": False, "severity_ok": False},
        ]}
        with self.assertRaises(ValueError):
            eval_critic.score_document_case(self.case, self.verdict, bad)

    def test_bad_judgment_cannot_receive_credit(self):
        bad = {"matches": [
            {"issue_id": "p1", "finding_index": 0, "diagnosis": "different",
             "category_ok": False, "severity_ok": False},
            {"issue_id": "p2", "finding_index": None, "diagnosis": "missed"}
        ]}
        row = eval_critic.score_document_case(self.case, self.verdict, bad)
        self.assertEqual(row["aligned"], 0)
        self.assertEqual(row["category_ok"], 0)

    def test_missing_model_verdict_counts_as_missed(self):
        result = eval_critic.score_document_case(self.case, None, {
            "matches": [{"issue_id": "p1", "finding_index": None, "diagnosis": "missed"},
                        {"issue_id": "p2", "finding_index": None, "diagnosis": "missed"}]})
        self.assertEqual(result["missed"], 2)
        self.assertFalse(result["document_rejected"])

    def test_synthetic_whole_document_fixture(self):
        root = REPO_ROOT / "tests/critic/fixtures"
        cases = json.loads((root / "doc-cases-synthetic.json").read_text(encoding="utf-8"))
        verdicts = json.loads((root / "doc-verdicts-synthetic.json").read_text(encoding="utf-8"))
        labels = json.loads((root / "doc-adjudications-synthetic.json").read_text(encoding="utf-8"))
        result = eval_critic.score_documents(cases, verdicts, labels)["totals"]
        self.assertEqual(result["documents"], 2)
        self.assertEqual(result["expected_issues"], 3)
        self.assertEqual(result["aligned"], 3)
        self.assertEqual(result["missed"], 0)
        self.assertEqual(result["document_approved"], 1)
        self.assertEqual(result["rejected_approved_document"], 0)
        self.assertEqual(result["unmatched_findings"], 0)

    def test_non_boolean_adjudication_is_rejected(self):
        bad = {"matches": [
            {"issue_id": "p1", "finding_index": 0, "diagnosis": "aligned",
             "category_ok": "yes", "severity_ok": True},
            {"issue_id": "p2", "finding_index": None, "diagnosis": "missed"}
        ]}
        with self.assertRaises(ValueError):
            eval_critic.score_document_case(self.case, self.verdict, bad)


if __name__ == "__main__":
    unittest.main()
