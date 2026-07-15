---
name: hr-records
description: Maintain accurate, confidential employee records and interact with the HRIS safely — organize the personnel file vs. a SEPARATE confidential medical file vs. payroll/tax vs. work-authorization/eligibility files (separation is legally important), apply a records-retention approach whose periods vary by jurisdiction and record type (verify, never assert), enforce access controls and confidentiality, track changes for accuracy, and treat HRIS access as READ-ONLY automatic with all writes drafted and confirmed in the main conversation. Use when the client wants to organize employee files, set up a records-retention plan, define who may access what, review a record for exposed sensitive data, or pull/update records via the HRIS.
---

# HR Employee Records & HRIS Management

Keeps employee records accurate, properly separated, access-controlled, and confidential — and interacts with the client's HRIS safely (read freely, write only with explicit confirmation). This is the plugin's most sensitive data surface: employee records, especially medical/health data, are the highest-risk PII the company holds. This skill owns HR function #11 and exports to `reports/employee-reports/` — the **confidential** zone (see the folder map). It never treats any of this data casually.

## Setup gate (run first)

Enforce the config gate before any work, per `${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`: look for `human-resources/config.yaml` at project root, require `version: 1` and `setup.completed: true`. If missing or invalid, STOP and tell the user exactly:
> Human resources isn't configured for this project yet. Run `/setup-human-resources` first.

Then load context: `company.size`, `company.locations` and `legal.jurisdictions` (retention periods and required records are jurisdiction- and record-type-specific), `confidentiality.pii_handling` and `confidentiality.records_dir` (where identifiable records live — treat as strict), and the `hris.*` block (`system`, `connection`, `auth_env_var`, `mcp_server_name`) for how — and whether — to touch the HRIS. Honor degraded modes: empty `legal.jurisdictions` → make **no** jurisdiction-specific retention or required-record claim; produce a general record-inventory framework labeled "retention periods must be localized and verified with counsel". HRIS unreachable / not configured → work file-based and produce a manual-entry guide; never block on system access.

## Two standing safety rules (paramount — this skill enforces them harder than any other)

1. **Drafts, not legal advice — file structure and retention are jurisdiction-specific.**
   - **File separation is a legal requirement in many jurisdictions, not a preference.** The general personnel file, a **separate confidential medical file**, payroll/tax records, and work-authorization/eligibility records must be kept apart with different access. Never co-mingle them. **Flag** the separation as jurisdiction-driven and route the specifics to counsel.
   - **Retention periods vary by jurisdiction and record type.** Never assert a specific retention period as fact. In the retention framework, every period is a **placeholder marked "verify per jurisdiction"** — never fabricate a number of years. Point to the jurisdiction's labor/employment agency and counsel.
   - When `legal.counsel_review: true`, stamp any formal records-management or retention policy with **"⚠️ Draft — requires review by qualified HR/legal counsel before use"**.
2. **Confidential by default — and this is where confidentiality is enforced for the whole plugin.** Employee records are the most sensitive PII the company holds; **medical/health data is the most sensitive of all**.
   - **Everything stays in-project** under `reports/employee-reports/` (the confidential zone). **Never** paste an employee record, name tied to sensitive data, SSN/national ID, bank/payroll detail, or any medical/health information into an external service, web search, MCP call, or any draft that leaves the project.
   - **Never invent employee data** — placeholder or supplied data only.
   - **Actively warn on exposure:** if you detect records, SSNs/national IDs, bank details, medical information, or credentials sitting in a **tracked (non-gitignored) or shareable** location, stop and warn the user, and offer to help move or redact them. The confidential zone should live in a gitignored area when the repo is shared.
   - **Medical files are separate** — the records skill is where the separation rule from the wellness skill is actually operated. Injury, leave, accommodation, and any health documentation belongs in the separate confidential medical file, never in the personnel file.

## Operating method

1. **Sort every record to the right file.** Employee records are not one pile. Using `references/records-retention-framework.md`, place each record in its file, each with its own access rule:
   - **Personnel file** — the general employment record: offer/employment agreement, job description, position/pay history, performance reviews, acknowledgments, discipline, training records.
   - **Confidential medical file (SEPARATE)** — anything medical/health: injury and workers'-comp records, leave-of-absence medical documentation, accommodation medical information, medical exam/fitness-for-duty results, benefits enrollment health data. **Kept physically/logically apart with tighter access — legally required in many jurisdictions; flag and verify.**
   - **Payroll / tax file** — compensation, tax-withholding, direct-deposit/banking, timekeeping and wage records. Financial PII — restricted access.
   - **Work-authorization / eligibility file (SEPARATE)** — employment-eligibility/work-authorization verification records are commonly required to be kept **separate** from the personnel file, with their own retention rule. **Which forms, how long, and where — jurisdiction-specific; flag and verify.**
   - Recruitment, performance, and employee-relations/investigation records also have their own homes and access rules — see the framework table.
2. **Set the retention approach.** For each record category, capture: file location, who may access, **retention period (placeholder — "verify per jurisdiction")**, and disposal method. Never assert a period as fact. Prefer a living retention schedule with a "last verified" date over one-off assertions. Coordinate the compliance view of retention with `legal-compliance/` (the hr-compliance skill tracks the retention *obligation*; this skill operates the *files*).
3. **Enforce access controls & confidentiality.** Define **who may see what**: managers see role-relevant personnel data on a need-to-know basis; medical, payroll, and work-authorization files are restricted to specifically authorized roles; employees have a right (jurisdiction-specific — verify) to access their own records. Least-privilege by default. Document the access model so it's applied evenly.
4. **Keep records accurate and track changes.** Records must be current and correct. When a record changes (name, address, status, pay, emergency contact), capture **what changed, when, and who authorized it** — a simple change log. Accuracy is both a legal and an operational obligation; a stale record causes real harm (wrong pay, wrong emergency contact). Never alter a record without an authorization trail.
5. **Interact with the HRIS safely — READ-ONLY automatic; WRITES drafted and confirmed.** Follow the hr-config skill's HRIS rules exactly (`${CLAUDE_PLUGIN_ROOT}/skills/hr-config/SKILL.md`):
   - `hris.connection: none` (default) → draft records and reports; a human enters data into the HRIS. Produce a clear manual-entry guide.
   - `hris.connection: api_key` / `mcp` → **read-only** endpoints (fetch roster, list positions, read a record) may be called freely to keep files accurate. **Any write — create, update, change status/pay, terminate — is never automatic.** Draft the change, show it, and perform it **only in the main conversation**, only when the user explicitly asks, never from a subagent, never speculatively. Source credentials inline from the client's gitignored `.env`; never write a credential value anywhere.
   - Any data pulled from the HRIS is PII — it stays in the confidential zone and never leaves the project.
6. **Review a record for exposed sensitive data** when asked (or when you notice it): scan for SSNs/national IDs, bank details, medical/health information, and credentials in the wrong file or a shareable/tracked location, and recommend separation, restriction, redaction, or gitignoring.

## When to use the reference

- **`references/records-retention-framework.md`** — organizing employee files and setting a retention schedule: a table of record categories (personnel, medical/confidential, payroll/tax, benefits, work-authorization/eligibility, recruitment, performance, employee-relations/investigation) with file location, who-may-access, retention period (placeholder + "verify per jurisdiction"), and disposal method; plus the separate-medical-file rule and a data-subject-access note (privacy-law-flagged).

## Boundaries

- Export **only** to `reports/employee-reports/` — the confidential zone. Never write identifiable records elsewhere and never invent new top-level folders. The confidential zone should be gitignored when the repo is shared.
- **Never** transmit an employee record, SSN/national ID, bank detail, or medical/health information outside the project — no external service, web search, or MCP call. Never invent employee data.
- **Separate files are mandatory:** personnel vs. confidential medical vs. payroll/tax vs. work-authorization/eligibility. Never co-mingle. Flag the separation as jurisdiction-driven and verify with counsel.
- **Never fabricate a retention period.** Every period is a placeholder marked "verify per jurisdiction"; point to the authoritative source. The retention *obligation* view lives in `legal-compliance/`.
- **HRIS writes are never automatic** — read-only free, writes drafted and confirmed in the main conversation only, per the hr-config HRIS rules. No credential value ever written to a file, draft, or commit.
