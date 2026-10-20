---
name: handoff
description: Assemble a completed work package into a concise PR or ticket handoff with traceable verification and review evidence. Use when preparing work for another engineer or release process.
---

# Hand off verified work

Read [the shared protocol](references/protocol.md), then run `gate --skill handoff`. A completed implementation needs a refreshed baseline; do not use an old work delta to evade final documentation refresh.

1. Resolve the intent/ticket, accepted design, source snapshot, criteria matrix, checks, and independent review reports.
2. Confirm mandatory evidence is current and complete. If not, produce an explicitly incomplete handoff with blockers rather than declaring completion.
3. Write `handoff.md` and, when useful, `pr-description.md` with the problem, resulting behavior, scope, validation, risks, and exact next action.
4. Update `progress.md` with completion or blocked status, artifact references, and remaining work. Preserve original ticket/source provenance.
5. Present the local drafts. Post or create external artifacts only when that action is already authorized by the user.
