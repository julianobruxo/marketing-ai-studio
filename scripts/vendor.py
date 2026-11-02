#!/usr/bin/env python3
"""Vendor de skills upstream: importação com lock e verificação de integridade.

Subcomandos:
  sync    importa uma seleção de um commit exato do upstream para vendor/<fonte>/
          e reescreve provenance/upstream-lock.json (ADR-02). Nunca faz commit,
          push ou merge.
  verify  confere vendor/ contra o lock: hashes, arquivos sobrando ou faltando,
          LICENSE e links markdown relativos (T14).

Só biblioteca padrão. compile, overlays e ferramentas de host ficam para o PR 2.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_REL = "provenance/upstream-lock.json"
LOCK_VERSION = 1

# Fontes conhecidas. A seleção de cada uma vive no lock, não aqui.
SOURCES = {
    "corey": {
        "owner": "coreyhaines31",
        "repo": "marketingskills",
        "license": "LICENSE",
    },
}

SHA_RE = re.compile(r"[0-9a-f]{40}")


# ---------------------------------------------------------------- utilitários

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def repo_url(source: str) -> str:
    cfg = SOURCES[source]
    return f"https://github.com/{cfg['owner']}/{cfg['repo']}"


def load_lock(root: Path) -> dict:
    path = root / LOCK_REL
    if not path.exists():
        return {"lock_version": LOCK_VERSION, "sources": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def write_lock(root: Path, lock: dict) -> None:
    path = root / LOCK_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(lock, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_bytes(text.encode("utf-8"))


def parse_frontmatter(text: str) -> dict:
    """Lê o subconjunto de YAML usado no frontmatter das skills.

    Devolve chaves de topo e chaves aninhadas como "pai.filho" (ex.: metadata.version).
    """
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}
    body = lines[1:end]
    out: dict = {}
    parent = None
    i = 0
    while i < len(body):
        line = body[i]
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        indent, key, value = len(m.group(1)), m.group(2), m.group(3).strip()
        if indent == 0:
            parent = key if value == "" else None
            full = key
        else:
            full = f"{parent}.{key}" if parent else key
        if value in (">", ">-", "|", "|-"):
            block = []
            i += 1
            while i < len(body) and (body[i].startswith(" " * (indent + 1)) or body[i].strip() == ""):
                block.append(body[i].strip())
                i += 1
            sep = "\n" if value.startswith("|") else " "
            out[full] = sep.join(b for b in block if b).strip()
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value != "":
            out[full] = value
        i += 1
    return out


# --------------------------------------------------------- links em markdown

_FENCE_RE = re.compile(r"^ {0,3}(```|~~~)")
_INLINE_CODE_RE = re.compile(r"(`+)(?:.+?)\1")
_INLINE_LINK_RE = re.compile(
    r"!?\[(?:[^\]\\]|\\.)*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
_REF_DEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def markdown_links(text: str):
    """Gera (linha, alvo) dos links de um markdown, fora de blocos e trechos de código."""
    in_fence = None
    for lineno, line in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        fence = _FENCE_RE.match(line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
            elif fence.group(1) == in_fence:
                in_fence = None
            continue
        if in_fence:
            continue
        clean = _INLINE_CODE_RE.sub("", line)
        for m in _INLINE_LINK_RE.finditer(clean):
            yield lineno, m.group(1)
        ref = _REF_DEF_RE.match(clean)
        if ref:
            yield lineno, ref.group(1)


def relative_link_path(target: str):
    """Caminho local de um link relativo, ou None se o link é externo ou só âncora."""
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or target.startswith("#") or _SCHEME_RE.match(target):
        return None
    path = re.split(r"[#?]", target, maxsplit=1)[0]
    if not path:
        return None
    return urllib.parse.unquote(path)


def resolve_link(md_file: Path, link_path: str, boundary: Path):
    """Resolve o link a partir do arquivo; devolve (ok, motivo)."""
    if link_path.startswith("/"):
        return False, "caminho absoluto"
    resolved = Path(os.path.normpath(md_file.parent / link_path))
    try:
        resolved.relative_to(boundary)
    except ValueError:
        return False, "aponta para fora do vendor da fonte"
    if not resolved.exists():
        return False, "alvo inexistente"
    return True, ""


# ---------------------------------------------------------------------- sync

def fetch_tarball(source: str, sha: str, dest: Path) -> Path:
    cfg = SOURCES[source]
    url = f"https://codeload.github.com/{cfg['owner']}/{cfg['repo']}/tar.gz/{sha}"
    target = dest / f"{cfg['repo']}-{sha}.tar.gz"
    with urllib.request.urlopen(url, timeout=120) as resp, open(target, "wb") as fh:
        shutil.copyfileobj(resp, fh)
    return target


def select_members(tar: tarfile.TarFile, skills, extras, license_path):
    """Mapeia caminho upstream -> membro do tar, só para a seleção."""
    members = tar.getmembers()
    prefix = members[0].name.split("/")[0] + "/"
    by_path = {}
    for m in members:
        if m.name == prefix.rstrip("/"):
            continue
        if not m.name.startswith(prefix):
            raise SystemExit(f"tarball inesperado: membro fora da raiz: {m.name}")
        by_path[m.name[len(prefix):]] = m

    wanted = {}
    problems = []
    for skill in skills:
        base = f"skills/{skill}/"
        found = False
        for rel, m in by_path.items():
            if not rel.startswith(base):
                continue
            found = True
            if m.isdir():
                continue
            if not m.isfile():
                problems.append(f"{rel}: não é arquivo regular (link ou especial)")
                continue
            wanted[rel] = m
        if not found:
            problems.append(f"skill inexistente no upstream: skills/{skill}")
    for rel in list(extras) + [license_path]:
        m = by_path.get(rel)
        if m is None:
            problems.append(f"arquivo inexistente no upstream: {rel}")
        elif not m.isfile():
            problems.append(f"{rel}: não é arquivo regular (link ou especial)")
        else:
            wanted[rel] = m
    if problems:
        raise SystemExit("sync abortado:\n  " + "\n  ".join(problems))
    return prefix, wanted


def extract_selection(tar_path: Path, workdir: Path, skills, extras, license_path) -> Path:
    """Extrai só a seleção num diretório temporário; devolve a raiz do upstream extraído."""
    with tarfile.open(tar_path, "r:gz") as tar:
        prefix, wanted = select_members(tar, skills, extras, license_path)
        kwargs = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        tar.extractall(workdir, members=list(wanted.values()), **kwargs)
    return workdir / prefix.rstrip("/")


def reachable_from(start_files, graph):
    seen = set()
    stack = list(start_files)
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        stack.extend(graph.get(f, ()))
    return seen


def link_graph(upstream: Path, files):
    """Grafo de links relativos entre arquivos markdown da seleção (caminhos upstream)."""
    graph = {}
    for rel in files:
        if not rel.endswith(".md"):
            continue
        src = upstream / rel
        edges = set()
        for _, target in markdown_links(src.read_text(encoding="utf-8", errors="replace")):
            lp = relative_link_path(target)
            if lp is None or lp.startswith("/"):
                continue
            edges.add(posixpath.normpath(str(PurePosixPath(rel).parent / lp)))
        graph[rel] = edges
    return graph


def snapshot_descriptions(vendor_dir: Path, skills):
    out = {}
    for skill in skills:
        p = vendor_dir / "skills" / skill / "SKILL.md"
        if p.exists():
            out[skill] = parse_frontmatter(p.read_text(encoding="utf-8")).get("description")
    return out


def all_lock_files(entry: dict) -> dict:
    files = {}
    for skill in entry.get("skills", {}).values():
        files.update(skill.get("files", {}))
    for path, meta in entry.get("extra_files", {}).items():
        files[path] = meta["sha256"]
    lic = entry.get("license")
    if lic:
        files[lic["path"]] = lic["sha256"]
    return files


def cmd_sync(args) -> int:
    root = Path(args.root).resolve() if args.root else REPO_ROOT
    source = args.source
    if source not in SOURCES:
        raise SystemExit(f"fonte desconhecida: {source} (conhecidas: {', '.join(SOURCES)})")
    if not SHA_RE.fullmatch(args.ref):
        raise SystemExit("--ref precisa ser um SHA completo de 40 caracteres hexadecimais")
    cfg = SOURCES[source]

    lock = load_lock(root)
    old = lock.get("sources", {}).get(source)
    if args.skills or args.extra:
        skills = sorted(set(args.skills or []))
        extras = sorted(set(args.extra or []))
    elif old:
        skills = sorted(old["selection"]["skills"])
        extras = sorted(old["selection"]["extra_files"])
    else:
        raise SystemExit("primeira importação: informe a seleção com --skills e --extra")

    vendor_rel = PurePosixPath("vendor") / source
    vendor_dir = root / vendor_rel
    old_desc = snapshot_descriptions(vendor_dir, skills + (sorted(old["skills"]) if old else []))

    with tempfile.TemporaryDirectory(prefix="vendor-sync-") as tmp:
        tmp = Path(tmp)
        tar_path = fetch_tarball(source, args.ref, tmp)
        upstream = extract_selection(tar_path, tmp / "x", skills, extras, cfg["license"])

        selected = sorted(
            str(p.relative_to(upstream).as_posix()) for p in upstream.rglob("*") if p.is_file()
        )
        graph = link_graph(upstream, selected)

        entry = {
            "repo": repo_url(source),
            "commit": args.ref,
            "retrieved_at": (
                old["retrieved_at"]
                if old and old.get("commit") == args.ref
                else _dt.datetime.now(_dt.timezone.utc).date().isoformat()
            ),
            "license": {
                "upstream_path": cfg["license"],
                "path": str(vendor_rel / cfg["license"]),
                "sha256": sha256_file(upstream / cfg["license"]),
            },
            "selection": {"skills": skills, "extra_files": extras},
            "skills": {},
            "extra_files": {},
        }
        for skill in skills:
            base = f"skills/{skill}/"
            files = {
                str(vendor_rel / rel): sha256_file(upstream / rel)
                for rel in selected
                if rel.startswith(base)
            }
            fm = parse_frontmatter((upstream / base / "SKILL.md").read_text(encoding="utf-8")) \
                if (upstream / base / "SKILL.md").exists() else {}
            entry["skills"][skill] = {
                "upstream_path": f"skills/{skill}",
                "version": fm.get("metadata.version") or fm.get("version"),
                "reason": "selecionada",
                "files": files,
            }
        for rel in extras:
            required_by = sorted(
                skill for skill in skills
                if rel in reachable_from([f for f in selected if f.startswith(f"skills/{skill}/")], graph)
            )
            entry["extra_files"][str(vendor_rel / rel)] = {
                "upstream_path": rel,
                "sha256": sha256_file(upstream / rel),
                "reason": "transitiva",
                "required_by": required_by,
            }

        # Reescreve vendor/<fonte>/ só com a seleção, byte a byte.
        if vendor_dir.exists():
            shutil.rmtree(vendor_dir)
        for rel in selected:
            dest = vendor_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((upstream / rel).read_bytes())

    lock["lock_version"] = LOCK_VERSION
    lock.setdefault("sources", {})[source] = entry
    write_lock(root, lock)

    new_desc = snapshot_descriptions(vendor_dir, skills)
    print_sync_report(source, old, entry, old_desc, new_desc)
    return 0


def print_sync_report(source, old, new, old_desc, new_desc) -> None:
    old_files = all_lock_files(old) if old else {}
    new_files = all_lock_files(new)
    added = sorted(set(new_files) - set(old_files))
    removed = sorted(set(old_files) - set(new_files))
    changed = sorted(p for p in set(new_files) & set(old_files) if new_files[p] != old_files[p])

    print(f"sync {source}: {new['repo']} @ {new['commit']}")
    if old:
        print(f"  commit anterior: {old.get('commit')}")
    else:
        print("  primeira importação")
    print(f"  arquivos no vendor: {len(new_files)}")
    for label, items in (("adicionados", added), ("removidos", removed), ("alterados", changed)):
        print(f"  {label}: {len(items)}")
        for p in items:
            print(f"    {p}")

    versions = []
    for skill, meta in sorted(new["skills"].items()):
        before = (old or {}).get("skills", {}).get(skill, {}).get("version")
        if before != meta["version"]:
            versions.append(f"    {skill}: {before} -> {meta['version']}")
    print(f"  versões alteradas: {len(versions)}")
    for v in versions:
        print(v)

    descs = []
    for skill in sorted(set(old_desc) | set(new_desc)):
        if old_desc.get(skill) != new_desc.get(skill):
            descs.append(skill)
    print(f"  descriptions alteradas: {len(descs)}")
    for skill in descs:
        if old_desc.get(skill) is None:
            print(f"    {skill}: nova")
            continue
        print(f"    {skill}")
        print(f"      antes:  {old_desc.get(skill)}")
        print(f"      depois: {new_desc.get(skill)}")
    print("  nenhum commit, push ou merge foi feito. Rode `vendor.py verify` antes de commitar.")


# -------------------------------------------------------------------- verify

def cmd_verify(args) -> int:
    root = Path(args.root).resolve() if args.root else REPO_ROOT
    problems = []
    lock_path = root / LOCK_REL
    if not lock_path.exists():
        print(f"FALHA: lock ausente: {LOCK_REL}")
        return 1
    lock = load_lock(root)
    sources = lock.get("sources", {})

    expected = {}
    license_paths = set()
    for name, entry in sorted(sources.items()):
        lic = entry.get("license")
        if not lic:
            problems.append(("LICENSE", f"{name}: lock sem entrada de LICENSE"))
        else:
            license_paths.add(lic["path"])
            lp = root / lic["path"]
            if not lp.is_file():
                problems.append(("LICENSE", f"{lic['path']}: ausente"))
            elif sha256_file(lp) != lic["sha256"]:
                problems.append(("LICENSE", f"{lic['path']}: sha256 diverge do lock"))
        expected.update(all_lock_files(entry))

    vendor = root / "vendor"
    present = set()
    if vendor.exists():
        for dirpath, dirnames, filenames in os.walk(vendor):
            dirnames.sort()
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                rel = p.relative_to(root).as_posix()
                if p.is_symlink():
                    problems.append(("LINK_SIMBOLICO", f"{rel}: links simbólicos não são aceitos no vendor"))
                present.add(rel)

    for rel in sorted(set(expected) - present):
        if rel not in license_paths:
            problems.append(("AUSENTE", f"{rel}: está no lock, mas não existe em vendor/"))
    for rel in sorted(present - set(expected)):
        problems.append(("FORA_DO_LOCK", f"{rel}: existe em vendor/, mas não está no lock"))
    for rel in sorted(set(expected) & present):
        if rel in license_paths:
            continue
        actual = sha256_file(root / rel)
        if actual != expected[rel]:
            problems.append(("HASH", f"{rel}: esperado {expected[rel][:12]}…, obtido {actual[:12]}…"))

    links_checked = 0
    for rel in sorted(present):
        if not rel.endswith(".md"):
            continue
        parts = PurePosixPath(rel).parts
        boundary = (root / parts[0] / parts[1]).resolve() if len(parts) > 2 else vendor.resolve()
        md = (root / rel).resolve()
        for lineno, target in markdown_links(md.read_text(encoding="utf-8", errors="replace")):
            lp = relative_link_path(target)
            if lp is None:
                continue
            links_checked += 1
            ok, why = resolve_link(md, lp, boundary)
            if not ok:
                problems.append(("LINK", f"{rel}:{lineno}: ({target}) {why}"))

    print(f"verify: {len(sources)} fonte(s), {len(expected)} arquivo(s) no lock, "
          f"{len(present)} em vendor/, {links_checked} link(s) relativo(s) checado(s)")
    if not problems:
        print("OK: vendor/ confere com o lock.")
        return 0
    print(f"FALHA: {len(problems)} problema(s)")
    for kind, msg in problems:
        print(f"  [{kind}] {msg}")
    return 1


# ----------------------------------------------------------------------- cli

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="vendor.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="importa a seleção de um commit exato do upstream")
    p_sync.add_argument("--source", required=True, choices=sorted(SOURCES))
    p_sync.add_argument("--ref", required=True, help="SHA completo do commit upstream")
    p_sync.add_argument("--skills", nargs="+", help="skills inteiras (só na primeira importação ou para mudar a seleção)")
    p_sync.add_argument("--extra", nargs="+", help="arquivos avulsos (caminhos upstream)")
    p_sync.add_argument("--root", help=argparse.SUPPRESS)
    p_sync.set_defaults(func=cmd_sync)

    p_verify = sub.add_parser("verify", help="confere vendor/ contra o lock")
    p_verify.add_argument("--root", help="raiz do repositório a verificar (padrão: este repo)")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
