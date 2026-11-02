"""Coerência de catalog/routing.yaml, catalog/skills.yaml e da skill de entrada."""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTING = json.loads((REPO_ROOT / "catalog/routing.yaml").read_text(encoding="utf-8"))
SKILLS = json.loads((REPO_ROOT / "catalog/skills.yaml").read_text(encoding="utf-8"))["skills"]
HOST = json.loads((REPO_ROOT / "hosts/claude-code/host.yaml").read_text(encoding="utf-8"))
ROLES = {"strategist", "writer", "critic"}


class CatalogTest(unittest.TestCase):
    def test_intent_skills_exist_loadable_with_role_and_compiled(self):
        for intent, spec in ROUTING["intents"].items():
            if spec.get("status") == "BLOCKED":
                self.assertTrue(spec.get("reason"), intent)
                continue
            uses = [(role, s) for role, names in spec["skills"].items() for s in names]
            if spec.get("research_skill"):
                uses.append(("strategist", spec["research_skill"]))
            for role, name in uses:
                with self.subTest(intent=intent, role=role, skill=name):
                    self.assertIn(role, ROLES)
                    self.assertIn(name, SKILLS)
                    self.assertTrue(SKILLS[name]["loadable"])
                    self.assertIn(role, SKILLS[name]["roles"])
                    self.assertTrue((REPO_ROOT / SKILLS[name]["compiled"]).is_file())

    def test_strategist_flag_matches_skills(self):
        for intent, spec in ROUTING["intents"].items():
            if spec.get("status") == "BLOCKED":
                continue
            self.assertEqual(spec["strategist"], "strategist" in spec["skills"], intent)
            if spec.get("research_skill"):
                self.assertTrue(spec["strategist"], intent)

    def test_unloadable_skills_have_no_compiled(self):
        for name, spec in SKILLS.items():
            if not spec["loadable"]:
                self.assertIsNone(spec["compiled"], name)
                self.assertTrue(spec.get("reason"), name)

    def test_every_compiled_file_is_cataloged(self):
        cataloged = {s["compiled"] for s in SKILLS.values() if s.get("compiled")}
        present = {p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "compiled").rglob("*.md")}
        self.assertEqual(present, cataloged)

    def test_roles_match_host_subagents(self):
        self.assertEqual({n.removeprefix("studio-") for n in HOST["subagents"]}, ROLES)
        for name, spec in SKILLS.items():
            self.assertTrue(set(spec.get("roles", [])) <= ROLES, name)

    def test_owner_rules_end_with_default(self):
        rules = ROUTING["owner_rules"]
        self.assertEqual(rules[-1]["match"], {})
        self.assertEqual(len({r["id"] for r in rules}), len(rules))

    def test_entry_skill_frontmatter(self):
        text = (REPO_ROOT / "skills/marketing-content-studio/SKILL.md").read_text(encoding="utf-8")
        lines = text.split("\n")
        self.assertEqual(lines[0], "---")
        end = lines.index("---", 1)
        fm = dict(line.split(": ", 1) for line in lines[1:end])
        self.assertEqual(fm["name"], "marketing-content-studio")
        self.assertTrue(json.loads(fm["description"]))
        self.assertTrue((REPO_ROOT / "skills/marketing-content-studio/references/compatibility.md").is_file())


if __name__ == "__main__":
    unittest.main()
