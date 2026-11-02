"""T01: roteamento determinístico (scripts/route.py) contra catalog/routing.yaml."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "route.py"


def route(persona="-", brand="-", channel="-", intent="-"):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--persona", persona, "--brand", brand,
                           "--channel", channel, "--intent", intent],
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise AssertionError(f"exit {proc.returncode}: {proc.stderr}")
    return json.loads(proc.stdout)


class RouteTest(unittest.TestCase):
    def test_yann_on_x_goes_to_brain(self):
        for persona, channel in (("yann", "x"), ("Yann", "twitter"), ("  YANN KRONBERG ", "X.com"),
                                 ("yann-kronberg", "tweet")):
            r = route(persona=persona, channel=channel, intent="social-post")
            self.assertEqual((r["owner"], r["status"], r["rule_id"]), ("brain", "ROUTED", "yann-on-x"), persona)
            self.assertEqual(r["skills"], {})
            self.assertFalse(r["strategist"])

    def test_yann_on_linkedin_is_studio(self):
        r = route(persona="yann", channel="linkedin", intent="social-post")
        self.assertEqual((r["owner"], r["status"]), ("studio", "ROUTED"))

    def test_zazmic_on_x_needs_operator(self):
        r = route(brand="Zazmic", channel="twitter", intent="social-post")
        self.assertEqual((r["owner"], r["status"], r["rule_id"]), (None, "NEEDS_OPERATOR", "zazmic-on-x"))

    def test_zazmic_linkedin_social_post(self):
        r = route(brand="zazmic.ai", channel="LinkedIn", intent="social-post")
        self.assertEqual((r["owner"], r["status"], r["intent"]), ("studio", "ROUTED", "social-post"))
        self.assertTrue(r["strategist"])
        self.assertEqual(r["skills"]["writer"], ["compiled/corey/social.md", "compiled/corey/copywriting.md"])
        self.assertEqual(r["skills"]["strategist"], ["compiled/corey/social.md"])
        self.assertIn("compiled/corey/copy-editing.md", r["skills"]["critic"])
        self.assertIsNone(r["research_skill"])
        self.assertEqual(r["max_rounds"], 3)

    def test_other_brand_on_x_is_studio(self):
        r = route(brand="acme", channel="x", intent="social-post")
        self.assertEqual((r["owner"], r["status"]), ("studio", "ROUTED"))

    def test_translation_without_strategist(self):
        r = route(brand="zazmic", channel="web", intent="translation")
        self.assertEqual((r["status"], r["fidelity"]), ("ROUTED", "strict-source"))
        self.assertFalse(r["strategist"])
        self.assertNotIn("strategist", r["skills"])
        self.assertEqual(r["skills"]["critic"], ["compiled/corey/copy-editing.md"])

    def test_article_and_newsletter_have_research_skill(self):
        for intent, writer in (("article", "compiled/corey/copywriting.md"),
                               ("newsletter", "compiled/bytedance/newsletter-generation.md")):
            r = route(brand="zazmic", channel="newsletter", intent=intent)
            self.assertEqual(r["status"], "ROUTED", intent)
            self.assertEqual(r["fidelity"], "research-backed")
            self.assertEqual(r["research_skill"], "compiled/bytedance/deep-research.md")
            self.assertTrue(r["strategist"])
            self.assertEqual(r["skills"]["writer"], [writer])

    def test_campaign_blocked(self):
        r = route(brand="zazmic", channel="linkedin", intent="campaign")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("ADR-19", r["reason"])
        self.assertEqual(r["skills"], {})

    def test_unknown_or_missing_intent_needs_operator(self):
        for intent in ("podcast", "-"):
            r = route(brand="zazmic", channel="linkedin", intent=intent)
            self.assertEqual((r["owner"], r["status"]), ("studio", "NEEDS_OPERATOR"), intent)

    def test_ad_email_copy_page(self):
        for intent, skill in (("ad", "ad-creative"), ("email", "emails"), ("copy-page", "copywriting")):
            r = route(brand="zazmic", channel="web", intent=intent)
            self.assertEqual(r["status"], "ROUTED", intent)
            self.assertEqual(r["skills"]["writer"], [f"compiled/corey/{skill}.md"])

    def test_usage_error_exits_nonzero(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--bogus", "x"], capture_output=True)
        self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
