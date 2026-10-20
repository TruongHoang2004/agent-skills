# Implementation status

The framework has 14 English skills in `skills/`, eight shared reviewer roles, and a selectable installer for Antigravity, Codex, and Claude Code. There are no per-host source bundles or proposal documents.

Installation creates file symlinks to canonical skills and references, renders native reviewer metadata, and copies runtime/contracts into `.aidlc/`. Project identity, configuration, rules, knowledge, and work history remain in `.aidlc/` across host additions and removals.

The Python standard-library runtime validates baseline evidence structure, source fingerprints, configuration, and scoped work anchors. It does not authenticate the truth of analysis or reviewer session IDs, enforce arbitrary filesystem writes, or provide remote ticket API clients.

## Verification scope

The automated suite exercises all hosts, symlink targets, migration from owned copies, broken links, rollback, protected local modifications, selective uninstall, shared memory, baseline freshness, and configuration isolation. Skill metadata/reference checks and native Codex TOML parsing are included. Tests use disposable projects and no model calls.

Run `python3 -m unittest discover -s tests -v` and `bash -n install.sh`.

Live host skill discovery and independent reviewer dispatch have not been tested. The previous CLI version/help inspection is not evidence of live execution. Linked installations require the source checkout to remain accessible; rerun the installer after moving it.
