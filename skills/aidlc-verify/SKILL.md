---
name: aidlc-verify
description: Execute configured checks and evaluate acceptance criteria against actual evidence. Use to verify a design, implementation, bug fix, or refactor before review and handoff.
---

# Verify with evidence

Read [the shared protocol](references/protocol.md), then run `gate --skill aidlc-verify` with the active `--work WORK_ID` when source has changed.

1. Resolve the target design/source snapshot, baseline, criteria, and `.aidlc/config/quality.json`. Read applicable test rules.
2. Choose checks relevant to the change and required by policy. Inspect configured commands before executing them under normal host permissions; config is not permission to run arbitrary side effects.
3. Record each command/check ID, working directory, environment limits, timestamps, exit code, source fingerprint, and output reference under the work's `verification/` directory.
4. Produce the acceptance matrix: criterion ID/revision, implementation references, verification method, check IDs, evidence, result, and limitations. Distinguish `passed`, `failed`, `not_run`, and `unavailable`. Manual observations require provenance.
5. Separate pre-existing failures from new failures; do not silently waive either. Report mandatory criteria lacking evidence as incomplete.
6. Update `progress.md`. Verification does not substitute for independent review, and source changes invalidate affected evidence.

Do not create tests that merely mirror implementation or claim full equivalence from a finite suite. Use `test-design` when the verification strategy itself is missing.
