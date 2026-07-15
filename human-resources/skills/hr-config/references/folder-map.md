# Export Folder Map

Every human-resources deliverable is written under `exports.root` (default `human-resources/`) in the **client project**. This map is the single source of truth for where each kind of output goes. Components must route by it and must not invent new top-level folders without the user's say-so.

`/setup-human-resources` creates this whole tree (with a `.gitkeep` in each empty dir) so every component can assume the paths exist.

```
human-resources/
├── config.yaml                         # per-client config (no secrets)
├── compensation-benefits/              # pay bands, comp philosophy, benefits summaries, total-rewards statements, offer comp models
├── diversity-equity-inclusion/         # DEI strategy, pay-equity analyses, inclusion initiatives, ERG plans, DEI reports
├── employee-relations/                 # case files, investigation notes, mediation/grievance records, disciplinary memos, labor-relations & CBA material
├── health-safety-wellness/             # safety programs, incident/OSHA-type logs, EAP & wellness program docs, ergonomic/return-to-work plans
├── legal-compliance/                   # compliance audits, required-posting checklists, statutory policy trackers, regulatory-change notes
├── offboarding/                        # exit checklists, exit-interview summaries, final-pay/property checklists, separation & termination packets
├── onboarding/                         # new-hire checklists, orientation plans, welcome packets, 30/60/90 plans, equipment/access requests
├── policies/                           # employee handbook, standalone policies, codes of conduct, policy acknowledgment forms
├── recruitment/                        # job descriptions, postings, sourcing plans, screening notes, interview kits, scorecards, offer letters
│   └── <req-or-role-slug>/             #   optional per-requisition subfolder for an active search
├── reports/
│   ├── analytics/                      # cross-function HR reports & dashboards (headcount, turnover, DEI, comp, hiring funnel) — YYYY-mm-dd-<topic>.md
│   └── employee-reports/               # CONFIDENTIAL — identifiable per-employee records
│       └── performance-management/     #   reviews, goals/OKRs, calibration, PIPs, 1:1 & feedback records
├── scheduling/                         # shift schedules, coverage/staffing plans, interview scheduling, PTO/leave calendars
├── strategy/                           # HR strategy, workforce planning, org design/charts, succession plans, headcount forecasts
└── training-development/               # training curricula, course outlines, LMS content, career-path & leadership-development plans
```

## Routing table (15 HR functions → folder)

| HR function | Primary folder | Notes |
|---|---|---|
| 1. Recruitment & staffing | `recruitment/` | per-search subfolder optional |
| 2. Onboarding & orientation | `onboarding/` | |
| 3. Compensation & benefits | `compensation-benefits/` | benchmarking reports may also land in `reports/analytics/` |
| 4. Performance management | `reports/employee-reports/performance-management/` | identifiable → confidential |
| 5. Training & development | `training-development/` | |
| 6. Employee relations | `employee-relations/` | case files are confidential |
| 7. Legal compliance | `legal-compliance/` | |
| 8. Policy development | `policies/` | the handbook lives here |
| 9. Health, safety, wellness | `health-safety-wellness/` | |
| 10. Diversity, equity, inclusion | `diversity-equity-inclusion/` | pay-equity analyses may also feed `reports/analytics/` |
| 11. Employee records & HRIS | `reports/employee-reports/` | confidential PII |
| 12. Workforce planning & org design | `strategy/` | |
| 13. Offboarding & termination | `offboarding/` | |
| 14. Labor relations | `employee-relations/` | only when `company.union: true` |
| 15. HR strategy & business partnership | `strategy/` | cross-function dashboards go to `reports/analytics/` |

## Confidentiality zones

`reports/employee-reports/` (including `performance-management/`) and `employee-relations/` hold **identifiable employee PII**. Per the hr-config skill: these stay in-project, are never sent to any external service, and should live in a gitignored area if the repo is shared. Everything else (templates, policies, generic plans) is shareable within the org.

## File naming

- Dated reports/analyses: `YYYY-mm-dd-<kebab-topic>.md`.
- Per-employee records: `<employee-slug>/` subfolder or `<employee-slug>-<doc>.md`, kept out of shareable areas.
- Formal documents (handbook, offer letter, policy): descriptive kebab-case names; version in front-matter or filename suffix (`-v2`) when iterating.
