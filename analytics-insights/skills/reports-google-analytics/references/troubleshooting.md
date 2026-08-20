# Troubleshooting

Start here, always:

```bash
python3 scripts/check_config.py
```

It separates the four things that go wrong — credentials, scope, property
access, and whether anything is being collected — and tells you which one it
is.

---

## Exit codes

Every script uses the same set, so a wrapper can branch on them.

| Code | Meaning | Next step |
|:--:|---|---|
| 0 | Success | — |
| 1 | Partial: core data retrieved, some optional datasets failed | Read `errors[]`; the report can still be written, with those sections omitted |
| 2 | Configuration problem | `configuration.md` |
| 3 | Authentication or property-access failure, or core data unavailable | `authentication.md` |
| 4 | Transient API failure | Retry; if it persists, quota |

---

## Configuration

**"The shared agency credential file is not there"**
`~/clients/agency.env` does not exist. Create it from
`assets/agency.env.example`, or point elsewhere with `--agency-env`.

**"Missing shared credential(s): …"**
The named key is absent from the agency file, the client `.env` and the
environment. It belongs in the agency file — not in the client project.

**"No GA4 property ID"**
Set `GA4_PROPERTY_ID` in the **client** project's `.env`, or pass
`--property-id` for one run. Find it at **Admin → Property → Property details**,
or run `check_config.py --list-properties`.

**"…which is a MEASUREMENT ID (the G- tag…)"**
`G-XXXXXXXXXX` is the tag on the website. The property ID is the number in the
same admin screen and in the `?p=` URL parameter.

---

## Authentication

**"OAuth refused the refresh token (invalid_grant)"**
In order of likelihood: the consent screen is still in *Testing* (those refresh
tokens expire after seven days); the token was revoked or the password changed;
the token does not belong to this client ID/secret pair.

**"The refresh token … was NOT granted a Google Analytics scope"**
The token is the Google Ads one. One token can carry both scopes — re-mint it
following `authentication.md`, and the Ads skill keeps working.

**`ACCESS_TOKEN_SCOPE_INSUFFICIENT`**
Same cause, surfacing at the report request instead of the token exchange.

---

## Property access

**`PERMISSION_DENIED` on the property**
The identity has never been added to this property. Someone with Administrator
rights must add it under **Admin → Property → Property access management** with
the **Viewer** role. Allow a few minutes to propagate; after ten it is real.

**`NOT_FOUND`**
The property does not exist or is invisible to this identity. Confirm the
number. `--list-properties` shows everything the identity can currently reach —
if the client's property is not in that list, access was never granted, or was
granted to a different Google account.

---

## API enablement

**"has not been used in project … or it is disabled" / `SERVICE_DISABLED`**
Enable the named API in the Google Cloud project that owns the credentials, then
wait a minute. This is a one-time agency-wide fix, not per client.

- Reporting needs the **Google Analytics Data API**.
- The **Google Analytics Admin API** is optional. Without it: no property name,
  no key-event definitions, no `--list-properties`. Numbers are unaffected.

---

## Quota and rate limits

**`RESOURCE_EXHAUSTED`**
Analytics Data API tokens are budgeted **per property per hour**, and shared
with anything else querying that property — including someone using the GA4
interface. The scripts back off and retry with jitter.

If it keeps failing:

- wait for the hour boundary and re-run;
- narrow the run: `--skip geo,browsers,os,pages,campaigns`;
- lower the row caps: `--top-n 25 --page-limit 50`;
- **never publish a partial run as a final report.** Exit code 1 means some
  sections are missing, and the report must say which.

The remaining quota is reported in `check_config.py` output under `quota` and
in the fetch summary, when the API returns it.

---

## Data problems that are not errors

**Zero sessions.** The property is reachable and recorded nothing. Establish
whether tracking is live before writing anything else — a report of zeros
presented as performance is worse than no report.

**Zero key events, with key events defined.** A measurement failure until
proven otherwise. Test each defined key event in GA4 DebugView or Realtime.
Do not report it as a conversion decline.

**Days with no data.** GA4 returned no rows for those dates. Period totals are
missing them, so every decline in the period is partly an artefact. The analysis
caveats those findings automatically; the report must keep the caveat.

**Everything is `(not set)` or `(other)`.** GA4 hit a cardinality limit or could
not attribute the traffic. Shares of total will not add up, and rows in those
buckets cannot be acted on.

**A large jump in direct traffic.** As often lost attribution — stripped UTMs, a
redirect dropping parameters, an app or email client hiding the referrer — as
genuine direct demand. Check tagging before celebrating.

**Two metrics that should agree do not.** GA4's user counts are modelled and
de-duplicated across sessions; `totalUsers` will not equal the sum of a
breakdown, and revenue will not tie exactly to a payment processor. Say so
rather than reconciling to a number that does not exist.

---

## Charts

**"matplotlib is not installed"** → `python3 -m pip install matplotlib`. Exit
code 4. The report can still be written, without charts and saying so.

**A chart is missing from the manifest as `not drawn`** → the reason field says
why, and it is nearly always "the data for it was not available". Do not
describe it in the report.

---

## Working offline

The whole pipeline below retrieval runs on fixtures, with no credentials and no
quota:

```bash
python3 scripts/make_fixtures.py                    # write the fixtures
python3 scripts/analyze_ga4.py --raw assets/fixtures/leadgen-healthy_raw.json --out /tmp/ga4
python3 scripts/make_charts.py --analysis /tmp/ga4/analysis.json --out /tmp/ga4/charts
```

That is also how to reproduce a bug in the analysis without waiting for the
right property to be in the right state: find the fixture that matches the
shape, or add one.
