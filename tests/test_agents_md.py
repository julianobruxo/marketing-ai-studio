"""AGENTS.md: arquivo central gerado, em sincronia com agents/ e catalog/ (ADR-20)."""
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_agents  # noqa: E402

CATALOG = json.loads((REPO_ROOT / "catalog/routing.yaml").read_text(encoding="utf-8"))


class AgentsMdTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    def test_is_in_sync(self):
        self.assertEqual(self.text, build_agents.build(), "rode scripts/build_agents.py")

    def test_every_intent_is_listed(self):
        for intent in CATALOG["intents"]:
            self.assertIn(f"`{intent}`", self.text)

    def test_owner_rules_come_in_catalog_order(self):
        positions = [self.text.index(rule["reason"]) for rule in CATALOG["owner_rules"]]
        self.assertEqual(positions, sorted(positions))

    def test_round_limit_matches_catalog(self):
        self.assertEqual(CATALOG["max_rounds"], 3)
        self.assertIn(f"`max_rounds`: {CATALOG['max_rounds']}", self.text)
        self.assertIn("**3 rounds**", self.text)

    def test_all_role_contracts_are_included(self):
        for title in ("Orchestrator", "Strategist", "Writer", "Critic"):
            self.assertIn(f"## {title} — Marketing Content Studio", self.text)

    def test_named_compiled_files_exist(self):
        for rel in set(re.findall(r"compiled/[a-z]+/[a-z-]+\.md", self.text)):
            self.assertTrue((REPO_ROOT / rel).is_file(), rel)
        for rel in set(re.findall(r"`((?:corey|bytedance)/[a-z-]+)`", self.text)):
            self.assertTrue((REPO_ROOT / "compiled" / f"{rel}.md").is_file(), rel)

    def test_host_pointers_lead_to_the_central_file(self):
        self.assertIn("@AGENTS.md", (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("AGENTS.md", (REPO_ROOT / "GEMINI.md").read_text(encoding="utf-8"))

    def test_link_alone_starts_the_studio(self):
        self.assertIn("Welcome to Marketing AI Studio!", self.text)
        self.assertIn("What would you like me to do now?", self.text)
        self.assertIn("only this repository's link", self.text)
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertLess(readme.index("AGENTS.md"), 300, "a instrução ao assistente abre o README")

    def test_operator_clarification_precedes_all_retry_causes(self):
        # A brief blocker cannot be fixed by generating a different draft.
        orchestrator = (REPO_ROOT / "agents/orchestrator.md").read_text(encoding="utf-8")
        self.assertLess(orchestrator.index("| `brief` |"), orchestrator.index("| `approach` |"))
        self.assertIn("even if another gate also reports", orchestrator)
        self.assertIn("Do not send the Writer or Strategist to retry", orchestrator)
        self.assertIn("pause does not count as an additional round", orchestrator)
        self.assertIn("even if another gate also reports", self.text)

    def test_a_critic_failure_restarts_all_configured_roles(self):
        orchestrator = (REPO_ROOT / "agents/orchestrator.md").read_text(encoding="utf-8")
        strategist = (REPO_ROOT / "agents/strategist.md").read_text(encoding="utf-8")
        self.assertIn("restarts **the entire configured workflow**", orchestrator)
        self.assertIn("**Strategist** (every round when the intent uses it)", orchestrator)
        self.assertIn("do not skip the Strategist", orchestrator.lower())
        self.assertIn("every rejected candidate", strategist.lower())
        self.assertIn("new independent sub-agent", orchestrator)
        self.assertIn("the entire configured workflow", self.text)

    def test_critic_must_judge_editorial_attention_not_only_compliance(self):
        contract = (REPO_ROOT / "agents/critic.md").read_text(encoding="utf-8")
        self.assertIn("Editorial publishability is a first-class requirement", contract)
        self.assertIn("Passing the first two does not grant a PASS on the third", contract)
        self.assertIn("public-facing post", contract)
        self.assertIn("A requested checklist can pass", contract)
        self.assertIn("cause: approach", contract)
        self.assertIn("KEEP AS IS", contract)

    def test_synthetic_attention_cases_are_contrasting_and_blindable(self):
        from pathlib import Path
        cases = json.loads((REPO_ROOT / "tests/critic/fixtures/reader-attention-synthetic.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 2)
        self.assertEqual([c["expected"]["verdict"] for c in cases], ["reject", "pass"])
        self.assertNotIn("Anna", json.dumps(cases))
        self.assertNotIn("Zazmic", json.dumps(cases))
        import eval_critic
        import tempfile
        with tempfile.TemporaryDirectory() as path:
            eval_critic.pack(cases, Path(path))
            blind = json.loads((Path(path) / "cases.json").read_text(encoding="utf-8"))
            self.assertEqual(len(blind), 2)
            self.assertTrue(all("expected" not in c and "test" not in c for c in blind))

    def test_demote_ignores_code_fences(self):
        self.assertEqual(build_agents.demote("# a\n```\n# b\n```\n## c"), "## a\n```\n# b\n```\n### c")


if __name__ == "__main__":
    unittest.main()
