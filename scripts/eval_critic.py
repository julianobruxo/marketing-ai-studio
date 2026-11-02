#!/usr/bin/env python3
"""Avaliação reproduzível do Critic (ADR-21).

  python scripts/eval_critic.py pack --cases tests/critic/cases.json --out <pasta>
      grava um pacote cego: contrato atual + casos, sem o resultado esperado.
  python scripts/eval_critic.py score --cases tests/critic/cases.json --verdicts <arquivo> [--labels <arquivo>]
      pontua os vereditos de forma determinística. Com --labels, mede também categoria,
      diagnóstico e severidade, a partir de um alinhamento adjudicado por caso.
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


def findings(verdict) -> list:
    """Achados numerados. No formato antigo, evidência em gate reprovado equivale a blocking."""
    found = []
    for gate in gates_of(verdict or []):
        for item in gate.get("evidence", []):
            severity = item.get("severity") or ("blocking" if gate.get("status") in BLOCKING else None)
            found.append({"gate": gate.get("gate"), "status": gate.get("status"), "severity": severity,
                          "quote": item.get("quote", ""), "issue": item.get("issue", "")})
    return found


def outcome(verdict) -> str:
    return "reject" if any(g.get("status") in BLOCKING for g in gates_of(verdict)) else "pass"


def rejected_only_on_facts(verdict) -> bool:
    gates = [g.get("gate") for g in gates_of(verdict) if g.get("status") in BLOCKING]
    return bool(gates) and all(gate == "facts" for gate in gates)


def flagged(verdict) -> bool:
    """O Critic apontou algo que importa, mesmo sem reprovar. Não diz se é o problema certo."""
    return outcome(verdict) == "reject" or (isinstance(verdict, dict) and verdict.get("decision") == "IMPROVE")


def overlaps(target: str, quote: str) -> bool:
    """A citação cobre o alvo, ou cobre ao menos metade dele. Citação curta não ganha crédito."""
    target, quote = target.casefold(), quote.casefold()
    return bool(quote) and (target in quote or (quote in target and len(quote) * 2 >= len(target)))


def contains(needle: str, texts: list) -> bool:
    return any(needle.casefold() in text.casefold() for text in texts if text)


def expected_category(case: dict):
    return case["expected"].get("category")


def score_case(case: dict, verdict, label=None) -> dict:
    expected = case["expected"]
    got = outcome(verdict) if verdict else "missing"
    row = {"id": case["id"], "expected": expected["verdict"], "got": got, "verdict_ok": expected["verdict"] == got,
           "flagged": bool(verdict) and flagged(verdict), "needs_context": bool(expected.get("needs_context"))}
    target = expected.get("target")
    if target and target != case.get("candidate"):
        quotes = [f["quote"] for f in findings(verdict) if f["status"] in BLOCKING]
        row["target_ok"] = any(overlaps(target, quote) for quote in quotes)
    if expected.get("keep"):
        kept = verdict.get("keep", []) if isinstance(verdict, dict) else []
        row["keep_ok"] = contains(expected["keep"], list(kept))
    if expected["verdict"] == "pass" and got == "reject":
        row["fact_dissent"] = rejected_only_on_facts(verdict)
    if label is not None and expected["verdict"] == "reject":
        items = findings(verdict)
        match = label.get("match")
        found = items[match] if isinstance(match, int) and 0 <= match < len(items) else None
        row["category_ok"] = bool(found) and bool(label.get("category"))
        row["diagnosis"] = label.get("diagnosis", "none") if found else "none"
        wanted = expected.get("severity", "blocking")
        row["severity_ok"] = bool(found) and (found["severity"] == "blocking" or
                                              (wanted == "material" and found["severity"] == "material"))
    return row


def tally(rows: list) -> dict:
    def count(key, value=True):
        marked = [r for r in rows if key in r]
        return {"ok": sum(1 for r in marked if r[key] == value), "total": len(marked)}
    rejects = [r for r in rows if r["expected"] == "reject"]
    passes = [r for r in rows if r["expected"] == "pass"]
    return {
        "verdict": count("verdict_ok"),
        "caught": {"ok": sum(1 for r in rejects if r["got"] == "reject"), "total": len(rejects)},
        "flagged": {"ok": sum(1 for r in rejects if r["flagged"]), "total": len(rejects)},
        "target": count("target_ok"),
        "category": count("category_ok"),
        "aligned": count("diagnosis", "aligned"),
        "partial": count("diagnosis", "partial"),
        "severity": count("severity_ok"),
        "keep": count("keep_ok"),
        "false_fail": {"bad": sum(1 for r in passes if r["got"] == "reject" and not r.get("fact_dissent")),
                       "total": len(passes)},
        "fact_dissent": {"bad": sum(1 for r in passes if r.get("fact_dissent")), "total": len(passes)},
    }


def score(cases: list, verdicts: dict, labels=None) -> dict:
    labels = labels or {}
    rows = [score_case(case, verdicts.get(case["id"]), labels.get(case["id"])) for case in cases]
    result = tally(rows)
    result["rows"] = rows
    result["without_context_cases"] = tally([r for r in rows if not r["needs_context"]])
    return result


def line(result: dict) -> str:
    def pair(key):
        return f"{result[key]['ok']}/{result[key]['total']}"
    def bad(key):
        return f"{result[key]['bad']}/{result[key]['total']}"
    text = (f"veredito {pair('verdict')} | reprovou {pair('caught')} | sinalizou {pair('flagged')} | "
            f"trecho {pair('target')} | categoria {pair('category')} | diagnóstico alinhado {pair('aligned')} "
            f"(parcial {pair('partial')}) | severidade {pair('severity')} | keep {pair('keep')} | "
            f"falso FAIL {bad('false_fail')} | objeção factual a texto aprovado {bad('fact_dissent')}")
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--cases", required=True)
    s.add_argument("--verdicts", required=True)
    s.add_argument("--labels", help="alinhamento adjudicado: caso -> match, category, diagnosis")
    c = sub.add_parser("compare")
    c.add_argument("--cases", required=True)
    c.add_argument("--before", required=True)
    c.add_argument("--after", required=True)
    c.add_argument("--labels-before")
    c.add_argument("--labels-after")
    args = parser.parse_args(argv)
    cases = load(args.cases)
    if args.command == "pack":
        pack(cases, Path(args.out))
        print(f"OK: {len(cases)} caso(s) em {args.out}")
    elif args.command == "score":
        result = score(cases, load(args.verdicts), load(args.labels) if args.labels else None)
        for row in result["rows"]:
            print(row)
        print(line(result))
        print("sem casos que exigem contexto: " + line(result["without_context_cases"]))
    else:
        before = score(cases, load(args.before), load(args.labels_before) if args.labels_before else None)
        after = score(cases, load(args.after), load(args.labels_after) if args.labels_after else None)
        print("antes:  " + line(before))
        print("depois: " + line(after))
        print("antes, sem casos que exigem contexto:  " + line(before["without_context_cases"]))
        print("depois, sem casos que exigem contexto: " + line(after["without_context_cases"]))
        for a, b in zip(before["rows"], after["rows"]):
            if a != b:
                print(f"{a['id']}: {a} -> {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
