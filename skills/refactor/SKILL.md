---
name: refactor
description: Restructure existing code while preserving explicit behavioral invariants. Use for bounded technical-debt work and structural improvements with defined compatibility constraints.
---

# Refactor with behavioral evidence

Read [the shared protocol](references/protocol.md), then run `gate --skill refactor`.

1. Define the target, motivation, observable invariants, API/data compatibility, and excluded changes.
2. Inspect existing coverage. Add characterization tests only where meaningful protection is missing.
3. Write a stepwise refactor plan and test strategy; resolve material architecture decisions before editing.
4. Start scoped work, perform small transformations, and run relevant checks after each meaningful increment.
5. Invoke aidlc-verify and aidlc-review, including Maintainability and impacted specialists.
6. Refresh baseline and produce handoff evidence. Report which behaviors were checked; do not claim proof of equivalence for all inputs.

If the work changes intended behavior, separate that requirement and route it to dev or inception rather than hiding it as refactoring.
