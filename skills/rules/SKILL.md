---
name: rules
description: Configure repository-specific engineering rules, ticket sources, verification commands, and review policies after reverse engineering. Use when project conventions or integration routing need setup or change.
---

# Author repository rules

Read [the shared protocol](references/protocol.md), then run the mandatory `gate --skill rules`. Rules are baseline-gated too.

1. Read the current baseline, existing repository guidance, `.aidlc/rules/index.md`, and `.aidlc/config/*.json`. Preserve established conventions.
2. Translate the user's requested policy into a focused English rule. Ask only for missing consequential choices: ticket provider/connection/project, acceptance-criteria field, test command, or architectural constraint. Do not guess account URLs, credentials, or connection names.
3. Update the applicable rule documents and typed config together. Use `.aidlc/config/tickets.json` for provider/routing data, `quality.json` for check definitions, and `review.json` for reviewer selection. Read [configuration contracts](references/configuration.md).
4. Keep routing data in JSON and explanations in Markdown. Maintain an index of rule IDs, path scopes, rationale, and sources. If instructions conflict, show the concrete conflict rather than silently choosing one.
5. Run `python3 .aidlc/runtime/aidlc.py config-check`. Report the effective provider, verification checks, reviewer roles, and unresolved connection availability.
6. Identify active work affected by changed rules and record which decisions/checks require revalidation. Preserve pinned ticket sources for existing work.

Keep secrets outside the repository. Defining a status transition or posting rule does not authorize performing it. Do not rewrite host configuration or unrelated instructions to enforce a project preference.
