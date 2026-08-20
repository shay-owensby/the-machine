# Troubleshooting

Run this first, always:

```bash
python3 scripts/check_config.py --project-root .
python3 scripts/check_config.py --list-sites     # what CAN this identity read?
```

Exit codes across the skill: `0` fine · `1` partial · `2` configuration · `3`
auth, permission or no data · `4` transient, retry.

## Configuration

**"The shared agency credential file is not there"**
`~/clients/agency.env` is missing. Create it from `assets/agency.env.example`,
or point elsewhere with `AGENCY_ENV=/path/to/agency.env`. Never copy it into a
client project.

**"No usable Google credentials"**
The OAuth trio is incomplete and no service-account key was found. Add the
missing keys to `agency.env`. `check_config.py --no-network` shows which are
`present` and which are `missing`, without printing any of them.

**"No Search Console property"**
`GSC_SITE_URL` is not set. It belongs in the **client project's** `.env`, not the
agency file. `check_config.py --list-sites` prints the exact strings available.

**"GSC_SITE_URL=... is not a Search Console property identifier"**
A bare hostname was given. It must be `sc-domain:example.com` or
`https://www.example.com/` — the skill will not guess which, because they are
different properties with different data.

## Authentication

**`invalid_grant`**
Usually an OAuth consent screen left in *Testing*, which expires refresh tokens
after seven days. Publish the app to Production or make it Internal, then
re-mint. Also caused by a revoked token or a changed password.

**`invalid_client`**
`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` do not match a live OAuth client.
Re-copy both from the Cloud console.

**`invalid_scope`, or the token works for Google Ads but not here**
The refresh token was minted without
`https://www.googleapis.com/auth/webmasters.readonly`. Re-mint the shared token
with both scopes, or add a Search Console-only `GSC_REFRESH_TOKEN` to
`agency.env`. See `references/authentication.md`.

**`unauthorized_client` with a service account**
Domain-wide delegation is not authorised for that client ID and scope. A
Workspace admin grants it under Security → API controls → Domain-wide delegation.

**"Service-account authentication needs an RSA signature..."**
Neither the `cryptography` package nor `openssl` is available. Either
`python3 -m pip install cryptography`, or use the OAuth user credentials, which
need nothing installed.

## Property access

**403 "Google Search Console API has not been used in project ... or it is disabled"**
A **Google Cloud** problem, not a Search Console one. Enable the *Google Search
Console API* on the project behind these credentials, wait a minute, re-run.

**403 "User does not have sufficient permission for site ..."**
A **Search Console** problem, not a Cloud one. The identity is not on the
property. Ask an Owner to add it: Settings → Users and permissions → Add user →
Full or Restricted. For a service account, the address to add is its
`client_email` from the key file.

**404 / "GSC_SITE_URL is not among the properties this identity can read"**
The identifier does not match exactly. `https://example.com/`,
`https://www.example.com/` and `sc-domain:example.com` are three different
properties. `check_config.py --list-sites` prints the exact strings, and the
error names a same-domain near miss when one exists.

**Permission level `siteUnverifiedUser`**
Listed on the property but granted no data. An Owner must change the level to
Full or Restricted.

## Data

**"The property returned no finalised data in the last 14 days"**
Either the property is newly verified, it has no search traffic, or the
identifier points at a property that is not the live site — an `http://` prefix
property for an `https://` site does this. Check the site really is indexed and
receiving impressions in the Search Console UI.

**The report stops two or three days before today**
Correct and deliberate. Search Console finalises data on a delay; the run uses
the latest finalised date and excludes provisional days. `freshness` in the
analysis file records both dates, and the report header states them.

**Numbers changed between two runs of the same period**
Search Console restates recent days. Run the analysis from the saved raw file
rather than re-fetching, and quote the retrieval date. If figures move for older
days, the earlier run probably included provisional data (`--data-state all`).

**Query clicks do not add up to total clicks**
Expected, always. Search Console withholds rows — anonymised queries especially.
`queries.reconciliation.coverage_pct` quantifies the gap for this property. Quote
property-level KPIs from the KPI table and treat query tables as the visible
subset.

**Search Console clicks do not match GA4 sessions**
They measure different things: a click on a search result versus a session on the
site. Redirects, bots, consent handling, cross-device behaviour and different
attribution windows all separate them. Neither is wrong, and no reconciliation
should be attempted in the report.

**Search appearance returns nothing**
Common. Many properties trigger no result features that Search Console reports.
The section is skipped with that reason rather than shown empty.

**HTTP 400 on a Search Analytics query**
Almost always an unsupported dimension combination: `searchAppearance` cannot be
combined with any other dimension; `discover` and `googleNews` have no `query`
dimension; `rowLimit` above 25,000; or a date outside the ~16-month window.

**The query extract looks truncated**
It is, and the analysis says so. Re-run with `--chunk-days 7` to retrieve in
slices and aggregate. Property-level KPIs are unaffected.

## Rate limits

**429 / `rateLimitExceeded`**
Quota is per property and per Cloud project. The scripts back off and retry five
times. If it still fails, wait and re-run — **do not report a partial extract as
final**. Trim optional datasets with `--skip query_page,countries` for a lighter
run.

**URL Inspection quota**
2,000 URLs per property per day, 600 per minute. The skill inspects at most
`GSC_MAX_URL_INSPECTIONS` (default 10) and only pages the performance data has
already flagged. On a quota error mid-run it stops, keeps what it has, and
records that the inspected set is partial.

## Charts

**"matplotlib is not installed"** — exit 4. Install it
(`python3 -m pip install matplotlib`) or accept a report without visuals: the
manifest lists every chart as skipped with that reason, and the report must say
the visuals are unavailable rather than describe charts that do not exist.

**A chart is missing from the manifest as "not drawn"** — read the `reason`. It
is written as a sentence the report can print. A chart is never drawn empty and
never filled with zeros.

## When nothing else explains it

```bash
python3 scripts/check_config.py --list-sites --json | head -40
python3 scripts/fetch_search_console.py --project-root . --days 7 \
  --skip query_page,countries,search_appearance --out /tmp/gsc-test --flat
python3 scripts/run_tests.py
```

A seven-day extract with the optional datasets skipped is a handful of calls and
isolates whether the problem is access, data, or analysis.
