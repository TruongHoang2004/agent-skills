---
name: reverse-engineer
description: Analyze an existing or empty repository and publish the required evidence-backed system baseline. Use for onboarding, a missing baseline, or refreshing knowledge after source changes.
---

# Reverse engineer the system

Read [the shared protocol](references/protocol.md). This is the only skill allowed before a valid baseline exists. Use it to understand what exists; intended future architecture belongs in inception.

1. Resolve the project root and read `.aidlc/project.json`. Inspect existing repository instructions. Run `python3 .aidlc/runtime/aidlc.py status` and `python3 .aidlc/runtime/aidlc.py inventory`. Inventory contains paths and hashes, not an architecture analysis.
2. Start a new knowledge revision with `python3 .aidlc/runtime/aidlc.py baseline-init`. The returned directory contains a frozen source inventory, document drafts, and an analysis manifest. Never edit a published revision.
3. Inspect entry points, component responsibilities, internal dependencies, representative business flows, persistent data, API/event contracts, integrations, authentication/authorization, build/test commands, and runtime configuration. Read source around important claims; reconcile stale documentation with code.
4. Complete all eight documents in the revision directory. Use `observed`, `inferred`, and `unknown` explicitly. Link claims to source paths and symbols. Explain absent concerns instead of inventing database tables, frameworks, or production topology. On an empty project, record an empty-system baseline and keep intended stack choices separate from observed facts.
5. Fill `analysis.json`: each document needs source `evidence` paths or a concrete `notPresent` explanation. Evidence paths must occur in the captured inventory. Record coverage limitations and `unknowns`; set `complete` only after checking the documents. Structural checks cannot decide whether an architectural statement is true.
6. Run `python3 .aidlc/runtime/aidlc.py baseline-publish --revision REVISION_ID`. Publication fails if source changed during analysis, evidence is missing, draft markers remain, or required documents are incomplete. Restart analysis against a new snapshot if needed; do not update hashes to conceal changes.
7. Summarize system boundaries, important flows, uncertainty, and the next action (`rules` on initial setup).

For refresh, compare the previous manifest's inventory to the new one, inspect changed and dependent components, and carry forward only still-supported claims. Include staged, unstaged, and untracked source through the runtime inventory. Incremental review still publishes a complete new revision. Do not inspect only the Git commit or rerun the entire repository analysis unnecessarily.
