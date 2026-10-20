# Independent review contract

Dispatch roles under their installed names `aidlc-ROLE`, for example `aidlc-security`. The coordinator owns state and report files. Reviewers only return their reports and must not modify source, post externally, or spawn additional agents.

Required roles: Solution Architect, Security, and Quality Assurance. Add Data for persisted-format/schema changes, Operations for runtime/deployment behavior, Performance for hot paths/NFRs, Frontend for user interaction, and Maintainability for broad refactors.

Every result includes:

```json
{
  "reviewId": "REV-001",
  "role": "security",
  "agentSessionId": "actual-host-session-id",
  "snapshotDigest": "actual-reviewed-snapshot",
  "status": "completed",
  "coverage": ["src/search.py"],
  "limitations": [],
  "findings": []
}
```

Each finding needs `id`, `severity` (`critical`, `high`, `medium`, `low`), `confidence`, `title`, `location`, `evidence`, `impact`, `recommendation`, and criterion/rule references where relevant. Use concrete paths/symbols. Do not fabricate observations, sessions, or scanner results.

Aggregate outcomes are `satisfied`, `changes_required`, `incomplete`, and `satisfied_with_accepted_risks`. Missing required sessions or mismatched snapshots is incomplete. Preserve raw findings and rationale for deduplication or dismissal. Valid risk acceptance names the actual user decision and affected revision.

Provide a shared factual envelope plus focused role context. Allow inspection of surrounding source from the same snapshot. Reviewers must not receive one another's conclusions before their initial assessment.

Native tool restrictions differ by host. For reliable read-only isolation, dispatch against a read-only source snapshot where available; a prompt alone cannot enforce filesystem permissions. Test execution belongs in verification, not reviewer shell commands.
