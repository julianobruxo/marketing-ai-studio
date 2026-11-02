#!/usr/bin/env python3
"""Instala o Marketing Content Studio num host de execução (ADR-12, ADR-18).

  python scripts/install_host.py --host claude-code --target <clone de execução>

O alvo precisa ser um clone do Studio (com hosts/claude-code/ e agents/). O instalador gera:
  <alvo>/.claude/agents/<nome>.md   frontmatter do host.yaml + corpo de agents/<papel>.md
  <alvo>/.claude/settings.json      env, permissions.deny e o hook PreToolUse do guard
  <alvo>/.claude/skills/marketing-content-studio/   cópia byte a byte da skill de entrada
Agentes studio-*.md que não estão mais no host.yaml são removidos.

O hook usa a forma exec do Claude Code (command + args, sem shell): caminhos absolutos do
interpretador (sys.executable) e do guard, sem problema de aspas no Windows, e
onFailure "block", para que um guard que não inicia ou trava bloqueie a ferramenta.

A saída é determinística e reinstalar é idempotente. No fim, um teste de fumaça executa o
comando exato do hook; se falhar, a instalação é desfeita.
Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOSTS = ("claude-code",)
SMOKE_JOB = "install-smoke"
SKILL_NAME = "marketing-content-studio"


def load_host(target: Path) -> dict:
    return json.loads((target / "hosts" / "claude-code" / "host.yaml").read_text(encoding="utf-8"))


def agent_file(name: str, spec: dict, body: str) -> str:
    front = [
        "---",
        f"name: {json.dumps(name)}",
        f"description: {json.dumps(spec['description'], ensure_ascii=False)}",
        f"tools: {', '.join(spec['tools'])}",
        f"model: {json.dumps(spec['model'])}",
        "---",
        "",
        "",
    ]
    return "\n".join(front) + body.replace("\r\n", "\n")


def settings(host: dict, guard: Path) -> dict:
    return {
        "env": dict(host["env"]),
        "permissions": {"deny": [f"Edit(/{pattern})" for pattern in host["deny_edit"]]},
        "hooks": {
            "PreToolUse": [{
                "matcher": "*",
                "hooks": [{
                    "type": "command",
                    "command": sys.executable,
                    "args": [str(guard)],
                    "onFailure": "block",
                    "timeout": 30,
                }],
            }],
        },
    }


def dump_json(data) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def run_hook(command: str, args, payload: str):
    try:
        proc = subprocess.run([command, *args], input=payload.encode("utf-8"),
                              capture_output=True, timeout=30)
    except subprocess.TimeoutExpired:
        return None, "hook estourou o tempo"
    except OSError as exc:
        return None, f"hook não iniciou ({exc.__class__.__name__})"
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        decision = json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None
    except (ValueError, KeyError, TypeError):
        decision = f"saída inválida: {out[:80]!r}"
    return proc.returncode, decision


def smoke_test(target: Path, host: dict) -> list:
    """Executa o comando do hook gravado no settings.json; devolve a lista de falhas."""
    hook = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hook = hook["hooks"]["PreToolUse"][0]["hooks"][0]
    active = target / host["active_job_file"]
    previous = active.read_bytes() if active.exists() else None
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(SMOKE_JOB + "\n", encoding="utf-8")

    def event(tool_input, tool="Write", agent_type="studio-writer"):
        return json.dumps({
            "hook_event_name": "PreToolUse", "cwd": str(target), "tool_name": tool,
            "tool_input": tool_input, "agent_type": agent_type, "agent_id": "install-smoke",
        })

    cases = [
        ("subagente grava fora do escopo", event({"file_path": str(target / "README.md"), "content": "x"}), "deny"),
        ("Writer grava em drafts", event({"file_path": str(target / "runs" / SMOKE_JOB / "drafts" / "c1.md"),
                                          "content": "x"}), "allow"),
        ("JSON malformado", '{"tool_name": "Write", ', "deny"),
    ]
    failures = []
    try:
        for label, payload, expected in cases:
            code, decision = run_hook(hook["command"], hook["args"], payload)
            status = "ok" if (code == 0 and decision == expected) else "FALHOU"
            print(f"  fumaça: {label}: {decision} (exit {code}) — esperado {expected} — {status}")
            if status != "ok":
                failures.append(label)
    finally:
        if previous is None:
            active.unlink()
        else:
            active.write_bytes(previous)
    return failures


def install_skill(target: Path) -> Path:
    """Espelha skills/marketing-content-studio/ em .claude/skills/, byte a byte."""
    src = target / "skills" / SKILL_NAME
    dst = target / ".claude" / "skills" / SKILL_NAME
    wanted = {p.relative_to(src) for p in src.rglob("*") if p.is_file()}
    if dst.exists():
        for p in sorted(dst.rglob("*"), reverse=True):
            if p.is_file() and p.relative_to(dst) not in wanted:
                p.unlink()
            elif p.is_dir() and not any(p.iterdir()):
                p.rmdir()
    for rel in sorted(wanted):
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        data = (src / rel).read_bytes()
        if not out.exists() or out.read_bytes() != data:
            out.write_bytes(data)
    return dst


def install(target: Path) -> int:
    host_file = target / "hosts" / "claude-code" / "host.yaml"
    guard = target / "hosts" / "claude-code" / "guard.py"
    if not host_file.is_file() or not guard.is_file():
        print(f"ERRO: {target} não é um clone do Studio (faltam hosts/claude-code/host.yaml ou guard.py)")
        return 2
    host = load_host(target)

    print("AVISO: o settings.json gerado nega edição em " + ", ".join(host["deny_edit"]) + ".")
    print("       Instale só no clone de execução (ex.: C:\\dev\\studio-run), nunca no clone de desenvolvimento.")
    if target.resolve() == REPO_ROOT.resolve():
        print("AVISO: o alvo é o próprio clone de onde este instalador está rodando.")

    agents_dir = target / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, spec in sorted(host["subagents"].items()):
        body = (target / spec["body"]).read_text(encoding="utf-8")
        path = agents_dir / f"{name}.md"
        path.write_bytes(agent_file(name, spec, body).encode("utf-8"))
        written.append(path)
        print(f"agente: {path.relative_to(target).as_posix()}")
    for stale in sorted(agents_dir.glob("studio-*.md")):
        if stale not in written:
            stale.unlink()
            print(f"removido (fora do host.yaml): {stale.relative_to(target).as_posix()}")

    skill_dst = install_skill(target)
    print(f"skill: {skill_dst.relative_to(target).as_posix()}/")

    settings_path = target / ".claude" / "settings.json"
    settings_path.write_bytes(dump_json(settings(host, guard.resolve())).encode("utf-8"))
    print(f"settings: {settings_path.relative_to(target).as_posix()}")

    try:
        failures = smoke_test(target, host)
    except Exception as exc:
        failures = [f"erro no teste de fumaça ({exc.__class__.__name__}: {exc})"]
    if failures:
        settings_path.unlink(missing_ok=True)
        for path in written:
            path.unlink(missing_ok=True)
        shutil.rmtree(skill_dst, ignore_errors=True)
        print("INSTALAÇÃO ABORTADA: o teste de fumaça do hook falhou (" + "; ".join(failures) + ").")
        print("settings.json, agentes e skill gerados foram removidos.")
        return 1
    print("OK: instalação concluída; teste de fumaça do hook passou.")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Instala o Studio num host de execução.")
    parser.add_argument("--host", required=True, choices=HOSTS)
    parser.add_argument("--target", required=True, help="clone de execução do Studio")
    args = parser.parse_args(argv)
    return install(Path(args.target).resolve())


if __name__ == "__main__":
    sys.exit(main())
