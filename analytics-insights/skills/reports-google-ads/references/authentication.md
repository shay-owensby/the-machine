# Authentication and configuration

## The architecture in one picture

```
~/clients/agency.env                  SHARED — every reports-* skill reads this
  GOOGLE_CLIENT_ID                    OAuth client (Google Cloud Console)
  GOOGLE_CLIENT_SECRET                OAuth client secret
  GOOGLE_REFRESH_TOKEN                long-lived user grant for the adwords scope
  GOOGLE_ADS_DEVELOPER_TOKEN          issued by the manager account's API Center
  GOOGLE_ADS_LOGIN_CUSTOMER_ID        the agency's default manager (MCC) account

<client project>/.env                 PER CLIENT — never holds a credential
  GOOGLE_ADS_CUSTOMER_ID              the account being reported on
  GOOGLE_ADS_LOGIN_CUSTOMER_ID        also accepted as the account (see below);
                                      otherwise this client's manager account
  GOOGLE_ADS_API_VERSION              optional: pin the API version, e.g. v21
  GOOGLE_ADS_REPORT_DAYS              optional: period length, default 30
  GOOGLE_ADS_LAG_DAYS                 optional: days to hold back for conversion lag
  GOOGLE_ADS_PRIMARY_CONVERSION_ACTIONS   optional: which actions are the real KPI
```

One credential file for the whole agency; one small config file per client. A
client project that holds a copy of the refresh token is a client project that
will still be using a revoked one in six months, in a directory nobody thinks to
check.

## Precedence

Later wins:

1. `~/clients/agency.env`
2. `<project root>/.env`
3. the process environment
4. explicit CLI flags — `--customer-id`, `--login-customer-id`, `--api-version`

**There is no CLI flag for any secret.** Tokens are accepted only from a file or
the environment, so they cannot end up in a shell history, a transcript, or a
process listing. `--agency-env` (or `AGENCY_ENV=`) relocates the shared file,
which is useful for testing against a copy and for machines that keep it
somewhere other than `~/clients/`.

## The three identifiers, and why they are confused

| | What it is | Example | Where it belongs |
|---|---|---|---|
| Developer token | Authorises the *application* against the Google Ads API. One per manager account. | `abcDEF...` | `agency.env` |
| Login customer ID | The **manager (MCC)** account the request authenticates *through*. Sent as the `login-customer-id` header. | `098-765-4321` | `agency.env`, overridable per client |
| Target customer ID | The **operating account** whose data you want. Goes in the request URL. | `123-456-7890` | client `.env` |

## One key, two jobs

`GOOGLE_ADS_LOGIN_CUSTOMER_ID` is Google's name for the manager account. It is
also, in practice, the key people label their Google Ads account with — every
`.env` file in this agency uses it that way. Rather than require dozens of files
to be relabelled before anything can run, the skill reads it as both:

```
account to report on   =  --customer-id                       (explicit, wins)
                       -> GOOGLE_ADS_CUSTOMER_ID              (the explicit name)
                       -> GOOGLE_ADS_LOGIN_CUSTOMER_ID        (this agency's convention)

manager header         =  GOOGLE_ADS_LOGIN_CUSTOMER_ID, sent ONLY when it names a
                          different account from the one being queried
```

Three consequences worth knowing:

- **A client `.env` with only `GOOGLE_ADS_LOGIN_CUSTOMER_ID` works.** That value
  becomes the account, no manager header is sent, and the account is queried
  directly. The run records `customer_id_key` so the choice is visible, and
  warns that the value came out of the manager slot.
- **Adding `GOOGLE_ADS_CUSTOMER_ID` changes the meaning of the other key back.**
  Once the account is named explicitly, `GOOGLE_ADS_LOGIN_CUSTOMER_ID` returns
  to its Google meaning and is sent as the manager header — which is exactly
  what an MCC-managed account needs.
- **Falling back to the shared `agency.env` value warns loudly.** A client with
  no ads configuration at all would otherwise silently report on the agency's
  own default account. It still resolves, so a one-off run is possible, but the
  warning says the account is very likely wrong and to check the name in the
  preflight output.

The safest configuration remains explicit: `GOOGLE_ADS_CUSTOMER_ID` for the
account, `GOOGLE_ADS_LOGIN_CUSTOMER_ID` for the manager, both named for what
they are.

The rules:

- **Querying an account that is managed by an MCC requires the login customer
  ID to be that MCC.** Without it you get `USER_PERMISSION_DENIED` even when the
  user genuinely has access.
- **The manager header is never sent for the account being queried.** When the
  two IDs are equal, the header is dropped and the account is queried directly.
  If that ID really is a manager, it holds no campaigns and everything returns
  zero — so `check_config.py` checks `customer.manager` on the account itself
  and stops the run when it is true. That check, not the key name, is what
  actually protects against reporting on a manager.
- **A client with its own MCC** (agencies sometimes inherit one) sets
  `GOOGLE_ADS_LOGIN_CUSTOMER_ID` in their project `.env`, which overrides the
  agency default for that client only.
- **A client account not under any manager** — the OAuth user has direct access —
  needs no login customer ID at all. Leave it unset and the header is omitted.

Both IDs are accepted dashed or bare; they are normalised to ten digits before
use, and anything that is not exactly ten digits is rejected before a call is
made rather than after.

## Setting up credentials the first time

Two things are called "API access" and they come from different places:

| | Where | How long |
|---|---|---|
| Google Cloud project with the Google Ads API enabled | console.cloud.google.com | minutes |
| Developer token with **Basic** access | Google Ads **manager** account → Admin → API Center | ~5 business days |

1. **Developer token.** In the manager account: Admin → API Center → accept the
   terms. The token issues immediately at *Test Account Access*, which only
   works against test accounts and returns `DEVELOPER_TOKEN_NOT_APPROVED`
   against every real one. Apply for **Basic access** from the same page —
   describe the use as reporting and analysis, because that is what it is and it
   is the simpler review.
2. **Cloud project.** APIs & Services → Library → enable *Google Ads API*.
3. **OAuth consent screen.** ⚠️ An **External** app left in *Testing* issues
   refresh tokens that expire after **seven days** — the setup works perfectly
   and then dies the following week for no visible reason. Either set User type
   to **Internal** (Workspace domains only) or publish the External app to
   **Production**. Add the scope `https://www.googleapis.com/auth/adwords`.
4. **OAuth client.** Credentials → Create credentials → OAuth client ID →
   **Desktop app**. Keep the client ID and secret.
5. **Refresh token.** Generate it once, signed in as a Google account with
   access to the accounts you will report on:

   ```bash
   python3 -m pip install google-ads
   curl -O https://raw.githubusercontent.com/googleads/google-ads-python/main/examples/authentication/generate_user_credentials.py
   python3 generate_user_credentials.py --client_id YOUR_ID --client_secret YOUR_SECRET
   ```

   Or Google's OAuth 2.0 Playground (gear icon → "Use your own OAuth
   credentials" → authorise the `adwords` scope → exchange for tokens).

   The scripts here do **not** need the `google-ads` library — that install is
   only for minting the token, and can be undone afterwards.

Put the five values in `~/clients/agency.env` (see
`assets/agency.env.example`), `chmod 600` it, and confirm it is not inside any
git repository.

## Which account does the OAuth user actually see?

The refresh token belongs to a Google *user*. That user's access is what decides
everything:

- The user must have access to the target account, directly or through the
  manager named in `login-customer-id`.
- Read-only access is enough. This skill never writes.
- Removing that user from the manager account breaks every client at once. When
  reports across all clients start failing on permissions, suspect the user
  before the code.

## Failure modes and what they mean

| Symptom | Cause | Fix |
|---|---|---|
| `invalid_grant` at token exchange | Consent screen left in Testing (7-day tokens), token revoked, or password changed | Publish the app to Production or make it Internal, then mint a new refresh token |
| `invalid_client` | Client ID/secret do not match a live OAuth client | Re-copy both from the Cloud console |
| `DEVELOPER_TOKEN_NOT_APPROVED` | Token still at Test Account Access | Apply for Basic access; wait |
| `USER_PERMISSION_DENIED` | Login customer ID is not the managing MCC, or the OAuth user has no access | Set the MCC as login customer ID; check the hierarchy |
| `CUSTOMER_NOT_FOUND` | Wrong ten digits | Re-check `GOOGLE_ADS_CUSTOMER_ID` |
| `CUSTOMER_NOT_ENABLED` | Account cancelled or suspended | Historical data may still query; live data will not |
| Everything returns zero | Target is the manager account | Point at the operating account |
| Worked yesterday, dead today across every client | Refresh token expired, or the OAuth user lost access | Re-mint the token |

`check_config.py` diagnoses all of these before a report run starts.
`references/troubleshooting.md` carries the longer catalogue.

## Never printed

`describe_config()` is the only function that renders configuration for human
eyes, and it renders each credential as `present` or `missing` — never a value,
never a prefix, never a length. Nothing else in the skill prints, logs, or
writes a secret, and no secret is ever written into a raw file, an analysis
file, a chart, or a report. If you add a debugging print, do not print the
config object.
