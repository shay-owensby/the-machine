# Data retrieval

## The endpoints in use

| API | Endpoint | Used for |
|---|---|---|
| **Search Analytics** | `POST /webmasters/v3/sites/{siteUrl}/searchAnalytics/query` | Every performance figure in the report |
| Sites | `GET /webmasters/v3/sites` · `GET .../sites/{siteUrl}` | Property validation and permission level |
| Sitemaps | `GET /webmasters/v3/sites/{siteUrl}/sitemaps` | Optional sitemap health |
| URL Inspection | `POST /v1/urlInspection/index:inspect` | Optional, selective index diagnostics |

Host: `https://searchconsole.googleapis.com`. The `siteUrl` is a path segment
and must be fully percent-encoded — `sc-domain:example.com` becomes
`sc-domain%3Aexample.com`, and `https://www.example.com/` becomes
`https%3A%2F%2Fwww.example.com%2F`. `gsc_common.encode_site_url()` does this;
building the path by hand is how a 404 gets mistaken for a missing property.

The Search Analytics report is the primary source. The other three are
diagnostics and stay out of the KPI figures entirely.

## The datasets retrieved

| Dataset | Dimensions | Periods | Why it is its own query |
|---|---|---|---|
| `totals` | *(none)* | both | The property-level KPI truth. Summing any dimensional export does not reproduce it. |
| `daily` | `date` | both | Trend, spikes, drops, the shape inside the period |
| `queries` | `query` | both | The search terms |
| `pages` | `page` | both | The landing pages |
| `query_page` | `query`, `page` | current only | Which page answers which query; cannibalisation signals |
| `devices` | `device` | both | Desktop / mobile / tablet |
| `countries` | `country` | both | Markets |
| `search_appearance` | `searchAppearance` | both | **Cannot be combined with any other dimension** — a separate query or an HTTP 400 |

Optional extras: `sitemaps` (`--sitemaps`) and `url_inspection`
(`--inspect-urls`), neither on by default.

## The request body

```jsonc
{
  "startDate": "2026-07-18",
  "endDate": "2026-08-16",
  "dimensions": ["query"],
  "type": "web",              // web | image | video | news | discover | googleNews
  "rowLimit": 25000,          // the API maximum
  "startRow": 0,              // offset for paging
  "dataState": "final"        // final = finalised only; all = includes fresh days
}
```

`dataState: "final"` is the default and stays the default for client reports.
`"all"` includes days Google has not finished counting; those days rise
afterwards, so a period ending in them always looks worse than it turns out to
be. `--data-state all` exists for investigating a very recent event, and the raw
file and the report both say when it was used.

## Pagination

**A single response is capped at 25,000 rows, and a first page that comes back
full is not a complete dataset.** `search_analytics()` pages with `startRow`
until a response returns fewer rows than the limit.

Two caps sit above that, both recorded when they bite:

- `--max-rows` (default 50,000) for `queries` and `pages`
- `--max-query-page-rows` (default 25,000) for the query+page export

When a cap stops paging, `meta.truncated` becomes true, `meta.complete` becomes
false, a warning enters the raw file, and the analysis surfaces it in
`data_quality`. Nothing presents a capped extract as the whole picture.

## Large properties: retrieve in slices

A property with more distinct queries in 30 days than the API will return in one
window loses its long tail. `--chunk-days N` retrieves the query and page
datasets in N-day slices and aggregates them:

```bash
python3 scripts/fetch_search_console.py --project-root . --chunk-days 7
```

- clicks and impressions are summed
- position is re-weighted by impressions
- CTR is recomputed from the summed counts

The result is **not identical** to a single 30-day request: it surfaces queries
the single request never showed, so its totals are higher. The dataset's `meta`
records `chunked: true`, the slice count, and a note saying exactly this, so a
report never claims two incompatible extracts should tie out.

Rule of thumb: use it when a 30-day query extract returns 25,000+ rows.

## Search types are separate datasets

`type` selects a surface, and the surfaces are not additive:

| Type | Query dimension | Notes |
|---|---|---|
| `web` | yes | The default and the basis of the KPI table |
| `image` | yes | Image search |
| `video` | yes | Video search |
| `news` | yes | News tab |
| `discover` | **no** | No query dimension, no meaningful position |
| `googleNews` | **no** | Google News app and news.google.com |

`GSC_EXTRA_SEARCH_TYPES=image,discover` retrieves those surfaces into
`extra_search_types` in the raw and analysis files, each with its own totals and
its own daily series, each labelled. **They are never added into the web totals.**
A single number combining web and Discover describes nothing that exists.

## API efficiency

Retrieval is the only stage that costs quota, so:

- Every date range is queried once. The raw file is the cache for the whole
  workflow; re-running analysis or charts costs nothing.
- Property validation makes one `sites` call, not one per dataset.
- The freshness probe is two 14-day queries by date, and its answer is reused
  for the whole run.
- URL Inspection runs only on pages the retrieved data has already flagged, and
  never by default.
- `--skip query_page,countries` trims optional datasets for a quick run.
- A seven-day window with `--skip` is the cheap way to test a new client's
  access without a full extract.

Roughly 16-20 API calls for a standard run on a small property, more with
chunking or extra search types.

## Retries and rate limits

Transient failures (429, 500, 502, 503, 504, `backendError`) are retried with
exponential backoff and jitter, up to five attempts. A 401 forces exactly one
token refresh and one retry. Anything else raises immediately with a diagnosis —
retrying a permission error just delays the same answer.

Quota is per property and per Cloud project. If retries exhaust, the run exits 4:
**re-run later rather than reporting the partial extract as final.**

## What comes back

```jsonc
{"rows": [
  {"keys": ["widget buying guide"], "clicks": 120, "impressions": 42000,
   "ctr": 0.00285, "position": 4.8}
]}
```

- `ctr` is a **fraction**. It is multiplied by 100 exactly once, in the analysis
  layer. Doing it twice turns 2.85% into 285%, and doing it nowhere turns it
  into 0.03%.
- `position` is a 1-based average where **lower is better**.
- **A response with no `rows` key is a valid answer meaning "no data for this
  query"**. It is not an error, and it is not zeros — nothing in the pipeline
  converts one into the other.
