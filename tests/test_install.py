"""T-INSTALL (instalação e configuração, sem Claude Code): scripts/install_host.py."""

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = REPO_ROOT / "scripts" / "install_host.py"
HOST = json.loads((REPO_ROOT / "hosts/claude-code/host.yaml").read_text(encoding="utf-8"))


def install(target: Path):
    proc = subprocess.run([sys.executable, str(INSTALLER), "--host", "claude-code", "--target", str(target)],
                          capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout + proc.stderr


def frontmatter(text: str) -> dict:
    lines = text.split("\n")
    end = lines.index("---", 1)
    out = {}
    for line in lines[1:end]:
        key, value = line.split(": ", 1)
        out[key] = json.loads(value) if value.startswith('"') else value
    out["_body"] = "\n".join(lines[end + 2:])
    return out


class InstallTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="install-test-")
        self.target = Path(self._tmp.name).resolve()
        for name in ("agents", "hosts", "skills"):
            shutil.copytree(REPO_ROOT / name, self.target / name, ignore=shutil.ignore_patterns("__pycache__"))
        (self.target / "README.md").write_text("# alvo\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def installed(self):
        code, out = install(self.target)
        self.assertEqual(code, 0, out)
        return out

    def agent(self, name):
        return frontmatter((self.target / ".claude/agents" / f"{name}.md").read_text(encoding="utf-8"))

    def settings(self):
        return json.loads((self.target / ".claude/settings.json").read_text(encoding="utf-8"))

    def test_agents_match_host_yaml(self):
        self.installed()
        files = sorted(p.name for p in (self.target / ".claude/agents").iterdir())
        self.assertEqual(files, sorted(f"{n}.md" for n in HOST["subagents"]))
        for name, spec in HOST["subagents"].items():
            fm = self.agent(name)
            self.assertEqual(fm["name"], name)
            self.assertEqual(fm["description"], spec["description"])
            self.assertEqual(fm["model"], spec["model"])
            self.assertEqual(fm["tools"].split(", "), spec["tools"])
            body = (self.target / spec["body"]).read_text(encoding="utf-8")
            self.assertEqual(fm["_body"], body)

    def test_tool_allowlists(self):
        self.installed()
        self.assertEqual(sorted(HOST["subagents"]), ["studio-critic", "studio-strategist", "studio-writer"])
        self.assertEqual(self.agent("studio-critic")["tools"], "Read")
        self.assertEqual(self.agent("studio-strategist")["tools"], "Read, WebSearch, WebFetch")
        self.assertEqual(self.agent("studio-writer")["tools"], "Read, Write")
        for name in HOST["subagents"]:
            tools = self.agent(name)["tools"].split(", ")
            self.assertNotIn("Bash", tools)
            self.assertNotIn("Agent", tools)
            self.assertNotIn("Task", tools)

    def test_settings(self):
        out = self.installed()
        s = self.settings()
        self.assertEqual(s["env"], {"CLAUDE_CODE_FORK_SUBAGENT": "0", "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"})
        self.assertEqual(s["permissions"]["deny"], [f"Edit(/{p})" for p in HOST["deny_edit"]])
        self.assertIn("Edit(/.claude/**)", s["permissions"]["deny"])
        groups = s["hooks"]["PreToolUse"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["matcher"], "*")
        hook = groups[0]["hooks"][0]
        self.assertEqual(hook["type"], "command")
        self.assertEqual(hook["onFailure"], "block")
        self.assertTrue(Path(hook["command"]).is_absolute())
        self.assertEqual(Path(hook["command"]), Path(sys.executable))
        self.assertTrue(Path(hook["args"][0]).is_absolute())
        self.assertEqual(Path(hook["args"][0]), self.target / "hosts/claude-code/guard.py")
        self.assertIn("teste de fumaça do hook passou", out)
        self.assertFalse((self.target / "runs/.active").exists(), "fumaça não pode deixar tarefa ativa")

    def test_reinstall_is_idempotent(self):
        self.installed()
        first = {p: p.read_bytes() for p in (self.target / ".claude").rglob("*") if p.is_file()}
        self.installed()
        second = {p: p.read_bytes() for p in (self.target / ".claude").rglob("*") if p.is_file()}
        self.assertEqual(first, second)

    def test_smoke_preserves_active_job(self):
        (self.target / "runs").mkdir()
        (self.target / "runs/.active").write_text("job-real\n", encoding="utf-8")
        self.installed()
        self.assertEqual((self.target / "runs/.active").read_text(encoding="utf-8"), "job-real\n")

    def test_entry_skill_copied_byte_for_byte(self):
        self.installed()
        src = self.target / "skills/marketing-content-studio"
        dst = self.target / ".claude/skills/marketing-content-studio"
        files = sorted(p.relative_to(src) for p in src.rglob("*") if p.is_file())
        self.assertIn(Path("SKILL.md"), files)
        self.assertEqual(sorted(p.relative_to(dst) for p in dst.rglob("*") if p.is_file()), files)
        for rel in files:
            self.assertEqual((dst / rel).read_bytes(), (src / rel).read_bytes(), rel)
        (dst / "sobra.md").write_text("velho\n", encoding="utf-8")
        self.installed()
        self.assertFalse((dst / "sobra.md").exists())

    def test_old_reviewer_removed(self):
        agents = self.target / ".claude/agents"
        agents.mkdir(parents=True)
        (agents / "studio-reviewer.md").write_text("---\nname: studio-reviewer\n---\n", encoding="utf-8")
        (agents / "outro-agente.md").write_text("não é do Studio\n", encoding="utf-8")
        self.installed()
        self.assertFalse((agents / "studio-reviewer.md").exists())
        self.assertTrue((agents / "outro-agente.md").exists())

    def test_target_required_and_must_be_studio_clone(self):
        proc = subprocess.run([sys.executable, str(INSTALLER), "--host", "claude-code"], capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        shutil.rmtree(self.target / "hosts")
        code, out = install(self.target)
        self.assertNotEqual(code, 0, out)

    def install_in_process(self, patches):
        """Roda install() no próprio processo, com partes do instalador trocadas."""
        spec = importlib.util.spec_from_file_location("install_host_under_test", INSTALLER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            for target, name, value in patches(module):
                stack.enter_context(mock.patch.object(target, name, value))
            stack.enter_context(contextlib.redirect_stdout(out))
            code = module.install(self.target)
        return code, out.getvalue()

    def assertRolledBack(self, code, out):
        self.assertNotEqual(code, 0, out)
        self.assertIn("INSTALAÇÃO ABORTADA", out)
        self.assertFalse((self.target / ".claude/settings.json").exists())
        self.assertEqual(list((self.target / ".claude/agents").glob("studio-*.md")), [])
        self.assertFalse((self.target / ".claude/skills/marketing-content-studio").exists())
        self.assertEqual((self.target / "runs/.active").read_text(encoding="utf-8"), "job-real\n")

    def test_smoke_process_errors_roll_back(self):
        def raising(exc):
            def run(*args, **kwargs):
                raise exc
            return run

        cases = (
            ("TimeoutExpired", subprocess.TimeoutExpired(cmd="guard", timeout=30), "hook estourou o tempo"),
            ("OSError", FileNotFoundError(2, "python não encontrado"), "hook não iniciou"),
        )
        for label, exc, message in cases:
            with self.subTest(label):
                (self.target / "runs").mkdir(exist_ok=True)
                (self.target / "runs/.active").write_text("job-real\n", encoding="utf-8")
                code, out = self.install_in_process(
                    lambda m: [(m.subprocess, "run", raising(exc))])
                self.assertRolledBack(code, out)
                self.assertIn(message, out)

    def test_unexpected_smoke_exception_rolls_back(self):
        (self.target / "runs").mkdir()
        (self.target / "runs/.active").write_text("job-real\n", encoding="utf-8")

        def boom(*args, **kwargs):
            raise RuntimeError("falha inesperada")

        code, out = self.install_in_process(lambda m: [(m, "run_hook", boom)])
        self.assertRolledBack(code, out)
        self.assertIn("RuntimeError", out)

    def test_broken_guard_aborts(self):
        (self.target / "hosts/claude-code/guard.py").write_text(
            'import json\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",'
            ' "permissionDecision": "allow"}}))\n', encoding="utf-8")
        code, out = install(self.target)
        self.assertEqual(code, 1, out)
        self.assertIn("INSTALAÇÃO ABORTADA", out)
        self.assertFalse((self.target / ".claude/settings.json").exists())


if __name__ == "__main__":
    unittest.main()
