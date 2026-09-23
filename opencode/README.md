# opencode/ — OpenCode v2 config (staging)

Source of truth for the OpenCode CLI v2 configuration. `../install.sh`
symlinks these files into `~/.config/opencode/` (the global config dir v2
reads; it also reads plain `.json`). Verified against the live v2 docs,
September 2026.

Markdown-first: **every setting that has a Markdown representation lives in
a `.md` file.** The jsonc file holds only the keys with no Markdown
equivalent in v2 (root default model, `default_agent`, global permission
policy, websearch provider, `update`).

## Layout

| File | Purpose |
| --- | --- |
| `opencode.jsonc` | JSON-only keys: root `model`, `default_agent`, global `permissions` (ordered, last match wins), `websearch.provider`, `warming`, `update`. |
| `AGENTS.md` | All standing rules (communication, work, conventions, testing/deps, shell safety, secrets), loaded automatically from `~/.config/opencode/AGENTS.md`. |
| `agents/*.md` | All agents: `build`, `plan`, `architect`, `quickfix`, `longread`, `research`, `title`, `summary`. Filename (minus `.md`) becomes the agent name; YAML frontmatter carries `description`, `mode`, `model`, `variant`, `permission`; the body is the system prompt. |
| `commands/*.md` | Slash commands: `review`, `test`, `plan-feature`, `research`. Frontmatter: `description`, `agent`, `subtask`. Body is the prompt template (`$ARGUMENTS`, `$1`…, `` !`shell` ``, `@file` all work). |
| `README.md` | This doc — repo-only, not installed. |

Precedence notes: `agents/` is the correct v2 directory name (plural), for
both global (`~/.config/opencode/agents/`) and project (`.opencode/agents/`)
overrides. A project-level agent with the same name overrides the global
one. The `tools` agent field is deprecated in v2 — use `permission`.

## Why these keys are in JSON (and their caveats)

`opencode.jsonc` is deliberately comment-free, pure JSON (editor-friendly);
everything it holds has no Markdown equivalent in v2:

- `model` — root default and fallback for any agent/session that doesn't
  pick one explicitly. Every shipped agent pins its own model, so this only
  catches ad-hoc/unset cases. Mirrors build's model.
- `default_agent: build` — the `build` agent itself is defined in
  `agents/build.md` (model + `variant: high` there).
- `permissions` — global permission policy, ordered rules where **last
  match wins** (broad rules first, specific allow/deny after). Per-agent
  permissions live in `agents/*.md` frontmatter. `external_directory` and
  `*.env` reads already default to `ask` in v2's base policy and are left
  untouched.
- `websearch.provider: random` — retries across connected providers; needs
  one of Exa/Firecrawl/Parallel/Tavily connected via `/connect`.
- `warming: false` — warming sends billable requests when enabled; kept off.
- Gone/renamed in v2 (do not re-add): `autoupdate`, `small_model`,
  `permission{bash}`, `agent{}`, `command{}`, `mcp{<name>}`, `provider{}`.
  `instructions` is superseded by `AGENTS.md`, which is loaded
  automatically. `share`, `lsp`, `formatter` are accepted v2 keys but not
  wired to runtime behavior yet — omitted on purpose.

## Model assignments

Role-based, cheapest-capable-model-per-job (pricing/quota reasoning lives as
comments in each agent file):

| Agent | Model | Why |
| --- | --- | --- |
| build (default) | `opencode-go/glm-5.3-flash` (variant: high) | Editing agent; fast but capable. |
| plan | `opencode-go/glm-5.3` (variant: high) | Whole-repo analysis, edit denied. |
| architect | `opencode-go/kimi-k3` | Strongest on the roster; short hard sessions only. |
| quickfix | `opencode-go/mimo-v2.6-flash` | Cheapest capable; high-volume small edits. |
| longread | `opencode-go/longcat-2.0` | Cheapest cached reads; large-context distillation. |
| research | `opencode-go/minimax-m3` (variant: high) | Tool-call-heavy web research. |
| title / summary | `opencode/mimo-v2.6-flash-free` | Free Zen tier; needs the separate `opencode` (Zen) connection via `/connect`. |

The root `model` in `opencode.jsonc` mirrors build's model as the fallback
for anything unset.

## After installing — verify

Model ids and variant support shift; these were checked 2026-09-23.

1. `opencode` → `/models` — confirm every id above exists on the connected
   providers (one `opencode-go` connection, plus a separate `opencode` Zen
   connection for the free title/summary models).
2. `/variants` — if GLM/MiniMax reasoning variants don't surface (Zen bug
   #24010 existed), remove the `variant` keys in `agents/build.md`,
   `agents/plan.md`, `agents/research.md`. Markdown-defined agents accept
   `variant` as a passed-through key — confirm it takes effect there.
3. `/connect` — set up websearch (Exa/Firecrawl/Parallel/Tavily) unless
   already connected; config uses `provider: "random"`.
4. `/agents` and the slash-command list — confirm all eight agents and four
   commands appear (title/summary should stay hidden unless overriding).

## Project-level overrides

For a specific repo, copy files into `.opencode/` (`opencode.json` or
`.opencode/opencode.jsonc`, `agents/`, `commands/`, plus a per-project
`AGENTS.md`) — project config wins over global. Remember: whole-object
replacement applies to some sections (e.g. `mcp.servers`), so repeat
required fields there.
