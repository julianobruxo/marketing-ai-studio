"""T-PATH e regras do guard (hosts/claude-code/guard.py), sem Claude Code.

Cada teste roda o guard de verdade, como o hook roda: um processo Python que lê a chamada
pela entrada padrão. O guard é copiado para um repositório temporário com runs/ sintético.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOST_DIR = REPO_ROOT / "hosts" / "claude-code"
JOB = "test-job"
WINDOWS = os.name == "nt"


class GuardTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="guard-test-")
        self._out = tempfile.TemporaryDirectory(prefix="guard-outside-")
        self.root = Path(self._tmp.name).resolve()
        self.outside = Path(self._out.name).resolve()
        shutil.copytree(HOST_DIR, self.root / "hosts" / "claude-code",
                        ignore=shutil.ignore_patterns("__pycache__"))
        for d in (f"runs/{JOB}/drafts", f"runs/{JOB}/eval-pack/r1", f"runs/{JOB}/.agents",
                  "runs/outra/drafts", "compiled/corey"):
            (self.root / d).mkdir(parents=True)
        (self.root / "runs/.active").write_text(JOB + "\n", encoding="utf-8")
        (self.root / "README.md").write_text("# repo\n", encoding="utf-8")
        (self.root / "compiled/corey/copywriting.md").write_text("x\n", encoding="utf-8")
        (self.outside / "secret.md").write_text("fora\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()
        self._out.cleanup()

    # ---------------------------------------------------------------- helpers

    def run_guard(self, payload):
        data = payload if isinstance(payload, (bytes, str)) else json.dumps(payload)
        if isinstance(data, str):
            data = data.encode("utf-8")
        proc = subprocess.run([sys.executable, str(self.root / "hosts/claude-code/guard.py")],
                              input=data, capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout.decode("utf-8").strip()
        if not out:
            return "pass", ""
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        return hso["permissionDecision"], hso["permissionDecisionReason"]

    def call(self, tool, tool_input, agent_type="studio-writer", cwd=None):
        event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
                 "cwd": str(cwd or self.root), "session_id": "s", "tool_use_id": "t"}
        if agent_type:
            event["agent_type"] = agent_type
            event["agent_id"] = f"id-{agent_type}"
        return self.run_guard(event)[0]

    def write(self, path, agent_type="studio-writer", tool="Write"):
        field = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return self.call(tool, {field: str(path), "content": "x"}, agent_type)

    def read(self, path, agent_type="studio-critic"):
        return self.call("Read", {"file_path": str(path)}, agent_type)

    def drafts(self, *parts):
        return self.root.joinpath("runs", JOB, "drafts", *parts)

    def log(self):
        lines = (self.root / "runs/tool-log.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def symlink(self, link, target, is_dir=False):
        try:
            os.symlink(target, link, target_is_directory=is_dir)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"este SO/usuário não cria symlink: {exc}")

    # ------------------------------------------------------------------ T-PATH

    def test_writer_in_drafts_allowed(self):
        self.assertEqual(self.write(self.drafts("c1.md")), "allow")
        self.assertEqual(self.write(f"runs/{JOB}/drafts/c2.md"), "allow")  # relativo ao cwd

    def test_dotdot_simple(self):
        self.assertEqual(self.write(str(self.drafts()) + "/../../../README.md"), "deny")
        self.assertEqual(self.write(f"runs/{JOB}/drafts/../eval-pack/r1/x.md"), "deny")

    def test_dotdot_encoded_and_multi_component(self):
        self.assertEqual(self.write(f"runs/{JOB}/drafts/%2e%2e/%2e%2e/outra/drafts/x.md"), "deny")
        self.assertEqual(self.write(f"runs\\{JOB}\\drafts\\..\\..\\outra\\drafts\\x.md"), "deny")
        self.assertEqual(self.write(f"runs/{JOB}/drafts/a/../../drafts/x.md"), "deny")

    def test_absolute_outside_repo(self):
        self.assertEqual(self.write(self.outside / "x.md"), "deny")
        self.assertEqual(self.read(self.outside / "secret.md", "studio-writer"), "deny")
        self.assertEqual(self.read(self.outside / "secret.md", None), "deny")

    def test_file_symlink_in_drafts(self):
        link = self.drafts("link.md")
        self.symlink(link, self.outside / "secret.md")
        self.assertEqual(self.write(link), "deny")
        self.assertEqual(self.read(link, "studio-writer"), "deny")

    def test_dir_symlink_in_drafts(self):
        link = self.drafts("linkdir")
        self.symlink(link, self.outside, is_dir=True)
        self.assertEqual(self.write(link / "x.md"), "deny")

    @unittest.skipUnless(WINDOWS, "junction só existe no Windows")
    def test_junction_in_drafts(self):
        link = self.drafts("junc")
        proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.outside)],
                              capture_output=True)
        if proc.returncode != 0:
            self.skipTest("mklink /J falhou")
        self.assertEqual(self.write(link / "x.md"), "deny")
        self.assertEqual(self.read(link / "secret.md", "studio-writer"), "deny")

    def test_drafts_evil(self):
        self.assertEqual(self.write(self.root / "runs" / JOB / "drafts-evil" / "x.md"), "deny")
        self.assertEqual(self.write(self.root / "runs" / JOB / "draftsx.md"), "deny")

    def test_other_job(self):
        self.assertEqual(self.write(self.root / "runs/outra/drafts/x.md"), "deny")
        self.assertEqual(self.read(self.root / "runs/outra/drafts/x.md"), "deny")

    def test_device_prefixes(self):
        self.assertEqual(self.write("\\\\?\\" + str(self.drafts("x.md"))), "deny")
        self.assertEqual(self.write("\\\\.\\" + str(self.drafts("x.md"))), "deny")
        self.assertEqual(self.write("//?/" + str(self.drafts("x.md")).replace("\\", "/")), "deny")

    def test_alternate_data_stream(self):
        self.assertEqual(self.write(str(self.drafts("x.md")) + ":stream"), "deny")
        self.assertEqual(self.write(str(self.drafts("x.md")) + "::$DATA"), "deny")

    def test_nul_byte(self):
        self.assertEqual(self.write(str(self.drafts("x")) + "\x00.md"), "deny")

    def test_case_variation(self):
        if os.path.normcase("A") != "a":
            self.skipTest("sistema de arquivos sensível a maiúsculas")
        upper = self.root / "RUNS" / JOB.upper() / "DRAFTS" / "c1.md"
        self.assertEqual(self.write(upper), "allow")
        self.assertEqual(self.write(self.root / "RUNS" / JOB.upper() / "DRAFTS-EVIL" / "c1.md"), "deny")
        self.assertEqual(self.write(self.root / "RUNS" / "TOOL-LOG.JSONL", None), "deny")
        self.assertEqual(self.write(self.root / "Runs" / "Outra" / "Drafts" / "x.md"), "deny")

    # ------------------------------------------------------------------ regras

    def test_no_active_job(self):
        (self.root / "runs/.active").unlink()
        self.assertEqual(self.write(self.drafts("c1.md")), "deny")
        self.assertEqual(self.read(self.root / "compiled/corey/copywriting.md"), "deny")
        self.assertEqual(self.write(self.root / "runs/.active", None), "allow")
        self.assertEqual(self.call("Bash", {"command": "ls"}, None), "pass")
        self.assertEqual(self.log()[-1]["decision"], "pass")

    def test_invalid_active_job(self):
        (self.root / "runs/.active").write_text("../x\n", encoding="utf-8")
        self.assertEqual(self.write(self.drafts("c1.md")), "deny")

    def test_unknown_agent_type(self):
        self.assertEqual(self.read(self.root / "compiled/corey/copywriting.md", "Explore"), "deny")
        self.assertEqual(self.write(self.drafts("c1.md"), "general-purpose"), "deny")

    def test_other_tools_for_subagents(self):
        for tool, tool_input in (("Bash", {"command": "echo hi"}), ("Glob", {"pattern": "**"}),
                                 ("Grep", {"pattern": "x"}), ("WebFetch", {"url": "https://example.com"}),
                                 ("WebSearch", {"query": "x"}), ("mcp__x__y", {})):
            self.assertEqual(self.call(tool, tool_input, "studio-critic"), "deny", tool)
            self.assertEqual(self.call(tool, tool_input, None), "pass", tool)

    def test_agent_tool(self):
        self.assertEqual(self.call("Agent", {"subagent_type": "studio-writer", "prompt": "p"}, None), "allow")
        self.assertEqual(self.call("Agent", {"subagent_type": "general-purpose", "prompt": "p"}, None), "deny")
        self.assertEqual(self.call("Agent", {"subagent_type": "fork", "prompt": "p"}, None), "deny")
        self.assertEqual(self.call("Agent", {"prompt": "p"}, None), "deny")
        self.assertEqual(self.call("Agent", {"subagent_type": "studio-critic", "prompt": "p"}), "deny")
        self.assertEqual(self.call("Task", {"subagent_type": "studio-writer", "prompt": "p"}, "studio-writer"), "deny")

    def test_critic_scope(self):
        self.assertEqual(self.read(self.drafts("c1.md")), "deny")
        self.assertEqual(self.read(self.root / f"runs/{JOB}/eval-pack/r1/candidate.md"), "allow")
        self.assertEqual(self.read(self.root / "compiled/corey/copywriting.md"), "allow")
        self.assertEqual(self.write(self.root / f"runs/{JOB}/verdicts/v.json", "studio-critic"), "deny")
        self.assertEqual(self.read(self.root / "README.md"), "deny")

    def test_tool_log_never_writable(self):
        for agent in (None, "studio-writer"):
            self.assertEqual(self.write(self.root / "runs/tool-log.jsonl", agent), "deny")
            self.assertEqual(self.write(self.root / "runs/tool-log.jsonl", agent, tool="Edit"), "deny")

    def test_orchestrator_write_rules(self):
        self.assertEqual(self.write(self.root / f"runs/{JOB}/brief.md", None), "allow")
        self.assertEqual(self.write(self.root / "runs/.active", None), "allow")
        self.assertEqual(self.write(self.drafts("c1.md"), None), "deny")
        self.assertEqual(self.write(self.root / "README.md", None), "deny")
        self.assertEqual(self.write(self.root / "runs/outra/brief.md", None), "deny")

    def test_notebook_and_edit_paths(self):
        self.assertEqual(self.write(self.drafts("n.ipynb"), tool="NotebookEdit"), "allow")
        self.assertEqual(self.write(self.root / "README.md", tool="NotebookEdit"), "deny")
        self.assertEqual(self.write(self.root / "README.md", tool="Edit"), "deny")

    def test_pathless_tools_follow_role_tool_list(self):
        self.assertEqual(self.call("WebSearch", {"query": "x"}, "studio-strategist"), "allow")
        self.assertEqual(self.call("WebFetch", {"url": "https://example.com"}, "studio-strategist"), "allow")
        self.assertEqual(self.call("WebSearch", {"query": "x"}, "studio-critic"), "deny")
        self.assertEqual(self.call("WebFetch", {"url": "https://example.com"}, "studio-writer"), "deny")
        self.assertEqual(self.call("Bash", {"command": "ls"}, "studio-strategist"), "deny")
        self.assertEqual(self.log()[0]["reason"], "WebSearch está na lista de ferramentas do papel")
        (self.root / "runs/.active").unlink()
        self.assertEqual(self.call("WebSearch", {"query": "x"}, "studio-strategist"), "deny")

    def test_report_tool_allowed_for_subagents(self):
        self.assertEqual(self.call("SubagentHandback", {"message": "relatório"}, "studio-critic"), "allow")

    # ------------------------------------------------------------ fail-closed

    def test_malformed_input(self):
        self.assertEqual(self.run_guard(b'{"tool_name": ')[0], "deny")
        self.assertEqual(self.run_guard(b"[1, 2]")[0], "deny")
        self.assertEqual(self.run_guard(b"\xff\xfe")[0], "deny")
        self.assertEqual(self.call("Write", "nao-e-objeto"), "deny")
        self.assertEqual(self.call("Write", {"content": "sem file_path"}), "deny")
        self.assertEqual(self.call("Read", {"file_path": 42}), "deny")

    def test_internal_exception_denies(self):
        (self.root / "hosts/claude-code/host.yaml").write_text("{ quebrado", encoding="utf-8")
        decision, reason = self.run_guard({"tool_name": "Write", "agent_type": "studio-writer",
                                           "tool_input": {"file_path": str(self.drafts("c1.md"))}})
        self.assertEqual(decision, "deny")
        self.assertIn("erro interno", reason)
        (self.root / "hosts/claude-code/host.yaml").unlink()
        self.assertEqual(self.write(self.drafts("c1.md"), None), "deny")

    def test_log_failure_denies_subagent(self):
        (self.root / "runs/tool-log.jsonl").mkdir()
        self.assertEqual(self.write(self.drafts("c1.md")), "deny")
        self.assertEqual(self.read(self.root / "compiled/corey/copywriting.md"), "deny")

    def test_every_call_is_logged(self):
        self.write(self.drafts("c1.md"))
        self.write(self.root / "README.md")
        self.call("Bash", {"command": "ls"}, None)
        entries = self.log()
        self.assertEqual([e["decision"] for e in entries], ["allow", "deny", "pass"])
        for key in ("ts", "job", "agent_id", "agent_type", "role", "tool", "target", "decision", "reason"):
            self.assertIn(key, entries[0])
        self.assertEqual(entries[0]["target"], f"runs/{JOB}/drafts/c1.md")
        self.assertEqual(entries[0]["agent_type"], "studio-writer")
        self.assertEqual(entries[0]["job"], JOB)


if __name__ == "__main__":
    unittest.main()
