---
name: change-impact
description: Analyze how a proposed change affects components, requirements, designs, tests, and existing decisions. Use before changing scope or when unexpected changes invalidate active work.
---

# Analyze change impact

Read [the shared protocol](references/protocol.md), then run `gate --skill change-impact` with the active work ID when applicable. If an unexplained source change makes the baseline stale, refresh through reverse engineering first.

1. Capture the proposed change and compare its inputs with the pinned work revisions.
2. Trace affected components, interfaces, data consumers, rules, dependencies, criteria, and operational assumptions.
3. Write `impact-analysis.md` with direct/transitive effects, compatibility risks, unaffected scope with rationale, and unknowns.
4. Mark affected decisions, tasks, verification, and review evidence stale in the work record while preserving history.
5. Recommend the exact stage to reopen and the smallest justified revalidation scope. Uncertain impact requires broader revalidation.

Do not silently expand implementation scope or invalidate unrelated decisions. Return the analysis to the responsible workflow before dependent code proceeds.
