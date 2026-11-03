#!/usr/bin/env python3
"""Roteador determinístico do Marketing Content Studio (sem LLM).

  python scripts/route.py --persona <p> --brand <b> --channel <c> --intent <i>

Use "-" para campo que não se aplica. Lê catalog/routing.yaml e catalog/skills.yaml (sintaxe
JSON) e imprime JSON com owner, status, rule_id, intent, fidelity, strategist, research_skill,
skills {papel: [caminhos compilados]}, skill_manifest {papel: [refs/sha/foco]},\nresearch_manifest, max_rounds e reason.

Exit 0 para ROUTED, BLOCKED e NEEDS_OPERATOR; 2 para erro de uso; 3 para catálogo inválido.
Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("persona", "brand", "channel")


class CatalogError(Exception):
    pass


def load(root: Path):
    try:
        routing = json.loads((root / "catalog/routing.yaml").read_text(encoding="utf-8"))
        skills = json.loads((root / "catalog/skills.yaml").read_text(encoding="utf-8"))["skills"]
    except (OSError, ValueError, KeyError) as exc:
        raise CatalogError(f"catálogo ilegível: {exc}") from None
    return routing, skills


def normalize(kind: str, value, aliases: dict):
    if value is None:
        return None
    value = value.strip().lower()
    if value in ("", "-"):
        return None
    for canonical, names in aliases.get(kind, {}).items():
        if value in (n.lower() for n in names):
            return canonical
    return value


def compiled_path(name: str, role: str, skills: dict, root: Path) -> str:
    spec = skills.get(name)
    if spec is None:
        raise CatalogError(f"skill {name!r} não existe em skills.yaml")
    if not spec.get("loadable"):
        raise CatalogError(f"skill {name!r} não é carregável: {spec.get('reason', '')}")
    if role not in spec.get("roles", []):
        raise CatalogError(f"skill {name!r} não serve ao papel {role!r}")
    if not spec.get("compiled") or not (root / spec["compiled"]).is_file():
        raise CatalogError(f"compilado de {name!r} não existe: {spec.get('compiled')}")
    return spec["compiled"]


def section_ranges(content: str, headings: list[str]) -> list[dict]:
    """Precise 1-based Markdown section spans, excluding fenced-code fake headings."""
    lines = content.splitlines()
    sections = []
    fence = None
    for index, line in enumerate(lines):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            continue
        if fence:
            continue
        m = re.match(r"^(#{1,6}) (.+)$", line)
        if m:
            sections.append((line, index + 1, len(m.group(1))))
    output = []
    for wanted in headings:
        hits = [i for i, v in enumerate(sections) if v[0] == wanted]
        if len(hits) != 1:
            raise CatalogError(f"heading ausente/ambíguo: {wanted!r} ({len(hits)})")
        i = hits[0]
        _, start, level = sections[i]
        next_starts = [n for _, n, lev in sections[i + 1:] if lev <= level]
        end = (next_starts[0] - 1) if next_starts else len(lines)
        output.append({"heading": wanted, "start_line": start, "end_line": end})
    return output


def skill_ref(name: str, role: str, skills: dict, root: Path) -> dict:
    """Pinned, role-scoped reading plan. This is an assignment, not evidence of a tool read."""
    path = compiled_path(name, role, skills, root)
    spec = skills[name]
    headings = spec.get("focus", {}).get(role)
    if not isinstance(headings, list) or not headings or len(set(headings)) != len(headings):
        raise CatalogError(f"skill {name!r} sem foco válido para {role!r}")
    data = (root / path).read_bytes()
    content = data.decode("utf-8")
    try:
        ranges = section_ranges(content, ["## Studio operating rules (read first)", *headings])
    except CatalogError as exc:
        raise CatalogError(f"{path}: {exc}") from exc
    return {
        "name": name,
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "focus": headings,
        "sections": ranges,
    }


def render_skill_context(refs: list[dict], root: Path = REPO_ROOT) -> list[dict]:
    """Build exact source excerpts once for each role, without interpretation by an LLM."""
    out = []
    trusted = (root / "compiled").resolve()
    for ref in refs:
        rel = ref.get("path", "")
        if not isinstance(rel, str) or not rel.startswith("compiled/"):
            raise CatalogError("Skill context path must live under compiled/")
        file = (root / rel).resolve()
        if not file.is_relative_to(trusted) or not file.is_file():
            raise CatalogError(f"Invalid compiled source path: {rel}")
        raw = file.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != ref.get("sha256"):
            raise CatalogError(f"Compiled source changed since routing: {rel}")
        lines = raw.decode("utf-8").splitlines()
        sections = []
        for section in ref.get("sections", []):
            start, end, heading = section["start_line"], section["end_line"], section["heading"]
            if (not isinstance(start, int) or not isinstance(end, int)
                    or start < 1 or end > len(lines) or start > end
                    or lines[start - 1] != heading):
                raise CatalogError(f"Invalid section range for {rel}: {heading}")
            sections.append({**section, "excerpt": "\n".join(lines[start - 1:end])})
        if not sections:
            raise CatalogError(f"Missing sections for skill {rel}")
        out.append({"name": ref["name"], "path": rel, "sha256": actual_sha, "sections": sections})
    return out


def route(persona, brand, channel, intent, root: Path = REPO_ROOT) -> dict:
    routing, skills = load(root)
    aliases = routing.get("aliases", {})
    values = {
        "persona": normalize("persona", persona, aliases),
        "brand": normalize("brand", brand, aliases),
        "channel": normalize("channel", channel, aliases),
    }
    intent = normalize("intent", intent, aliases)

    rule = next((r for r in routing["owner_rules"]
                 if all(values.get(k) == v for k, v in r.get("match", {}).items())), None)
    if rule is None:
        raise CatalogError("nenhuma owner_rule casou; falta a regra default")

    out = {"owner": rule.get("owner"), "status": rule["status"], "rule_id": rule["id"], "intent": intent,
           "fidelity": None, "strategist": False, "research_skill": None, "skills": {},
           "skill_manifest": {}, "research_manifest": None,
           "max_rounds": routing.get("max_rounds", 3), "reason": rule.get("reason", "")}
    if rule.get("owner") != "studio" or rule["status"] != "ROUTED":
        return out

    spec = routing.get("intents", {}).get(intent) if intent else None
    if spec is None:
        out.update(status="NEEDS_OPERATOR",
                   reason="intent ausente" if not intent else f"intent desconhecida: {intent!r}")
        return out
    if spec.get("status") == "BLOCKED":
        out.update(status="BLOCKED", reason=spec.get("reason", "intent bloqueada"))
        return out

    research = spec.get("research_skill")
    out.update(
        fidelity=spec.get("fidelity"),
        strategist=bool(spec.get("strategist")),
        research_skill=compiled_path(research, "strategist", skills, root) if research else None,
        skills={role: [compiled_path(s, role, skills, root) for s in names]
                for role, names in sorted(spec.get("skills", {}).items())},
        skill_manifest={role: [skill_ref(s, role, skills, root) for s in names]
                        for role, names in sorted(spec.get("skills", {}).items())},
        research_manifest=skill_ref(research, "strategist", skills, root) if research else None,
        max_rounds=spec.get("max_rounds", out["max_rounds"]),
        reason=f"{rule.get('reason', '')}; intent {intent}",
    )
    if out["strategist"] and "strategist" not in out["skills"]:
        raise CatalogError(f"intent {intent!r} usa Strategist sem skills de strategist")
    return out


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Roteador determinístico do Studio.")
    for name in (*FIELDS, "intent"):
        parser.add_argument(f"--{name}", default="-", help='valor ou "-" (não se aplica)')
    parser.add_argument("--with-skill-context", action="store_true",
                        help="include exact role-scoped source excerpts, not only paths/hashes")
    parser.add_argument("--research", action="store_true",
                        help="include DeerFlow research excerpts only when the operator requested research")
    args = parser.parse_args(argv)
    try:
        result = route(args.persona, args.brand, args.channel, args.intent)
        if args.with_skill_context and result["status"] == "ROUTED" and result["owner"] == "studio":
            result["skill_context"] = {
                role: render_skill_context(refs) for role, refs in result["skill_manifest"].items()
            }
            if args.research and result["research_manifest"] is not None:
                result["research_context"] = render_skill_context([result["research_manifest"]])
    except CatalogError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
