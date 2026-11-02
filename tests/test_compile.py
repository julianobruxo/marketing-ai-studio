"""T-COMPILE: overlays declarativos e compilação determinística (scripts/vendor.py compile).

Os casos de falha rodam numa cópia temporária; o repositório nunca é alterado.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "vendor.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "compile-basic"
FX_COMPILED = "compiled/synthetic/demo.md"
FX_OVERLAY = "overlays/synthetic/demo.md"
FX_SKILL = "vendor/synthetic/skills/demo/SKILL.md"


def run(*args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout + proc.stderr


def frontmatter(text: str) -> str:
    end = text.index("\n---\n", 4)
    return text[: end + 5]


class _TempRepo(unittest.TestCase):
    source_dirs = ()
    source_root = None

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="compile-test-")
        self.root = Path(self._tmp.name)
        for name in self.source_dirs:
            shutil.copytree(self.source_root / name, self.root / name)

    def tearDown(self):
        self._tmp.cleanup()

    def read(self, rel: str) -> str:
        return (self.root / rel).read_bytes().decode("utf-8")

    def write(self, rel: str, text: str):
        (self.root / rel).write_bytes(text.encode("utf-8"))

    def replace(self, rel: str, old: str, new: str):
        text = self.read(rel)
        self.assertIn(old, text)
        self.write(rel, text.replace(old, new, 1))


class CompileFixtureTest(_TempRepo):
    source_dirs = ("vendor", "provenance", "overlays", "compiled")
    source_root = FIXTURE

    def assertCompileFails(self, *needles):
        before = self.read(FX_COMPILED)
        code, out = run("compile", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        for needle in needles:
            self.assertIn(needle, out)
        self.assertEqual(self.read(FX_COMPILED), before, "compile com falha não pode escrever")
        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)

    def test_reproducible(self):
        committed = (self.root / FX_COMPILED).read_bytes()
        for _ in range(2):
            code, out = run("compile", "--root", self.root)
            self.assertEqual(code, 0, out)
            self.assertEqual((self.root / FX_COMPILED).read_bytes(), committed)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)

    def test_missing_anchor_fails(self):
        self.replace(FX_OVERLAY, "| ## Tools -->", "| ## Nao Existe -->")
        self.assertCompileFails("[OVERLAY]", "'## Nao Existe' não encontrada")

    def test_duplicate_anchor_fails(self):
        self.write(FX_SKILL, self.read(FX_SKILL) + "\n## Tools\n\nDuplicado.\n")
        self.assertCompileFails("[OVERLAY]", "'## Tools' ocorre 2x")

    def test_heading_in_code_block_ignored(self):
        out = self.read(FX_COMPILED)
        self.assertIn("```markdown\n## Before Writing\ntítulo falso dentro de bloco de código\n```", out)
        sub = out.index("Texto da subseção.")
        added = out.index("**Studio:** acréscimo sintético.")
        tools = out.index('Section "Tools" is disabled')
        self.assertLess(sub, added)
        self.assertLess(added, tools)

    def test_altered_trecho_fails(self):
        self.replace(FX_OVERLAY, "exists, read it.", "exists, read it now.")
        self.assertCompileFails("[OVERLAY]", "trecho literal")

    def test_header_has_commit_and_copyright(self):
        out = self.read(FX_COMPILED)
        self.assertIn("commit: " + "1" * 40, out)
        self.assertIn("Copyright (c) 2026 Fixture Sintética. MIT License — see vendor/synthetic/LICENSE.", out)

    def test_frontmatter_identical_to_upstream(self):
        self.assertEqual(frontmatter(self.read(FX_COMPILED)), frontmatter(self.read(FX_SKILL)))

    def test_rewritten_links_resolve(self):
        out = self.read(FX_COMPILED)
        self.assertIn("](../../vendor/synthetic/skills/demo/references/guide.md#secao)", out)
        self.assertIn("](https://example.com/x)", out)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)

    def test_new_host_mention_fails_verify(self):
        rel = "vendor/synthetic/skills/demo/references/guide.md"
        self.write(rel, self.read(rel) + "\nRode npx algo.\n")
        lock_path = self.root / "provenance/upstream-lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["sources"]["synthetic"]["skills"]["demo"]["files"][rel] = hashlib.sha256(
            (self.root / rel).read_bytes()).hexdigest()
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")

        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("[MENCOES_HOST]", out)
        self.assertNotIn("[HASH]", out)
        code, out = run("compile", "--root", self.root, "--accept-mentions")
        self.assertEqual(code, 0, out)
        self.assertIn("references/guide.md\t\\bnpx\\b\t1", out)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)

    def test_upstream_version_mismatch_fails(self):
        self.replace(FX_OVERLAY, "upstream_version: 1.0.0", "upstream_version: 0.9.0")
        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("[VERSAO]", out)

    def test_edited_compiled_fails_verify(self):
        self.write(FX_COMPILED, self.read(FX_COMPILED) + "editado à mão\n")
        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"[COMPILADO_DIVERGE] {FX_COMPILED}", out)

    def test_compiled_without_overlay_fails_verify(self):
        (self.root / FX_OVERLAY).unlink()
        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"[COMPILADO_SEM_OVERLAY] {FX_COMPILED}", out)

    def test_overlay_without_compiled_fails_verify(self):
        (self.root / FX_COMPILED).unlink()
        code, out = run("verify", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"[COMPILADO_AUSENTE] {FX_COMPILED}", out)


class CompileRepoTest(_TempRepo):
    source_dirs = ("vendor", "provenance", "overlays", "compiled")
    source_root = REPO_ROOT
    SKILLS = ("ad-creative", "copy-editing", "copywriting", "emails", "product-marketing", "social")

    def test_repo_compile_reproducible(self):
        committed = {s: (self.root / f"compiled/corey/{s}.md").read_bytes() for s in self.SKILLS}
        for _ in range(2):
            code, out = run("compile", "--root", self.root)
            self.assertEqual(code, 0, out)
            for s in self.SKILLS:
                self.assertEqual((self.root / f"compiled/corey/{s}.md").read_bytes(), committed[s], s)

    def test_repo_headers_and_frontmatter(self):
        for s in self.SKILLS:
            out = self.read(f"compiled/corey/{s}.md")
            self.assertIn("commit: 88c79f6528a9347420e57ceb1fff9a60de651768", out)
            self.assertIn("Copyright (c) 2025 Corey Haines. MIT License — see vendor/corey/LICENSE.", out)
            self.assertEqual(frontmatter(out), frontmatter(self.read(f"vendor/corey/skills/{s}/SKILL.md")), s)

    def test_copywriting_keeps_profound_attribution(self):
        upstream = self.read("vendor/corey/skills/copywriting/SKILL.md").split("\n")
        line = next(l for l in upstream if "adapted from Profound's `improved-copywriting`" in l)
        self.assertIn(line, self.read("compiled/corey/copywriting.md").split("\n"))


if __name__ == "__main__":
    unittest.main()
