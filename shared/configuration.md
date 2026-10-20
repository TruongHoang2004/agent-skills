# Configuration contract

All paths are relative to the installed project root. Never derive a provider from another project's config.

`tickets.json` has `schemaVersion: 1`, `defaultProvider` (null until configured), a `providers` object, a `routing` array, and `writeBack: "draft"`. A local provider requires `root`. Remote providers require a `connection` identifying an available host connector or CLI; optional `baseUrl`, `projectKeys`, and `fieldMapping` describe actual project values. Do not store credentials or embed arbitrary shell code.

Example:

```json
{
  "schemaVersion": 1,
  "defaultProvider": "local",
  "providers": {"local": {"root": "tickets"}},
  "routing": [{"prefix": "local:", "provider": "local"}],
  "writeBack": "draft"
}
```

Resolve explicitly qualified provider references first, then configured URL/prefix matches, then the default. More than one matching provider is an error. Fetch through tools actually available in the host; unavailable remote transports block rather than silently fall back. Remote provider fetching is performed by the skill using the host's connected tools, not by the installer.

`quality.json` has `schemaVersion: 1` and `checks`: objects with unique `id`, argv-style `command` array, relative `cwd`, and `required` boolean. Commands run only after inspection and under host permissions. No checks configured is not equivalent to all checks passed.

`review.json` has `schemaVersion: 1`, `requiredRoles` including `solution-architect`, `security`, and `quality-assurance`, `blockingSeverities`, and a positive `maxRemediationCycles`. Additional supported roles are `maintainability`, `performance`, `data`, `operations`, and `frontend`. Match conditional specialists to semantic impact even when not listed as globally required.

Rule documents explain IDs, scope, rationale, source, and decisions in English. Keep machine routing in config and avoid conflicting duplicate values in prose.
