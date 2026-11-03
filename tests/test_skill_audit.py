"""Skill handoff audit: pre-tool traces cannot prove successful reads or quality."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_skill_use  # noqa: E402


def event(agent_id, role, path, *, job="job-one", decision="allow"):
    return {
        "job": job, "agent_id": agent_id, "agent_type": "studio-" + role,
        "tool": "Read", "target": path, "decision": decision,
    }


class SkillAuditTest(unittest.TestCase):
    def setUp(self):
        self.route = {
            "owner": "studio", "status": "ROUTED", "strategist": True,
            "skill_manifest": {
                "strategist": [{"name": "corey/social", "path": "compiled/corey/social.md"}],
                "writer": [{"name": "corey/social", "path": "compiled/corey/social.md"},
                           {"name": "corey/copywriting", "path": "compiled/corey/copywriting.md"}],
                "critic": [{"name": "corey/social", "path": "compiled/corey/social.md"},
                           {"name": "corey/copy-editing", "path": "compiled/corey/copy-editing.md"}],
            },
        }
        self.agents = {"rounds": [
            {"round": 1, "agents": {"strategist": "s1", "writer": "w1", "critic": "c1"}},
            {"round": 2, "agents": {"strategist": "s2", "writer": "w2", "critic": "c2"}},
        ]}

    def test_all_roles_and_rounds_need_individual_read_requests(self):
        log = []
        for r in self.agents["rounds"]:
            for role, refs in self.route["skill_manifest"].items():
                for ref in refs:
                    log.append(event(r["agents"][role], role, ref["path"]))
        result = audit_skill_use.audit(self.route, self.agents, log, "job-one")
        self.assertEqual((result["checked"], result["missing"]), (10, 0))
        self.assertTrue(all(e["evidence"] == "allowed-read-request" for e in result["entries"]))
        self.assertTrue(all(not e["verified_tool_completion"] and not e["verified_editorial_application"]
                            for e in result["entries"]))

    def test_first_round_read_does_not_cover_fresh_second_round_agent(self):
        log = []
        for role, refs in self.route["skill_manifest"].items():
            for ref in refs:
                log.append(event(self.agents["rounds"][0]["agents"][role], role, ref["path"]))
        result = audit_skill_use.audit(self.route, self.agents, log, "job-one")
        self.assertEqual((result["checked"], result["observed_allowed_requests"], result["missing"]),
                         (10, 5, 5))
        self.assertEqual({e["round"] for e in result["entries"] if e["evidence"] == "not-observed"}, {2})

    def test_wrong_role_denial_and_other_job_cannot_fake_use(self):
        entries = [
            event("c1", "writer", "compiled/corey/social.md"),
            event("c1", "critic", "compiled/corey/social.md", decision="deny"),
            event("c1", "critic", "compiled/corey/social.md", job="other"),
        ]
        result = audit_skill_use.audit(self.route, self.agents, entries, "job-one")
        critic = [x for x in result["entries"] if x["round"] == 1 and x["role"] == "critic"]
        self.assertTrue(all(x["evidence"] == "not-observed" for x in critic))

    def test_bad_agent_maps_are_rejected(self):
        for invalid in [
            {"rounds": []},
            {"rounds": [{"round": 1, "agents": {"writer": "w1"}}]},
            {"rounds": [{"round": 1, "agents": {"strategist": "s1", "writer": "w1", "critic": "c1"}},
                        {"round": 1, "agents": {"strategist": "s2", "writer": "w2", "critic": "c2"}}]},
        ]:
            with self.assertRaises(ValueError):
                audit_skill_use.audit(self.route, invalid, [], "job-one")


if __name__ == "__main__":
    unittest.main()
