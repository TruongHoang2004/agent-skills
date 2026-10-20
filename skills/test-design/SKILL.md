---
name: test-design
description: Derive meaningful verification scenarios and fixtures from acceptance criteria and system risks. Use when a change needs a test strategy before implementation or verification.
---

# Design verification

Read [the shared protocol](references/protocol.md), then run `gate --skill test-design`.

1. Read criteria, NFRs, affected architecture, existing tests, and quality rules.
2. Map each criterion to observable behavior and suitable unit, integration, contract, end-to-end, benchmark, or manual verification.
3. Include relevant boundaries, negative paths, authorization, failure/retry behavior, and regression protection. Avoid exhaustive unrelated checklists.
4. Write `test-strategy.md` with scenarios, fixture/data needs, environment prerequisites, assertions, and criteria links.
5. Identify coverage gaps and checks that cannot run in the available environment. Hand the strategy to construction/dev or aidlc-verify.

This skill plans tests. If the user also requests test code, start scoped implementation work and follow verification/review contracts. Do not treat scenario documentation as execution evidence.
