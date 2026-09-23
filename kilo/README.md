# kilo/ — Kilo CLI config (staging)

Source of truth for the Kilo CLI configuration. `../install.sh` symlinks
these files into `~/.config/kilo/`. Kilo CLI 1.x is a fork of OpenCode and
shares its config surface, so the layout mirrors `../opencode/`. Verified
against kilo.ai/docs, September 2026.

Markdown-first: **every setting that has a Markdown representation lives in
a `.md` file.** The jsonc file holds only the keys with no Markdown
equivalent (root default model, global permission policy, telemetry flags).

## Layout

| File | Purpose |
| --- | --- |
| `kilo.jsonc` | JSON-only keys: root `model`, global `permissions` (ordered, last match wins), optional `privacy_mode` / telemetry. Provider auth is **not** here — use `/connect` or `kilo auth`. |
| `AGENTS.md` | All standing rules (communication, work, conventions, testing/deps, shell safety, secrets), loaded automatically. `/init` maintains per-project AGENTS.md files. |
| `agents/*.md` | All agents: `build`, `plan`, `architect`, `quickfix`, `longread`, `research`. Filename becomes the agent name; YAML frontmatter carries `description`, `mode`, `model`, `permission`; the body is the system prompt. Invoke via the Task tool (automatic), `@agent-name`, or `kilo agent create`. |
| `commands/*.md` | Slash commands: `review`, `test`, `plan-feature`, `research`. Frontmatter: `description`, `agent`, `subtask` (the legacy `.kilocode/workflows/` format is auto-migrated to this command format). |
| `tui.jsonc` *(optional)* | TUI appearance/settings, read from `~/.config/kilo/tui.jsonc` or `.kilo/tui.json`. |
| `README.md` | This doc — repo-only, not installed. |

Merge order for agents: built-ins → global jsonc → project jsonc → global
md files → project md files; later sources override earlier.

## Model assignments — PLACEHOLDERS, verify first

The Kilo Gateway exposes 500+ models and its catalog shifts. The ids below
carry the same role split as the opencode config but are **best guesses**:

| Agent | Placeholder | Role |
| --- | --- | --- |
| build / root | `kilo-code/claude-sonnet-4-5` | Everyday editing agent + fallback. |
| plan | `kilo-code/claude-sonnet-4-5` | Read-only planning, edit denied. |
| architect | `kilo-code/claude-opus-4-6` | Frontier model; short hard sessions only. |
| quickfix | `kilo-code/grok-code-fast-1` | Cheap, fast, high-volume edits. |
| longread | `kilo-code/gemini-3-flash` | Cheap long-context distillation. |
| research | `kilo-code/claude-sonnet-4-5` | Tool-call-heavy web research. |

## Why these keys are in JSON (and their caveats)

`kilo.jsonc` is deliberately comment-free, pure JSON (editor-friendly);
everything it holds has no Markdown equivalent:

- `model` — root default and fallback for anything unset. **Best-guess
  placeholder** — see the table above and repoint via `kilo models`.
- `permissions` — global permission policy, ordered rules where **last
  match wins** (broad rules first, specific allow/deny after). Per-agent
  permissions live in `agents/*.md` frontmatter. Kilo adds `*`/`?`
  wildcards, `external_directory`, and `allow`/`ask`/`deny` effects on top
  of the upstream OpenCode format.
- Provider auth is **not** in this file: use `/connect` or `kilo auth`.
  `{env:VAR}` references are honored only in trusted config (this global
  file, `KILO_CONFIG`, or MDM) — never in repo-committed project config.
- Optional, omitted by default: `privacy_mode: true` /
  `experimental.openTelemetry: false` (telemetry is on by default), `mcp`,
  `formatter`, `lsp`. TUI appearance belongs in `tui.jsonc` next to this
  file. `instructions` is superseded by `AGENTS.md`, which loads
  automatically.
- Project-level config (`./kilo.jsonc` or `./.kilo/`) takes precedence over
  this global file; restart the CLI after editing.

## After installing — verify

1. `kilo models` — list real gateway model ids and repoint every
   assignment above (root `model` in kilo.jsonc, `model:` in agents/*.md).
2. `/connect` (or `kilo auth`) — add provider credentials. `{env:VAR}`
   references work in this global config but never in repo-committed
   project config.
3. `/agents` and the slash-command list — confirm the markdown-defined
   agents and commands appear.
4. Optional: `privacy_mode: true` / `experimental.openTelemetry: false` in
   kilo.jsonc if you want telemetry off (it's on by default).
5. Restart the CLI after editing config files.

## Project-level overrides

Per-repo config lives in `./kilo.jsonc` or inside `./.kilo/` (the CLI does
**not** read `.opencode/` dirs — migrate those), plus a per-project
`AGENTS.md`. Skills go in `~/.kilo/skills/` (global) or `.kilo/skills/`
(project), one `SKILL.md`-per-directory, name matching the directory name.
Recent CLI versions avoid creating `.kilo/` in non-git folders and skip
committing it in subdirectory workspaces.
