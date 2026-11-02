#!/usr/bin/env python3
"""Avaliação reproduzível do Critic (ADR-21).

  python scripts/eval_critic.py pack --cases tests/critic/cases.json --out <pasta>
      grava um pacote cego: contrato atual + casos, sem o resultado esperado.
  python scripts/eval_critic.py score --cases tests/critic/cases.json --verdicts <arquivo>
      pontua os vereditos de forma determinística.
  python scripts/eval_critic.py compare --cases tests/critic/cases.json --before <a> --after <b>
      compara duas execuções sobre os mesmos casos.

O modelo gera os vereditos; a pontuação não usa modelo. Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKING = {"FAIL", "UNVERIFIED"}


def load(path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pack(cases: list, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    blind = [{k: v for k, v in case.items() if k not in ("expected", "test")} for case in cases]
    (out / "cases.json").write_text(json.dumps(blind, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy(REPO_ROOT / "agents/critic.md", out / "contract.md")


def gates_of(verdict) -> list:
    return verdict["gates"] if isinstance(verdict, dict) else verdict


def outcome(verdict) -> str:
    return "reject" if any(g.get("status") in BLOCKING for g in gates_of(verdict)) else "pass"


def noticed(verdict) -> bool:
    """O Critic apontou algo que importa, mesmo sem reprovar (achado material)."""
    return outcome(verdict) == "reject" or (isinstance(verdict, dict) and verdict.get("decision") == "IMPROVE")


def quotes(verdict) -> list:
    found = []
    for gate in gates_of(verdict):
        if gate.get("status") in BLOCKING:
            found += [e.get("quote", "") for e in gate.get("evidence", [])]
    return found


def hits(needle: str, texts: list) -> bool:
    needle = needle.casefold()
    return any(t and (needle in t.casefold() or t.casefold() in needle) for t in texts)


def score_case(case: dict, verdict) -> dict:
    expected = case["expected"]
    result = {"id": case["id"], "expected": expected["verdict"], "got": outcome(verdict) if verdict else "missing"}
    result["verdict_ok"] = result["expected"] == result["got"]
    result["noticed"] = bool(verdict) and noticed(verdict)
    if expected.get("target") and result["got"] == "reject":
        result["target_ok"] = hits(expected["target"], quotes(verdict))
    elif expected.get("target"):
        result["target_ok"] = False
    if expected.get("keep"):
        kept = verdict.get("keep", []) if isinstance(verdict, dict) else []
        result["keep_ok"] = hits(expected["keep"], list(kept))
    return result


def score(cases: list, verdicts: dict) -> dict:
    rows = [score_case(case, verdicts.get(case["id"])) for case in cases]
    def count(key):
        marked = [r for r in rows if key in r]
        return {"ok": sum(1 for r in marked if r[key]), "total": len(marked)}
    rejects = [r for r in rows if r["expected"] == "reject"]
    passes = [r for r in rows if r["expected"] == "pass"]
    return {
        "rows": rows,
        "verdict": count("verdict_ok"),
        "caught": {"ok": sum(1 for r in rejects if r["got"] == "reject"), "total": len(rejects)},
        "false_fail": {"bad": sum(1 for r in passes if r["got"] == "reject"), "total": len(passes)},
        "noticed": {"ok": sum(1 for r in rejects if r["noticed"]), "total": len(rejects)},
        "noticed_on_good": {"bad": sum(1 for r in passes if r["noticed"]), "total": len(passes)},
        "target": count("target_ok"),
        "keep": count("keep_ok"),
    }


def line(result: dict) -> str:
    return (f"veredito {result['verdict']['ok']}/{result['verdict']['total']} | "
            f"pegou {result['caught']['ok']}/{result['caught']['total']} | "
            f"apontou o trecho certo {result['target']['ok']}/{result['target']['total']} | "
            f"falso FAIL {result['false_fail']['bad']}/{result['false_fail']['total']} | "
            f"notou {result['noticed']['ok']}/{result['noticed']['total']} | "
            f"apontou em texto bom {result['noticed_on_good']['bad']}/{result['noticed_on_good']['total']} | "
            f"keep {result['keep']['ok']}/{result['keep']['total']}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--cases", required=True)
    s.add_argument("--verdicts", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--cases", required=True)
    c.add_argument("--before", required=True)
    c.add_argument("--after", required=True)
    args = parser.parse_args(argv)
    cases = load(args.cases)
    if args.command == "pack":
        pack(cases, Path(args.out))
        print(f"OK: {len(cases)} caso(s) em {args.out}")
    elif args.command == "score":
        result = score(cases, load(args.verdicts))
        for row in result["rows"]:
            print(row)
        print(line(result))
    else:
        before, after = score(cases, load(args.before)), score(cases, load(args.after))
        print("antes:  " + line(before))
        print("depois: " + line(after))
        for a, b in zip(before["rows"], after["rows"]):
            if a != b:
                print(f"{a['id']}: {a} -> {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
