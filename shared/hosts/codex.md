# Codex integration

Skills are installed under `.agents/skills/`; use the skill picker or `$skill-name`, for example `$dev local:ABC-1`. Repository guidance is added as a marked block in `AGENTS.md`.

Reviewer definitions are `.codex/agents/aidlc-ROLE.toml`. Use the native subagent dispatch tools available in the current session and collect actual session identities. If the surface cannot load definitions, give the same role instructions from `.aidlc/reviewers/ROLE.md` to a separate native agent. If separate agents are unavailable, required review is blocked.

Models and sandbox permissions inherit from the user's host configuration. This installer does not change `.codex/config.toml`, model settings, trust, or permission policy. Reviewer prompts require read-only work, but do not claim to override the parent's sandbox. Use an isolated read-only snapshot for stronger enforcement.

All project memory is in `.aidlc/`, shared with other hosts. Restart or refresh skill discovery after installation if necessary.
