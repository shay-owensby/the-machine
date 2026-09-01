---
name: github-search
description: Find and rank current, top-starred open-source GitHub repositories that can improve workflows in Claude Code, Claude Cowork, ChatGPT Work, or Codex. Use when the user wants compatible agent tools, skills, plugins, MCP servers, extensions, automation frameworks, or developer utilities; return the findings in chat rather than exporting a report.
---

# GitHub Search

Find relevant repositories using current GitHub data, verify that each recommendation is genuinely usable in at least one requested environment, and present no more than 10 results in the conversation.

## Clarify the search

If the user has not given enough detail to distinguish relevant repositories from generally popular software, ask one concise message covering only the missing choices: what they want to accomplish, which of the four environments matter, and any hard constraints such as language, license, local-only operation, or ease of setup. Proceed without questions when the request already provides a usable topic and constraints.

When the user gives no platform preference, search across Claude Code, Claude Cowork, ChatGPT Work, and Codex. Interpret “use in” as practical integration with an agent workflow—not merely a repository whose code an agent could edit.

## Research and selection

1. Search the live web and GitHub rather than relying on remembered rankings or star counts. Prefer GitHub repository pages, READMEs, releases, and official product documentation as evidence.
2. Build a broad candidate set with multiple relevant terms because ecosystems use different labels, including skills, plugins, MCP, agents, commands, hooks, connectors, extensions, and automation. Do not install, clone, or execute a candidate unless the user separately asks.
3. Confirm that each candidate is a public GitHub repository with an identifiable open-source license. Exclude archived repositories, mirrors, abandoned proofs of concept, repositories without a license, and generic “awesome” lists unless the user explicitly wants those categories.
4. Verify platform fit from documentation or an explicit integration path. MCP support or another shared standard can establish cross-platform potential, but label it as such rather than claiming native support. Never infer compatibility solely from marketing language, repository topics, or the fact that the project is written in a common programming language.
5. Rank qualified candidates by current GitHub star count, highest first. Relevance and documented usability are eligibility gates, not hidden ranking factors. If fewer than 10 candidates meet the requirements, return fewer and explain why rather than lowering the bar.
6. Check recent maintenance signals and material caveats such as operating-system limits, paid-service dependencies, required API keys, self-hosting burden, or stale releases. A caveat does not automatically disqualify a repository, but disclose it when it affects practical use.

## Chat response

Return the findings directly in chat; do not create or export a file. State the interpreted search scope and the date checked, then list up to 10 repositories in descending star order.

For every result, include:

- repository name linked directly to GitHub;
- current star count, license, and most relevant supported environment or integration route;
- a 3–5 sentence summary explaining what it does, why it fits the user’s goal, how it connects to the named environment(s), and the most important setup consideration or caveat.

Keep factual claims traceable with links to the repository or its documentation. Clearly distinguish documented native support, standards-based compatibility, and reasoned but unverified potential. End with a brief note describing the eligibility filters and confirming that ordering is by stars.

## Boundaries

- Never return more than 10 repositories.
- Do not present proprietary or source-available software as open source.
- Do not pad the list with marginal matches.
- Do not export a Markdown, CSV, spreadsheet, or other artifact.
- Do not claim that a repository is safe or trustworthy merely because it is popular; advise the user to review permissions and installation scripts when a tool can execute code or access sensitive data.
