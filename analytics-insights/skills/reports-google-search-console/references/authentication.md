# Authentication and configuration

## The architecture in one picture

```
~/clients/agency.env                  SHARED — every reports-* skill reads this
  GOOGLE_CLIENT_ID                    OAuth client (Google Cloud Console)
  GOOGLE_CLIENT_SECRET                OAuth client secret
  GOOGLE_REFRESH_TOKEN                long-lived user grant, all scopes
  GSC_REFRESH_TOKEN                   optional: a Search Console-only token
  GOOGLE_SERVICE_ACCOUNT_FILE         optional: path to a service-account key
  GOOGLE_IMPERSONATE_SUBJECT          optional: user to impersonate (delegation)

<client project>/.env                 PER CLIENT — never holds a credential
  GSC_SITE_URL                        REQUIRED: the Search Console property
  GSC_BRAND_TERMS                     optional: enables the branded split
  GSC_PRIMARY_COUNTRY                 optional: ISO alpha-3, e.g. usa
  GSC_SEARCH_TYPE                     optional: default web
  GSC_EXTRA_SEARCH_TYPES              optional: image,video,news,discover,googleNews
  GSC_REPORT_DAYS                     optional: period length, default 30
  GSC_LAG_DAYS                        optional: hold both windows back N days
  GSC_ROW_LIMIT                       optional: rows per request, max 25000
  GSC_INSPECT_URLS                    optional: true enables URL Inspection
  GSC_MAX_URL_INSPECTIONS             optional: cap on inspection calls, default 10
  CLIENT_NAME                         optional: display name for the report
```

One credential file for the whole agency; one small config file per client. A
client project holding a copy of the refresh token is a client project that will
still be using a revoked one in six months, in a directory nobody thinks to
check.

## Precedence

Later wins:

1. `~/clients/agency.env`
2. `<project root>/.env`
3. the process environment
4. explicit CLI flags — `--site-url`, `--search-type`

**There is no CLI flag for any credential.** Tokens and key paths are accepted
only from a file or the environment, so they cannot end up in a shell history, a
transcript, or a process listing. `--agency-env` (or `AGENCY_ENV=`) relocates the
shared file, which is useful for testing against a copy.

## Two APIs, and why the distinction matters when reading errors

| | What it is | What it gives you |
|---|---|---|
| **Google Cloud** (`console.cloud.google.com`) | Where the OAuth client lives and where the Search Console API is switched on for the project | Permission for the *application* to call the API at all |
| **Google Search Console API** (`searchconsole.googleapis.com`) | The data itself: Search Analytics, Sites, Sitemaps, URL Inspection | The property's clicks, impressions, CTR and position |

Google Cloud is **not** a data source. Nothing in this skill queries a "Google
Cloud Console API" — the phrase describes two different things stitched
together, and the errors from each point at different fixes.

Two failures look alike and are not:

- **`accessNotConfigured` (403)** — the Search Console API is not enabled on the
  Cloud project. Fix in Google Cloud.
- **`forbidden` / insufficient permission (403)** — the API is fine; the
  authenticated identity has not been added to the property. Fix in Search
  Console, under Settings → Users and permissions.

## Required Google APIs

Enable on the Cloud project behind the credentials:

- **Google Search Console API** — Search Analytics, Sites, Sitemaps, URL Inspection

That is the only one this skill needs. It never writes: no sitemap submissions,
no indexing requests.

## Scopes

```
https://www.googleapis.com/auth/webmasters.readonly
```

Read-only is sufficient for every call here, including URL Inspection.

⚠️ **A refresh token minted for Google Ads cannot read Search Console.** The
agency's `GOOGLE_REFRESH_TOKEN` may carry only
`https://www.googleapis.com/auth/adwords`, in which case the token exchange
succeeds and the first Search Console call fails. Two ways out, both fine:

1. **Re-mint the shared token with both scopes** — `adwords` and
   `webmasters.readonly` — and every `reports-*` skill keeps working from one
   value.
2. **Add `GSC_REFRESH_TOKEN`** to `agency.env` as a Search Console-only token.
   This skill prefers it when present and falls back to `GOOGLE_REFRESH_TOKEN`
   when it is not.

`check_config.py` reports which key the token came from.

## Authentication method 1 — OAuth user credentials (the agency default)

This is what `agency.env` already holds, and it is the path with the fewest
moving parts: the identity is a Google account a human already has, and its
Search Console access is whatever that person's access is.

**Minting a refresh token with the Search Console scope:**

1. Google Cloud Console → APIs & Services → Library → enable **Google Search
   Console API**.
2. OAuth consent screen. ⚠️ An **External** app left in *Testing* issues refresh
   tokens that expire after **seven days** — the setup works perfectly and then
   dies the following week for no visible reason. Set User type to **Internal**
   (Workspace domains only) or publish the External app to **Production**. Add
   the scope `https://www.googleapis.com/auth/webmasters.readonly`.
3. Credentials → Create credentials → OAuth client ID → **Desktop app**. Keep
   the client ID and secret.
4. Mint the token, signed in as a Google account with access to the client
   properties. Google's OAuth 2.0 Playground is the shortest route:
   - gear icon → "Use your own OAuth credentials" → paste the client ID and
     secret
   - Step 1 → enter the scope(s) manually:
     `https://www.googleapis.com/auth/webmasters.readonly` (add
     `https://www.googleapis.com/auth/adwords` too if this is the shared token)
   - authorise → Step 2 → "Exchange authorization code for tokens"
   - copy the **refresh token**

   Anything that performs a standard installed-app OAuth flow with that scope
   works equally well; the Playground is convenient, not special.
5. Put the values in `~/clients/agency.env`, `chmod 600` it, and confirm it is
   outside every git repository.

**Which properties does the OAuth user see?** Whatever that Google account can
see in Search Console — no more. Removing that person from a client's property
breaks that client's reports and nothing else; removing the account from the
agency breaks every client at once. When every client fails on permissions at
once, suspect the identity before the code.

## Authentication method 2 — a service account (optional)

Useful when the reporting identity should be a system rather than a person.

1. Google Cloud Console → IAM & Admin → Service Accounts → create one; download
   the **JSON key**.
2. Store the key outside every repository and point at it:
   `GOOGLE_SERVICE_ACCOUNT_FILE=/Users/you/clients/.keys/gsc-reporting.json`
   (`GOOGLE_APPLICATION_CREDENTIALS` is accepted as an alias).
3. **Grant the service account access to each property.** This is the step
   people miss. The service account has an email address like
   `gsc-reporting@my-project.iam.gserviceaccount.com`. In Search Console, for
   each client property: Settings → Users and permissions → **Add user** → that
   email → **Full** or **Restricted**. Cloud IAM roles do not grant Search
   Console access; only the property owner can.
4. For Google Workspace domain-wide delegation instead, set
   `GOOGLE_IMPERSONATE_SUBJECT` to the user to impersonate, and have a Workspace
   admin authorise the service account's client ID for the
   `webmasters.readonly` scope.

**One dependency note:** a service account signs a JWT with RS256, which the
Python standard library cannot do. The skill uses the `cryptography` package if
it is importable and otherwise shells out to `openssl` (present on macOS and
Linux). If neither is available it says so plainly rather than failing
obscurely. The OAuth user path needs nothing installed at all.

## Property access is a prerequisite, not a credential

Credentials prove *who* is calling. Property access decides *what* they can
read, and it is granted inside Search Console, per property, by someone with
Owner rights on it:

> Search Console → the property → Settings → Users and permissions → Add user
> → the identity's email → permission **Full** or **Restricted**

Both levels are enough for this skill. `siteUnverifiedUser` is not — it grants
no data, and the run warns when it sees one.

Ask the client to add the agency identity as part of onboarding, alongside GA4
and Google Ads access. It is a two-minute task for them and a blocked report for
everyone otherwise.

## Failure modes and what they mean

| Symptom | Cause | Fix |
|---|---|---|
| `invalid_grant` at token exchange | Consent screen left in Testing (7-day tokens), token revoked, or password changed | Publish the app to Production or make it Internal, then re-mint |
| `invalid_client` | Client ID/secret do not match a live OAuth client | Re-copy both from the Cloud console |
| `invalid_scope` | Token minted without `webmasters.readonly` | Re-mint with the scope, or add `GSC_REFRESH_TOKEN` |
| 403 `accessNotConfigured` | Search Console API not enabled on the Cloud project | Enable it in APIs & Services → Library |
| 403 insufficient permission | Identity not added to the property | Add it in Search Console → Users and permissions |
| 404 on the property | The identifier does not match exactly | `check_config.py --list-sites` prints the exact strings |
| `unauthorized_client` | Domain-wide delegation not granted for the scope | Workspace admin authorises the client ID |
| 429 / `rateLimitExceeded` | Per-property or per-project quota | The script backs off; re-run later, do not report partial data as final |
| Worked yesterday, dead today across every client | Refresh token expired, or the identity lost access | Re-mint the token |

`check_config.py` diagnoses all of these before a report run starts, and
`references/troubleshooting.md` carries the longer catalogue.

## Never printed

`describe_config()` is the only function that renders configuration for human
eyes, and it renders each credential as `present` or `missing` — never a value,
never a prefix, never a length. Nothing else in the skill prints, logs, or writes
a credential, and no credential is ever written into a raw file, an analysis
file, a chart, or a report. If you add a debugging print, do not print the config
object.
