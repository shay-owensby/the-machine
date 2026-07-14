# config.yaml — Canonical Schema (version 1)

Location: `<client-project>/email-marketing/config.yaml`. Written by `/setup-email-marketing`, read by every command/skill/agent. YAML (not JSON) so humans can annotate it with comments.

**Hard rule: no secrets in this file.** Credentials are referenced by env var NAME; values live in the client's gitignored `.env`.

## Annotated schema

```yaml
version: 1                          # schema version — bump only with plugin migration guidance

setup:
  completed: true                   # THE gate. false/missing → all commands refuse to run
  completed_at: "2026-07-14"        # ISO date of last successful setup run
  plugin_version: "0.1.0"           # plugin version that wrote this config

platform:
  name: mailchimp                   # mailchimp | klaviyo | constant_contact | omnisend | moosend | moego
  connection: api_key               # api_key | oauth | mcp | none (moego/file_only)
  auth_env_var: MAILCHIMP_API_KEY   # env var NAME holding the key/token (api_key). oauth platforms may
                                    # use multiple vars — see extras and the platform reference doc
  mcp_server_name: null             # connection: mcp → server key in the client's .mcp.json
  extras: {}                        # platform-specific values, documented per platform reference, e.g.:
                                    #   mailchimp:        { server_prefix: us21 }
                                    #   constant_contact: { client_id_env: CC_CLIENT_ID,
                                    #                       client_secret_env: CC_CLIENT_SECRET,
                                    #                       refresh_token_env: CC_REFRESH_TOKEN }

delivery:
  mode: api_draft                   # api_draft (create platform draft — NEVER send) | file_only
  drafts_dir: email-marketing/drafts  # relative to project root; issues live in <dir>/YYYY-mm-dd/

audience:                           # required when delivery.mode: api_draft
  list_id: "abc123def4"             # platform list/audience id
  segment_id: null                  # optional narrower segment
  from_name: "Acme Grooming"
  from_email: "hello@acme.example"
  reply_to: "hello@acme.example"

brand:
  about_file: ABOUT.md              # resolved path (project-root relative) or null → no business-facts source
  soul_file: SOUL.md                # resolved path (project-root relative) or null → degraded voice mode
  design_file: DESIGN.md            # resolved path or null → degraded image styling
  industry: "Pet grooming salon"    # derived from ABOUT.md when present; fallback when about_file: null
  audience_description: "Local pet owners, mostly dogs, family-oriented"  # same derivation/fallback rule
  website: "https://acme.example"   # same derivation/fallback rule
  topic_hints:                      # 3–5 seed themes the researcher should orbit
    - seasonal coat care
    - new services
  timezone: America/Chicago

sections:                           # recurring blocks in every issue; array order = order within a position
  - id: latest-blog
    title: "From the Blog"
    type: dynamic                   # dynamic = fetched fresh each issue from `source`
    source: "https://acme.example/blog"
    position: after_body            # top | after_body | bottom
  - id: booking-cta
    title: "Book Now"
    type: static                    # static = fixed content below, rendered verbatim each issue
    content: |
      <p>Ready for a fresh cut? <a href="https://acme.example/book">Book your appointment</a>.</p>
    position: bottom

images:
  enabled: true
  provider: higgsfield_mcp          # only supported provider currently
  hosting: platform_upload          # platform_upload (re-upload to platform media library — recommended
                                    # for api_draft) | hosted_url (use generator CDN URL; user must
                                    # re-host before sending — flagged in meta.yaml)
  per_issue: 1                      # hero image count target; sections may add more
  style_notes: ""                   # additions beyond DESIGN.md, never contradicting it

analytics:
  enabled: true                     # run email-campaign-analyst pre-pass (api_draft platforms only)

schedule:                           # informational only — the plugin NEVER sends or schedules
  cadence: weekly
  send_day: tuesday
```

## Validation matrix

| Field | Required when | Notes |
|---|---|---|
| `setup.completed: true` | always | the gate |
| `platform.name` | always | one of the six supported values |
| `platform.auth_env_var` | `connection: api_key` | name only |
| `platform.mcp_server_name` | `connection: mcp` | must exist in client `.mcp.json` |
| `audience.list_id`, `from_*` | `delivery.mode: api_draft` | |
| `delivery.mode: file_only` | `platform.name: moego` | forced — no public campaign API |
| `sections[].source` | `type: dynamic` | URL fetched fresh each issue |
| `sections[].content` | `type: static` | HTML or markdown rendered verbatim |

## meta.yaml (per-issue, written by the orchestrator into drafts/YYYY-mm-dd/)

```yaml
date: "2026-07-14"
topic: "Summer coat care for double-coated breeds"
topic_slug: summer-coat-care
subject:
  a: "Is your dog's summer cut making them hotter?"
  b: "The double-coat mistake most owners make in July"
  c: "Keep them cool: summer grooming, done right"
  chosen: a                        # null until the user picks
preview_text: "What the fluff — shaving isn't always the answer."
images:
  - file: images/hero.png
    url: "https://…"               # final URL used in HTML
    hosting: platform_upload       # hosted_url ⇒ add re_host_before_send: true
    alt: "Golden retriever being brushed outdoors"
campaign_id: null                  # platform draft id when delivery.mode: api_draft
platform: mailchimp
status: draft                      # draft | delivered_api | delivered_file
qa: passed                        # passed | passed_with_warnings | see notes
notes: ""
```
