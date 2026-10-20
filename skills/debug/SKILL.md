---
name: debug
description: Investigate an unexpected failure, reproduce its cause, and implement a focused fix when requested. Use for debugging and hotfix investigation beyond an already actionable ticket.
---

# Investigate and fix a failure

Read [the shared protocol](references/protocol.md), then run `gate --skill debug`.

1. Capture symptoms, environment, timestamps, logs, and expected/actual behavior. Redact credentials and personal data from stored evidence.
2. Trace likely paths from baseline to source. Form competing hypotheses and gather evidence that distinguishes them.
3. Reproduce the failure, preferably with a regression test that fails before the fix. If reproduction is unavailable, state uncertainty instead of claiming a confirmed root cause.
4. Write `rca.md` and a minimal fix plan. For a fix request, use `work-start` with explicit paths before editing. Investigation-only requests stop at diagnosis.
5. Implement the focused change, run aidlc-verify and independent aidlc-review, then refresh knowledge and hand off.

Hotfix mode narrows scope and prioritizes a bounded remedy; it does not bypass baseline/review gates or authorize production access. Preserve unrelated refactors for separate work.
