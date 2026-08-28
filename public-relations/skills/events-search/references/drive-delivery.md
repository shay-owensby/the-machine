# Google Drive delivery

Slack cannot take a file upload from this toolset, so Drive is the hosting layer.
The chain is: the repo holds the source markdown, Drive holds the readable copy,
Slack holds the decision and a link to it.

## Where the folder comes from

The **Google Drive Folder ID** in `events-search-parameters.md`, under
`## Report Delivery`. A folder ID is the long opaque string from the folder's
URL — `https://drive.google.com/drive/folders/<THIS>` — not the folder's name.

**Never guess a folder.** No `search_files` for something that looks right, no
reusing a folder from a previous run for a different client. A blank ID skips the
upload; say so and let the Slack message link the repo path instead.

## The call

```
create_file
  title:           "Events Report — {Business}, {YYYY-MM-DD}"
  parentId:        {Google Drive Folder ID}
  textContent:     {the full report markdown}
  contentMimeType: "text/markdown"
```

Capture the file ID and web link from the response. If the response carries no
link, fetch it with `get_file_metadata` — do not hand-build a Drive URL.

## Upload it as a Doc, not a raw .md

`create_file` converts supported content to a Google first-party type **by
default**. That default is the one you want here: the report becomes a Google Doc
with real headings and rendered tables.

The link gets opened on a phone by someone who will not clone a repo. A Doc
reads; a raw `.md` file downloads, or renders as a wall of `##` and pipes.

- `contentMimeType: "text/markdown"` → converts to a Doc, keeping heading levels
  and tables. This is the path to use.
- `contentMimeType: "text/plain"` → also converts to a Doc, but the markdown is
  not interpreted: every `##` and `|` shows literally. Only acceptable as a
  fallback, and say so when you fall back.
- `disableConversionToGoogleType: true` → keeps the raw file. Use only if the
  client has actually asked for the markdown source in Drive.

## Re-runs create duplicates

Drive allows two files with the same title in the same folder, and nothing warns
you. Before uploading, check:

```
search_files  query: "parentId = '{folder}' and title contains 'Events Report'"
```

If a report with today's date is already there, this is a re-run. Upload with a
`(rev 2)` suffix in the title rather than creating a second file with an
identical name — the client should be able to tell which link Slack points at.

**`update_file` cannot replace content.** It updates the title and the parent
only. There is no edit-in-place path: a corrected report is a new upload, and the
Slack message should link the new one.

## The access trap

This is the failure that produces a perfect-looking run and a useless link.

The uploaded file inherits the **folder's** sharing. If that folder is not shared
with the people in the Slack channel, every one of them clicks the link and gets
*Request access* — and the failure surfaces hours later, from them, not from the
tool.

- `share_file` grants access to a **named email address** at `reader`,
  `commenter`, or `writer`. It cannot make a link public to anyone.
- So the fix for a channel of people is on the folder, once — not per file, per
  run.

On the first run against a new folder, say plainly in the final report that link
access depends on the folder's sharing, and that it is worth one person clicking
the Slack link to confirm before the next run.

## Failure modes

| Failure | What it means | What to do |
|---|---|---|
| Folder ID not found | Stale ID, or the folder was deleted or moved out of reach | Surface the ID that failed and ask. Do not search for a replacement |
| No permission to write | The account cannot add to that folder | Report it; the client must grant write access to the folder |
| Blank folder ID | Delivery not configured | Skip the upload, note it, let Slack link the repo path |
| Upload succeeds, link denied | Folder sharing, not the file | See the access trap above |

In every case the report file is already written. State what failed, give the one
action that fixes it, and carry on to Step 8 with the repo path as the link.
