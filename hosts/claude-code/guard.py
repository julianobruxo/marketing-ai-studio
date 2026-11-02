#!/usr/bin/env python3
"""Hook PreToolUse do Marketing Content Studio no Claude Code (ADR-18). FAIL-CLOSED.

Lê a chamada de ferramenta em JSON pela entrada padrão e imprime a decisão no formato
documentado do PreToolUse (hookSpecificOutput.permissionDecision), sempre com exit 0:

  deny   a chamada é bloqueada; o motivo vai para o modelo;
  allow  a chamada está dentro do escopo do papel e segue sem pedido de permissão
         (regras deny das settings continuam valendo);
  (nada) só para ferramentas que o orquestrador usa sem confinamento por caminho
         (Bash, WebFetch...): segue o fluxo normal de permissões do Claude Code.

Qualquer erro, entrada inesperada ou falha ao gravar o log de um subagente vira deny.
A raiz do repositório é a pasta que contém hosts/claude-code/ (dois níveis acima deste arquivo).
Só biblioteca padrão.
"""

from __future__ import annotations

import datetime as _dt
import fnmatch
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HOST_FILE = ROOT / "hosts" / "claude-code" / "host.yaml"

PATH_FIELDS = {
    "Read": "file_path",
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
AGENT_TOOLS = {"Agent", "Task"}
# Ferramenta interna que entrega o relatório do subagente ao orquestrador (modo auto).
# Não lê nem grava arquivos; negá-la impediria o relatório de chegar.
REPORT_TOOLS = {"SubagentHandback"}
JOB_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
ORCHESTRATOR = "orchestrator"


class Deny(Exception):
    pass


# ------------------------------------------------------------------ caminhos

def _parts(path: str):
    return [p for p in re.split(r"[\\/]+", path) if p]


def _is_link(path: str) -> bool:
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    return bool(isjunction and isjunction(path))


def canonical(raw, cwd: str | None) -> str:
    """Caminho canônico relativo à raiz, com '/', ou Deny."""
    if not isinstance(raw, str) or not raw:
        raise Deny("caminho ausente ou inválido")
    if "\x00" in raw:
        raise Deny("caminho com NUL")
    if raw.replace("/", "\\").startswith(("\\\\?\\", "\\\\.\\")):
        raise Deny("prefixo de dispositivo (\\\\?\\ ou \\\\.\\) não é aceito")
    if ":" in re.sub(r"^[A-Za-z]:", "", raw):
        raise Deny("':' fora da letra de unidade (alternate data stream)")
    for candidate in (raw, urllib.parse.unquote(raw)):
        if ".." in _parts(candidate):
            raise Deny("componente '..' não é aceito")

    base = cwd or os.environ.get("CLAUDE_PROJECT_DIR") or str(ROOT)
    absolute = os.path.normpath(os.path.join(base, raw))
    root_abs = os.path.normpath(str(ROOT))
    root_real = os.path.realpath(root_abs)

    rel = None
    for root in (root_abs, root_real):
        try:
            candidate = os.path.relpath(absolute, root)
        except ValueError:  # outra unidade no Windows
            continue
        if candidate == "." or not _parts(candidate)[0] == "..":
            rel, anchor = candidate, root
            break
    if rel is None:
        raise Deny("fora da raiz do repositório")

    current = anchor
    for part in _parts(rel):
        if part == ".":
            continue
        current = os.path.join(current, part)
        if not os.path.lexists(current):
            break
        if _is_link(current):
            raise Deny("symlink ou junction no caminho")

    real = os.path.realpath(absolute)
    try:
        real_rel = os.path.relpath(real, root_real)
    except ValueError:
        raise Deny("fora da raiz do repositório") from None
    real_parts = _parts(real_rel)
    if real_parts[:1] == [".."]:
        raise Deny("fora da raiz do repositório")
    return "/".join(p for p in real_parts if p != ".")


def matches(rel: str, pattern: str) -> bool:
    """Casa caminho relativo com padrão por componente: '*' dentro do componente, '**' em vários."""
    path = [os.path.normcase(p) for p in rel.split("/") if p]
    pat = [os.path.normcase(p) for p in pattern.split("/") if p]

    def walk(i: int, j: int) -> bool:
        if j == len(pat):
            return i == len(path)
        if pat[j] == "**":
            return any(walk(k, j + 1) for k in range(i, len(path) + 1))
        return i < len(path) and fnmatch.fnmatchcase(path[i], pat[j]) and walk(i + 1, j + 1)

    return walk(0, 0)


# -------------------------------------------------------------------- regras

def load_host() -> dict:
    return json.loads(HOST_FILE.read_text(encoding="utf-8"))


def active_job(host: dict):
    path = ROOT / host["active_job_file"]
    if not path.is_file():
        return None
    job = path.read_text(encoding="utf-8").strip()
    return job if JOB_RE.fullmatch(job) and job not in (".", "..") else None


def expand(patterns, job):
    return [p.replace("{job}", job) for p in patterns]


def decide(event: dict, host: dict):
    """Devolve (papel, decisão, motivo, alvo). Decisão: allow, deny ou pass."""
    agent_type = event.get("agent_type") or ""
    subagents = host["subagents"]
    if not agent_type:
        role = ORCHESTRATOR
    elif agent_type in subagents:
        role = agent_type
    else:
        return f"desconhecido:{agent_type}", "deny", "agent_type fora do host.yaml", None

    tool = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tool_input, dict):
        raise Deny("entrada sem tool_name ou tool_input válidos")
    job = active_job(host)
    is_sub = role != ORCHESTRATOR

    if is_sub and job is None:
        return role, "deny", "nenhuma tarefa ativa em runs/.active", None

    if tool in AGENT_TOOLS:
        target = tool_input.get("subagent_type")
        if is_sub:
            return role, "deny", "subagente não lança subagentes", target
        if isinstance(target, str) and target in subagents:
            return role, "allow", "subagente nomeado do Studio", target
        return role, "deny", "só os subagentes studio-* podem ser lançados", target

    if tool in PATH_FIELDS:
        field = PATH_FIELDS[tool]
        if field not in tool_input:
            raise Deny(f"{tool} sem o campo {field}")
        raw = tool_input[field]
        try:
            rel = canonical(raw, event.get("cwd"))
        except Deny as exc:
            return role, "deny", str(exc), raw
        if matches(rel, host["tool_log"]) and tool in WRITE_TOOLS:
            return role, "deny", "o tool-log não é gravável por ferramenta", rel
        kind = "write" if tool in WRITE_TOOLS else "read"
        if not is_sub and job is None:
            if any(matches(rel, p) for p in host[kind][ORCHESTRATOR] if "{job}" not in p):
                return role, "allow", f"{kind} do orquestrador sem tarefa ativa", rel
            return role, "pass", "orquestrador sem tarefa ativa: fluxo normal de permissões", rel
        if not is_sub and kind == "write":
            if any(matches(rel, p) for p in expand(host["write"].get("orchestrator_except", []), job)):
                return role, "deny", "o orquestrador não grava aqui", rel
        if any(matches(rel, p) for p in expand(host[kind].get(role, []), job)):
            return role, "allow", f"{kind} dentro do escopo do papel", rel
        return role, "deny", f"{kind} fora do escopo do papel", rel

    if tool in REPORT_TOOLS and is_sub:
        return role, "allow", "entrega do relatório do subagente", None
    if is_sub:
        return role, "deny", f"{tool} não é permitido a subagentes", None
    return role, "pass", "orquestrador: ferramenta sem confinamento por caminho (registrada)", None


# ----------------------------------------------------------------------- log

def write_log(host, event, job, role, decision, reason, target) -> bool:
    try:
        path = ROOT / host["tool_log"]
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"),
            "job": job,
            "agent_id": event.get("agent_id"),
            "agent_type": event.get("agent_type"),
            "role": role,
            "tool": event.get("tool_name"),
            "target": target,
            "decision": decision,
            "reason": reason,
        }
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return True
    except Exception:
        return False


def emit(decision: str, reason: str) -> None:
    if decision == "pass":
        return
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"[studio-guard] {reason}",
    }}
    # ASCII puro em bytes: no Windows o stdout em pipe não é UTF-8.
    sys.stdout.buffer.write((json.dumps(out, ensure_ascii=True) + "\n").encode("ascii"))
    sys.stdout.flush()


def main() -> int:
    event, host, job = {}, None, None
    try:
        host = load_host()
        job = active_job(host)
        try:
            event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        except ValueError:
            raise Deny("entrada não é JSON válido") from None
        if not isinstance(event, dict):
            event = {}
            raise Deny("entrada não é um objeto JSON")
        role, decision, reason, target = decide(event, host)
    except Deny as exc:
        role, decision, reason, target = "?", "deny", str(exc), None
    except Exception as exc:
        role, decision, reason, target = "?", "deny", f"erro interno do guard ({type(exc).__name__})", None

    if host is not None:
        logged = write_log(host, event, job, role, decision, reason, target)
        if not logged and role != ORCHESTRATOR and decision != "deny":
            decision, reason = "deny", "falha ao gravar o tool-log"
    emit(decision, reason)
    return 0


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        emit("deny", "erro fatal do guard")
    sys.exit(0)
