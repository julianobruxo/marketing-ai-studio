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
        self.assertIn("do not skip the strategist", orchestrator.lower())
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

    def test_keep_exception_contract_reaches_independent_critic(self):
        orchestrator = (REPO_ROOT / "agents/orchestrator.md").read_text(encoding="utf-8")
        writer = (REPO_ROOT / "agents/writer.md").read_text(encoding="utf-8")
        critic = (REPO_ROOT / "agents/critic.md").read_text(encoding="utf-8")
        for contract in (orchestrator, writer, critic, self.text):
            self.assertIn("keep_exceptions", contract)
        self.assertIn("selected_approach", orchestrator)
        self.assertIn("selected_approach", critic)
        self.assertIn("original_line", writer)
        self.assertIn("original_line", critic)
        self.assertIn("not** automatic permission", orchestrator)
        self.assertIn("Missing, vague or false justification", critic)
        self.assertIn("A valid, necessary exception must not trigger a failure", critic)
        self.assertIn("private reasoning", orchestrator)
        self.assertIn("independently", critic)

    def test_every_role_receives_selected_corey_or_deerflow_knowledge(self):
        orchestrator = (REPO_ROOT / "agents/orchestrator.md").read_text(encoding="utf-8")
        strategist = (REPO_ROOT / "agents/strategist.md").read_text(encoding="utf-8")
        writer = (REPO_ROOT / "agents/writer.md").read_text(encoding="utf-8")
        critic = (REPO_ROOT / "agents/critic.md").read_text(encoding="utf-8")
        self.assertIn("**Skill reading plan (mandatory, role-scoped).**", self.text)
        self.assertIn("skill_manifest", orchestrator)
        self.assertIn("Required skill use", strategist)
        self.assertIn("Required skill use", writer)
        self.assertIn("Required independent skill review", critic)
        self.assertIn("skill_checks", critic)
        self.assertIn("skills assigned to the **Critic**", critic)
        self.assertNotIn("Open a compiled skill only where a row below tells", critic)
        self.assertIn("skill-unavailable", orchestrator)
        self.assertIn("allowed-read-request", orchestrator)
        self.assertIn("PreToolUse", orchestrator)
        self.assertIn("profiles/", orchestrator)
        self.assertIn("the exact deliverable", strategist)
        self.assertIn("promotional caption", critic)
        self.assertIn("cause: writing", critic)
        self.assertIn("Brain without copying it", orchestrator)

    def test_synthetic_deliverable_cases_are_blindable_and_contrasting(self):
        import eval_critic
        import tempfile
        cases = json.loads((REPO_ROOT / "tests/critic/fixtures/deliverable-synthetic.json").read_text(encoding="utf-8"))
        self.assertEqual([x["expected"]["verdict"] for x in cases], ["reject", "pass", "pass"])
        self.assertEqual(cases[0]["expected"]["cause"], "writing")
        with tempfile.TemporaryDirectory() as p:
            eval_critic.pack(cases, Path(p))
            blind = json.loads((Path(p) / "cases.json").read_text(encoding="utf-8"))
            self.assertEqual(len(blind), 3)
            self.assertTrue(all("expected" not in item for item in blind))

    def test_private_profiles_and_goldens_are_gitignored(self):
        ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("profiles/*", ignore)
        self.assertIn("examples/*", ignore)
        self.assertIn("!profiles/README.md", ignore)
        self.assertTrue((REPO_ROOT / "profiles/README.md").is_file())
        self.assertTrue((REPO_ROOT / "examples/README.md").is_file())

    def test_demote_ignores_code_fences(self):
        self.assertEqual(build_agents.demote("# a\n```\n# b\n```\n## c"), "## a\n```\n# b\n```\n### c")


if __name__ == "__main__":
    unittest.main()
