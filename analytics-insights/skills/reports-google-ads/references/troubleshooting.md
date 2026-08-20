# Troubleshooting

Run `python3 scripts/check_config.py --project-root .` first. It reproduces
almost every failure below in about a second, without spending a report's worth
of quota to find out.

## Exit codes

| Script | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| `check_config.py` | ready | — | configuration problem | auth/permission failure | transient |
| `fetch_google_ads.py` | complete | partial (optional datasets failed) | configuration problem | core data unavailable | transient |
| `analyze_performance.py` | ok | — | bad or missing input file | — | — |
| `make_charts.py` | charts drawn | — | no analysis file | nothing drawable | matplotlib missing |
| `run_tests.py` | all passed | failures | — | — | — |

## Configuration

**`The shared agency credential file is not there: ~/clients/agency.env`**
Create it from `assets/agency.env.example`, or point elsewhere with
`--agency-env` / `AGENCY_ENV=`. Do not put credentials in the client project.

**`Missing shared credential(s): GOOGLE_REFRESH_TOKEN`**
The file exists but is short a value. Keys must be `KEY=value`, one per line;
`export ` prefixes and quotes are fine, spaces around `=` are fine, a line
continuation is not.

**`No Google Ads account to report on`**
Neither `GOOGLE_ADS_CUSTOMER_ID` nor `GOOGLE_ADS_LOGIN_CUSTOMER_ID` was found in
the client `.env`, the shared `agency.env`, or the environment. Either key names
the account (see `references/authentication.md`); for a one-off, pass
`--customer-id 123-456-7890`.

**`... is 9 digits after stripping punctuation`**
Google Ads customer IDs are exactly ten digits. Dashes and spaces are fine; nine
digits means a typo or a truncated paste.

## Authentication

**`OAuth refused the refresh token (invalid_grant)`**
In order of likelihood:

1. The OAuth consent screen is still in **Testing** — those refresh tokens
   expire after seven days. Publish to Production, or make the app Internal.
2. The token was revoked, or the Google account's password changed.
3. The refresh token does not belong to this client ID/secret pair.

All three need a new `GOOGLE_REFRESH_TOKEN` in `agency.env`. Because the file is
shared, this failure hits every client at once — which is the tell.

**`OAuth refused the client credentials (invalid_client)`**
`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` do not match a live OAuth client.
Re-copy both; check the Cloud project is the one with the Google Ads API
enabled.

**`HTTP 401` on every request**
The access token is refreshed automatically and retried once. Persisting means
the refresh token itself is bad — see `invalid_grant`.

## Permissions and account access

**`authorizationError.USER_PERMISSION_DENIED`**
The commonest error in the whole skill, and it is almost always the
login-customer-id header:

1. Is `GOOGLE_ADS_LOGIN_CUSTOMER_ID` the **manager** account, not the account
   being queried?
2. Is the target account actually linked to that manager?
3. Does the Google account behind the refresh token have access to the manager?
4. Is the client account under a *different* manager? Then set
   `GOOGLE_ADS_LOGIN_CUSTOMER_ID` in that client's `.env`.

**`authorizationError.DEVELOPER_TOKEN_NOT_APPROVED`**
The developer token is at Test Account Access. It works only against test
accounts. Apply for Basic access in the manager account's API Center — around
five business days, and nothing else unblocks it.

**`authenticationError.DEVELOPER_TOKEN_PROHIBITED` / `INVALID_DEVELOPER_TOKEN`**
The token is not valid for this Cloud project, or is mistyped. Copy it again
from API Center.

**`CUSTOMER_NOT_FOUND` / `NOT_ADS_USER`**
Those ten digits do not resolve to an account this login can reach.

**`CUSTOMER_NOT_ENABLED`**
Cancelled or suspended. Historical data may still query; live data will not.

**Everything is zero and the account looks dead**
Check `is_manager` in the `check_config.py` output. A manager account holds no
campaigns. If `customer_id_key` says `GOOGLE_ADS_LOGIN_CUSTOMER_ID`, the account
was read from the manager slot and that is the likely cause — set
`GOOGLE_ADS_CUSTOMER_ID` to the operating account, and the manager ID will then
be sent as the login header instead of being queried.

**The report is about the wrong account**
`check_config.py` prints `customer_id_key` and `customer_id_source`. If the
source is the shared `agency.env`, the run fell back to the agency-wide default
because the client project named no account of its own — set
`GOOGLE_ADS_CUSTOMER_ID` in that client's `.env`.

## Data problems

**`quotaError.RESOURCE_EXHAUSTED` / HTTP 429**
Rate limited, or out of daily operations (Basic access allows 15,000/day —
generous for reporting; a loop over many accounts can still hit it). The client
retries five times with exponential backoff. If it still fails, wait and re-run
— never publish a partial retrieval as if it were complete.

**`Method not found. Requested version was not found.`**
The API version has been sunset. The client walks down its version ladder
automatically and warns. Pin a current version with `GOOGLE_ADS_API_VERSION` to
stop it happening again.

**`UNRECOGNIZED_FIELD` / `UNKNOWN_FIELD`**
A field in a query does not exist in this version — usually after an automatic
version fallback to something much older. Pin a known-good version.

**Campaign spend does not reconcile with account spend**
The validator flags it. Usually a failed or truncated campaign query. Re-run the
fetch; if it persists, do not present campaign figures as a complete breakdown.

**Numbers do not match the Google Ads UI**

1. Date range — the UI's default is not this window, and the window here is in
   the *account's* time zone.
2. Conversion lag — conversions are still being attributed to recent days, so a
   report run today and re-run next week will differ.
3. `conversions` versus `all conversions` — the UI's "Conversions" column
   matches `metrics.conversions`; a per-action breakdown uses all-conversions.
4. Attribution model changes restate history.

Differences of a few percent on recent periods are normal. Ten percent is not —
check the window and the customer ID first.

**Impression share is missing or looks too small**
Only Search (and some Shopping) campaigns report it. A Performance
Max-heavy account has little or no impression-share coverage, and the analysis
states what share of impressions its figure covers. Do not present it as an
account-wide number when it is not.

**Conversions are zero but the client says they get leads**
Either tracking is broken, or the conversion actions that fire are excluded from
the `conversions` metric. Check `conversion_actions` in the analysis:
`included_in_conversions_metric: false` on the action they care about explains
it exactly.

## Environment

**`matplotlib` missing**
`python3 -m pip install matplotlib`. Without it the pipeline still runs; the
report says the visuals are unavailable.

**`zoneinfo` cannot resolve the account time zone**
Rare on macOS and Linux; possible on a stripped container. `pip install tzdata`.
The run falls back to local dates and warns — the window may be a day off.

**Python version**
Standard library only, 3.8+. `zoneinfo` needs 3.9+; older versions fall back to
local dates with a warning.

## Nothing here matches

Re-run the failing script with the raw error visible, and check the two things
that produce the most confusing symptoms:

1. **Which account?** `check_config.py` prints the name. A valid report on the
   wrong account looks completely normal.
2. **Which credentials?** `describe_config` shows the source file of each value.
   A stray `GOOGLE_ADS_CUSTOMER_ID` exported in the shell overrides the client's
   `.env` and follows you between projects.
