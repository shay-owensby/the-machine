*Fill and send with `slack_send_message`. Budget 3,000 characters, 5,000 hard
ceiling. Cut finalists before cutting the ACT NOW block.*

*`<!channel>` opens every message and is never dropped. The Drive URL closes
every message, bare on its own line so Slack unfurls it into a card.*

*This is not the Step 9 report to the user. Do not write one summary and use it
for both — that is how the opener and the closer get lost. Before sending, check
the first line is exactly `<!channel>` and the last line is a bare Drive URL.*

---

<!channel>

**Events report — {Business Category}, {City}**
{N} events screened across {RADIUS} miles · window {MONTH YYYY} – {MONTH YYYY}

:rotating_light: **Act now — closes in {N} days**
**[{Event}]({url})** — {dates} · {booth or sponsor cost}
Application closes **{deadline}**. {One sentence on why it is worth the money.}

*(Omit this whole block when nothing closes inside 30 days, and say so in one
line instead: "Nothing closes in the next 30 days — earliest deadline is
{date}.")*

**Top picks**

| Event | When | Cost | Why |
|---|---|---|---|
| [{Event}]({url}) | {dates} | {$X booth} | {one clause} |
| [{Event}]({url}) | {dates} | {$X sponsor} | {one clause} |
| [{Event}]({url}) | {dates} | {$X booth} | {one clause} |

**Also found:** {N} more finalists in the full report · {N} considered and passed

**Biggest gap:** {the calendar that could not be opened, the cost nobody
publishes, or the question only the client can answer}

:page_facing_up: *Full report — organizer contacts, deadlines, vendor rules:*
{drive webViewLink, bare — e.g. https://docs.google.com/document/d/{fileId}/edit}

*(Bare, not wrapped in a markdown link: Slack unfurls a Drive URL into a card
showing the document title. Use the link captured in Step 7 — never one you
assembled from a file ID. If the upload was skipped or failed, say so in one line
and give the repo path instead: `Public Relations/Events/{YYYY-MM-DD}-events-report.md`)*
