---
name: aidlc-review
description: Coordinate independent specialist agents to review a design or code snapshot and aggregate evidence-backed findings. Use for architecture, implementation, and pre-handoff review.
---

# Coordinate independent specialist review

Read [the shared protocol](references/protocol.md), then run `gate --skill aidlc-review` with the active work ID when appropriate. Read [the review contract](references/review.md) and the current host integration under `.aidlc/hosts/`.

1. Resolve a concrete design revision or source snapshot/diff. Include relevant untracked files. Build an immutable review packet with baseline, rules digest, criteria, decisions, checks, and limitations.
2. Read `.aidlc/config/review.json`. Dispatch separate SA, Security, and QA agent sessions plus specialists required by semantic impact. All role prompts are installed in host-native agent locations and mirrored under `.aidlc/reviewers/`.
3. Give each agent the shared packet plus a focused context slice, relevant role prompt, allowed source access, and output contract. Initially exclude other reviewers' conclusions.
4. Use the host's native subagent tools; run separate sessions sequentially if concurrency is limited. Do not emulate independent agents by changing persona. If unavailable, return `REVIEW_CAPABILITY_UNAVAILABLE` and do not mark the gate satisfied.
5. Collect session IDs, coverage, limitations, and findings. A timeout, malformed result, missing required role, or wrong snapshot makes review incomplete.
6. Validate evidence, retain raw reports, deduplicate by root cause, and resolve disagreements using targeted evidence. Preserve conflicting tradeoffs for a decision rather than vote.
7. Write `reviews/REVIEW_ID/summary.md` and `findings.json`. Confirmed critical/high findings block by default; unfulfilled mandatory criteria and incomplete reviewers also block. Risk acceptance must name the user decision, scope, and revision.
8. Return findings to the implementation skill. Bound remediation loops by config and re-review changed scope. Reviewers never fix product source themselves.
