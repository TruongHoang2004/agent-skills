#!/usr/bin/env python3
"""Render native reviewer metadata at installation time."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("antigravity", "codex", "claude-code")


def outputs():
    result = {}
    roles = json.loads((ROOT / "shared/reviewers.json").read_text())
    for host in HOSTS:
        for role, data in roles.items():
            name = "aidlc-" + role
            body = (
                "# " + data["description"] + "\n\n"
                "You are an independent specialist reviewer. Inspect the coordinator's "
                "immutable snapshot and relevant project rules. Do not edit source, execute "
                "commands, post externally, or delegate. Return findings to the coordinator.\n\n"
                + "\n".join("- " + check for check in data["checks"])
                + "\n\nReturn JSON with reviewId, role (\"" + role + "\"), agentSessionId, "
                "snapshotDigest, status (completed or incomplete), coverage, limitations, "
                "and findings. Each finding needs id, severity, confidence, title, location, "
                "evidence, impact, recommendation, and relevant criterion/rule references. "
                "Never invent a session ID or claim checks were executed. Report missing "
                "evidence as a limitation. Follow the full contract in "
                ".aidlc/contracts/review.md when available.\n"
            )
            if host == "codex":
                text = (
                    "name = " + json.dumps(name) + "\n"
                    "description = " + json.dumps(data["description"]) + "\n"
                    "developer_instructions = " + json.dumps(body) + "\n"
                )
                result[Path(host) / "agents" / (name + ".toml")] = text
            else:
                metadata = (
                    "tools: Read, Grep, Glob\n" if host == "claude-code" else
                    "tools:\n  - view_file\n  - grep_search\n"
                    'subagent: true\nmainAgent: false\ncommandExecutionPolicy: "off"\n'
                )
                result[Path(host) / "agents" / (name + ".md")] = (
                    "---\nname: " + name + "\ndescription: "
                    + json.dumps(data["description"]) + "\n" + metadata + "---\n\n" + body
                )
            # Shared memory stores portable prompts, not host-specific agent metadata.
            result[Path("shared/reviewers") / (role + ".md")] = body
    return result

