#!/usr/bin/env python3
"""Gera AGENTS.md, o arquivo central do Studio (ADR-20).

  python scripts/build_agents.py           grava AGENTS.md
  python scripts/build_agents.py --check   falha se AGENTS.md estiver desatualizado

Fontes canônicas: agents/*.md e catalog/*.yaml. AGENTS.md nunca é editado à mão.
Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = "AGENTS.md"
BANNER = "<!-- Gerado por scripts/build_agents.py a partir de agents/ e catalog/. Não edite à mão. -->"
SKILL_NOTE = "A role's skills are the files under `compiled/`, for example `corey/social` is `compiled/corey/social.md`."


def read(repo: Path, rel: str) -> str:
    return (repo / rel).read_text(encoding="utf-8").replace("\r\n", "\n").strip()


def demote(text: str) -> str:
    """Desce um nível nos títulos, fora de blocos de código."""
    out, fence = [], None
    for line in text.split("\n"):
        mark = re.match(r"^(`{3,})", line)
        if mark:
            if fence is None:
                fence = mark.group(1)
            elif line.strip() == fence:
                fence = None
        out.append("#" + line if fence is None and re.match(r"^#{1,5} ", line) else line)
    return "\n".join(out)


def names(items: list[str]) -> str:
    return ", ".join(f"`{i}`" for i in items) if items else "none"


def routing(catalog: dict, skill_catalog: dict) -> str:
    lines = ["## Routing", ""]
    lines.append("If you have a shell, run this and follow its JSON exactly; use `-` for a field that does not apply:")
    lines += ["", "```", "python scripts/route.py --persona <persona> --brand <brand> --channel <channel> --intent <intent>", "```", ""]
    lines += ["Without a shell, apply the tables below, which come from the same catalog. Never change a route by judgment.", ""]

    lines += ["**Aliases.** Normalize these values first, ignoring case:", ""]
    for field, groups in catalog["aliases"].items():
        for canon, values in groups.items():
            lines.append(f"- {field} `{canon}`: {', '.join(values)}")
    lines.append("")

    lines += ["**Owner rules.** The first match wins:", ""]
    for n, rule in enumerate(catalog["owner_rules"], 1):
        match = " and ".join(f"{k} is `{v}`" for k, v in rule["match"].items()) or "anything else"
        owner = f"owner `{rule['owner']}`" if rule["owner"] else "no owner yet"
        result = f"{owner}, status `{rule['status']}`"
        lines.append(f"{n}. {match}: {result}. {rule['reason']}.")
    lines.append("")
    lines += [
        "- Owner `brain`: start no sub-agent. Tell the operator this belongs to the X Content Brain and must run in a Brain session.",
        "- `NEEDS_OPERATOR` or `BLOCKED`: show the reason to the operator and stop.",
        "- Owner `studio`: run the loop with the intent's row below.",
        "",
    ]

    lines += ["**Intents.** " + SKILL_NOTE, ""]
    lines += ["| Intent | Fidelity | Strategist | Research skill | Strategist skills | Writer skills | Critic reference skills |"]
    lines += ["|---|---|---|---|---|---|---|"]
    blocked = []
    for intent, spec in catalog["intents"].items():
        if spec.get("status") == "BLOCKED":
            blocked.append(f"- `{intent}` is `BLOCKED`: {spec['reason']}.")
            continue
        skills = spec["skills"]
        lines.append(
            f"| `{intent}` | `{spec['fidelity']}` | {'yes' if spec['strategist'] else 'no'} "
            f"| {names([spec['research_skill']] if spec['research_skill'] else [])} "
            f"| {names(skills.get('strategist', []))} | {names(skills.get('writer', []))} "
            f"| {names(skills.get('critic', []))} |"
        )
    lines += ["", *blocked, f"- `max_rounds`: {catalog['max_rounds']}.", ""]
    lines += [
        "**Skill reading plan (mandatory, role-scoped).** For each routed skill, read the",
        "`## Studio operating rules (read first)` section plus the focus sections below.",
        "Read additional sections/references only when specifically relevant to the deliverable.",
        "A skill path in this table is NOT evidence that an agent read the file.",
        "",
        "| Skill | Role | Focus sections |",
        "|---|---|---|",
    ]
    for name, spec in skill_catalog["skills"].items():
        if not spec.get("loadable"):
            continue
        for role in spec["roles"]:
            sections = spec.get("focus", {}).get(role, [])
            focus = "; ".join(sections) if sections else "MISSING"
            lines.append(f"| `{name}` | `{role}` | {focus} |")
    return "\n".join(lines)


def build(repo: Path = REPO_ROOT) -> str:
    catalog = json.loads(read(repo, "catalog/routing.yaml"))
    skill_catalog = json.loads(read(repo, "catalog/skills.yaml"))
    parts = [BANNER, read(repo, "agents/boot.md"), routing(catalog, skill_catalog)]
    parts += [demote(read(repo, f"agents/{role}.md")) for role in ("orchestrator", "strategist", "writer", "critic")]
    return "\n\n".join(parts) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="só confere; não grava")
    args = parser.parse_args(argv)
    path = REPO_ROOT / TARGET
    text = build()
    if args.check:
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != text:
            print(f"ERRO: {TARGET} desatualizado. Rode: python scripts/build_agents.py")
            return 1
        print(f"OK: {TARGET} confere com agents/ e catalog/.")
        return 0
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"OK: {TARGET} gravado ({len(text.encode('utf-8'))} bytes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
