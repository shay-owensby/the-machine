# Authentication and property access

Two different things have to be true before a single number comes back, and
they fail in different places for different reasons:

1. **The agency has credentials** that Google will mint a token for, and that
   token carries an Analytics scope. This is agency-wide, configured once.
2. **That identity has been granted access to this client's GA4 property.**
   This is per client, and it is done by someone with Administrator rights on
   the property — not by anyone in the Google Cloud project.

Most first-run failures are (2). Nothing in the credential file can fix them.

---

## The shared agency credential file

Every skill whose name begins with `reports-` reads its Google credentials from
one file:

```
~/clients/agency.env
```

It is never copied into a client project, never committed, and never printed.
Client projects hold only their own non-secret identifiers.

The file this skill expects — the same OAuth credentials `reports-google-ads`
already uses:

```bash
# ~/clients/agency.env      (placeholders -- never commit real values)
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-<your-client-secret>
GOOGLE_REFRESH_TOKEN=<your-refresh-token>

# Google Ads uses the same three, plus its own developer token. Analytics does
# not need a developer token -- there is no such thing for the Analytics APIs.
GOOGLE_ADS_DEVELOPER_TOKEN=xxxxxxxxxxxxxxxxxxxxxx
```

Override the location for one run with `--agency-env /path/to/agency.env` or
`AGENCY_ENV=...`. The path is resolved, reported and never printed with its
contents.

### Why OAuth user credentials and not a service account

The agency file already carries a working OAuth client and refresh token, and a
GA4 property can be shared with a Google account exactly as easily as with a
service account. Adding a second credential type would mean two things to keep
alive, two things to rotate, and two ways for a client property to be shared
with the wrong one. The OAuth path also needs no third-party library at all —
`urllib` and a refresh token are the whole implementation.

Service accounts are supported for agencies that prefer them (see below), but
they are the alternative, not the default.

---

## The one scope that matters

```
https://www.googleapis.com/auth/analytics.readonly
```

Read-only by design: a token minted for this scope cannot change a property,
which is the correct blast radius for a reporting tool.

**The likely first failure:** the refresh token already in `agency.env` was
minted for Google Ads (`https://www.googleapis.com/auth/adwords`) and carries
no Analytics scope. The token is valid; it simply cannot see Analytics. The
skill detects this at the token exchange — before any report request — and says
so directly rather than letting it surface as a confusing permission error.

### Re-minting one refresh token that carries both scopes

A single refresh token can hold both scopes, so re-minting does not mean
maintaining two tokens or breaking the Ads skill.

1. In the Google Cloud project that owns the OAuth client, enable both:
   - **Google Analytics Data API** (`analyticsdata.googleapis.com`) — required
   - **Google Analytics Admin API** (`analyticsadmin.googleapis.com`) — optional
     but recommended; it supplies the property name and key-event definitions
2. Check the OAuth consent screen is **Internal**, or **External and
   published**. An External app left in *Testing* issues refresh tokens that
   expire after seven days — the single most common cause of a report that
   worked last month and does not today.
3. Open the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/),
   open the settings gear, tick **Use your own OAuth credentials**, and paste
   the client ID and secret from `agency.env`. Add
   `https://developers.google.com/oauthplayground` as an authorised redirect
   URI on that OAuth client first.
4. In step 1 of the Playground, enter **both** scopes, space separated:
   ```
   https://www.googleapis.com/auth/analytics.readonly https://www.googleapis.com/auth/adwords
   ```
5. Authorise as the Google account the agency uses for client access, then
   exchange the authorisation code for tokens.
6. Copy the refresh token into `GOOGLE_REFRESH_TOKEN` in `agency.env`.
7. Verify: `python3 scripts/check_config.py --list-properties`

If you mint tokens with your own flow instead, the request needs
`access_type=offline` and `prompt=consent` — without them Google returns an
access token and no refresh token.

---

## Property access — the per-client prerequisite

Credentials get the agency to Google's door. Access gets it into a property.

**This is not a credential and it does not belong in any `.env` file.** For
each client:

1. Someone with the **Administrator** role on the GA4 property opens
   **Admin → Property → Property access management**.
2. **+ → Add users**, entering the agency's Google account address (or the
   service account's `client_email` if that path is in use).
3. Role: **Viewer** is enough for everything this skill does. Analyst or
   Editor also work. Administrator is not required and should not be requested.
4. Leave "Notify new users by email" as they prefer. Save.
5. Access can take a few minutes to propagate. A `PERMISSION_DENIED` in the
   first minute after granting is normal; after ten minutes it is real.

Access granted at **account** level cascades to every property in that account,
which is convenient for a client with several properties and a mistake for an
agency that only reports on one.

To confirm what the identity can currently see:

```bash
python3 scripts/check_config.py --list-properties
```

That lists every property the identity can reach, with its property ID — which
is also the fastest way to find a `GA4_PROPERTY_ID` without asking the client.
It needs the Admin API; if that API is off, read the ID from the GA4 interface
instead (**Admin → Property → Property details**).

---

## The service-account alternative

Set either variable in `agency.env` and the skill uses the key file instead.
The OAuth trio still wins when it is complete, so adding a key file cannot
silently change how existing clients authenticate.

```bash
# ~/clients/agency.env
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account-key.json
# GOOGLE_APPLICATION_CREDENTIALS is accepted as an alias
```

What changes:

- The key file must stay outside every client project and outside version
  control. It is a credential in a file, with all the handling that implies.
- Each client property must be shared with the service account's
  `client_email`, exactly as for a user account.
- Signing the JWT needs RSA, which the standard library cannot do. Install
  `cryptography` (`python3 -m pip install cryptography`) or `rsa`. The OAuth
  path needs neither.
- Service accounts have no consent screen and no seven-day token expiry, which
  is their main advantage.

---

## Required Google APIs

Enabled in the Google Cloud project that owns the credentials — once, for the
whole agency, not per client:

| API | Host | Required? | What this skill uses it for |
|---|---|:--:|---|
| Google Analytics Data API | `analyticsdata.googleapis.com` | **Yes** | Every reporting number: `runReport`, `getMetadata`, `checkCompatibility` |
| Google Analytics Admin API | `analyticsadmin.googleapis.com` | No | Property name, time zone, currency, key-event definitions, data streams, property discovery |

Google Cloud is where these APIs are *provisioned and authorised*. The
reporting data itself comes from the Google Analytics APIs above — there is no
"Google Cloud Console API" involved in a GA4 report.

The Admin API being disabled is not fatal. Reporting continues; the property
name shows as unknown rather than being invented, key-event definitions cannot
be read, and `--list-properties` stops working.

---

## Diagnosing a failure

Run the preflight first, every time. Thirty seconds here saves a confused
half-hour later:

```bash
python3 scripts/check_config.py                 # config + live probe
python3 scripts/check_config.py --no-network    # config only
```

| Exit | Meaning | Where to look |
|:--:|---|---|
| 0 | Ready | — |
| 2 | Configuration problem | `agency.env` or the client `.env` |
| 3 | Authentication or property access | This file |
| 4 | Transient API failure | Retry; if it persists, quota |

| Symptom | Cause | Fix |
|---|---|---|
| `invalid_grant` at the token exchange | Consent screen still in Testing (7-day expiry), token revoked, or password changed | Publish the app, re-mint the refresh token |
| `invalid_client` | Client ID/secret do not match a live OAuth client | Re-copy both from the Cloud project |
| "was NOT granted a Google Analytics scope" | The token is the Ads token | Re-mint with both scopes, above |
| `ACCESS_TOKEN_SCOPE_INSUFFICIENT` | Same cause, surfacing later | Same fix |
| `PERMISSION_DENIED` on the property | The identity was never added to the property | Property access management, above |
| `SERVICE_DISABLED` / "has not been used in project" | The API is off in the Cloud project | Enable it, wait a minute, retry |
| `NOT_FOUND` on the property | Wrong number — usually a measurement ID | Use the numeric property ID |
| `RESOURCE_EXHAUSTED` | Data API tokens spent for this property this hour | Wait for the hour to roll; never publish partial data as final |

---

## Handling rules this skill follows

- Secrets are read at run time, held in memory for one process, and never
  written to stdout, a log, a report, a JSON file, a CSV, a chart, or an error
  message.
- `describe_config()` is the only function that renders configuration for human
  eyes, and it renders a credential as `present` or `missing` — never a value,
  never a prefix, never a length.
- There is no command-line flag for any secret, so a credential cannot end up
  in shell history or a transcript.
- No generated output file contains a credential; `references/testing.md` lists
  this among the checks to run against any change that touches configuration
  or output.
