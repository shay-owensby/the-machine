# config.yaml — Canonical Schema (version 1)

Location: `<client-project>/human-resources/config.yaml`. Written by `/setup-human-resources`, read by every command/skill/agent. YAML (not JSON) so humans can annotate it with comments.

**Hard rule: no secrets in this file.** Credentials are referenced by env var NAME; values live in the client's gitignored `.env`.

## Annotated schema

```yaml
version: 1                          # schema version — bump only with plugin migration guidance

setup:
  completed: true                   # THE gate. false/missing → all commands refuse to run
  completed_at: "2026-07-14"        # ISO date of last successful setup run
  plugin_version: "0.1.0"           # plugin version that wrote this config

company:
  about_file: ABOUT.md              # resolved path (project-root relative) or null → no company-facts source
  soul_file: SOUL.md                # resolved path or null → degraded voice mode (employee-facing comms)
  design_file: DESIGN.md            # resolved path or null → degraded document styling
  name: "Acme Co"                   # legal/common name used in documents
  industry: "Regional coffee retailer"
  size: 45                          # current headcount (integer) — drives which policies/thresholds apply
  employment_types:                 # types the company actually uses
    - full_time
    - part_time
    - contractor
  locations:                        # physical/legal presence — the ground truth for compliance work
    - country: US
      region: California            # state/province; drives jurisdiction-specific rules
      city: Oakland
  remote_policy: hybrid             # onsite | hybrid | remote | null
  union: false                      # true → enables labor-relations (CBA/grievance/bargaining) features
  timezone: America/Los_Angeles

legal:
  jurisdictions:                    # authoritative list for all compliance/statutory work; codes are free-form
    - US-Federal                    #   but stable, e.g. US-Federal, US-CA, CA-ON, UK, EU
    - US-CA
  counsel_review: true              # true → stamp policies/contracts/terminations/audits with the review banner
  disclaimer_required: true         # always true — outputs are drafts for review, not legal advice

hris:
  system: none                      # bamboohr | gusto | rippling | workday | adp | other | none
  connection: none                  # none | manual | api_key | mcp
  auth_env_var: null                # connection: api_key → env var NAME holding the token
  mcp_server_name: null             # connection: mcp → server key in the client's .mcp.json
  extras: {}                        # system-specific values (e.g. { subdomain: acme })

exports:
  root: human-resources             # base dir (project-root relative) for ALL deliverables; see folder-map.md

confidentiality:
  pii_handling: strict              # strict (default) — PII never leaves the project; records segregated
  records_dir: human-resources/reports/employee-reports   # where identifiable records/reviews live

defaults:
  approver: "HR Manager"            # named role that signs off drafts (informational, used in doc footers)
  document_footer: ""               # optional standard footer appended to formal HR documents
```

## Validation matrix

| Field | Required when | Notes |
|---|---|---|
| `setup.completed: true` | always | the gate |
| `company.name` | always | used throughout generated documents |
| `company.size` | always | integer headcount; some statutory thresholds key off it (e.g. FMLA-size rules) |
| `company.locations` (≥1) | always | at least one location with `country` |
| `legal.jurisdictions` (≥1) | always | required before any compliance/termination/statutory-policy output |
| `hris.auth_env_var` | `hris.connection: api_key` | name only, never a value |
| `hris.mcp_server_name` | `hris.connection: mcp` | must exist in client `.mcp.json` |
| always | no secrets | env var names only; scan for accidental values |

## Notes for setup

- `company.size` and `legal.jurisdictions` together determine which statutory rules can even be discussed. Never assert a threshold-based rule (leave entitlements, ACA, WARN, etc.) without checking size and jurisdiction — and always flag it for counsel verification.
- `union: true` unlocks references and agent behaviors for collective bargaining, grievance procedures, and contract interpretation; when false, those paths are skipped rather than half-built.
- Keep `exports.root` as the default `human-resources` unless the client insists — the folder map and every component assume it.
