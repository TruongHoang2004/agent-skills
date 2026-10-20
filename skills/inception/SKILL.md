---
name: inception
description: Turn a business intent or architectural change into requirements, solution design, and delivery units before coding. Use for new capabilities or changes that still need design decisions.
---

# Design before construction

Read [the shared protocol](references/protocol.md), then run `gate --skill inception`. Do not modify product source during this skill.

1. Capture intent, business outcome, scope/exclusions, constraints, and unresolved questions in `.aidlc/work/WORK_ID/intent.md`.
2. Inspect the baseline and impacted source. Write `design/impact-analysis.md` mapping proposed changes to existing modules, interfaces, data, and dependencies.
3. Write `design/requirements.md` with requirement IDs, acceptance criteria, and relevant measurable NFRs. Mark unknowns and resolve decisions that block design.
4. Write `design/solution-design.md`, contract/data changes, and ADRs. Compare realistic alternatives and explain the selected tradeoffs. Use diagrams when they clarify boundaries or flows.
5. Write `design/test-strategy.md` and `design/units.json`. Units have stable IDs, dependency IDs, criteria IDs, output, and completion conditions. Validate dependency order and avoid artificial independent units that actually share unfinished contracts.
6. Run `aidlc-review` against the versioned design package using separate SA, Security, and QA sessions. Address findings and record material scope/design decisions with artifact digests.
7. Update `progress.md` with the accepted design revision, first dependency-ready unit, and construction handoff.

Reuse an accepted design when it already covers the work. New approval is needed only for decisions outside existing authorization. A technical spike must be explicitly scoped and its findings returned to the design.
