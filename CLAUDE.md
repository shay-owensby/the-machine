# the-machine

A collection of Claude Code plugins (skills, agents, MCP configs) built for reuse across projects. Each plugin lives in its own top-level directory (e.g. `email-marketing/`) following the standard Claude Code plugin layout:

```
.claude-plugin/
  marketplace.json      # catalog — every plugin must be listed here
<plugin-name>/
  .claude-plugin/
    plugin.json         # bump "version" on every release
  agents/
  skills/
  mcp.json
```

## Rules

- **Reference official plugin docs**: When creating or modifying plugins, consult [_guides/plugins-reference.md](_guides/plugins-reference.md) — the official Claude Code plugins reference documentation — to ensure layout, manifests, and conventions match spec.

- **Brand-agnostic**: All skills, agents, and plugins created in this project must be brand-agnostic. Do not hardcode client names, brand voice, product details, or other client-specific context into skill/agent instructions. Client- or brand-specific configuration belongs in the consuming project (e.g. via arguments, config files, or MCP resources supplied at call time), not baked into the plugin itself. This project's plugins are shared globally across all of the user's other projects, so anything brand-specific here would leak into unrelated work.

- **Setup command required**: Every plugin must ship a `/setup-<skill name>` command that the client runs to configure the plugin for their project before first use (e.g. collecting client-specific config, credentials, or brand context and writing it to the consuming project). Skills and agents in the plugin must check whether this setup has been completed for the current project, and if not, guide the user through running `/setup-<skill name>` before proceeding rather than failing silently or proceeding with missing configuration.

- **Prefix skills and agents with the plugin's short name**: Every skill and agent in a plugin must be named with a short, identifiable prefix derived from the plugin name, so they group together in the slash-command list and stay unambiguous when several plugins are installed side by side. Use the plugin name directly when it is already short (`email-marketing` → `email-`, `social-media` → `social-`); when it is long, use a recognizable abbreviation instead (`search-engine-optimization` → `seo-`). Pick the prefix once per plugin and keep it stable.
  - Apply it to all three places that must agree: the skill's directory name (`skills/<prefix>-<name>/SKILL.md`), the agent's filename, and the `name:` field in that file's frontmatter. A mismatch between filename and frontmatter `name:` breaks invocation.
  - Commands follow the same convention (`/email-newsletter`), except the mandatory setup command, which keeps its `/setup-<plugin-name>` form.
  - **Never apply the prefix to files the plugin writes into the client project.** Those are data paths that existing installs depend on — e.g. the topic log stays `email-marketing/references/topic-researcher.md` even though the agent that writes it is now `email-topic-researcher`. Renaming a component is cosmetic; renaming a client data file destroys history.

- **Publishing plugin updates**: This repo is a plugin marketplace (`the-machine`, catalog at [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json)). Teammates install these plugins in the Claude Cowork desktop app with auto-sync on, so a change only reaches them once it is committed, pushed, **and carries a new version number**. When releasing a change to a plugin, consult [_guides/plugin-marketplace.md](_guides/plugin-marketplace.md) and:
  1. **Bump `version` in the plugin's `.claude-plugin/plugin.json`** — patch for a fix, minor for a new skill/agent/command, major for a breaking config change. This is mandatory, not optional: Claude Code compares this string to decide whether to update an installed plugin, so pushing commits without bumping it delivers nothing to teammates and reports no error. Never set `version` in both `plugin.json` and `marketplace.json` — `plugin.json` silently wins.
  2. **Register new plugins in the catalog** — a new plugin directory is invisible to teammates until it is added to the `plugins` array in `.claude-plugin/marketplace.json`. Never rename or remove a plugin's `name` without adding a `renames` entry: the name is the stable identifier in teammates' settings, and changing it breaks every existing install.
  3. **Validate before pushing** — run `claude plugin validate .` from the repo root, and against the plugin directory itself (e.g. `claude plugin validate ./email-marketing`) to check skill and agent frontmatter.
  4. **Commit and push to the GitHub remote** — auto-sync pulls from the default branch, so an unpushed commit reaches no one.

- **Parallel agent/subagent execution**: Dispatch agents in parallel when there are 3+ independent tasks with no shared files — send the Agent calls in a single message, or use `parallel`/`pipeline` in workflow scripts. Go sequential when tasks have dependencies (a later step needs an earlier step's output) or when they write to overlapping files.
