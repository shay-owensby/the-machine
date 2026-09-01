# HTML output and visualization rules

Use these rules for every report produced by this skill. The Markdown report remains the factual source of truth; the HTML report is a self-contained presentation of the same report.

## Required deliverables

- Save the completed Markdown report at the path required by the skill.
- Build a companion HTML file with the same basename and an .html extension.
- Use scripts/build_report_outputs.py to generate chart assets, update the Markdown image references, and build the HTML.
- The HTML must embed the exact stylesheet from assets/report.css. Do not add report-specific CSS overrides.
- The HTML must be self-contained: no remote fonts, stylesheets, JavaScript, analytics, trackers, or chart services.
- Keep the generated <report-basename>-assets directory beside the report. It contains the SVG charts displayed by the Markdown file. The HTML embeds those SVGs.

## Visual system

The shared stylesheet is intentionally neutral and executive-facing: deep navy hierarchy, cobalt and teal accents, accessible risk colors, system fonts, responsive tables, and print rules. Preserve these tokens and layout rules across all analytics skills.

Do not add report-specific gradients, 3D charts, gauges, clip art, emoji as status indicators, or platform-specific brand colors. Preserve the stylesheet's fixed header treatment. Color must reinforce hierarchy or distinguish data series, never substitute for labels.

## Required visualizations

Create three useful visualizations when the data supports them:

1. An executive horizontal bar chart comparing material period-over-period KPI changes.
2. A line chart showing the primary daily or weekly performance trend.
3. A bar or horizontal bar chart comparing a meaningful campaign, channel, page, query, platform, account, content type, device, or other report-specific dimension.

If a third chart would be misleading because the necessary data is unavailable or the sample is too small, include two charts and explain the limitation in the report. Never fabricate values to satisfy a chart count.

Every chart must:

- visualize reconciled values already present in a nearby report table;
- use one comparable unit per axis;
- include a precise title, axis label, series labels, and honest period/scope context;
- use raw JSON numbers, not formatted currency or percent strings;
- use bar charts with a zero baseline;
- avoid dual axes, pie/donut charts, and truncated axes that exaggerate change;
- remain legible with color removed and include meaningful alternative text through its title and series labels.

## Chart directive

Place a report-chart comment at the intended chart location. The build script inserts or refreshes the Markdown image immediately before the comment and embeds the chart into HTML.

~~~json
<!-- report-chart
{
  "id": "daily-primary-trend",
  "type": "line",
  "title": "Daily organic clicks",
  "subtitle": "Current 30-day period",
  "x_label": "Date",
  "y_label": "Clicks",
  "include_zero": false,
  "labels": ["2026-07-01", "2026-07-02", "2026-07-03"],
  "series": [
    {"name": "Clicks", "values": [120, 134, 128]}
  ]
}
-->
~~~

Supported types are line, bar, and horizontal-bar. Use a lowercase ASCII id with hyphens, 2–90 labels, and 1–4 series. Each series must have the same number of numeric or null values as labels. Use null only for genuinely unavailable points. The optional subtitle should state scope, period, or an important caveat. Bar charts always include zero; line charts follow include_zero, which defaults to false.

Run the builder only after the Markdown report is complete and all chart directives contain final values:

    python3 <skill-directory>/scripts/build_report_outputs.py <markdown-report-path>

Then run the skill validator against the Markdown path. It validates the Markdown, companion HTML, shared stylesheet identity, source synchronization, chart assets, and minimum visualization count.
