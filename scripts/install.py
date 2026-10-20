#!/usr/bin/env python3
"""Link shared AI-DLC skills into selected hosts without replacing project memory."""
import argparse
import json
import os
from pathlib import Path
import sys
import uuid
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters import outputs

if sys.version_info < (3, 9):
    sys.exit("Python 3.9 or newer is required.")

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "runtime"))
from aidlc import (Failure, START, END, atomic_write, digest, encoded,  # noqa: E402
                   read_json, safe_path, write_lock, config_check)

HOSTS = ("antigravity", "codex", "claude-code")
LAYOUT = {
    "antigravity": (".agents/skills", ".agents/agents", "AGENTS.md"),
    "codex": (".agents/skills", ".codex/agents", "AGENTS.md"),
    "claude-code": (".claude/skills", ".claude/agents", "CLAUDE.md"),
}
BLOCK = (
    START + "\n"
    "## AI-DLC shared project workflow\n\n"
    "Project memory is `.aidlc/`, shared by Antigravity, Codex, and Claude Code. "
    "Never store framework knowledge or work history in host-specific directories.\n\n"
    "Before using any AI-DLC skill other than `reverse-engineer`, run "
    "`python3 .aidlc/runtime/aidlc.py gate --skill <name>` from the project root "
    "(add `--work <id>` only when resuming its scoped implementation). If blocked, "
    "stop that workflow and follow the reported remedy. Do not fabricate a baseline.\n\n"
    "After the gate passes, read `.aidlc/rules/index.md` and applicable rules/config. "
    "Use `.aidlc/work/` for decisions, evidence, and resumable progress. "
    "Document design before code; ready tickets use `dev`. Required review uses "
    "separate SA, Security, and QA agent sessions. Follow `.aidlc/hosts/` for host details. "
    "Host permissions and existing repository instructions remain authoritative.\n"
    + END
).encode()


def bridge_parts(data):
    if isinstance(data, Link):
        raise Failure("INSTALL_CONFLICT", "Instruction bridge cannot be a symlink.")
    if data.count(START.encode()) != data.count(END.encode()) or data.count(START.encode()) > 1:
        raise Failure("BRIDGE_CONFLICT", "Malformed or duplicated AI-DLC instruction markers.")
    if START.encode() not in data:
        return None
    start, end = data.index(START.encode()), data.index(END.encode()) + len(END)
    if end < start:
        raise Failure("BRIDGE_CONFLICT", "Reversed AI-DLC instruction markers.")
    return start, end, data[start:end]


@dataclass(frozen=True)
class Link:
    target: str


def destination(root, name):
    # Only the leaf may be a managed link. Never traverse a linked parent.
    relative = Path(name)
    safe_path(root, str(relative.parent)) if str(relative.parent) != "." else None
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise Failure("INVALID_PATH", f"Invalid destination: {name}")
    return root / relative


def fingerprint(data):
    return digest(("symlink:" + data.target).encode() if isinstance(data, Link) else data)


def current_bytes(root, name):
    path = destination(root, name)
    if path.is_symlink():
        return Link(os.readlink(path))
    if path.exists() and not path.is_file():
        raise Failure("PATH_CONFLICT", f"Expected a file: {path}")
    return path.read_bytes() if path.exists() else None


def selected_hosts(values, all_hosts):
    if all_hosts and values:
        raise Failure("INVALID_ARGUMENT", "Choose --all or --agent, not both.")
    names = HOSTS if all_hosts or not values else [part for value in values for part in value.split(",")]
    result = set()
    for name in names:
        name = {"claude": "claude-code", "claudecode": "claude-code"}.get(name.strip(), name.strip())
        if name not in HOSTS:
            raise Failure("INVALID_AGENT", f"Unknown agent: {name}")
        result.add(name)
    return sorted(result)


def desired_files(hosts):
    result = {}
    skill_sources = sorted((SOURCE / "skills").glob("*/SKILL.md"))
    if not skill_sources:
        raise Failure("SOURCE_MISSING", "The shared skills library is missing or empty.")
    adapters = outputs()

    def add(name, data, owners):
        if name in result:
            if result[name]["data"] != data:
                raise Failure("BUNDLE_CONFLICT", f"Host bundles disagree at {name}")
            result[name]["hosts"] = sorted(set(result[name]["hosts"]) | set(owners))
        else:
            result[name] = {"data": data, "hosts": sorted(owners)}

    for host in hosts:
        skills, agents, bridge = LAYOUT[host]
        for source in skill_sources:
            base = skills + "/" + source.parent.name
            add(base + "/SKILL.md", Link(str(source)), [host])
            for reference in ("protocol", "configuration", "review"):
                add(base + "/references/" + reference + ".md",
                    Link(str(SOURCE / "shared" / (reference + ".md"))), [host])
        for relative, text in adapters.items():
            if relative.parts[0] == host:
                add(agents + "/" + relative.name, text.encode(), [host])
        add(".aidlc/hosts/" + host + ".md", (SOURCE / "shared/hosts" / (host + ".md")).read_bytes(), [host])
        add(bridge, BLOCK, [host])
    add(".aidlc/runtime/aidlc.py", (SOURCE / "runtime/aidlc.py").read_bytes(), hosts)
    for name in ("protocol", "configuration", "review"):
        add(".aidlc/contracts/" + name + ".md", (SOURCE / "shared" / (name + ".md")).read_bytes(), hosts)
    for path, text in adapters.items():
        if path.parts[0] == "shared":
            add(".aidlc/reviewers/" + path.name, text.encode(), hosts)
    return result


def seed_files():
    return {
        ".aidlc/project.json": encoded({"schemaVersion": 1, "repositoryId": str(uuid.uuid4()),
                                       "memoryDirectory": ".aidlc"}),
        ".aidlc/config/tickets.json": encoded({"schemaVersion": 1, "defaultProvider": None,
                                             "providers": {}, "routing": [], "writeBack": "draft"}),
        ".aidlc/config/quality.json": encoded({"schemaVersion": 1, "checks": []}),
        ".aidlc/config/review.json": encoded({
            "schemaVersion": 1, "requiredRoles": ["solution-architect", "security", "quality-assurance"],
            "blockingSeverities": ["critical", "high"], "maxRemediationCycles": 2}),
        ".aidlc/rules/index.md": (
            "# Project rule index\n\n"
            "Run reverse-engineer, then rules to configure this project. "
            "No ticket provider or verification commands are inferred during installation.\n\n"
            "- Record architecture, coding, testing, ticket, and review rules here with scope and source.\n"
            "- Machine-readable settings belong in `.aidlc/config/`.\n"
            "- Existing repository instructions remain authoritative.\n"
        ).encode(),
        ".aidlc/README.md": (
            "# Shared AI-DLC project memory\n\n"
            "This directory is shared by every installed agent. Keep project configuration, "
            "rules, knowledge revisions, work decisions, and verification/review evidence here.\n\n"
            "- `knowledge/revisions/`: immutable published system baselines.\n"
            "- `knowledge/current.json`: current baseline pointer, created by reverse engineering.\n"
            "- `work/`: ticket/intent work, progress, decisions, and evidence.\n"
            "- `config/` and `rules/`: project-owned configuration and guidance.\n"
            "- `install.json`, `runtime/`, `contracts/`, `hosts/`, `reviewers/`: installer-managed files.\n\n"
            "Do not store secrets. Commit sanitized rules/knowledge/work as appropriate; "
            "review logs and ticket content before committing. Uninstall preserves project memory.\n"
        ).encode(),
    }


def load_install(root):
    path = safe_path(root, ".aidlc/install.json")
    if not path.exists():
        return {"schemaVersion": 1, "hosts": [], "files": {}}
    value = read_json(path)
    if (not isinstance(value, dict) or value.get("schemaVersion") != 1
            or not isinstance(value.get("files"), dict)
            or not isinstance(value.get("hosts"), list)
            or not set(value["hosts"]) <= set(HOSTS)):
        raise Failure("INSTALL_STATE_INVALID", "Unrecognized install manifest; no files changed.")
    for name, record in value["files"].items():
        destination(root, name)
        if (not isinstance(record, dict) or record.get("kind") not in ("file", "block", "symlink")
                or not isinstance(record.get("sha256"), str)
                or not isinstance(record.get("hosts"), list)):
            raise Failure("INSTALL_STATE_INVALID", f"Invalid ownership record: {name}")
    return value


def plan(root, hosts, remove=False):
    old = load_install(root)
    records = dict(old["files"])
    operations = {}
    conflicts = []
    next_hosts = sorted(set(old["hosts"]) - set(hosts) if remove else set(old["hosts"]) | set(hosts))
    version = (SOURCE / "VERSION").read_text().strip()
    if remove:
        for name, record in list(records.items()):
            remaining = sorted(set(record["hosts"]) - set(hosts))
            if remaining:
                records[name] = {**record, "hosts": remaining}
                continue
            data = current_bytes(root, name)
            if data is not None:
                parts = bridge_parts(data) if record["kind"] == "block" else None
                actual = parts[2] if parts else data
                if fingerprint(actual) != record["sha256"]:
                    conflicts.append(name)
                    continue
                if parts:
                    # Remove only our block; preserve all outside bytes.
                    new = data[:parts[0]] + data[parts[1]:]
                    operations[name] = new if new.strip() else None
                else:
                    operations[name] = None
            del records[name]
    else:
        # Reconcile all installed hosts so shared files stay at one release version.
        for name, desired in desired_files(next_hosts).items():
            data = current_bytes(root, name)
            kind = "block" if name in ("AGENTS.md", "CLAUDE.md") else ("symlink" if isinstance(desired["data"], Link) else "file")
            record = records.get(name)
            if isinstance(data, Link) and kind == "block":
                conflicts.append(name)
                continue
            if kind == "block":
                parts = bridge_parts(data or b"")
                if parts:
                    if not record or digest(parts[2]) != record["sha256"]:
                        conflicts.append(name)
                        continue
                    new = data[:parts[0]] + desired["data"] + data[parts[1]:]
                elif record:
                    conflicts.append(name + " (managed block removed)")
                    continue
                else:
                    prefix = data or b""
                    separator = b"" if not prefix else (b"\n" if prefix.endswith(b"\n") else b"\n\n")
                    new = prefix + separator + desired["data"] + b"\n"
            else:
                if data is not None and (not record or fingerprint(data) != record["sha256"]):
                    conflicts.append(name)
                    continue
                new = desired["data"]
            if data != new:
                operations[name] = new
            records[name] = {"kind": kind, "sha256": fingerprint(desired["data"]), "hosts": desired["hosts"]}
        # Detect removed/renamed generated paths on upgrades; never leave obsolete skills active.
        desired_names = set(desired_files(next_hosts))
        for name in set(records) - desired_names:
            record = records[name]
            data = current_bytes(root, name)
            if data is not None and fingerprint(data) != record["sha256"]:
                conflicts.append(name)
            else:
                operations[name] = None
                del records[name]
        for name, value in seed_files().items():
            data = current_bytes(root, name)
            if data is None:
                operations[name] = value
            elif isinstance(data, Link):
                conflicts.append(name)
            elif name == ".aidlc/project.json":
                project = read_json(safe_path(root, name))
                if (not isinstance(project, dict) or project.get("schemaVersion") != 1
                        or project.get("memoryDirectory") != ".aidlc" or not project.get("repositoryId")):
                    conflicts.append(name + " (incompatible project memory)")
    if conflicts:
        raise Failure("INSTALL_CONFLICT", "Preserved modified/unowned files: " + ", ".join(conflicts),
                      "Resolve or relocate those files, then retry. No force overwrite is provided.")
    state = {"schemaVersion": 1, "version": version, "hosts": next_hosts, "files": records}
    if old != state:
        operations[".aidlc/install.json"] = encoded(state)
    return operations, state


def write_entry(root, name, data):
    path = destination(root, name)
    if data is None:
        if path.exists() or path.is_symlink():
            path.unlink()
    elif isinstance(data, Link):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex)
        try:
            temporary.symlink_to(data.target)
            os.replace(temporary, path)
        finally:
            if temporary.is_symlink():
                temporary.unlink()
    else:
        atomic_write(path, data)


def apply(root, operations):
    backups = {name: current_bytes(root, name) for name in operations}
    written = []
    try:
        for name, data in operations.items():
            written.append(name)
            write_entry(root, name, data)
    except BaseException:
        for name in reversed(written):
            write_entry(root, name, backups[name])
        raise


def doctor(root):
    state = load_install(root)
    problems = []
    for name, record in state["files"].items():
        data = current_bytes(root, name)
        if data is None:
            problems.append(name + ": missing")
            continue
        parts = bridge_parts(data) if record["kind"] == "block" else None
        if fingerprint(parts[2] if parts else data) != record["sha256"]:
            problems.append(name + ": modified")
        if isinstance(data, Link) and not (root / name).is_file():
            problems.append(name + ": broken link")
    if problems:
        raise Failure("INSTALL_DRIFT", "; ".join(problems))
    if not state["hosts"]:
        raise Failure("NOT_INSTALLED", "No installed hosts.")
    config_check(root)
    return {"status": "ok", "hosts": state["hosts"], "memory": ".aidlc",
            "checkedFiles": len(state["files"]), "liveHostExecution": "not tested by installer"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", help="Target project directory (Git not required)")
    parser.add_argument("--target", "--repo", dest="target", help="Target project directory")
    parser.add_argument("--agent", "--agents", action="append", help="antigravity, codex, claude-code; repeat or comma-separate")
    parser.add_argument("--all", action="store_true", help="Install all hosts (default)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--uninstall", action="store_true", help="Remove selected owned bundles; preserve memory")
    parser.add_argument("--check", action="store_true", help="Check installed file integrity and configuration")
    args = parser.parse_args()
    try:
        if args.project and args.target:
            raise Failure("INVALID_ARGUMENT", "Supply one target path.")
        if not (args.project or args.target):
            parser.error("a target project path is required")
        if args.check and (args.uninstall or args.dry_run):
            parser.error("--check cannot be combined with --uninstall or --dry-run")
        root = Path(args.project or args.target).expanduser().resolve()
        if root.exists() and not root.is_dir():
            raise Failure("INVALID_TARGET", "Target must be a directory.")
        hosts = selected_hosts(args.agent, args.all)
        if args.check:
            print(json.dumps(doctor(root), indent=2))
            return 0
        # Check everything first; dry-run does not even create the target directory.
        operations, state = plan(root, hosts, args.uninstall)
        if not args.dry_run:
            root.mkdir(parents=True, exist_ok=True)
            safe_path(root, ".aidlc").mkdir(exist_ok=True)
            with write_lock(root):
                # Revalidate after acquiring the cross-process writer lock.
                operations, state = plan(root, hosts, args.uninstall)
                apply(root, operations)
                if not args.uninstall:
                    for directory in ("knowledge/revisions", "work"):
                        safe_path(root, ".aidlc/" + directory).mkdir(parents=True, exist_ok=True)
        print(json.dumps({
            "status": "dry-run" if args.dry_run else ("uninstalled" if args.uninstall else "installed"),
            "root": str(root), "hosts": state["hosts"], "memory": str(root / ".aidlc"),
            "changes": [{"path": name, "action": "remove" if data is None else "write"}
                        for name, data in operations.items()],
            "next": "Open the selected agent in the project; run reverse-engineer, then rules.",
        }, indent=2))
        return 0
    except (Failure, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "code": getattr(exc, "code", "INSTALL_ERROR"),
                          "reason": str(exc), "requiredAction": getattr(exc, "remedy", "Inspect the target and retry.")},
                         indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
