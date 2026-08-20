# Property validation

## Why this comes before everything else

A Google Ads customer ID that is wrong returns an error. A Search Console
property identifier that is wrong often returns *data* — just not the client's.
`https://example.com/` and `https://www.example.com/` are different properties
with different traffic, and both can be real.

So the first thing every run does is prove the property exists, is readable, and
is the one intended. It never falls back to a similar one.

## The two kinds of property

| | Identifier | Covers |
|---|---|---|
| **Domain property** | `sc-domain:example.com` | Every subdomain (`www`, `blog`, `shop`), both `http` and `https`, all paths — one dataset |
| **URL-prefix property** | `https://www.example.com/` | Exactly that scheme, that host, and paths under that prefix |

Consequences that change what a report means:

- A domain property's numbers include subdomains a URL-prefix property never
  sees. Traffic that "appeared" after switching property type did not appear.
- `https://example.com/` and `https://www.example.com/` are separate properties.
  A site that redirects one to the other still records the visible traffic under
  whichever URL Google indexes.
- A URL-prefix property on `http://` when the site is `https://` reports almost
  nothing, and that is not a traffic collapse.
- Trailing slashes matter. `https://www.example.com` is not a valid identifier;
  `https://www.example.com/` is.

The skill normalises only what is unambiguous — surrounding whitespace, a
missing trailing slash on an origin, `SC-Domain:` casing. It never adds or
removes `www`, never switches scheme, and never converts between the two kinds.
Those changes ask for a different property.

A bare hostname (`example.com`) is rejected rather than guessed, with both valid
forms in the error message, because guessing right half the time is worse than
failing every time.

## What validation actually checks

`check_config.py` and `fetch_search_console.py` both do this before spending
quota:

1. **Enumerate.** `GET /webmasters/v3/sites` — every property this identity can
   read, with its permission level.
2. **Match exactly.** Is `GSC_SITE_URL` in that list, character for character?
3. **Near-miss help.** If not, is the same domain readable under a different
   identifier? The error names it: *"the same domain IS readable as
   `sc-domain:example.com` — that is a different property with different
   data"*. It reports the near miss; it does not silently use it.
4. **Permission level.** `siteOwner`, `siteFullUser` and `siteRestrictedUser`
   all return data. `siteUnverifiedUser` does not, and the run warns.
5. **Data availability.** One Search Analytics probe over the last 14 days. A
   property that is readable but returns no finalised rows is reported as
   exactly that — not as a property with zero traffic.

## Seeing what the identity can reach

```bash
python3 scripts/check_config.py --list-sites
```

```
https://www.example.com/                           siteFullUser
sc-domain:anotherclient.com                        siteOwner
https://shop.example.com/                          siteRestrictedUser
```

Copy the exact string into the client's `.env`. This command is also the fastest
way to answer "has the client actually granted us access yet?".

## Failure behaviour

| Situation | What happens |
|---|---|
| Property not in the list | Exit 3, naming near-miss properties and how to grant access |
| Unverified user | Runs, but warns that no data will come back |
| Readable, no finalised data | Exit 3 — a report cannot be written from nothing |
| API disabled on the Cloud project | Exit 3, pointing at Cloud rather than Search Console |
| Rate limited during validation | Exit 4 — retry, do not proceed on a guess |

**No silent fallback, ever.** Not to a `www` variant, not to a domain property,
not to the only property in the list. A report about the wrong site is worse than
no report, because it will be believed.
