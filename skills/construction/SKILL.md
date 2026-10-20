---
name: construction
description: Implement an accepted design as dependency-ordered units, documenting detailed design before code. Use when an inception package or equivalent accepted technical design is ready.
---

# Construct an accepted design

Read [the shared protocol](references/protocol.md), then run `gate --skill construction` (with `--work WORK_ID` when resuming).

1. Locate the accepted design, decisions, units, and criteria. If absent or materially outdated, stop with `DESIGN_REQUIRED` and route to inception. Never manufacture approval.
2. Select a dependency-ready unit. Write or reference `units/UNIT_ID/unit-design.md` and `test-strategy.md` before editing product source. Include interfaces, state/error behavior, impacted files, data migration/recovery where applicable, and criteria-to-check links.
3. Record the unit stage: `design_draft`, `design_in_review`, `design_ready`, `building`, `verifying`, `reviewing`, or `completed`. Bind `design_ready` to the actual design revision and applicable user decision. A changed material design reopens this stage.
4. Create tasks/bolts with verifiable increments. Run `work-start --id WORK_ID --skill construction --allow PATH` for each affected path before coding; use the resulting anchored baseline on subsequent gate calls.
5. Implement one increment at a time. Prefer test-first development for reproducible behavior changes. Record check evidence, completed tasks, and source fingerprints. Do not weaken tests to make them pass.
6. Invoke `aidlc-verify` and `aidlc-review` for the unit; fix blocking findings and reverify. Run relevant cross-unit integration checks before final completion.
7. Refresh knowledge through `reverse-engineer`, then use `handoff`. Update shared progress so another host can resume.

Material scope or architecture deviations return to design. Do not continue dependent code based on an unapproved new assumption. Do not publish, merge, or deploy merely because construction finished.
