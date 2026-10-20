---
name: release-readiness
description: Assess a verified change for release and prepare rollout, migration, observability, and recovery artifacts. Use before release planning; it does not deploy or merge.
---

# Prepare a release

Read [the shared protocol](references/protocol.md), then run `gate --skill release-readiness`.

1. Identify the exact release snapshot and included work. Confirm verification, review, criteria, and accepted risks refer to that snapshot.
2. Report missing or stale evidence. Do not reuse a passing review from another revision.
3. Write a release runbook covering applicable deployment order, configuration changes, feature flags, migration/backfill, health checks, metrics, owners, and recovery criteria.
4. Assess rollback or forward recovery realistically, including irreversible data changes. Do not invent a safe down migration.
5. Produce changelog/PR-ready local drafts and a readiness outcome with unresolved blockers and accepted risks.

This skill prepares artifacts. It does not grant or perform production deployment, external posting, merge, or ticket transitions without separate user authorization.
