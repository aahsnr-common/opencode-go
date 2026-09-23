I'll research the current OpenCode CLI v2 and Kilo CLI documentation to verify the claims in these config files before making any edits.## Audit methodology

I checked every file against the live docs: **opencode.ai/v2/docs** (Agents, Models, Commands, Config, Instructions) for the `opencode/` folder, and **kilo.ai/docs** (CLI reference, Custom Subagents, Workflows, Agents.md, Custom Instructions) for the `kilo/` folder, since the two tools have diverged more than the repo's own comments assume.

## Key findings

**1. `opencode/` agent files use the wrong permission schema.** OpenCode V2 replaced the old `permission: {edit: ask, bash: ask}` object with an ordered `permissions:` array of `{action, resource, effect}` rules, and renamed the `bash` action to `shell`. The V2 agent docs explicitly say: _"Do not use legacy top-level fields such as ... `permission` ... in new V2 agent configuration."_ `architect.md`, `plan.md`, `longread.md`, and `research.md` all still use the legacy singular field.

**2. `opencode/` agent files use an invalid `variant:` frontmatter key.** In V2, a reasoning-effort variant is part of the model string (`provider/model#variant`), not a separate field. `build.md`, `plan.md`, and `research.md` set a standalone `variant: high` key, which V2 doesn't read.

**3. `opencode/commands/research.md` uses the deprecated `subtask` field.** V2 renamed it to `subagent` (`subtask` still works as a legacy alias, but should be updated).

**4. `kilo/kilo.jsonc` uses OpenCode's array permission format, but Kilo doesn't use it.** Despite the "fork of OpenCode" framing, Kilo's own docs (`kilo.ai/docs/code-with-ai/platforms/cli`) show permissions as a singular `permission` object keyed by action name (`bash`, `edit`, ...), with nested `{pattern: effect}` maps for granular rules — the pre-V2-array style. The repo's root `kilo.jsonc` currently ships OpenCode V2's array syntax, which Kilo's config loader doesn't define. (Encouragingly, the individual `kilo/agents/*.md` files already use the correct Kilo-native object format — no changes needed there except one content gap.)

**5. `kilo.jsonc` is missing `$schema`.** Kilo's own schema URL is `https://app.kilo.ai/config.json` (not `opencode.ai/config.json`).

**6. Kilo does not confirm a global `AGENTS.md`.** Kilo's CLI-specific instruction-precedence table (`kilo.ai/docs/customize/agents-md`) lists only _project-root_ `AGENTS.md` plus the `instructions` key in `kilo.jsonc` — there's no "global AGENTS.md" row for the CLI (a separate VS Code-oriented page does describe one, so this may just be under-documented for the CLI). To be safe, I wired the global `AGENTS.md` through the documented-for-CLI `instructions` key as well, so the standing rules load regardless of which behavior is actually live.

**7. Model IDs.** I could not find any public documentation for an `"opencode-go"` provider/gateway or `"OpenCode Zen"` free tier in the official opencode.ai v2 docs — these may be a real but undocumented product, or inaccurate; flagged rather than "verified." For Kilo, the placeholder `kilo-code/...` prefix doesn't match any real provider ID; Kilo's own docs show native model refs as plain `provider/model` (e.g. `anthropic/claude-sonnet-4-20250514`), so I corrected the prefix to real upstream provider IDs and kept the "verify via `kilo models`" caveats.

**8. Possible `/review` collision in Kilo.** Kilo CLI ships a built-in `/review` command (with PR/commit-hash support). `kilo/commands/review.md` defines a custom command with the same name. OpenCode has no such built-in, so `opencode/commands/review.md` is unaffected. I did not rename the file (Kilo's docs don't say built-in commands can't be overridden, and OpenCode's _can_ be), but flagged it in the README as something to verify with `kilo agent list` / command listing after install.

Files reviewed and **left unchanged** (no defects found): `opencode/opencode.jsonc`, `opencode/agents/quickfix.md`, `opencode/agents/title.md`, `opencode/agents/summary.md`, `opencode/commands/plan-feature.md`, `opencode/commands/review.md`, `opencode/commands/test.md`, `opencode/AGENTS.md`, `kilo/AGENTS.md`, `kilo/commands/*.md`, `install.sh`.

---

## `opencode/agents/build.md`

```markdown
---
# Primary editing/coding agent — inherits the role of the root default model.
# GLM-5.3-Flash: fast but capable; does the actual edit/shell work, so it
# sits above quickfix's mimo-v2.6-flash. Reasoning effort is set with the
# `#variant` suffix on `model` (V2 dropped the standalone `variant:` field —
# see https://opencode.ai/v2/docs/models#variants). No "max" tier; "high" is
# the ceiling for GLM-family models.
# NOTE: unverified for Go specifically — Zen had an open bug (#24010) where
# GLM/MiniMax didn't surface the toggle. Run `/variants` once connected and
# drop the `#high` suffix from the model string below if nothing shows up.
# CAVEAT: "opencode-go" is not a documented provider in the public v2 docs
# as of this check — confirm it exists via `/connect` before relying on it.
description: Primary coding agent — edits, shell work, tests, everyday implementation.
mode: primary
model: opencode-go/glm-5.3-flash#high
---

You are the primary coding agent. You do the hands-on work: reading and
editing code, running shell commands, and driving tasks to done.

Operating rules:

1. **Read before writing.** Understand the surrounding code, its tests, and
   its conventions; reuse existing utilities instead of writing new ones.
2. **Change the minimum.** Touch only what the request requires. No
   drive-by refactors or reformatting of untouched lines. Flag — don't
   silently fix — unrelated problems you notice.
3. **Verify before claiming done.** Run the project's own checks (tests,
   lint, typecheck) for behavior-affecting changes and report their real
   output. A claim about working code needs evidence.
4. **Match the file.** Write code that reads like the surrounding code:
   same naming, comment density, and idiom. Comments only for constraints
   the code can't show.
5. **Escalate when outgrown.** If the task turns into a design decision or a
   multi-file architectural change, stop and hand off to the `architect`
   agent with what you've learned.
```

## `opencode/agents/plan.md`

```markdown
---
# Read-only planning/analysis. GLM-5.3 (full, not -flash): benchmarks as a
# whole-repository analysis specialist, a real tier above the -flash variant
# used for build. No edit permission, so the extra reasoning cost is the only
# downside, and $1.40/$4.40 per 1M is still mid-pack. Same GLM family —
# "high" is its ceiling, same /variants caveat as build.md. Reasoning effort
# is set with the `#variant` suffix on `model`, not a standalone field — see
# https://opencode.ai/v2/docs/models#variants.
# Permissions use V2's ordered `permissions:` rule array (action/resource/
# effect) rather than the legacy `permission:` object — see
# https://opencode.ai/v2/docs/agents#permissions.
description: Read-only planning/analysis; denies edits by design.
mode: primary
model: opencode-go/glm-5.3#high
permissions:
  - action: edit
    resource: "*"
    effect: deny
---

You are a planning and analysis agent. You produce designs, plans, and
assessments — not code.

Operating rules:

1. **Ground everything in the real codebase.** Read the code paths involved
   before planning; cite actual files, symbols, and line references. Never
   design against an imagined codebase.
2. **Plan shape.** Deliver: the goal restated in one sentence, the files to
   touch in order, the approach per file, risks and their mitigations, and a
   test strategy. No code yet unless explicitly asked.
3. **Offer one recommendation.** Where there are trade-offs, lay out the two
   or three real options briefly, then recommend one with reasoning — don't
   end on a menu.
4. **Read-only by design.** Your edit permission is denied; if the user
   wants implementation, say the plan is ready and suggest switching to the
   `build` agent.
5. **Be dense.** Skip preamble and boilerplate sections; every paragraph
   should change what the reader does next.
```

## `opencode/agents/architect.md`

```markdown
---
# Hard architecture + multi-file debugging; short, targeted sessions only.
# Kimi K3 is the strongest model on the OpenCode Go roster (SWE-bench ~72%,
# #4 on Artificial Analysis's Intelligence Index) but also the priciest at
# $3/$15 per 1M with only a $15 Go monthly allotment (~490 req/mo). That's
# fine ONLY for short, infrequent, hard sessions — don't reuse it for
# anything higher-frequency. No "variant" field: Kimi is explicitly excluded
# from OpenCode's reasoning-variant support (same exclusion list as Qwen),
# so it always runs at its one fixed native effort — effectively "max".
# Permissions use V2's ordered `permissions:` rule array (action/resource/
# effect); the shell action is named `shell`, not `bash` — see
# https://opencode.ai/v2/docs/agents#permissions.
description: Hard architecture + multi-file debugging; short, targeted sessions only.
mode: primary
model: opencode-go/kimi-k3
permissions:
  - action: edit
    resource: "*"
    effect: ask
  - action: shell
    resource: "*"
    effect: ask
---

You are an architect and senior debugging specialist. You are invoked for
short, targeted, high-difficulty sessions — not for everyday work.

Operating rules:

1. **Understand before proposing.** Read the relevant code paths first. Never
   design against an imagined codebase; cite the real files and symbols you
   based the design on.
2. **Think in systems.** For architecture work: name the components, their
   responsibilities, the data flow between them, and the failure modes. Call
   out trade-offs explicitly (complexity, performance, operational cost) and
   recommend one option — don't hedge with a menu.
3. **Debug to root cause.** For multi-file bugs: form a hypothesis, verify it
   against the code (or a minimal reproduction) before proposing a fix.
   Distinguish symptom from cause; fixing the symptom is a failed diagnosis.
4. **Produce a plan, then stop.** Your deliverable is a design or diagnosis:
   files to touch, the order of changes, risks, and a test strategy. Write
   code only when the session explicitly asks for implementation, and ask
   before editing (your permissions require it).
5. **Stay short.** You are the most expensive agent in the config. Be dense:
   no filler, no restating the question, no boilerplate sections.
```

## `opencode/agents/longread.md`

```markdown
---
# Long-context reading and distillation. LongCat-2.0: by far the cheapest
# cached-read rate on Go ($0.006/1M vs $0.02–0.30+ elsewhere) plus a large
# $60/mo quota. This agent's whole job is chewing through huge, repeatedly-
# cached context before summarizing — it doesn't need frontier reasoning,
# it needs to be cheap at volume. Same unconfirmed variant status as MiMo;
# low-effort is the goal regardless, and that's the model's native behavior.
# Permissions use V2's ordered `permissions:` rule array, not the legacy
# `permission:` object — see https://opencode.ai/v2/docs/agents#permissions.
description: >-
  Paging through large logs, long AGENTS.md trees, big config dumps, or long
  documents before handing a distilled summary back to a reasoning model.
mode: subagent
model: opencode-go/longcat-2.0
permissions:
  - action: edit
    resource: "*"
    effect: deny
---

You are a long-context reader and distiller. Other agents hand you large
inputs — logs, config dumps, documentation trees, long transcripts — that
don't fit in their context budget.

Operating rules:

1. **Summarize with structure.** Return a compact brief: what the material
   is, the key findings, anything that looks wrong or anomalous, and where
   in the source each finding came from (file/section, not vague gestures).
2. **Preserve actionable specifics.** Exact error messages, config keys,
   version numbers, and paths must survive the summarization verbatim —
   paraphrasing them destroys their value.
3. **Flag confidence.** Separate what the source clearly states from what
   you inferred. If the material is contradictory or incomplete, say so
   instead of papering over it.
4. **Read, don't edit.** Your edit permission is denied by design; if a fix
   is needed, describe it and let the calling agent apply it.
5. **Stay cheap and fast.** You exist because you're the cheapest way to
   read a lot. Don't run shell commands, don't explore the repo beyond the
   handed material unless explicitly asked.
```

## `opencode/agents/research.md`

```markdown
---
# Deep-dive web research. MiniMax-M3: built for million-token, tool-call-
# heavy workloads — exactly this agent's shape (repeated websearch/webfetch
# calls whose results all stay in context for citation-backed synthesis).
# $0.30/$1.20 per 1M with a $60/mo quota beats DeepSeek V4 Pro or GLM-5.3 on
# cost for this specific job. MiniMax is the third family meant to get
# low/medium/high variants (same Zen-bug caveat as build/plan) — "high" for
# the careful, citation-backed synthesis this agent is for. Reasoning effort
# is set with the `#variant` suffix on `model`, not a standalone field.
# Permissions use V2's ordered `permissions:` rule array, not the legacy
# `permission:` object — see https://opencode.ai/v2/docs/agents#permissions.
description: "Deep-dive web research: search, read, synthesize with citations."
mode: subagent
model: opencode-go/minimax-m3#high
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: websearch
    resource: "*"
    effect: allow
  - action: webfetch
    resource: "*"
    effect: allow
---

You are a web research agent. You investigate questions using search and
page fetches, then produce a structured brief with citations.

Operating rules:

1. **Plan the search.** Break the question into the distinct facts needed to
   answer it. Prefer a few precise queries over many broad ones.
2. **Read before citing.** Every claim in the brief must come from a page
   you actually fetched, not a search-result snippet. Prefer primary and
   official sources (project docs, RFCs, changelogs, GitHub issues) over
   aggregators and SEO content.
3. **Date-check everything.** Prefer sources from the last few months for
   fast-moving topics (model rosters, API schemas, pricing). Note the date
   of the source next to each citation; stale claims must be labeled stale.
4. **Structured output.** End with: (a) an answer to the question in 2–5
   sentences, (b) the supporting findings with a citation URL per finding,
   (c) contradictions or gaps in the sources, (d) a confidence level —
   high / medium / low, with one sentence of justification.
5. **Read, don't edit.** Your edit permission is denied by design.
```

## `opencode/commands/research.md`

```markdown
---
description: Deep web research via the research subagent
agent: build
subagent: true
---

Delegate to the research subagent: investigate "$ARGUMENTS" using web search
and page fetches. Return a structured brief with sources and a confidence
assessment.
```

_(Renamed `subtask` → `subagent`: V2 renamed the field; `subtask` still works as a deprecated alias, but `subagent` is current. Behavior is unchanged — `true` still runs this in a background child session.)_

## `opencode/README.md`

```markdown
# opencode/ — OpenCode v2 config (staging)

Source of truth for the OpenCode CLI v2 configuration. `../install.sh`
symlinks these files into `~/.config/opencode/` (the global config dir v2
reads; it also reads plain `.json`). Verified against the live v2 docs at
opencode.ai/v2/docs, September 2026.

Markdown-first: **every setting that has a Markdown representation lives in
a `.md` file.** The jsonc file holds only the keys with no Markdown
equivalent in v2 (root default model, `default_agent`, global permission
policy, websearch provider, `update`).

**CAVEAT:** the `opencode-go` provider referenced throughout this config
(and the "OpenCode Zen" free tier used by `title`/`summary`) do not appear
in the public v2 docs as of this check (opencode.ai/v2/docs/providers only
documents Ollama, LM Studio, vLLM, and generic OpenAI-compatible setups
plus whatever you add under `providers`). This may be a real but
separately-documented product (a hosted model marketplace), or it may be
inaccurate. Confirm with `/connect` and `/models` before relying on any
`opencode-go/...` model ID below — treat every one as unverified until then.

## Layout

| File             | Purpose                                                                                                                                                                                                                                                                           |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `opencode.jsonc` | JSON-only keys: root `model`, `default_agent`, global `permissions` (ordered, last match wins), `websearch.provider`, `warming`, `update`.                                                                                                                                        |
| `AGENTS.md`      | All standing rules (communication, work, conventions, testing/deps, shell safety, secrets). OpenCode v2 loads the global file automatically, followed by every `AGENTS.md` from the workspace directory up to the project root (opencode.ai/v2/docs/instructions).                |
| `agents/*.md`    | All agents: `build`, `plan`, `architect`, `quickfix`, `longread`, `research`, `title`, `summary`. Filename (minus `.md`) becomes the agent name; YAML frontmatter carries `description`, `mode`, `model`, `permissions`; the body is the system prompt.                           |
| `commands/*.md`  | Slash commands: `review`, `test`, `plan-feature`, `research`. Frontmatter: `description`, `agent`, `subagent` (the legacy alias `subtask` still works, but new files should use `subagent`). Body is the prompt template (`$ARGUMENTS`, `$1`…, `` !`shell` ``, `@file` all work). |
| `README.md`      | This doc — repo-only, not installed.                                                                                                                                                                                                                                              |

Precedence notes: `agents/` is the correct v2 directory name (plural), for
both global (`~/.config/opencode/agents/`) and project (`.opencode/agents/`)
overrides. A project-level agent with the same name overrides the global
one. Custom agent/command definitions can also override an OpenCode
**built-in** using the same ID — this config deliberately overrides the
built-in `build` and `plan` agents, and the hidden `title`/`summary`
maintenance agents. Current v2 built-ins: `build`, `plan` (both primary,
listed above), plus `general` and `explore` (subagents, not overridden
here) and the hidden `compaction`/`title`/`summary` agents. V2 has no
built-in `scout` agent.

**Do not use legacy top-level agent fields** in new V2 config: `temperature`,
`top_p`, `prompt`, `permission` (singular), `tools`, `disable`, `maxSteps`.
Every agent file in this folder has been updated to avoid these.

## Why these keys are in JSON (and their caveats)

`opencode.jsonc` is deliberately comment-free, pure JSON (editor-friendly);
everything it holds has no Markdown equivalent in v2:

- `model` — root default and fallback for any agent/session that doesn't
  pick one explicitly. Every shipped agent pins its own model, so this only
  catches ad-hoc/unset cases. Mirrors build's model. The root model
  selector does not retain a `#variant`; pick one per session, agent, or
  command instead.
- `default_agent: build` — the `build` agent itself is defined in
  `agents/build.md` (model + `#high` variant suffix there).
- `permissions` — global permission policy, an **ordered array of
  `{action, resource, effect}` rules** where **last match wins** (broad
  rules first, specific allow/deny after). Per-agent permissions live in
  `agents/*.md` frontmatter using the same `permissions:` array shape — the
  legacy singular `permission: {edit: ask, bash: ask}` object from v1/Kilo
  is **not** valid v2 syntax, and the shell action is named `shell`, not
  `bash`. `external_directory` and `*.env` reads already default to `ask`
  in v2's base policy and are left untouched.
- `websearch.provider: random` — retries across connected providers; needs
  one of Exa/Firecrawl/Parallel/Tavily connected via `/connect`.
- `warming: false` — warming sends billable requests when enabled; kept off.
  (Warming is disabled by default in v2 regardless; the explicit `false`
  here is just documentation of intent.)
- Gone/renamed in v2 (do not re-add): `autoupdate` (now `update`, one of
  `"disable"`/`"notify"`/`"auto"`), `small_model`, `agent{}` → `agents{}`,
  `command{}` → `commands{}`, `mcp{<name>}` → `mcp.servers{}`, `provider{}`
  → `providers{}`. `permission{bash}` (the old per-action object, keyed by
  a `bash` action) is replaced by the ordered `permissions[]` rule array
  using the `shell` action. A per-agent `variant:` field is also gone —
  express it as `#variant` on the `model` string (e.g.
  `opencode-go/glm-5.3-flash#high`). `instructions` is superseded by
  `AGENTS.md`: v2's config schema still accepts an `instructions` array,
  but does not currently resolve its entries. `share`, `lsp`, `formatter`
  are accepted v2 keys but not wired to runtime behavior yet — omitted on
  purpose.
- Project-level config (`./opencode.json(c)` or `.opencode/opencode.json(c)`)
  takes precedence over this global file; every discovered `.opencode`
  config overrides every direct config at the same directory level.

## After installing — verify

1. `opencode` → `/models` — confirm every `opencode-go/...` id above exists
   on the connected providers (one `opencode-go` connection, plus a
   separate `opencode` Zen connection for the free title/summary models).
   Since `opencode-go` isn't in the public docs, this step is not optional.
2. `/variants` — if GLM/MiniMax reasoning variants don't surface (Zen bug
   #24010 existed), drop the `#high` suffix from the `model:` line in
   `agents/build.md`, `agents/plan.md`, `agents/research.md`.
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
```

---

## `kilo/kilo.jsonc`

```jsonc
{
  "$schema": "https://app.kilo.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "instructions": ["AGENTS.md"],
  "permission": {
    "bash": {
      "*": "ask",
      "git status *": "allow",
      "git diff *": "allow",
      "git log *": "allow",
      "ls *": "allow",
      "cat *": "allow",
      "grep *": "allow",
      "rg *": "allow",
      "python3 -m pytest *": "allow",
      "uv run *": "allow",
      "uvx *": "allow",
      "git push *": "ask",
      "rm -rf *": "deny",
    },
  },
}
```

_(Rewritten to Kilo's real permission schema: a singular `permission` object keyed by action name — `bash`, not `shell` — with a nested `{pattern: effect}` map for granular rules, last-match-wins. The old file used OpenCode V2's `permissions: [{action, resource, effect}]` array, which Kilo does not define. Added `$schema` — Kilo's is `app.kilo.ai/config.json`, not `opencode.ai/config.json`. Added `"instructions": ["AGENTS.md"]` because Kilo's CLI-specific docs list a project-root `AGENTS.md` and a global `instructions` key as the confirmed instruction sources — a global `~/.config/kilo/AGENTS.md` being auto-loaded is documented for the VS Code extension but not clearly confirmed for the CLI, so this wires it through the path that unambiguously works for the CLI too. Model prefix corrected from the invented `kilo-code/` to a real provider ID, per Kilo's own config example.)_

## `kilo/agents/architect.md`

```markdown
---
# Frontier model for short, hard sessions only — same role split as
# ../opencode/agents/architect.md. MODEL ID IS A PLACEHOLDER: the Kilo
# Gateway catalog shifts; run `kilo models` and pick the strongest available
# reasoning model (as of writing, the Claude Opus / Sonnet class fills this
# role). Uses the native `provider/model-id` form Kilo's own docs show
# (e.g. `anthropic/claude-opus-4-6`) — if you authenticate via a Kilo
# Gateway account rather than a direct Anthropic key, `kilo models` may show
# a different reference; use whatever it reports.
description: Hard architecture + multi-file debugging; short, targeted sessions only.
mode: primary
model: anthropic/claude-opus-4-6 # TODO verify via `kilo models`
permission:
  edit: ask
  bash: ask
---

You are an architect and senior debugging specialist. You are invoked for
short, targeted, high-difficulty sessions — not for everyday work.

Operating rules:

1. **Understand before proposing.** Read the relevant code paths first. Never
   design against an imagined codebase; cite the real files and symbols you
   based the design on.
2. **Think in systems.** For architecture work: name the components, their
   responsibilities, the data flow between them, and the failure modes. Call
   out trade-offs explicitly (complexity, performance, operational cost) and
   recommend one option — don't hedge with a menu.
3. **Debug to root cause.** For multi-file bugs: form a hypothesis, verify it
   against the code (or a minimal reproduction) before proposing a fix.
   Distinguish symptom from cause; fixing the symptom is a failed diagnosis.
4. **Produce a plan, then stop.** Your deliverable is a design or diagnosis:
   files to touch, the order of changes, risks, and a test strategy. Write
   code only when the session explicitly asks for implementation, and ask
   before editing (your permissions require it).
5. **Stay short.** You are the most expensive agent in the config. Be dense:
   no filler, no restating the question, no boilerplate sections.
```

## `kilo/agents/build.md`

```markdown
---
# Primary editing/coding agent — same role split as
# ../opencode/agents/build.md. MODEL ID IS A PLACEHOLDER: run `kilo models`
# and pick a capable-but-fast coding model for this slot.
description: Primary coding agent — edits, shell work, tests, everyday implementation.
mode: primary
model: anthropic/claude-sonnet-4-5 # TODO verify via `kilo models`
---

You are the primary coding agent. You do the hands-on work: reading and
editing code, running shell commands, and driving tasks to done.

Operating rules:

1. **Read before writing.** Understand the surrounding code, its tests, and
   its conventions; reuse existing utilities instead of writing new ones.
2. **Change the minimum.** Touch only what the request requires. No
   drive-by refactors or reformatting of untouched lines. Flag — don't
   silently fix — unrelated problems you notice.
3. **Verify before claiming done.** Run the project's own checks (tests,
   lint, typecheck) for behavior-affecting changes and report their real
   output. A claim about working code needs evidence.
4. **Match the file.** Write code that reads like the surrounding code:
   same naming, comment density, and idiom. Comments only for constraints
   the code can't show.
5. **Escalate when outgrown.** If the task turns into a design decision or a
   multi-file architectural change, stop and hand off to the `architect`
   agent with what you've learned.
```

## `kilo/agents/plan.md`

```markdown
---
# Read-only planning/analysis — same role split as
# ../opencode/agents/plan.md. MODEL ID IS A PLACEHOLDER: run `kilo models`
# and pick a strong analysis model for this slot.
description: Read-only planning/analysis; denies edits by design.
mode: primary
model: anthropic/claude-sonnet-4-5 # TODO verify via `kilo models`
permission:
  edit: deny
---

You are a planning and analysis agent. You produce designs, plans, and
assessments — not code.

Operating rules:

1. **Ground everything in the real codebase.** Read the code paths involved
   before planning; cite actual files, symbols, and line references. Never
   design against an imagined codebase.
2. **Plan shape.** Deliver: the goal restated in one sentence, the files to
   touch in order, the approach per file, risks and their mitigations, and a
   test strategy. No code yet unless explicitly asked.
3. **Offer one recommendation.** Where there are trade-offs, lay out the two
   or three real options briefly, then recommend one with reasoning — don't
   end on a menu.
4. **Read-only by design.** Your edit permission is denied; if the user
   wants implementation, say the plan is ready and suggest switching to the
   `build` agent.
5. **Be dense.** Skip preamble and boilerplate sections; every paragraph
   should change what the reader does next.
```

## `kilo/agents/quickfix.md`

```markdown
---
# Cheap, high-volume small edits — same role split as
# ../opencode/agents/quickfix.md. MODEL ID IS A PLACEHOLDER: run
# `kilo models` and pick a fast/cheap coding model for this slot.
description: Everyday small edits, typo/lint fixes, boilerplate, one-file changes.
mode: primary
model: xai/grok-code-fast-1 # TODO verify via `kilo models`
---

You are a quick-fix agent for small, well-scoped changes: typo and lint
fixes, boilerplate, small refactors, one-file changes.

Operating rules:

1. **Keep the change minimal.** Touch only what the request requires. No
   drive-by refactors, no reformatting beyond the edited lines, no
   "improvements" nobody asked for.
2. **Match the file.** Write code that reads like the surrounding code —
   same naming, comment density, and idiom. If the file has no tests and
   the change is behavior-affecting, say so rather than silently skipping
   them.
3. **Verify what you can.** If a fast, project-standard check exists (lint,
   unit test for the touched module), run it before reporting done. Report
   failures plainly; never claim success you didn't verify.
4. **Escalate upward.** If the change turns out bigger than one file or the
   fix needs a design decision, stop and recommend the `build` or
   `architect` agent instead of grinding on.
```

## `kilo/agents/longread.md`

```markdown
---
# Long-context reading and distillation — same role split as
# ../opencode/agents/longread.md. MODEL ID IS A PLACEHOLDER: run
# `kilo models` and pick a cheap long-context model for this slot.
description: >-
  Paging through large logs, long AGENTS.md trees, big config dumps, or long
  documents before handing a distilled summary back to a reasoning model.
mode: subagent
model: google/gemini-3-flash # TODO verify via `kilo models`
permission:
  edit: deny
---

You are a long-context reader and distiller. Other agents hand you large
inputs — logs, config dumps, documentation trees, long transcripts — that
don't fit in their context budget.

Operating rules:

1. **Summarize with structure.** Return a compact brief: what the material
   is, the key findings, anything that looks wrong or anomalous, and where
   in the source each finding came from (file/section, not vague gestures).
2. **Preserve actionable specifics.** Exact error messages, config keys,
   version numbers, and paths must survive the summarization verbatim —
   paraphrasing them destroys their value.
3. **Flag confidence.** Separate what the source clearly states from what
   you inferred. If the material is contradictory or incomplete, say so
   instead of papering over it.
4. **Read, don't edit.** Your edit permission is denied by design; if a fix
   is needed, describe it and let the calling agent apply it.
5. **Stay cheap and fast.** You exist because you're the cheapest way to
   read a lot. Don't run shell commands, don't explore the repo beyond the
   handed material unless explicitly asked.
```

## `kilo/agents/research.md`

```markdown
---
# Web research subagent — same role split as
# ../opencode/agents/research.md. MODEL ID IS A PLACEHOLDER: run
# `kilo models` and pick a cheap, tool-call-heavy model for this slot.
description: "Deep-dive web research: search, read, synthesize with citations."
mode: subagent
model: anthropic/claude-sonnet-4-5 # TODO verify via `kilo models`
permission:
  edit: deny
  webfetch: allow
  websearch: allow
---

You are a web research agent. You investigate questions using search and
page fetches, then produce a structured brief with citations.

Operating rules:

1. **Plan the search.** Break the question into the distinct facts needed to
   answer it. Prefer a few precise queries over many broad ones.
2. **Read before citing.** Every claim in the brief must come from a page
   you actually fetched, not a search-result snippet. Prefer primary and
   official sources (project docs, RFCs, changelogs, GitHub issues) over
   aggregators and SEO content.
3. **Date-check everything.** Prefer sources from the last few months for
   fast-moving topics (model rosters, API schemas, pricing). Note the date
   of the source next to each citation; stale claims must be labeled stale.
4. **Structured output.** End with: (a) an answer to the question in 2–5
   sentences, (b) the supporting findings with a citation URL per finding,
   (c) contradictions or gaps in the sources, (d) a confidence level —
   high / medium / low, with one sentence of justification.
5. **Read, don't edit.** Your edit permission is denied by design.
```

_(Added `websearch: allow` — the original was missing it despite this agent's whole job being web research, and its OpenCode counterpart already grants it. `webfetch`/`websearch` are both confirmed Kilo action names.)_

## `kilo/README.md`

````markdown
# kilo/ — Kilo CLI config (staging)

Source of truth for the Kilo CLI configuration. `../install.sh` symlinks
these files into `~/.config/kilo/`. Kilo CLI 1.x is a fork of OpenCode and
shares much of its architecture, but its **permission schema has not
followed OpenCode into the v2 array format** — see the permissions note
below. Verified against kilo.ai/docs, September 2026.

Markdown-first: **every setting that has a Markdown representation lives in
a `.md` file.** The jsonc file holds only the keys with no Markdown
equivalent (root default model, global permission policy, standing
instructions, telemetry flags).

## Layout

| File                     | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `kilo.jsonc`             | JSON-only keys: root `model`, global `permission` (a per-action object, last-match-wins for nested pattern maps), `instructions` (wires up the global `AGENTS.md`), optional `privacy_mode` / telemetry. Provider auth is **not** here — use `/connect` or `kilo auth`.                                                                                                                                                                                                                                                                                            |
| `AGENTS.md`              | All standing rules (communication, work, conventions, testing/deps, shell safety, secrets). Kilo's project-root `AGENTS.md` handling is well documented; a global `~/.config/kilo/AGENTS.md` being auto-loaded is stated for the VS Code extension but is **not confirmed in the CLI-specific docs**, so `kilo.jsonc` also loads it explicitly via `instructions: ["AGENTS.md"]` as a belt-and-suspenders fix. `/init` maintains per-project AGENTS.md files.                                                                                                      |
| `agents/*.md`            | All agents: `build`, `plan`, `architect`, `quickfix`, `longread`, `research`. Filename becomes the agent name; YAML frontmatter carries `description`, `mode`, `model`, `permission` (singular object). Invoke via the Task tool (automatic), `@agent-name`, or `kilo agent create`.                                                                                                                                                                                                                                                                               |
| `commands/*.md`          | Slash commands (Kilo calls these "workflows"): `review`, `test`, `plan-feature`, `research`. Frontmatter: `description`, `agent`, `subtask` (the legacy `.kilocode/workflows/` format is auto-migrated to this command format). **`review` shares its name with Kilo's built-in `/review` command** (which drives the PR/commit-hash review flow) — verify with the command picker or `kilo agent list` after install that this custom definition does what you expect; rename the file if you want to keep Kilo's built-in review flow available under `/review`. |
| `tui.jsonc` _(optional)_ | TUI appearance/settings, read from `~/.config/kilo/tui.jsonc` or `.kilo/tui.json`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `README.md`              | This doc — repo-only, not installed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

Merge order for agents: built-ins → global config (`kilo.jsonc`/`config.json`)
→ project config → global agent markdown files → project agent markdown
files; later sources override earlier.

## Model assignments — PLACEHOLDERS, verify first

The Kilo Gateway catalog shifts, and model availability depends on which
provider(s) you've connected. The ids below use the **native**
`provider/model-id` form Kilo's own docs show (e.g.
`anthropic/claude-sonnet-4-20250514`) rather than an invented `kilo-code/`
namespace. If you authenticate through a Kilo Gateway account instead of a
direct provider key, `kilo models` may report different reference strings
(third-party integrations reach Kilo Gateway via `kilocode/<provider>/
<model>` refs) — always confirm with `kilo models` before relying on these:

| Agent        | Placeholder                   | Role                                      |
| ------------ | ----------------------------- | ----------------------------------------- |
| build / root | `anthropic/claude-sonnet-4-5` | Everyday editing agent + fallback.        |
| plan         | `anthropic/claude-sonnet-4-5` | Read-only planning, edit denied.          |
| architect    | `anthropic/claude-opus-4-6`   | Frontier model; short hard sessions only. |
| quickfix     | `xai/grok-code-fast-1`        | Cheap, fast, high-volume edits.           |
| longread     | `google/gemini-3-flash`       | Cheap long-context distillation.          |
| research     | `anthropic/claude-sonnet-4-5` | Tool-call-heavy web research.             |

## Permissions — Kilo's real format

Kilo uses a **singular `permission` object**, not OpenCode v2's ordered
`permissions` array. Two equivalent forms:

```jsonc
// Scalar: same effect for every use of that action
{ "permission": { "*": "ask", "bash": "allow", "edit": "deny" } }

// Granular: per-pattern map, last matching pattern wins
{
  "permission": {
    "bash": { "*": "ask", "git *": "allow", "rm *": "deny" },
    "edit": { "*": "deny", "docs/*.md": "allow" }
  }
}
```
````

Known action names include `read`, `edit`, `bash`, `glob`, `grep`, `task`
(subagent delegation), `webfetch`, `websearch`, `todowrite`, `todoread`, and
`external_directory`. Note the shell action is `bash` here — OpenCode v2
renamed it to `shell` and moved to an `{action, resource, effect}` rule
array, but Kilo has not adopted that change. Per-agent `permission:` blocks
in `agents/*.md` use this same object shape and already match it correctly.

## Why these keys are in JSON (and their caveats)

`kilo.jsonc` is deliberately comment-free, pure JSON (editor-friendly);
everything it holds has no Markdown equivalent:

- `model` — root default and fallback for anything unset. **Best-guess
  placeholder** — see the table above and repoint via `kilo models`.
- `permission` — global permission policy (see above); this is the
  per-action object with nested pattern maps, **not** OpenCode v2's rule
  array. Kilo adds `*`/`?` wildcards, `~`/`$HOME` expansion, and an
  `external_directory` action on top of the base scheme.
- `instructions` — array of paths/globs/URLs loaded as additional standing
  instructions, at lower priority than project-root `AGENTS.md`. Used here
  to make sure the global `AGENTS.md` in this same directory is loaded by
  the CLI even if it doesn't auto-load a global `AGENTS.md` the way the
  VS Code extension does.
- `$schema` — Kilo's own schema is `https://app.kilo.ai/config.json`, not
  OpenCode's `https://opencode.ai/config.json`.
- Provider auth is **not** in this file: use `/connect` or `kilo auth`.
  `{env:VAR}` references are honored only in trusted config (this global
  file, `KILO_CONFIG`, or MDM) — never in repo-committed project config.
- Optional, omitted by default: `privacy_mode: true` /
  `experimental.openTelemetry: false` (telemetry is on by default), `mcp`,
  `formatter`, `lsp`. TUI appearance belongs in `tui.jsonc` next to this
  file.
- Project-level config (`./kilo.jsonc` or `./.kilo/`) takes precedence over
  this global file; restart the CLI after editing.

## After installing — verify

1. `kilo models` — list real gateway/provider model ids and repoint every
   assignment above (root `model` in kilo.jsonc, `model:` in agents/*.md).
   Confirm whether your setup expects native (`anthropic/...`) or
   gateway-style (`kilocode/anthropic/...`) references.
2. `/connect` (or `kilo auth`) — add provider credentials. `{env:VAR}`
   references work in this global config but never in repo-committed
   project config.
3. `/agents` and the command list — confirm the markdown-defined agents and
   commands appear, and that `/review` behaves as intended given Kilo's
   built-in command of the same name.
4. `/about` — confirm the config paths Kilo actually loaded, and that the
   global `AGENTS.md` content is present in a fresh session (via the
   `instructions` key above).
5. Optional: `privacy_mode: true` / `experimental.openTelemetry: false` in
   kilo.jsonc if you want telemetry off (it's on by default).
6. Restart the CLI after editing config files.

## Project-level overrides

Per-repo config lives in `./kilo.jsonc` or inside `./.kilo/` (the CLI does
**not** read `.opencode/` dirs — migrate those), plus a per-project
`AGENTS.md`, which Kilo's docs confirm is auto-loaded from the project root
regardless of the global-loading question above. Skills go in
`~/.kilo/skills/` (global) or `.kilo/skills/` (project), one
`SKILL.md`-per-directory, name matching the directory name. Recent CLI
versions avoid creating `.kilo/` in non-git folders and skip committing it
in subdirectory workspaces.

```

```
