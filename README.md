# The Machine

An agency in a box — a Claude Code plugin marketplace where each installable
plugin is one department of a marketing agency.

Private repository. Add it in Claude Cowork or Claude Code from this repo and it
stays in sync as departments are added.

## Installing

```
/plugin marketplace add shay-owensby/the-machine
/plugin install public-relations@the-machine
```

## Departments

| Plugin | What it does |
|---|---|
| **public-relations** | Press releases, media lists, pitch angles, spokesperson prep, event and sponsorship scouting, reputation management |

## Layout

```
.claude-plugin/
  marketplace.json          declares every department plugin
<department>/
  skills/
    <skill-name>/
      SKILL.md              the spine — read first, kept short
      references/           method detail, loaded only when needed
      assets/               templates the skill writes from
```

Departments are declared entirely in the root `marketplace.json`; individual
department folders do not carry their own `plugin.json`.

## Skills

### public-relations / events-search

Finds local events — festivals, fairs, expos, charity runs, markets, school and
civic events — where a business should buy a booth or a sponsorship, then
qualifies the finalists with attendance, cost, application deadlines, and
organizer contacts.

Brand-agnostic. Every run reads the client project's own brief at
`Public Relations/Events/references/events-search-parameters.md` before searching,
writes a dated report to `Public Relations/Events/`, uploads it to the client's
Google Drive folder, and posts a decision summary to their Slack channel — both
destinations named in that same brief.

The repo holds the source, Drive holds the readable copy, Slack holds the
decision and the link. Slack caps a message at 5,000 characters and cannot take a
file upload, so the channel gets the deadlines, the top three picks, and the
biggest gap — not the whole report.

Neither destination is ever guessed. A blank folder or channel ID skips that
delivery and says so, rather than falling back to somewhere that looked right.
