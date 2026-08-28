# Slack delivery

The report file is the document, Drive hosts the readable copy, and the Slack
message is the decision. Do not try to make the message be the report — and note
that this toolset cannot attach a file to a Slack message, which is why Step 7
uploads to Drive first.

## Where the channel comes from

The **Slack Channel ID** in `events-search-parameters.md`, normally under a
`## Report Delivery` heading. A Slack channel ID looks like `C08PT0A2YPQ` — it
starts with `C` (public or private channel) or `D` (DM), and it is not a channel
name.

Three rules, in order of how much damage breaking them does:

1. **Never guess a channel.** No `slack_search_channels` by name, no "the one
   that sounds right," no falling back to a channel used on a previous run for a
   different client. Posting a client's report into another client's channel is
   not recoverable.
2. **A missing ID is not an error to route around.** Write the report, tell the
   user Slack delivery was skipped because the field is blank, and stop.
3. **If the ID appears twice with different values, ask.** Do not pick one.

If the user asks you to look up the channel, `slack_search_channels` is the tool
— but write the ID they confirm back into the parameters file so the next run
does not have to ask again.

## The 5,000-character ceiling

`slack_send_message` caps a text element at 5,000 characters. A finalist report
runs well past that.

**Budget 3,000 characters. Treat 5,000 as the wall.**

When the summary does not fit, cut in this order:

1. Drop finalists 4+ from the message entirely — they are in the file.
2. Collapse the "why" lines to one clause each.
3. Drop the considered-and-passed count line.

**Do not split the report across several messages.** Three consecutive walls of
text in a client channel is worse than one tight summary plus a file path. And
do not silently truncate mid-table — Slack will render a broken table rather than
fail.

## Every message opens with @channel

The message begins with `<!channel>`, on its own line, before anything else.

**Write `<!channel>`, not `@channel`.** The Slack Web API takes channel-wide
mentions in angle-bang form. A literal `@channel` in the message body posts as
plain grey text and notifies nobody — the message looks right in the channel and
silently fails at the only job the mention has.

| Want | Write |
|---|---|
| Notify everyone in the channel | `<!channel>` |
| Notify active members only | `<!here>` |
| A specific person | `<@U01RQT2Q9TJ>` |

**Verify this once, on the first run against a new workspace.** Open the posted
message and check the mention rendered as a blue, highlighted `@channel` rather
than literal text. If it came through literally, the MCP layer escaped it — say
so, fall back to plain `@channel`, and tell the user the notification did not
fire.

Two things worth knowing, neither of which changes the rule:

- `@channel` notifies **every member**, including people who are offline or on
  Do Not Disturb. The desktop app's "are you sure?" prompt for large channels
  does not exist on the API path — it just sends.
- Some workspaces restrict `@channel` to admins. Where it is restricted the
  message still posts, but the mention does not notify. If the client reports no
  alert, this is the first thing to check.

## Message shape

Structure and exact wording: `assets/slack-summary-template.md`. In brief:

- `<!channel>` on its own line, first
- A headline naming the business and the window searched
- **ACT NOW** first, if anything closes inside 30 days — this is the reason the
  message exists at all
- Top three finalists: name, date, cost, one reason
- Counts: candidates found, finalists, passed
- The one biggest gap
- The Google Drive URL from Step 7, bare on its own line, last

Formatting notes for `slack_send_message`:

- Standard markdown — `**bold**`, `_italic_`, `` `code` ``, lists, links, tables
- Tables use `|` delimiters; do **not** escape the structural pipes, only a
  literal `|` inside a cell value
- Keep tables to three or four columns. Slack renders wide tables badly on
  mobile, and this message gets read on a phone
- Link event names to their source URL rather than pasting bare URLs
- The closing link is the Drive URL from Step 7, pasted **bare** on its own line
  rather than wrapped in markdown — Slack unfurls a Drive URL into a card showing
  the document title, which a `[label](url)` link suppresses
- Use the link Drive returned. Never assemble a Drive URL from a file ID
- Fall back to the repo path only when the upload was skipped or failed, and say
  which it was
- Do not put anything sensitive in link query parameters

## Preview before sending

Show the composed message and the destination channel ID in the terminal, then
send. If the user has not seen the text — an unattended or scheduled run counts —
use `slack_send_message_draft` instead of `slack_send_message`, so a human
releases it.

Return the message permalink in the final report to the user.

## The four ways this fails

| Failure | What you will see | What to do |
|---|---|---|
| **Slack Connect channel** | Posting to externally shared channels is not supported | Report the block; the channel must be an internal one |
| **Not a member of the channel** | `not_in_channel` | Tell the user to invite the Slack app to the channel; do not try another channel |
| **Bad or stale channel ID** | `channel_not_found` | Do not search for a replacement — surface the ID that failed and ask |
| **Free workspace** | Canvas creation unavailable | Only relevant if using a canvas; the plain message path is unaffected |
| **@channel restricted** | Message posts, nobody is notified | Workspace policy limits `@channel` to admins — tell the user; it is not fixable from here |

In every case: the report file is already written, so the run has still produced
its deliverable. Say what failed, say the report is on disk, and hand the user
the one action that fixes it.

## Optional — canvas for the full report

On a paid workspace, `slack_create_canvas` can carry the whole report, and the
message then links to it. Worth doing when the client works out of Slack rather
than out of the repo.

Two constraints if you do: canvas markdown is its own dialect — ATX headings only
(`#`, `##`, `###`), no headings inside list items, no code blocks inside list
items, and channel references written as `![](#C08PT0A2YPQ)`. And it is not
available on free teams, so the plain-message path must still work when canvas
creation fails.
