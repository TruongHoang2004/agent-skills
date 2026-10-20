#!/usr/bin/env python3
"""Repository-local AI-DLC baseline and configuration checks (Python 3.9+)."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

DOCUMENTS = (
    "system-overview.md", "architecture.md", "domain-model.md", "interfaces.md",
    "data-model.md", "runtime-and-operations.md", "testing-and-quality.md",
    "risks-and-unknowns.md",
)
SKILLS = (
    "reverse-engineer", "rules", "inception", "construction", "dev",
    "aidlc-review", "aidlc-verify", "ticket-refine", "change-impact",
    "test-design", "debug", "refactor", "release-readiness", "handoff",
)
ROLES = {"solution-architect", "security", "quality-assurance",
         "maintainability", "performance", "data", "operations", "frontend"}
REQUIRED_ROLES = {"solution-architect", "security", "quality-assurance"}
START = "<!-- AIDLC-FRAMEWORK-START -->"
END = "<!-- AIDLC-FRAMEWORK-END -->"
EXCLUDED_DIRS = {".git", ".aidlc", "node_modules", ".venv", "venv", "__pycache__",
                 ".pytest_cache", ".mypy_cache", ".next", ".cache"}


class Failure(Exception):
    def __init__(self, code, reason, remedy="Inspect the reported input and retry."):
        self.code, self.reason, self.remedy = code, reason, remedy
        super().__init__(reason)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def safe_path(root, relative):
    """Reject absolute/traversal paths and symlinks in any destination component."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise Failure("INVALID_PATH", f"Expected a project-relative path: {relative}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise Failure("SYMLINK_PATH", f"Refusing symlink path: {current}")
    return current


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise Failure("INVALID_JSON", f"Cannot read {path}: {exc}") from exc


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".aidlc-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def write_lock(root):
    path = safe_path(root, ".aidlc/.write-lock")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise Failure("WORKSPACE_LOCKED", f"Writer lock exists: {path}",
                      "Check the recorded PID. Remove only an abandoned lock, then retry.") from exc
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump({"pid": os.getpid(), "createdAt": now()}, stream)
        yield
    finally:
        path.unlink()


def project_root(explicit=None):
    start = Path(explicit).expanduser().resolve() if explicit else Path.cwd().resolve()
    candidates = [start] if explicit else [start, *start.parents]
    for candidate in candidates:
        if (candidate / ".aidlc/project.json").exists():
            project = read_json(safe_path(candidate, ".aidlc/project.json"))
            if not isinstance(project, dict) or project.get("schemaVersion") != 1 or not project.get("repositoryId"):
                raise Failure("INVALID_PROJECT", "Unrecognized .aidlc/project.json")
            return candidate, project
    raise Failure("NOT_INSTALLED", f"No .aidlc/project.json found from {start}",
                  "Install the framework into the intended project first.")


def strip_bridge(data):
    start, end = START.encode(), END.encode()
    if start in data and end in data:
        before, rest = data.split(start, 1)
        _, after = rest.split(end, 1)
        return before.rstrip() + after.lstrip()
    return data


def inventory(root):
    """Hash source including dirty/untracked files; do not follow symlinks."""
    owned = {}
    manifest_path = safe_path(root, ".aidlc/install.json")
    if manifest_path.exists():
        installed = read_json(manifest_path)
        owned = installed.get("files", {})
    names = None
    try:
        git = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others",
             "--exclude-standard", "-z"], capture_output=True, check=False,
        )
        if git.returncode == 0:
            names = sorted(set(os.fsdecode(n) for n in git.stdout.split(b"\0") if n))
    except FileNotFoundError:
        pass
    if names is None:
        names = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            for d in list(dirs):
                p = Path(directory) / d
                if p.is_symlink():
                    names.append(p.relative_to(root).as_posix())
                    dirs.remove(d)
            names.extend((Path(directory) / f).relative_to(root).as_posix() for f in files)
    result = {}
    for name in sorted(names):
        rel = Path(name)
        if any(p in EXCLUDED_DIRS for p in rel.parts) or name == ".DS_Store":
            continue
        entry = owned.get(name, {})
        if entry.get("kind") in ("file", "symlink"):
            continue
        path = root / rel
        # Never follow an intermediate directory symlink from a tracked path.
        if any((root / Path(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts))):
            continue
        if path.is_symlink():
            data = ("symlink:" + os.readlink(path)).encode()
        elif path.is_file():
            data = path.read_bytes()
            if name in ("AGENTS.md", "CLAUDE.md"):
                data = strip_bridge(data)
                if not data.strip():
                    continue
        else:
            continue
        result[name] = digest(data)
    return result


def config_check(root, require_ticket=False):
    tickets = read_json(safe_path(root, ".aidlc/config/tickets.json"))
    quality = read_json(safe_path(root, ".aidlc/config/quality.json"))
    review = read_json(safe_path(root, ".aidlc/config/review.json"))
    for config in (tickets, quality, review):
        if not isinstance(config, dict) or config.get("schemaVersion") != 1:
            raise Failure("CONFIG_INVALID", "Config schemaVersion must be 1.")
    providers = tickets.get("providers")
    if not isinstance(providers, dict):
        raise Failure("CONFIG_INVALID", "tickets.providers must be an object.")
    default = tickets.get("defaultProvider")
    if default is not None and default not in providers:
        raise Failure("CONFIG_INVALID", "Default ticket provider is not configured.")
    if require_ticket and default is None and not providers:
        raise Failure("PROVIDER_NOT_CONFIGURED", "No ticket source configured.",
                      "Run the rules skill to configure a local or remote ticket source.")
    for name, provider in providers.items():
        if not isinstance(provider, dict):
            raise Failure("CONFIG_INVALID", f"Invalid provider: {name}")
        if name == "local":
            if not isinstance(provider.get("root"), str):
                raise Failure("CONFIG_INVALID", "Local tickets require a relative root.")
            safe_path(root, provider["root"])
        elif not isinstance(provider.get("connection"), str) or not provider["connection"].strip():
            raise Failure("CONFIG_INVALID", f"{name} requires a host connection reference.")
    routing = tickets.get("routing", [])
    if not isinstance(routing, list):
        raise Failure("CONFIG_INVALID", "routing must be an array.")
    prefixes = set()
    for route in routing:
        if (not isinstance(route, dict) or not isinstance(route.get("prefix"), str)
                or not route["prefix"] or route.get("provider") not in providers):
            raise Failure("CONFIG_INVALID", "Routes need a prefix and configured provider.")
        if route["prefix"] in prefixes:
            raise Failure("CONFIG_INVALID", "Duplicate ticket routing prefix.")
        prefixes.add(route["prefix"])
    if tickets.get("writeBack") != "draft":
        raise Failure("CONFIG_INVALID", "This release supports draft ticket write-back only.")
    checks = quality.get("checks")
    if not isinstance(checks, list):
        raise Failure("CONFIG_INVALID", "quality.checks must be an array.")
    ids = set()
    for check in checks:
        if (not isinstance(check, dict) or not isinstance(check.get("id"), str)
                or not check["id"] or check["id"] in ids
                or not isinstance(check.get("command"), list) or not check["command"]
                or not all(isinstance(x, str) and x for x in check["command"])
                or not isinstance(check.get("required"), bool)):
            raise Failure("CONFIG_INVALID", "Checks need unique IDs, argv commands, and required booleans.")
        cwd = check.get("cwd", ".")
        if cwd != ".":
            safe_path(root, cwd)
        ids.add(check["id"])
    roles = review.get("requiredRoles")
    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
        raise Failure("CONFIG_INVALID", "requiredRoles must be an array of role names.")
    if not REQUIRED_ROLES <= set(roles) or not set(roles) <= ROLES:
        raise Failure("CONFIG_INVALID", "Review requires SA, Security, QA and known optional roles.")
    limit = review.get("maxRemediationCycles")
    if type(limit) is not int or limit < 1:
        raise Failure("CONFIG_INVALID", "maxRemediationCycles must be a positive integer.")
    severities = review.get("blockingSeverities")
    if (not isinstance(severities, list) or not {"critical", "high"} <= set(severities)
            or not set(severities) <= {"critical", "high", "medium", "low"}):
        raise Failure("CONFIG_INVALID", "Blocking severities must include critical and high.")
    return {"status": "valid", "ticketProvider": default, "checks": len(checks), "reviewRoles": roles}


def revision_dir(root, revision):
    if not re.fullmatch(r"KB-[A-Za-z0-9-]+", revision):
        raise Failure("INVALID_REVISION", "Invalid knowledge revision ID.")
    return safe_path(root, f".aidlc/knowledge/revisions/{revision}")


def validate_baseline(root, project, revision=None):
    if revision is None:
        current_path = safe_path(root, ".aidlc/knowledge/current.json")
        if not current_path.exists():
            raise Failure("BASELINE_MISSING", "No published system baseline.",
                          "Run the reverse-engineer skill first.")
        revision = read_json(current_path).get("revision")
    if not isinstance(revision, str):
        raise Failure("BASELINE_INVALID", "Missing baseline revision.")
    directory = revision_dir(root, revision)
    manifest = read_json(safe_path(directory, "manifest.json"))
    if manifest.get("schemaVersion") != 1 or manifest.get("revision") != revision:
        raise Failure("BASELINE_INVALID", "Invalid baseline manifest.")
    if manifest.get("repositoryId") != project["repositoryId"]:
        raise Failure("BASELINE_INVALID", "Baseline belongs to a different repository.")
    if manifest.get("scope") != ["."]:
        raise Failure("BASELINE_INVALID", "This release requires repository-wide coverage.")
    docs = manifest.get("documents", {})
    if set(docs) != set(DOCUMENTS):
        raise Failure("BASELINE_INVALID", "Required knowledge documents are missing.")
    for name in DOCUMENTS:
        path = safe_path(directory, name)
        if not path.is_file() or digest(path.read_bytes()) != docs[name]:
            raise Failure("BASELINE_INVALID", f"Published document changed or missing: {name}")
    analysis = safe_path(directory, "analysis.json")
    if digest(analysis.read_bytes()) != manifest.get("analysisDigest"):
        raise Failure("BASELINE_INVALID", "Published evidence metadata changed.")
    if not isinstance(manifest.get("inventory"), dict):
        raise Failure("BASELINE_INVALID", "Missing source inventory.")
    return manifest


def changed_paths(before, after):
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def work_path(root, work):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", work):
        raise Failure("INVALID_WORK_ID", "Use a short alphanumeric work ID with hyphens/underscores.")
    return safe_path(root, f".aidlc/work/{work}/state.json")


def gate(root, project, skill, work=None):
    if skill not in SKILLS:
        raise Failure("UNKNOWN_SKILL", skill)
    if skill == "reverse-engineer":
        return {"status": "allowed", "skill": skill, "reason": "baseline producer"}
    state = read_json(work_path(root, work)) if work else None
    baseline = validate_baseline(root, project, state.get("baselineRevision") if state else None)
    current = inventory(root)
    changes = changed_paths(baseline["inventory"], current)
    if state:
        if state.get("repositoryId") != project["repositoryId"]:
            raise Failure("INVALID_WORK", "Work belongs to another repository.")
        paths = state.get("allowedPaths")
        if not isinstance(paths, list) or not paths:
            raise Failure("INVALID_WORK", "Missing declared work paths.")
        for path in paths:
            safe_path(root, path)
        changes = [c for c in changes if not any(c == p or c.startswith(p.rstrip("/") + "/") for p in paths)]
    if changes:
        raise Failure("BASELINE_STALE", "Unaccounted source changes: " + ", ".join(changes[:20]),
                      "Refresh through reverse-engineer, or resume the explicitly scoped work.")
    config_check(root, require_ticket=skill in ("dev", "ticket-refine"))
    return {"status": "allowed", "skill": skill, "baselineRevision": baseline["revision"],
            "workId": work, "sourceDigest": digest(encoded(current))}


def baseline_init(root, project):
    revision = "KB-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    directory = revision_dir(root, revision)
    source = inventory(root)
    with write_lock(root):
        directory.mkdir(parents=True)
        atomic_write(directory / "snapshot.json", encoded(source))
        analysis = {
            "schemaVersion": 1, "repositoryId": project["repositoryId"], "revision": revision,
            "complete": False, "scope": ["."], "unknowns": [],
            "documents": {name: {"evidence": [], "notPresent": ""} for name in DOCUMENTS},
        }
        atomic_write(directory / "analysis.json", encoded(analysis))
        for name in DOCUMENTS:
            title = name[:-3].replace("-", " ").title()
            atomic_write(directory / name, (
                f"# {title}\n\nDRAFT: Replace this text with observed facts, source references, "
                "inferences, and explicit unknowns. Explain absent concerns with evidence.\n"
            ).encode())
    return {"revision": revision, "directory": str(directory), "sourceFiles": len(source)}


def baseline_publish(root, project, revision):
    directory = revision_dir(root, revision)
    with write_lock(root):
        if (directory / "manifest.json").exists():
            raise Failure("IMMUTABLE_REVISION", "Published revisions cannot be overwritten.")
        analysis = read_json(safe_path(directory, "analysis.json"))
        source = read_json(safe_path(directory, "snapshot.json"))
        if analysis.get("complete") is not True or analysis.get("repositoryId") != project["repositoryId"]:
            raise Failure("ANALYSIS_INCOMPLETE", "Complete the analysis for this repository first.")
        if analysis.get("revision") != revision or analysis.get("scope") != ["."]:
            raise Failure("ANALYSIS_INCOMPLETE", "Analysis revision/scope does not match.")
        if not isinstance(analysis.get("unknowns"), list):
            raise Failure("ANALYSIS_INCOMPLETE", "Record unknowns as an array.")
        if source != inventory(root):
            raise Failure("SOURCE_CHANGED", "Source changed during reverse engineering.",
                          "Start a new baseline revision and reconcile against the current source.")
        metadata = analysis.get("documents", {})
        hashes = {}
        for name in DOCUMENTS:
            text = safe_path(directory, name).read_text()
            if "DRAFT:" in text or not re.search(r"\S", re.sub(r"(?m)^#.*$", "", text)):
                raise Failure("ANALYSIS_INCOMPLETE", f"Complete document: {name}")
            item = metadata.get(name, {})
            evidence, absent = item.get("evidence"), item.get("notPresent")
            if (not isinstance(evidence, list)
                    or any(not isinstance(p, str) or p not in source for p in evidence)
                    or not isinstance(absent, str) or not (evidence or absent.strip())):
                raise Failure("EVIDENCE_MISSING", f"Provide source evidence or an absence explanation: {name}")
            hashes[name] = digest(text.encode())
        manifest = {
            "schemaVersion": 1, "repositoryId": project["repositoryId"], "revision": revision,
            "scope": ["."], "publishedAt": now(), "documents": hashes, "inventory": source,
            "analysisDigest": digest(safe_path(directory, "analysis.json").read_bytes()),
        }
        atomic_write(directory / "manifest.json", encoded(manifest))
        atomic_write(safe_path(root, ".aidlc/knowledge/current.json"), encoded({"revision": revision}))
    return {"status": "published", "revision": revision, "sourceFiles": len(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Installed project root; default searches current directory ancestors")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "inventory", "config-check", "baseline-init"):
        sub.add_parser(name)
    publish = sub.add_parser("baseline-publish")
    publish.add_argument("--revision", required=True)
    check = sub.add_parser("gate")
    check.add_argument("--skill", required=True, choices=SKILLS)
    check.add_argument("--work")
    work = sub.add_parser("work-start")
    work.add_argument("--id", required=True)
    work.add_argument("--skill", required=True, choices=("construction", "dev", "debug", "refactor", "test-design"))
    work.add_argument("--allow", action="append", required=True)
    args = parser.parse_args()
    try:
        root, project = project_root(args.root)
        if args.command == "inventory":
            data = {"files": inventory(root)}
        elif args.command == "config-check":
            data = config_check(root)
        elif args.command == "gate":
            data = gate(root, project, args.skill, args.work)
        elif args.command == "baseline-init":
            data = baseline_init(root, project)
        elif args.command == "baseline-publish":
            data = baseline_publish(root, project, args.revision)
        elif args.command == "work-start":
            with write_lock(root):
                result = gate(root, project, args.skill)
                path = work_path(root, args.id)
                if path.exists():
                    raise Failure("WORK_EXISTS", "Resume existing work; do not overwrite its state.")
                allowed = []
                for name in args.allow:
                    safe_path(root, name)
                    if name == "." or Path(name).parts[0] in (".aidlc", ".git"):
                        raise Failure("INVALID_SCOPE", "Declare specific product paths, not the root or framework state.")
                    allowed.append(Path(name).as_posix())
                data = {"schemaVersion": 1, "workId": args.id, "skill": args.skill,
                        "repositoryId": project["repositoryId"], "createdAt": now(),
                        "baselineRevision": result["baselineRevision"],
                        "allowedPaths": sorted(set(allowed)), "status": "started"}
                atomic_write(path, encoded(data))
        else:
            try:
                result = gate(root, project, "rules")
            except Failure as exc:
                result = {"status": "blocked", "code": exc.code, "reason": exc.reason}
            data = {"root": str(root), "repositoryId": project["repositoryId"], "baseline": result,
                    "memory": ".aidlc", "work": sorted(p.parent.name for p in (root / ".aidlc/work").glob("*/state.json"))}
        print(json.dumps(data, indent=2))
        return 0
    except (Failure, OSError, ValueError, TypeError, AttributeError) as exc:
        if isinstance(exc, Failure):
            error = {"code": exc.code, "reason": exc.reason, "requiredAction": exc.remedy}
        else:
            error = {"code": "INVALID_STATE", "reason": str(exc),
                     "requiredAction": "Inspect the project files and retry; do not bypass validation."}
        print(json.dumps({"status": "blocked", **error}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
