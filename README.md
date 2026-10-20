# AI-DLC Agent Skills

English engineering skills for **Antigravity, Codex, and Claude Code**, with a project-local installer and shared memory outside every agent directory.

## Install

Requires Bash and Python **3.9+** on macOS, Linux, or WSL. No package manager, network download, Git repository, or application-language dependency is required.

From this repository:

```sh
# One agent
./install.sh --agent codex /path/to/project
./install.sh --agent antigravity /path/to/project
./install.sh --agent claude-code /path/to/project

# All three agents in one project
./install.sh --all /path/to/project

# Selected agents; paths with spaces work
./install.sh --agent codex,claude-code --target "/path/to/my project"

# Inspect changes without creating files
./install.sh --agent codex --dry-run /path/to/project
```

The target may be an existing codebase or an empty directory. Calling this script by its absolute path from another working directory also works. `--agent` can be repeated; `claude` and `claudecode` are accepted aliases for `claude-code`. With no agent flag, all three are installed.

The script installs framework files into the project; it does not install the host applications, configure accounts, or connect to Jira.

## Source and installed layouts

All hosts use one skill library:

```text
agent-skill/
  skills/<skill>/SKILL.md         # Single English source per skill
  skills/<skill>/references      # Link to shared reference content
  shared/                        # Contracts, reviewer roles, host guidance
  runtime/aidlc.py
  scripts/adapters.py             # Renders native reviewer metadata at install time
  scripts/install.py
  install.sh
```

The installer creates file symlinks for `SKILL.md` and its references in each host's discovery directory. Native reviewer files are rendered from `shared/reviewers.json`:

| Agent | Installed skills | Installed reviewers | Instruction bridge |
|---|---|---|---|
| Antigravity | `.agents/skills/` | `.agents/agents/` | Managed block in `AGENTS.md` |
| Codex | `.agents/skills/` | `.codex/agents/` | Managed block in `AGENTS.md` |
| Claude Code | `.claude/skills/` | `.claude/agents/` | Managed block in `CLAUDE.md` |

Codex and Antigravity share the same installed links. Claude Code links to the same source library. Keep this checkout at its installed location: skill edits here immediately apply to linked projects. Links are absolute and local to this machine; other machines must run the installer against their own checkout. If you move the checkout, reinstall from the new location to update owned links. `--check` reports broken links.

Editing an installed skill through its symlink edits the shared library. Put project-specific policies in `.aidlc/rules/`. Existing unmodified copied installations are migrated to links on reinstall; locally modified files remain protected.

**Every agent uses the same memory:**

```text
your-project/
  .aidlc/                         # Shared memory; outside all host directories
    project.json                  # Stable repository identity
    config/                       # Tickets, checks, review roles
    rules/index.md
    knowledge/
      revisions/                  # Reverse-engineering documents and evidence
      current.json                # Created only after baseline publication
    work/                         # Tickets, designs, decisions, progress, evidence
    hosts/                        # Installed host instructions
    reviewers/                    # Portable reviewer prompts
    contracts/
    runtime/aidlc.py
    install.json                  # Ownership hashes and installed hosts
  .agents/                        # Agent integrations, not project memory
  .codex/
  .claude/
```

Installing another agent preserves the same project ID, rules, knowledge, and work history.

## Start working

Open your agent in the target project and refresh/restart skill discovery if needed:

1. Invoke `reverse-engineer` to analyze the actual codebase and publish its baseline.
2. Invoke `rules` to configure ticket sources, verification commands, and repository conventions.
3. Use `inception` then `construction` for design-led changes, or `dev` for an actionable ticket.
4. Use `aidlc-verify` and `aidlc-review`, refresh the baseline, then `handoff`.

For example, select `$reverse-engineer` in Codex or `/reverse-engineer` in Antigravity/Claude Code. Host UI/version may change explicit selection syntax; the skill's name and procedure remain the same.

Every other skill, including `rules`, requires a valid baseline first. Installation does **not** create a fake completed baseline.

## Included skills

| Skill | Purpose |
|---|---|
| `reverse-engineer` | Analyze and refresh the evidence-backed system baseline |
| `rules` | Configure repository policy and ticket routing |
| `inception` | Requirements, architecture, decisions, and units |
| `construction` | Detailed design, tasks, implementation, and verification |
| `dev` | Implement a ready ticket |
| `aidlc-review` | Independent specialist review |
| `aidlc-verify` | Execute checks and collect acceptance evidence |
| `ticket-refine` | Resolve incomplete ticket requirements |
| `change-impact` | Analyze effects and stale decisions/evidence |
| `test-design` | Design meaningful verification scenarios |
| `debug` | Root-cause investigation and focused fixes, including hotfix mode |
| `refactor` | Restructure code with explicit behavioral invariants |
| `release-readiness` | Prepare rollout and recovery artifacts |
| `handoff` | Produce evidence-linked PR/ticket drafts |

Eight reviewer definitions are included: Solution Architect, Security, QA, Maintainability, Performance, Data, Operations, and Frontend/Accessibility. The review skill dispatches through the host's native tools. It reports a capability blocker if independent agents are unavailable; sequential persona imitation does not count.

## Manage an installation

```sh
# Check installed file integrity and configuration
./install.sh --check /path/to/project

# Upgrade/reconcile to this checkout's version; also updates existing host integrations
./install.sh --agent codex /path/to/project

# Remove one host while retaining shared files still used by other hosts
./install.sh --uninstall --agent codex /path/to/project

# Remove all host integrations; preserve project-owned memory and history
./install.sh --uninstall --all /path/to/project
```

Existing `AGENTS.md` and `CLAUDE.md` content is preserved outside the marked framework block. Existing host settings are not replaced. A modified managed file, conflicting skill name, malformed bridge, or symlink in a destination parent directory causes installation to fail before writing files. Resolve the reported conflict and retry; there is no destructive `--force`.

Reinstalling unchanged content is idempotent. Normal write failures roll back already written files. A process kill/power failure can leave a writer lock or partial installation; inspect `.aidlc/.write-lock` and `--check` before recovery. This release does not claim power-failure-atomic multi-file installation.

Uninstall preserves configuration, rules, baselines, and work records. Empty agent directories may remain. `.aidlc/install.json` records the remaining hosts.

## Shared runtime

Run from the installed project root:

```sh
python3 .aidlc/runtime/aidlc.py status
python3 .aidlc/runtime/aidlc.py inventory
python3 .aidlc/runtime/aidlc.py config-check
python3 .aidlc/runtime/aidlc.py gate --skill inception
```

The reverse-engineering skill uses `baseline-init` and `baseline-publish --revision ID`. Publication requires all documents, evidence metadata, and an unchanged source inventory. Fingerprints include dirty/untracked files; Git ignored files and common dependency/cache directories are excluded. Non-Git and unborn-Git projects work.

Implementation skills use `work-start --id ID --skill dev --allow src --allow tests` and subsequent `gate --skill aidlc-review --work ID` calls. An anchored baseline plus declared changes supports review while code is being implemented. Work scope is recorded guidance, not a filesystem permission boundary.

This release uses conservative repository-wide baselines. A material unexplained source change requires refresh; package-specific dependency-aware freshness is not implemented.

## Verification and limits

Run the local suite:

```sh
python3 -m unittest discover -s tests -v
bash -n install.sh
```

The tests exercise installation/removal for all three hosts, shared-memory preservation, collision/symlink handling, idempotence, rollback, baseline checks, dirty/untracked changes, scoped work, and configuration isolation.

The helper validates structural evidence and source fingerprints. It cannot prove the semantic truth of an architecture document, independently authenticate agent-session IDs, or block arbitrary edits outside compliant skill execution. No unverified global write-blocking hooks are installed.

Remote tickets use the agent's configured and available connector/CLI; this package does not ship a Jira API client or credentials. Local ticket reading is described by the same skill contract. Automated production deployment is outside this release.

Per-host files follow the documented discovery formats. CLI version/help inspection and offline format validation are recorded in [implementation status](docs/implementation-status.md); live model-driven skill execution and reviewer dispatch across all hosts are not claimed as tested.

## Develop the library

Edit `skills/<skill>/SKILL.md`, `shared/*.md`, `shared/reviewers.json`, or `shared/hosts/`. Skill and reference links reflect edits immediately. Rerun the installer after changing the runtime, contracts, reviewer definitions, host guidance, or adding/removing a skill. There is no bundle generation step. All skill and reviewer instructions are English.
