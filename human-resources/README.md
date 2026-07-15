# human-resources

A brand-agnostic Claude Code plugin that acts as a per-client **HR department**: a team of skills and agents covering the full HR lifecycle described in the 15 core HR functions — recruitment, onboarding, compensation & benefits, performance management, training & development, employee & labor relations, legal compliance, policy/handbook development, health-safety-wellness, DEI, employee records/HRIS, scheduling, workforce strategy & org design, and offboarding.

> **Two safety rules baked into every component:**
> 1. **Drafts, not legal advice.** HR touches employment law. Everything produced is a draft/analysis for review by the client's qualified HR professional and/or employment counsel — never definitive legal advice, never a compliance guarantee. Jurisdiction-specific claims are scoped to the configured `legal.jurisdictions` and flagged for verification.
> 2. **Confidential by default.** Employee PII stays inside the client project, is never sent to an external service, and lives in segregated confidential zones. The plugin never changes an employee's status/pay/employment in a live system automatically — it drafts, confirms, then acts only on explicit instruction.

## Quick start (in a client project)

1. Install/enable this plugin, then run **`/setup-human-resources`** in the client project. The wizard configures company facts, headcount, locations → jurisdictions, union status, HRIS connection (env var names only — secrets live in the client's gitignored `.env`), brand files (`ABOUT.md`, `SOUL.md`, `DESIGN.md`), and confidentiality settings, and creates the export folder tree.
2. Run a pipeline command (`/hr-hire`, `/hr-onboard`, `/hr-offboard`, `/hr-review-cycle`, `/hr-handbook`) or just ask for the task ("draft a PTO policy", "screen these resumes", "audit our job postings for compliance") — the matching `hr-*` skill handles it.

Everything refuses to run until `/setup-human-resources` has completed.

## What lands in the client project

All deliverables are written under `human-resources/` per the [folder map](skills/hr-config/references/folder-map.md):

```
<client>/
├── ABOUT.md / SOUL.md / DESIGN.md      # company facts / voice / doc styling (read, never written)
└── human-resources/
    ├── config.yaml                     # per-client config (no secrets)
    ├── recruitment/                    # JDs, postings, screening notes, interview kits, offers
    ├── onboarding/  offboarding/       # checklists, orientation & 30/60/90 plans, exit packets
    ├── compensation-benefits/          # pay bands, comp philosophy, benefits & total-rewards docs
    ├── diversity-equity-inclusion/     # DEI strategy, pay-equity analyses, ERG plans
    ├── employee-relations/             # case files, investigations, grievances, CBA material (confidential)
    ├── legal-compliance/               # audits, posting checklists, statutory trackers
    ├── policies/                       # employee handbook, standalone policies, codes of conduct
    ├── health-safety-wellness/         # safety programs, incident logs, EAP & wellness docs
    ├── training-development/           # curricula, course outlines, career/leadership paths
    ├── scheduling/                     # shift/coverage plans, interview & PTO calendars
    ├── strategy/                       # workforce planning, org design, succession, forecasts
    └── reports/
        ├── analytics/                  # cross-function HR reports & dashboards
        └── employee-reports/           # CONFIDENTIAL identifiable records
            └── performance-management/ #   reviews, goals, calibration, PIPs
```

## Architecture

**Commands** (orchestration):
- `setup-human-resources` — per-client configuration wizard + folder-tree creation; everything else refuses to run until it completes.
- `hr-hire` — recruitment pipeline: intake → JD → posting/sourcing → screening → interview kit → offer.
- `hr-onboard` — new-hire onboarding: checklist, orientation, access/equipment, 30/60/90 plan.
- `hr-offboard` — separation/termination: eligibility & risk check, exit checklist, final-pay/property, exit interview.
- `hr-review-cycle` — performance review cycle: self/manager inputs → calibration → review packets.
- `hr-handbook` — build or update the employee handbook from the policy library.

**Skills** (domain expertise + playbooks + reference knowledge), one per HR function, all prefixed `hr-`:
- `hr-config` — config loading/validation, the setup gate, export folder map, and the two standing safety rules. **Read by everything.**
- `hr-recruitment`, `hr-onboarding`, `hr-offboarding`, `hr-compensation-benefits`, `hr-performance`, `hr-training`, `hr-employee-relations`, `hr-compliance`, `hr-policy`, `hr-wellness`, `hr-records`, `hr-scheduling`, `hr-strategy`, `hr-dei`, `hr-reports`.

**Agents** (isolated subagent system prompts for heavier generative/analytical work):
- `hr-recruiter` — job descriptions, sourcing plans, resume screening.
- `hr-interview-designer` — structured interview kits, question banks, scorecards.
- `hr-policy-writer` — handbook sections and standalone policies.
- `hr-compliance-auditor` — audits documents/practices against a jurisdiction checklist.
- `hr-comp-analyst` — pay-band design and compensation benchmarking.
- `hr-performance-reviewer` — review packets, calibration inputs, PIPs.
- `hr-training-designer` — curricula and course outlines.
- `hr-er-advisor` — employee-relations casework, investigation plans, documentation.
- `hr-report-writer` — cross-function HR reports and dashboards.

## Conventions

- **Brand-agnostic**: no client is named in the plugin. All specifics come from `config.yaml` + `ABOUT.md`/`SOUL.md`/`DESIGN.md` in the consuming project.
- **Setup gate**: components read config through `hr-config` and stop with a single instruction to run `/setup-human-resources` if it's missing.
- **Prefix**: skills, agents, and commands are prefixed `hr-` (except the mandatory `/setup-human-resources`). Export **data paths** are never prefixed — they match the folder map.
