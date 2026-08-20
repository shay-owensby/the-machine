# Running the workflow, and invoking it from another agent

## The four commands

Run from the **client project root** — the directory holding that client's
`.env`.

```bash
SKILL=~/the-machine/analytics-insights/skills/reports-google-analytics

# 1. Preflight. Thirty seconds, every time.
python3 $SKILL/scripts/check_config.py

# 2. Retrieve. The only step that touches the network.
python3 $SKILL/scripts/fetch_ga4.py

# 3. Analyse. Reads the raw file, writes the contract, CSVs and tables.
python3 $SKILL/scripts/analyze_ga4.py --raw reports/google-analytics/<END>/data/raw.json

# 4. Draw.
python3 $SKILL/scripts/make_charts.py \
  --analysis reports/google-analytics/<END>/data/analysis.json --update-analysis
```

`<END>` is the last day of the current period — the folder name `fetch_ga4.py`
prints in its summary as `raw_file`. Take it from there rather than computing
it: if `GA4_LAG_DAYS` is set, or the run used `--end-date`, it will not be
yesterday.

Every step prints a JSON summary on stdout and progress on stderr, so a wrapper
can parse one and show the other.

### Useful variations

```bash
--days 90                                    # 90 vs the preceding 90
--current 2026-07-01:2026-07-31 --previous 2026-06-01:2026-06-30
--skip geo,browsers,os,pages                 # fewer requests, less quota
--top-n 25 --page-limit 50                   # smaller breakdowns
--material-pct 5                             # a lower bar for "material"
--min-sessions 250                           # a higher bar before judging a segment
```

---

## Reading the exit codes

| Code | Do this |
|:--:|---|
| 0 | Continue |
| 1 | Continue — core data is there. Read `errors[]` and name the missing sections in the report |
| 2 | Stop. Configuration problem; fix and re-run |
| 3 | Stop. Authentication or property access; `authentication.md` |
| 4 | Retry once. If it persists, quota — `troubleshooting.md` |

---

## Invoking the skill from another agent

The contract is: **the skill produces `analysis.json`; the agent turns it into
the report.** The agent does not call the API, does not recompute a percentage,
and does not decide whether a missing value means zero.

1. Run steps 1–4 above from the client project root.
2. Read `reports/google-analytics/<END>/data/analysis.json`.
3. Optionally read `tables.md` for tables already rendered as Markdown, and
   `charts/charts.json` for what was drawn.
4. Write `reports/google-analytics/<END>/google-analytics-report-<END>.md`.

What the agent must carry through untouched:

- **Both date ranges**, verbatim, in the header.
- **`verdict`, not the sign of the change** — the verdict already knows what
  the metric means.
- **`notes` on every KPI it quotes** — that is where the caveats live.
- **Every `fail` and material `warn`** from `data_quality.checks`.
- **`null` as "not available"**, never as zero.
- **Only charts with `status: "drawn"`**, embedded using their `markdown`
  field.

What the agent adds, and the skill deliberately does not:

- which two or three findings actually matter to this business;
- the narrative that connects them;
- the executive summary;
- the final ordering of the recommendations.

---

## Scheduling

The workflow is idempotent: the output folder is named for the last day of
data, so re-running the same period overwrites rather than accumulating. A
monthly run needs no state beyond the client's `.env`.

Quota is per property per hour, so stagger clients rather than firing every one
at midnight.
