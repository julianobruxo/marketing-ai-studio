#!/usr/bin/env python3
"""Roteador determinístico do Marketing Content Studio (sem LLM).

  python scripts/route.py --persona <p> --brand <b> --channel <c> --intent <i>

Use "-" para campo que não se aplica. Lê catalog/routing.yaml e catalog/skills.yaml (sintaxe
JSON) e imprime JSON com owner, status, rule_id, intent, fidelity, strategist, research_skill,
skills {papel: [caminhos compilados]}, max_rounds e reason.

Exit 0 para ROUTED, BLOCKED e NEEDS_OPERATOR; 2 para erro de uso; 3 para catálogo inválido.
Só biblioteca padrão.
"""

from __future__ import annotations

import argparse
import json
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
    args = parser.parse_args(argv)
    try:
        result = route(args.persona, args.brand, args.channel, args.intent)
    except CatalogError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
