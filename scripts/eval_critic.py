#!/usr/bin/env python3
"""Avaliação reproduzível do Critic (ADR-21).

  python scripts/eval_critic.py pack --cases tests/critic/cases.json --out <pasta>
      grava um pacote cego: contrato atual + casos, sem o resultado esperado.
  python scripts/eval_critic.py score --cases tests/critic/cases.json --verdicts <arquivo> [--labels <arquivo>]
      pontua os vereditos de forma determinística. Com --labels, mede também categoria,
      diagnóstico e severidade, a partir de um alinhamento adjudicado por caso.
  python scripts/eval_critic.py score-doc --cases <private-cases> --verdicts <verdicts> --adjudications <adjudications>
      avalia comentários individuais em documentos completos, sem inferir semântica por substring.
  python scripts/eval_critic.py compare --cases tests/critic/cases.json --before <a> --after <b>
      compara duas execuções sobre os mesmos casos.

O modelo gera os vereditos; a pontuação não usa modelo. Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKING = {"FAIL", "UNVERIFIED"}


def load(path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# Explicitly allowed eval-pack fields. Never silently pass reviewer feedback to a Critic.
# Real review files may contain source_comment, labels, suggestions or author names.
PACK_FIELDS = ("id", "intent", "fidelity", "brief", "job_context", "inputs",
               "candidate", "original", "context", "research_notes",
               "previous_candidate", "keep", "selected_approach", "keep_exceptions")


def validate_keep_exceptions(case: dict) -> None:
    """Reject malformed preservation metadata before constructing a blind review packet."""
    if "keep_exceptions" not in case:
        return
    records = case["keep_exceptions"]
    if not isinstance(records, list):
        raise ValueError("keep_exceptions must be a list: " + str(case.get("id")))
    old_lines = case.get("keep", [])
    if not isinstance(old_lines, list) or any(not isinstance(line, str) for line in old_lines):
        raise ValueError("keep must be a list of lines: " + str(case.get("id")))
    seen = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("keep_exceptions entries must be objects")
        line = item.get("original_line")
        if not isinstance(line, str) or not line.strip() or line not in old_lines:
            raise ValueError("Exception must identify an exact prior keep line")
        if line in seen:
            raise ValueError("Duplicate keep_exceptions line")
        seen.add(line)
        if item.get("action") not in ("removed", "rewritten"):
            raise ValueError("Invalid keep exception action")
        if item.get("reason") not in ("factual", "blocking", "approach"):
            raise ValueError("Invalid keep exception reason")
        explanation = item.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("Keep exception must explain the change")
    if any(item["reason"] == "approach" for item in records):
        approach = case.get("selected_approach")
        if not isinstance(approach, str) or not approach.strip():
            raise ValueError("Approach exceptions require the selected approach summary")


def pack(cases: list, out: Path, contract=None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs")
    for case in cases:
        validate_keep_exceptions(case)
    blind = [{k: case[k] for k in PACK_FIELDS if k in case} for case in cases]
    (out / "cases.json").write_text(json.dumps(blind, ensure_ascii=False, indent=2), encoding="utf-8")
    source = Path(contract) if contract else REPO_ROOT / "agents/critic.md"
    shutil.copyfile(source, out / "contract.md")
    manifest = {
        "contract_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "case_ids": ids, "case_count": len(ids),
        "blind_fields": list(PACK_FIELDS),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


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



def score_document_case(case: dict, verdict, adjudication: dict) -> dict:
    """Score one entire document against individually adjudicated human review issues.

    No lexical matching is used to claim semantic alignment. A human or an
    independently isolated judge must supply a one-to-one finding mapping.
    """
    issues = [x for x in case["expected"].get("issues", []) if x.get("kind", "problem") == "problem"]
    ids = [x["id"] for x in issues]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate reviewer issue IDs in " + case["id"])
    matches = adjudication.get("matches", [])
    by_id = {x["issue_id"]: x for x in matches}
    if len(by_id) != len(matches) or set(by_id) != set(ids):
        raise ValueError("Adjudication must cover each reviewer issue exactly once: " + case["id"])
    predicted = findings(verdict) if verdict else []
    used = set()
    rows = []
    for issue in issues:
        m = by_id[issue["id"]]
        index = m.get("finding_index")
        if index is None:
            if m.get("diagnosis") != "missed":
                raise ValueError("Unmatched issue must be marked missed: " + issue["id"])
            rows.append({"issue_id": issue["id"], "diagnosis": "missed",
                         "category_ok": False, "severity_ok": False})
            continue
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(predicted):
            raise ValueError("Invalid finding index for " + issue["id"])
        if index in used:
            raise ValueError("One finding cannot explain two reviewer issues without separate adjudication")
        used.add(index)
        diagnosis = m.get("diagnosis")
        if diagnosis not in ("aligned", "partial", "different"):
            raise ValueError("Match requires aligned, partial or different: " + issue["id"])
        if not isinstance(m.get("category_ok"), bool) or not isinstance(m.get("severity_ok"), bool):
            raise ValueError("Match requires adjudicated category_ok and severity_ok: " + issue["id"])
        rows.append({"issue_id": issue["id"], "diagnosis": diagnosis,
                     "category_ok": m["category_ok"], "severity_ok": m["severity_ok"]})
    approved = case["expected"].get("document_approved") is True
    rejected = bool(verdict) and outcome(verdict) == "reject"
    return {
        "id": case["id"],
        "expected_issues": len(rows),
        "human_praise_count": sum(x.get("kind") == "praise" for x in case["expected"].get("issues", [])),
        "document_approved": approved,
        "rejected_approved_document": approved and rejected,
        "facts_only_objection_to_approved": approved and rejected and rejected_only_on_facts(verdict),
        "aligned": sum(x["diagnosis"] == "aligned" for x in rows),
        "partial": sum(x["diagnosis"] == "partial" for x in rows),
        "missed": sum(x["diagnosis"] == "missed" for x in rows),
        "different": sum(x["diagnosis"] == "different" for x in rows),
        "category_ok": sum(x["category_ok"] for x in rows),
        "severity_ok": sum(x["severity_ok"] for x in rows),
        "unmatched_findings": len(predicted) - len(used),
        "predicted_findings": len(predicted),
        "document_rejected": rejected,
    }


def score_documents(cases: list, verdicts: dict, adjudications: dict) -> dict:
    """Report document and issue metrics separately; no fabricated 'accuracy'."""
    rows = []
    for case in cases:
        if case["id"] not in adjudications:
            raise ValueError("Missing adjudication for document " + case["id"])
        rows.append(score_document_case(case, verdicts.get(case["id"]), adjudications[case["id"]]))
    keys = ("expected_issues", "aligned", "partial", "missed", "different",
            "category_ok", "severity_ok", "unmatched_findings", "predicted_findings",
            "human_praise_count", "document_approved", "rejected_approved_document",
            "facts_only_objection_to_approved")
    totals = {k: sum(r[k] for r in rows) for k in keys}
    totals["documents"] = len(rows)
    totals["documents_rejected"] = sum(r["document_rejected"] for r in rows)
    return {"rows": rows, "totals": totals}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--contract", help="frozen Critic contract; defaults to agents/critic.md")
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
    d = sub.add_parser("score-doc", help="adjudicated full-document issue recall; private inputs stay local")
    d.add_argument("--cases", required=True)
    d.add_argument("--verdicts", required=True)
    d.add_argument("--adjudications", required=True)
    args = parser.parse_args(argv)
    cases = load(args.cases)
    if args.command == "pack":
        pack(cases, Path(args.out), contract=args.contract)
        print(f"OK: {len(cases)} caso(s) em {args.out}")
    elif args.command == "score":
        result = score(cases, load(args.verdicts), load(args.labels) if args.labels else None)
        for row in result["rows"]:
            print(row)
        print(line(result))
        print("sem casos que exigem contexto: " + line(result["without_context_cases"]))
    elif args.command == "score-doc":
        result = score_documents(cases, load(args.verdicts), load(args.adjudications))
        t = result["totals"]
        print(f"documents {t['documents']} | rejected {t['documents_rejected']} | "
              f"human issues {t['expected_issues']} | aligned {t['aligned']} | "
              f"partial {t['partial']} | missed {t['missed']} | different {t['different']} | "
              f"category {t['category_ok']} | severity {t['severity_ok']} | "
              f"unmatched findings {t['unmatched_findings']} | "
              f"human praise {t['human_praise_count']} | "
              f"rejected approved docs {t['rejected_approved_document']} "
              f"(facts-only {t['facts_only_objection_to_approved']})")
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
