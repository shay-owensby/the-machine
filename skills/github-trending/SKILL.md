---
name: github-trending
description: Find and report public repositories on GitHub's daily Trending page that have more than 50 total stars and documented compatibility with ChatGPT, Claude, or Grok. Use for on-demand or scheduled GitHub trend monitoring and daily AI-workflow repository notifications.
---

# GitHub Trending

Produce a concise daily watchlist of qualifying repositories. A scheduler may deliver the result as a notification, but this skill does not create or change schedules.

## Run the watch

1. From the user's active project directory, run:

   ```bash
   python3 ~/.codex/skills/github-trending/scripts/collect_trending.py --env-file ./.env --limit 10
   ```

2. Read the JSON result. The helper obtains candidates from GitHub's all-language daily Trending page, then uses the GitHub API to verify repository metadata and inspect each README. It reads `GITHUB_TOKEN` from the specified `.env` file; never print or expose the token.
3. Review the compatibility evidence before including a repository. Keep it only when the README documents a practical integration, setup, tool, agent, API, or workflow usable with at least one of ChatGPT/OpenAI, Claude/Anthropic, or Grok/xAI. A passing keyword alone is candidate evidence, not conclusive proof. Exclude incidental mentions, comparisons, unsupported roadmap claims, and repositories that merely discuss a model without enabling a workflow.
4. Return no more than 10 repositories in Trending-page order. Do not pad the result when fewer qualify.

## Qualification rules

- Include only public repositories currently listed on GitHub's daily Trending page for all languages.
- Require `stargazers_count > 50`. This is total repository stars; there is no star-growth window.
- Require documented compatibility with at least one of ChatGPT, Claude, or Grok. Treat an explicitly documented OpenAI-compatible interface as ChatGPT/OpenAI compatibility.
- Deduplicate repositories within the run.
- Do not substitute advertisements, sponsored placements, GitHub search popularity, or weekly/monthly Trending results.

## Report

Lead with either `N qualifying repositories today` or `No qualifying repositories today`.

For each result, include:

- linked `owner/repository` name;
- total stars and, when GitHub exposes it, stars gained today;
- compatible platform(s);
- one sentence explaining the usable workflow based on the README evidence;
- primary language when available.

Keep the report scannable. State that stars are total stars, not stars gained during the last 72 hours. If the helper returns a warning or the Trending page cannot be verified, disclose the limitation rather than presenting fallback search results as Trending.

## Failure handling

- If `./.env` or `GITHUB_TOKEN` is missing, ask the user to add `GITHUB_TOKEN=...` to the active project's `.env` file.
- If GitHub rejects the token, report the authentication error without echoing credentials.
- If GitHub changes the Trending page and no candidates can be parsed, use a browser to inspect `https://github.com/trending?since=daily`, apply the same rules manually, and clearly note that the helper parser needs maintenance.
- Make no repository changes, comments, stars, follows, or other GitHub mutations.
