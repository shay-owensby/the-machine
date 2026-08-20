# Configuration

Two files, one job each.

| File | Holds | Shared? | In git? |
|---|---|---|---|
| `~/clients/agency.env` | Google credentials | Every `reports-*` skill, every client | **Never** |
| `<client project>/.env` | Which property to report on | This client only | Only if the repo is private, and even then no secret belongs in it |

The split is the whole design: a credential lives in exactly one place on the
machine, and a client project can be copied, shared or archived without
carrying one.

---

## Resolution order

Later wins:

1. `~/clients/agency.env`
2. `<project root>/.env`
3. the process environment
4. explicit CLI flags (`--property-id`, `--agency-env`)

Secrets are only ever accepted from 1–3. There is no CLI flag for a credential.

Every run records where each value came from. `check_config.py` prints it under
`credential_sources` and `property.property_id_source`, which answers "why is
it reporting on the wrong property" in one line.

---

## Client configuration

The only value a client project must define:

```bash
# <client project>/.env
GA4_PROPERTY_ID=123456789
```

**Where to find it:** GA4 → **Admin → Property → Property details**. It is also
the `p=` parameter in a GA4 report URL. It is digits only.

It is **not**:

| What people paste | What it actually is |
|---|---|
| `G-XXXXXXXXXX` | Measurement ID — the tag on the website |
| `UA-12345-1` | A Universal Analytics property, dead since 2023 |
| `GTM-XXXXXX` | A Google Tag Manager container |
| `accounts/12345` | The Analytics account, one level above the property |

Each of these produces its own error message naming what it is and where the
right value lives. `properties/123456789` is accepted and unwrapped, because
that is the form the API itself uses.

Unlike Google Ads, GA4 has **no login customer ID**. There is no manager-account
header, no hierarchy to traverse: the property ID plus a granted identity is the
whole address.

### Optional client values

None of these are required. Set one only when it earns its place.

```bash
GA4_PROPERTY_NAME="Acme Home Services"   # fallback name when the Admin API is off
GA4_CLIENT_NAME="Acme Ltd"               # display name for the report header
GA4_SITE_URL=https://www.acme.com        # recorded in the output; never fetched
GA4_ACCOUNT_ID=98765                     # informational only
GA4_REPORT_DAYS=30                       # days per period (default 30)
GA4_LAG_DAYS=0                           # extra settling days before "yesterday"
GA4_CURRENCY_SYMBOL=$                    # override the symbol in tables
GA4_KEY_EVENTS=generate_lead,purchase    # which key events matter to THIS business
```

`GA4_KEY_EVENTS` is worth explaining. GA4 records which events are marked as key
events; it does not record what they mean. Listing the ones that represent real
business outcomes here lets the report distinguish a lead from a scroll-depth
milestone instead of saying the meaning is undetermined. Leave it unset and the
report says exactly that — which is the honest default, not a failure.

`GA4_LAG_DAYS` shifts the window further from today. GA4 data is generally
stable within 24–48 hours; set it to 1 or 2 for a property where late-arriving
data has caused a report to disagree with itself.

---

## Reporting periods

Default, and what the report states verbatim:

- **Current period:** the most recent 30 *fully completed* days, ending
  yesterday.
- **Comparison period:** the 30 days immediately before that.
- **Today is never included.** A partial day compared against a whole one
  invents a decline.

"Yesterday" is computed in the **property's own time zone**, not the machine's.
GA4 days are property-time-zone days, and getting this wrong shifts the whole
window by a day. When the time zone cannot be read, the run says so and uses the
local date.

Overrides:

```bash
--days 90                                  # 90 vs the preceding 90
--end-date 2026-07-31                      # end the current period there
--current 2026-07-01:2026-07-31 --previous 2026-06-01:2026-06-30
```

`--current` and `--previous` must be given together. Unequal-length periods are
allowed and produce a loud warning that percentage changes will mislead —
because they will.

---

## Output layout

Everything is written under the client project root, in a directory named for
the **last day of data** rather than the day the report was generated. Re-running
the same period overwrites the same folder instead of creating a new one each
day, and the folder name says what the report is about.

```
reports/
└── google-analytics/
    └── 2026-08-19/                          <- last day of the current period
        ├── google-analytics-report-2026-08-19.md
        ├── data/
        │   ├── raw.json                     everything the API returned
        │   ├── analysis.json                the output contract
        │   ├── kpis.json                    the KPI block alone
        │   ├── tables.md                    pre-rendered Markdown tables
        │   ├── daily.csv
        │   ├── acquisition.csv
        │   ├── acquisition-source-medium.csv
        │   ├── landing-pages.csv
        │   ├── pages.csv
        │   ├── devices.csv
        │   ├── geography.csv
        │   ├── events.csv
        │   └── ecommerce.csv                only when the property sells
        └── charts/
            ├── charts.json                  the manifest, including what was NOT drawn
            ├── kpi-change.png
            ├── daily-performance.png
            ├── channel-performance.png
            ├── landing-page-performance.png
            ├── key-event-performance.png
            ├── device-performance.png
            ├── ecommerce-performance.png
            └── ecommerce-funnel.png
```

**Only files with data are written.** A property with no ecommerce gets no
`ecommerce.csv` and no ecommerce charts — not empty ones. A chart that could not
be drawn appears in `charts.json` with the reason, so the report can say the
visual is unavailable instead of describing a picture that does not exist.

Override with `--out` on any script. The default keeps `data/` and `charts/`
siblings so the relative paths in the report (`./charts/daily-performance.png`)
resolve wherever the folder is moved.

---

## Placeholder examples

Copy-ready files, with placeholders only:

- `assets/agency.env.example`
- `assets/client.env.example`

Neither contains a real value, and neither should ever be filled in and
committed.
