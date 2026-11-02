"""T14: integridade do vendor contra o lock (scripts/vendor.py verify).

Os casos de falha rodam numa cópia temporária de vendor/ e provenance/;
o repositório nunca é alterado.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "vendor.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_verify(root: Path):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "verify", "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout + proc.stderr


class VerifyRepoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="vendor-test-")
        self.root = Path(self._tmp.name)
        for name in ("vendor", "provenance"):
            shutil.copytree(REPO_ROOT / name, self.root / name)

    def tearDown(self):
        self._tmp.cleanup()

    def assertFailsWith(self, kind: str, path: str):
        code, out = run_verify(self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"[{kind}] {path}", out)

    def test_clean_repo_passes(self):
        code, out = run_verify(REPO_ROOT)
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)

    def test_clean_copy_passes(self):
        code, out = run_verify(self.root)
        self.assertEqual(code, 0, out)

    def test_one_byte_change_fails(self):
        rel = "vendor/corey/skills/copywriting/SKILL.md"
        target = self.root / rel
        data = bytearray(target.read_bytes())
        data[-1] ^= 0x01
        target.write_bytes(bytes(data))
        self.assertFailsWith("HASH", rel)

    def test_extra_file_fails(self):
        rel = "vendor/corey/skills/copywriting/references/intruso.md"
        (self.root / rel).write_text("# intruso\n", encoding="utf-8")
        self.assertFailsWith("FORA_DO_LOCK", rel)

    def test_missing_locked_file_fails(self):
        rel = "vendor/corey/skills/emails/evals/evals.json"
        (self.root / rel).unlink()
        self.assertFailsWith("AUSENTE", rel)

    def test_missing_license_fails(self):
        rel = "vendor/corey/LICENSE"
        (self.root / rel).unlink()
        self.assertFailsWith("LICENSE", rel)


class VerifyFixtureTest(unittest.TestCase):
    def test_synthetic_ok_passes(self):
        code, out = run_verify(FIXTURES / "synthetic-ok")
        self.assertEqual(code, 0, out)

    def test_broken_relative_link_fails(self):
        code, out = run_verify(FIXTURES / "synthetic-broken-link")
        self.assertNotEqual(code, 0, out)
        self.assertIn("[LINK] vendor/synthetic/skills/demo/SKILL.md:11", out)
        self.assertIn("FALHA: 1 problema(s)", out)


if __name__ == "__main__":
    unittest.main()
