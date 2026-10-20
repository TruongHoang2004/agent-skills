---
name: ticket-refine
description: Refine an incomplete ticket into actionable behavior, acceptance criteria, scope, and dependencies. Use when a ticket cannot yet be implemented without guessing.
---

# Refine a ticket

Read [the shared protocol](references/protocol.md), then run `gate --skill ticket-refine`.

1. Read the explicitly supplied ticket or configured provider source and preserve provenance in a work record.
2. Compare the request to the system baseline. Identify ambiguous behavior, missing criteria, dependencies, affected users, and compatibility constraints.
3. Ask focused questions about consequential gaps. Distinguish user-confirmed decisions from proposed assumptions.
4. Write `ticket-refinement.md` with revised scope, exclusions, acceptance criteria, dependencies, design references, and remaining questions.
5. Classify readiness as `ready`, `needs_clarification`, or `needs_design`. Hand off to dev only when actionable; route material architectural decisions to inception.

Do not modify product source or update the external ticket unless explicitly authorized. A local refinement supplements the source ticket; it is not a claim that the provider was updated.
