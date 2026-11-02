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

    def test_demote_ignores_code_fences(self):
        self.assertEqual(build_agents.demote("# a\n```\n# b\n```\n## c"), "## a\n```\n# b\n```\n### c")


if __name__ == "__main__":
    unittest.main()
