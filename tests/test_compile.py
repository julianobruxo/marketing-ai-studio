"""T-COMPILE: overlays declarativos e compilação determinística (scripts/vendor.py compile).

Os casos de falha rodam numa cópia temporária; o repositório nunca é alterado.
"""

import hashlib
import importlib.util
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
FENCES = Path(__file__).resolve().parent / "fixtures" / "compile-fences"
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

    def test_bytedance_compile_reproducible_with_copyright(self):
        names = ("deep-research", "newsletter-generation")
        committed = {n: (self.root / f"compiled/bytedance/{n}.md").read_bytes() for n in names}
        for _ in range(2):
            code, out = run("compile", "--root", self.root)
            self.assertEqual(code, 0, out)
            for n in names:
                self.assertEqual((self.root / f"compiled/bytedance/{n}.md").read_bytes(), committed[n], n)
        for n in names:
            out = self.read(f"compiled/bytedance/{n}.md")
            self.assertIn("commit: 12c304f12ce5c0bf66d8927386e5dd18ea84f685", out)
            self.assertIn(f"upstream_path: skills/public/{n}/SKILL.md", out)
            self.assertIn("Copyright (c) 2025 Bytedance Ltd. and/or its affiliates; "
                          "Copyright (c) 2025-2026 DeerFlow Authors. MIT License — see vendor/bytedance/LICENSE.", out)
            self.assertEqual(frontmatter(out),
                             frontmatter(self.read(f"vendor/bytedance/skills/public/{n}/SKILL.md")), n)

    def test_copywriting_keeps_profound_attribution(self):
        upstream = self.read("vendor/corey/skills/copywriting/SKILL.md").split("\n")
        line = next(l for l in upstream if "adapted from Profound's `improved-copywriting`" in l)
        self.assertIn(line, self.read("compiled/corey/copywriting.md").split("\n"))


def load_vendor_module():
    spec = importlib.util.spec_from_file_location("vendor_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodeBlockMaskTest(unittest.TestCase):
    """Regras CommonMark de bloco de código cercado, direto no helper."""

    @classmethod
    def setUpClass(cls):
        cls.mask = staticmethod(load_vendor_module().code_block_mask)

    def test_longer_fence_contains_shorter_one(self):
        lines = ["````", "```", "## Tools", "```", "````", "## Tools"]
        self.assertEqual(self.mask(lines), [True, True, True, True, True, False])

    def test_shorter_closing_fence_does_not_close(self):
        lines = ["`````", "```", "## Dentro", "````", "## Ainda dentro", "`````", "## Fora"]
        self.assertEqual(self.mask(lines), [True] * 6 + [False])

    def test_tilde_fence(self):
        lines = ["~~~text", "## Dentro", "```", "~~~", "## Fora"]
        self.assertEqual(self.mask(lines), [True, True, True, True, False])

    def test_unclosed_fence_runs_to_end(self):
        lines = ["texto", "```", "## Dentro", "[x](y.md)"]
        self.assertEqual(self.mask(lines), [False, True, True, True])

    def test_closing_fence_rules(self):
        # Fechamento com info string não fecha; com espaços depois, fecha.
        self.assertEqual(self.mask(["```", "```python", "x", "```   ", "## Fora"]),
                         [True, True, True, True, False])
        # Cerca de crase com ` na info string não abre bloco.
        self.assertEqual(self.mask(["``` a`b", "## Fora"]), [False, False])
        # Até 3 espaços de recuo abrem; 4 não.
        self.assertEqual(self.mask(["   ```", "x", "   ```"]), [True, True, True])
        self.assertEqual(self.mask(["    ```", "## Fora"]), [False, False])


class CompileFencesTest(_TempRepo):
    source_dirs = ("vendor", "provenance", "overlays", "compiled")
    source_root = FENCES
    COMPILED = "compiled/fences/demo.md"
    OVERLAY = "overlays/fences/demo.md"

    def test_four_backtick_block_heading_ignored(self):
        committed = (self.root / self.COMPILED).read_bytes()
        code, out = run("compile", "--root", self.root)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.root / self.COMPILED).read_bytes(), committed)
        text = self.read(self.COMPILED)
        self.assertIn("```bash\necho oi\n```\n\n## Tools\n\n[link no bloco de 4 crases]", text)
        self.assertLess(text.index("\n````\n\n## Tools\n"), text.index("acréscimo na seção real de Tools"))

    def test_links_in_code_blocks_untouched(self):
        text = self.read(self.COMPILED)
        for link in ("](references/nao-existe-4.md)", "](references/nao-existe-til.md)",
                     "](references/nao-existe-fim.md)"):
            self.assertIn(link, text)
        self.assertIn("](../../vendor/fences/skills/demo/references/guide.md)", text)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)
        self.assertNotIn("nao-existe", out)

    def test_tilde_block_heading_ignored(self):
        text = self.read(self.COMPILED)
        self.assertLess(text.index("Formato real."), text.index("acréscimo na seção real de Output Format"))
        self.assertLess(text.index("acréscimo na seção real de Output Format"), text.index("## Tail"))

    def test_unclosed_block_runs_to_end(self):
        self.write(self.OVERLAY, self.read(self.OVERLAY)
                   + "\n<!-- op: acrescentar-após | ## Notes -->\nnão deveria achar.\n<!-- /op -->\n")
        code, out = run("compile", "--root", self.root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("'## Notes' não encontrada", out)


class OrphanCleanupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="orphan-test-")
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def copy_fixture(self, fixture: Path):
        for name in ("vendor", "overlays", "compiled"):
            shutil.copytree(fixture / name, self.root / name, dirs_exist_ok=True)
        lock_path = self.root / "provenance/upstream-lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() \
            else {"lock_version": 1, "sources": {}}
        lock["sources"].update(
            json.loads((fixture / "provenance/upstream-lock.json").read_text(encoding="utf-8"))["sources"])
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")

    def test_last_source_removed(self):
        self.copy_fixture(FIXTURE)
        shutil.rmtree(self.root / "overlays/synthetic")
        code, out = run("compile", "--root", self.root)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / "compiled/synthetic").exists(), out)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)

    def test_source_removed_with_other_present(self):
        self.copy_fixture(FIXTURE)
        self.copy_fixture(FENCES)
        kept = (self.root / "compiled/fences/demo.md").read_bytes()
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)
        shutil.rmtree(self.root / "overlays/synthetic")
        code, out = run("compile", "--root", self.root)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / "compiled/synthetic").exists(), out)
        self.assertEqual((self.root / "compiled/fences/demo.md").read_bytes(), kept)
        code, out = run("verify", "--root", self.root)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
