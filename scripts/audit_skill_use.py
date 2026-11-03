#!/usr/bin/env python3
"""Audit *per-agent, per-round* allowed Read requests for routed compiled skills.

Usage:
  python scripts/audit_skill_use.py --route runs/<job>/skill-plan.json \
    --agents runs/<job>/agent-ids.json --log runs/tool-log.jsonl --job <job>

Requires a JSON agent map:
  {"rounds": [{"round": 1, "agents": {"strategist": "<agent_id>", "writer": "<agent_id>", "critic": "<agent_id>"}}]}

Important: Claude Code PreToolUse logs a Read *request* and permission decision,
not tool completion or mental application. This audit must NEVER claim a successful
read or high-quality use of the skill. A reported read from an agent is weaker still.
Portable hosts with injected source excerpts need a separately recorded handoff.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NATIVE_ROLES = {"strategist": "studio-strategist", "writer": "studio-writer", "critic": "studio-critic"}


def audit(route: dict, agent_map: dict, log: list[dict], job: str) -> dict:
    manifest = route.get("skill_manifest")
    if route.get("status") != "ROUTED" or route.get("owner") != "studio" or not isinstance(manifest, dict):
        raise ValueError("Expected a ROUTED Studio manifest with skill_manifest")
    rounds = agent_map.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise ValueError("Expected at least one round in agent map")
    result = []
    seen = set()
    for round_info in rounds:
        num, ids = round_info.get("round"), round_info.get("agents")
        if not isinstance(num, int) or num < 1 or num in seen or not isinstance(ids, dict):
            raise ValueError("Invalid, duplicate or missing round/agents")
        seen.add(num)
        for role, refs in manifest.items():
            if role not in NATIVE_ROLES or not isinstance(refs, list):
                raise ValueError("Unexpected role or refs in skill manifest")
            if role == "strategist" and not route.get("strategist"):
                raise ValueError("Strategist refs configured when role disabled")
            agent_id = ids.get(role)
            if not isinstance(agent_id, str) or not agent_id.strip():
                raise ValueError(f"Missing agent id for round {num}: {role}")
            for ref in refs:
                path = ref.get("path")
                if not isinstance(path, str) or not path.startswith("compiled/"):
                    raise ValueError("Invalid compiled skill path")
                observed = any(
                    event.get("job") == job
                    and event.get("agent_id") == agent_id
                    and event.get("agent_type") == NATIVE_ROLES[role]
                    and event.get("tool") == "Read"
                    and event.get("decision") == "allow"
                    and event.get("target") == path
                    for event in log
                )
                result.append({
                    "round": num, "role": role, "agent_id": agent_id,
                    "skill": ref.get("name"), "path": path,
                    "evidence": "allowed-read-request" if observed else "not-observed",
                    "verified_tool_completion": False,
                    "verified_editorial_application": False,
                })
    return {
        "job": job,
        "checked": len(result),
        "observed_allowed_requests": sum(r["evidence"] == "allowed-read-request" for r in result),
        "missing": sum(r["evidence"] == "not-observed" for r in result),
        "evidence_limit": "PreToolUse proves an allowed Read request only; it does not prove file content was received or applied.",
        "entries": result,
    }


def read_jsonl(path: Path) -> list[dict]:
    output = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("Log entry must be an object")
            output.append(record)
    return output


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--route", required=True)
    p.add_argument("--agents", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--job", required=True)
    args = p.parse_args(argv)
    try:
        route = json.loads(Path(args.route).read_text(encoding="utf-8"))
        agent_map = json.loads(Path(args.agents).read_text(encoding="utf-8"))
        result = audit(route, agent_map, read_jsonl(Path(args.log)), args.job)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
