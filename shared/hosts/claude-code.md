# Claude Code integration

Skills are installed under `.claude/skills/` and invoked as `/skill-name`, for example `/dev local:ABC-1`. A marked block in `CLAUDE.md` points to shared memory and workflow prerequisites.

Reviewer definitions are `.claude/agents/aidlc-ROLE.md`. Dispatch them through the native Agent/subagent tool, collecting independent session identities and results. They allow Read, Grep, and Glob only; tests and shell commands run in the verification workflow. If the host cannot discover a role, pass `.aidlc/reviewers/ROLE.md` to a separate native agent with equivalent restrictions.

This installation does not replace `.claude/settings.json` or configure account credentials. Existing model, permission, and trust settings remain authoritative. Restart the session when necessary to discover newly added agent directories.

All project rules, knowledge, decisions, and progress live in `.aidlc/`, not Claude's private memory directory. Other installed hosts read the same state.
