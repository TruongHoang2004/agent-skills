# Antigravity integration

Skills are installed under `.agents/skills/`. Invoke `/skill-name`, for example `/dev local:ABC-1`, or select the skill through the host UI. `AGENTS.md` contains the small shared-memory bridge.

Reviewer definitions are `.agents/agents/aidlc-ROLE.md`. Use native independent subagent dispatch where supported on the current App/CLI/IDE surface. Verify role loading rather than assuming every surface has the same capabilities. If definitions are not discoverable but native independent dispatch exists, pass the role body from `.aidlc/reviewers/ROLE.md` explicitly.

Reviewer definitions allow documented read/search tools only and disable command execution. If tool names are unavailable on a particular version, report the capability mismatch; do not silently grant unrestricted tools. A missing independent-agent capability blocks required review.

All memory lives in `.aidlc/`. No legacy workflow files or unverified write-blocking hooks are installed. Refresh skill discovery after installation if necessary.
