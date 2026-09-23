# OpenCode Go — Ultimate Setup Guide

A single, opinionated setup for running **OpenCode v2** on an **OpenCode Go**
subscription ($10/mo) across all your projects — tuned to get the most out of
the quota without slamming into usage limits, with optional layers for
governance (LiteLLM), validated tooling (Pydantic + LangGraph MCP), deep
research for scientists, IDE/GUI integration, and productivity tools.

Everything here reflects the **v2** config schema (`opencode.ai/config.json`,
fetched September 2026) and the **September 2026** Go usage-limit model.
OpenCode moves fast — re-check opencode.ai/docs/go and `/models` before
trusting exact model IDs or caps.

---

## 1. The verdict in one paragraph

Use **OpenCode itself** (TUI, Web, Desktop share one config) with a **lean
global config** in `~/.config/opencode/` that bakes in Go model tiering,
permission guardrails, and token hygiene. Skip the heavy machinery
(LiteLLM/Docker/Postgres, custom MCP servers) for daily work — OpenCode's Go
integration already meters everything in dollars with its own 5-hour/weekly/
monthly windows, so a self-hosted gateway adds latency and double-accounting
without adding control. Keep LiteLLM and the Pydantic/LangGraph MCP servers as
*optional* layers, documented below. This folder is your **central kit**: the
global config applies to every project; per-project `AGENTS.md` files stay
project-specific.

### What stock OpenCode v2 already includes

Per [opencode.ai](https://opencode.ai)'s feature list — but the marketing
list is partly **v1-era**: two of those features don't exist in v2 yet. The
full, version-accurate picture is in **§1.1**; the short version:

- **Multi-session** ✅ real in v2, and deeper than the list implies —
  shared background service, session tabs, background subagents, git
  worktrees (§1.1).
- **LSP enabled** ⚠️ **v1-only** — v2 runs no language servers; the config
  key is accepted and ignored (§1.1).
- **Share links** ⚠️ **v1-only** — "OpenCode V2 does not support session
  sharing yet" (§1.1).
- **GitHub Copilot / ChatGPT Plus/Pro logins** ✅ real — subscription
  logins with their own billing; interactions and known v2 bugs in §1.1.
- **Any model (75+ providers via Models.dev, incl. local)** ✅ real —
  live-fetched catalog, auto-discovery of Ollama/LM Studio/vLLM (§1.1).
- **Any editor** ✅ — TUI, desktop, web, IDE extensions (§3, §10).

### 1.1 Stock features in depth (verified for v2.0.14)

#### Multi-session & parallel agents

v2's architecture is a **shared background service**: one server per user
account owns sessions, config, credentials, permissions, and tool
execution, and every TUI/desktop/web client is just a client of it
([v2 CLI docs](https://opencode.ai/v2/docs/cli/)) — state lives in
`~/.local/share/opencode/opencode.db` (SQLite). Practical consequences:

- **Parallel sessions**: multiple TUIs (or TUI + desktop + web) work the
  same project concurrently through the service. Inside one TUI you get
  **session tabs**: `<leader>n` new session, `<leader>l` session list,
  `ctrl+o` recent sessions/projects, quick slots `<leader>1–9`, tab
  navigation `ctrl+tab`, rename `ctrl+r`, fork (`session.fork`),
  background-tool output `ctrl+b` ([v2 keybinds](https://opencode.ai/v2/docs/cli/keybinds)).
  CLI: `opencode session list|delete|export|import`, `opencode service
  status|restart`, `opencode stats --cost` for real spend.
- **Background subagents**: the `subagent` tool accepts `background: true`
  — "returns immediately and notifies the parent when the child finishes";
  children get fresh context and their own configured model/permissions
  ([v2 tools docs](https://opencode.ai/v2/docs/tools/)). This is the
  intended parallelism: fan out cheap `mimo-v2.6-flash` children, keep the
  parent on the strong model only for synthesis.
- **Git worktrees are first-class in v2**: `dialog.move_session.new`
  (`ctrl+m`) moves a session into a fresh worktree ("New worktree"),
  configurable via `"worktree": { "directory": "../worktrees" }`, with a
  startup script hook per worktree ([v2 config docs](https://opencode.ai/v2/docs/config/)).
  That's the clean way to run truly isolated parallel agents on one repo.
- **Checkpoints**: v2 snapshots capture the working tree before each model
  call; `<leader>u` undo stages a rollback, `<leader>r` redo cancels it
  ([v2 snapshots](https://opencode.ai/v2/docs/snapshots/)). Requires git.
- **Quota reality**: Go's dollar windows are **account-level per model** —
  N parallel sessions/subagents burn the shared bucket N× faster. Session
  reuse (`-c`, tabs) earns prompt-cache discounts (stable
  `x-opencode-session`); brand-new sessions re-pay cold context. Keep
  `warming` **off** — v2's optional warm-up requests "consume tokens, incur
  costs, count against rate limits" ([v2 warming docs](https://opencode.ai/v2/docs/warming/)),
  which is pure loss on a flat plan.

#### Share links — v1-only

v1: `/share` syncs the **full transcript** to OpenCode's servers and returns
a **public, non-expiring** link (`opencd.ai/s/…`); `/unshare` deletes it;
`share` config: `manual` (default) / `auto` / `disabled`; no redaction is
documented ([v1 share docs](https://opencode.ai/docs/share)). **v2: "OpenCode
V2 does not support session sharing yet"** — the config key is accepted and
inert, and the `/share` keybinds default to `none`
([v2 sharing](https://opencode.ai/v2/docs/sharing/)). Keep `share: "manual"`
for when it returns; nothing is uploaded on v2.0.14 today.

#### LSP — removed in v2

The migration guide, verbatim: "V2 accepts and preserves `lsp`
configuration, but it does not run language servers, expose LSP tools, or
produce LSP diagnostics" ([v2 migrate-v1](https://opencode.ai/v2/docs/migrate-v1/)).
v1 auto-loaded 30+ language servers and fed the agent diagnostics after
edits; v2 does none of that. The supported replacement: declare your
lint/typecheck/build commands in `AGENTS.md` or a skill and let the agent
run them via shell — output is capped by `tool_output` config, which is
also the cheaper path on a dollar-quota plan (no silent diagnostic
injection). Don't rely on `"lsp": true` doing anything on v2.0.14.

#### GitHub Copilot login (provider, not the IDE plugin)

Official GitHub partnership (Jan 2026): Copilot Pro/Pro+/Business/Enterprise
subscriptions work in OpenCode via **device OAuth** — `/connect` → GitHub
Copilot → enter the code at `github.com/login/device` → `/models`
([GitHub changelog](https://github.blog/changelog/2026-01-16-github-copilot-now-supports-opencode/),
[v2 providers](https://opencode.ai/v2/docs/providers)). The model list is
fetched live from your Copilot account (only models with tool-calls support
appear). Billing hits your **Copilot plan**, not Go: since June 2026 that's
**GitHub AI Credits** (Pro 1,000/mo, Pro+ 3,900/mo base) with model
multipliers — 0×-class models (GPT-4.1/GPT-5-mini) are effectively free
overflow, premium Claude-class models burn credits fast.
**Warning for v2 users on legacy per-request Copilot plans**:
[anomalyco/opencode#48330](https://github.com/anomalyco/opencode/issues/48330)
(open, Sep 2026) reports a whole 1,500-request month draining in one session
(header-classification regression). Also note the direction: this is
OpenCode using Copilot models; §10's BYOK point is Copilot Chat using your
Go key.

#### ChatGPT Plus/Pro login

Implemented as **Codex-style browser OAuth** (`/connect` → OpenAI →
"ChatGPT Plus/Pro"); you get the Codex-transport GPT family
(`gpt-5.6-luna/sol/terra`, `gpt-6-astra`) and usage counts against the
ChatGPT plan's **Codex allowance — its own 5-hour/weekly windows**, shared
across Codex surfaces ([OpenAI help](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)).
That makes a dormant Plus/Pro a decent **overflow pool with an independent
window** next to Go. **Known v2 bug**: when a Zen/Go credential is also
configured, ChatGPT-OAuth requests can get the wrong Authorization header
([#49847](https://github.com/anomalyco/opencode/issues/49847), open Sep 2026)
— if you add ChatGPT login alongside Go and see "API keys are not supported
by this endpoint", that's why; `opencode auth switch` between credentials or
wait for the fix.

#### Combining providers, credentials, and Models.dev

- Multiple providers coexist (Go + Copilot + ChatGPT + …); each keeps its
  own quota. **v1** stores credentials in `~/.local/share/opencode/auth.json`
  and allows one credential per provider; **v2** stores them in the
  **`credential` table inside `opencode.db`** and supports **multiple
  credentials per provider** with `opencode auth switch`. Switching models
  is per-session via `/models` (session choice overrides config default) or
  permanent via `agent.<name>.model`.
- The provider catalog comes from **Models.dev** (open-source, MIT,
  `anomalyco/models.dev`): OpenCode fetches it live (≈5-minute cache TTL,
  offline snapshot fallback), so **new providers/models appear without an
  OpenCode update**.
- **Local models are first-class**: running **Ollama**
  (`127.0.0.1:11434`), **LM Studio** (`:1234/v1`), or **vLLM** (`:8000/v1`)
  is auto-discovered and appears in `/models` with zero config; anything
  else OpenAI-compatible uses the custom-provider recipe
  ([v2 providers](https://opencode.ai/v2/docs/providers)). Local models
  cost nothing and touch no quota — the natural fourth tier when Go,
  Copilot, and ChatGPT windows all run dry. (v1's `enabled_providers` /
  `disabled_providers` keys are gone in v2 — they map to policies; v2 uses
  per-model `"disabled": true`.)

### 1.2 v1 or v2? (release-channel reality)

Your three observations are all correct, and they're material:

- **v2 has no GitHub releases at all** — only tags (latest: v2.0.14).
  Every GitHub release, the "Latest" badge, and **all desktop installers**
  (20 assets per release: .deb/.rpm) attach to **v1.18.x** tags (v1.18.32,
  Sep 21, 2026). v2 is distributed only via its own install script
  (`opencode.ai/v2/install`), npm `@opencode/cli`, and AUR
  `opencode-beta` — a preview track in practice, whatever the naming.
- The main `opencode.ai/docs` tree documents **v1**; v2's docs live at
  `/v2/docs` and are thinner (a one-sentence sharing page, no published v2
  config schema — `/v2/config.json` is 404).
- v2 removed/reworked things mid-flight: LSP and session sharing are gone,
  `opencode attach` is gone, several v1 config keys are silently dropped
  (`subagent_depth`, `prune`), and two open provider bugs affect
  subscription mixing (#48330 Copilot legacy plans, #49847 Go-key leak into
  ChatGPT OAuth) — the exact overflow strategy §1.1 suggests.

**Recommendation for this setup: run v1 as the daily driver today; keep v2
installed side-by-side; re-evaluate monthly.** Everything this guide needs
(Go, websearch, MCP, agents, permissions, commands) is fully shipped,
documented, and release-bearing on v1, and v1.18.24+ reads supported v2
config fields so the eventual migration is smoothed. Switch to v2 for good
when: v2 starts cutting real releases (desktop included), the two provider
bugs close, or you want its new architecture (worktrees, background
subagents, session tabs, multi-credential auth) enough to accept preview
roughness.

Running both is cheap. On Arch: `opencode-bin` (v1) and `opencode-beta`
(v2) coexist; both read the same `~/.config/opencode/opencode.json`, with
separate state (v1: `auth.json` + its own session store; v2:
`opencode.db`). On Fedora: `opencode.ai/install` (v1) vs
`opencode.ai/v2/install` (v2). The §4.1 config is deliberately written to
work on **both** lines — v1 keys, with v2 behavior annotated inline.

## 2. How OpenCode Go billing actually works (know this first)

From [opencode.ai/docs/go](https://opencode.ai/docs/go) (September 2026):

- **$10/month, one plan**, one member per workspace. Subscribe at OpenCode
  Zen, copy your API key, then run `/connect` → **OpenCode Go** → paste key.
  `/models` lists everything Go includes (~30 open models).
- **Limits are dollar amounts, per model** (not pooled): a rolling **5-hour
  window = 20%** of the model's monthly cap, **weekly = 50%**, **monthly =
  100%**. Example: a $60 model → $12 per 5 hours, $30 per week, $60 per
  month.
- **Per-model caps and headroom** — verbatim from
  [opencode.ai/docs/go](https://opencode.ai/docs/go#usage-limits), fetched
  Sep 23, 2026. This table changes; the docs page is authoritative. Prices
  are per 1M tokens; "req/5h" is the docs' own estimated requests per
  5-hour window (sorted by headroom):

  | Model | Monthly cap | Est. req / 5h | In / Out $ per 1M |
  |---|---|---|---|
  | Muse Spark 1.3 / 1.2 Contributor † | $60 | 45,300 | $0.10 / $0.20 |
  | MiMo-V2.6-Flash, MiMo-V2.5 | $60 | 30,100 | $0.14 / $0.28 |
  | DeepSeek V4 Flash | $30 | 13,000 | $0.15 / $0.60 off-peak ‡ |
  | DeepSeek V4.1 Flash — **4× promo, ends Sep 27: $15 → $60** | $60 (promo) | 26,000 (promo) | $0.15 / $0.60 off-peak ‡ |
  | LongCat-2.0 | $60 | 11,400 | $0.30 / $1.20 |
  | GLM-5.3-Flash | $60 | 6,320 | $0.15 / $0.50 |
  | DeepSeek V4 Flash Vision Exp | $15 | 6,500 | $0.15 / $0.60 off-peak ‡ |
  | Qwen3.8 Flash | $30 | 5,400 | $0.15 / $0.47 |
  | Qwen3.7 Plus, Hy3 | $60 | 4,300 | $0.40/$1.60 · $0.14/$0.58 |
  | MiniMax M2.7 / M3 / M2.5 | $60 | 3,400 / 3,200 / — | $0.30 / $1.20 |
  | Qwen3.6 Plus | $60 | 3,300 | $0.50 / $3.00 |
  | MiMo-V2.6-Pro, MiMo-V2.5-Pro | $15 | 3,250 | $0.435 / $0.87 |
  | Kimi K2.7 Code / K2.6 | $60 | 1,350 / 1,150 | $0.95 / $4.00 |
  | GPT 5.6 Luna | $15 | 2,050 | $0.20 / $1.20 |
  | Hy4 preview | $30 | 1,350 | $0.834 / $2.501 |
  | DeepSeek V4 Pro | $15 | 1,050 | $0.66 / $1.98 off-peak ‡ |
  | GLM-5.2, GLM-5.1 | $60 | 880 | $1.40 / $4.40 |
  | Qwen3.7 Max | $30 | 170 | $2.50 / $7.50 |
  | Qwen3.8 Max | $15 | 160 | $2.00 / $6.00 |
  | Grok 4.7, Grok 4.6 | $15 | 169 | $2.00 / $6.00 |
  | GLM-5.3 | $15 | 220 | $1.40 / $4.40 |
  | Kimi K3 | $15 | 110 | $3.00 / $15.00 |

  † Muse Spark Contributor models are region-limited and train on your
  prompts. ‡ DeepSeek V4-family peak hours are 01:00–04:00 and 06:00–10:00
  UTC Mon–Fri at 2× the off-peak price (see §5). Cached reads are far
  cheaper than the input price for every model (e.g. $0.0028/1M on MiMo) —
  the docs table has the full pricing.
- **Hit a cap?** Free models keep working. Optionally enable **"Use
  balance"** in the [Console](https://opencode.ai/console) to fall back to
  pay-as-you-go Zen credits instead of blocking.
- **Track usage** in the Console (per-model breakdown was recently removed —
  overall monthly only). Machine-readable quota: `GET
  https://opencode.ai/zen/go/v1/usage` (rolling-5h and monthly percentages).
- **Promos and peak pricing**: DeepSeek V4.1 Flash currently carries a 4×
  usage promo ($15 → $60 monthly cap, ending Sep 27, 2026), and the
  DeepSeek V4 family prices peak hours (01:00–04:00 and 06:00–10:00 UTC,
  Mon–Fri) at 2× the off-peak rate — nights and weekends buy roughly twice
  the tokens for the same cap.
- The Go API is **OpenAI-compatible**
  (`https://opencode.ai/zen/go/v1/chat/completions`) and also exposes
  Anthropic-compatible `/messages`. Clients should send a **stable session ID
  header** (`x-opencode-session`) — OpenCode does this natively; it's what
  makes prompt caching (and your quota) go further. Traffic is monitored for
  abuse; use your own user-agent if you write custom clients.

**The lever that matters:** which model eats which workload. Flash-tier
models on $60 caps should absorb ~95% of your tokens; $15-cap premium models
should only see hard planning/review/research steps.

## 3. Install (Fedora and Arch)

OpenCode has two release tracks — **v1** (1.18.x, the release line: GitHub
releases + desktop builds) and **v2** (2.0.x, preview line: tags only). See
**§1.2** for which to pick; both can be installed side-by-side.

### Arch Linux

```bash
# v1 (recommended daily driver): AUR opencode-bin = 1.18.32 (release line)
paru -S opencode-bin
# v2 (preview): AUR opencode-beta = 2.0.14; extra/opencode tracks v2 but lags
paru -S opencode-beta

# Desktop (Electron): GitHub .deb/.rpm assets attach to v1.18.x releases;
# AUR carries opencode-desktop (v1 source build) and
# opencode-desktop-bin (v2 line, 2.0.14-1, builds the upstream .deb)
paru -S opencode-desktop-bin
```

### Fedora

No official RPM/Copr (the community `sureclaw/opencode` Copr's latest build
was failing — don't rely on it):

```bash
# v1 (recommended daily driver): install script or npm
curl -fsSL https://opencode.ai/install | bash
# or: npm install -g opencode-ai

# v2 (preview):
curl -fsSL https://opencode.ai/v2/install | bash
# or: npm install -g @opencode/cli   (bun/pnpm also documented)

# Desktop: .rpm/.deb assets attach to v1.18.x releases
# (github.com/anomalyco/opencode/releases → latest v1.18.x)
```

### OpenCode Web (browser UI, self-hosted, same config)

v2 ships password-protected browser access out of the box:

```bash
opencode pair     # prints a local http://127.0.0.1:PORT URL + generated
                  # username/password; a background `service` keeps it running
```

(On v1 the equivalent is `opencode web --port 4096` plus
`OPENCODE_SERVER_PASSWORD`; v1's `opencode attach <url>` is **gone in v2** —
v2's shared background `service` already links every local client, and
`opencode serve --port 4096` starts an explicit v2 API/web server. The v1
`server` config block is accepted but unsupported on v2.)

**Auth for all three front-ends is shared:** `/connect` once, and the TUI,
Web, and Desktop all use it. Provider/agent/MCP config in
`~/.config/opencode/opencode.json` applies across TUI, CLI, Desktop, and Web.

## 4. The lean core config (this replaces the old per-project stack)

### 4.1 Global config — `~/.config/opencode/opencode.json`

Config sources merge in this order (later wins):
remote → **global** → `OPENCODE_CONFIG` → **project** `opencode.json` →
`.opencode/` dirs → inline. So: set defaults here once; override per project
only when a project genuinely needs it.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",   // the published schema (v1 line); v2 accepts and maps it (§1.2)
  "autoupdate": true,
  "share": "manual",                              // v1: nothing shared unless /share — v2: sharing not shipped yet (§1.1)
  "default_agent": "build",
  "subagent_depth": 2,                            // v1: native. v2: dropped silently — if you stay on v2, also add
                                                  // "experimental": { "subagent_depth": 2 } (verified working there)

  // ---- Go model tiering (cap tiers as of Sep 2026) ----
  // Workhorse on the $60 tier; premium $15-cap models only for hard steps.
  "model": "opencode-go/mimo-v2.6-flash",         // $60 cap; highest request headroom
  "small_model": "opencode-go/mimo-v2.6-flash",   // titles/summaries — v1 native; v2 maps it to the title agent

  "agent": {
    "plan": {
      "mode": "primary",
      "model": "opencode-go/glm-5.2",             // $60 tier; read-only planner
      "description": "Read-only planning/analysis; edits and bash require approval."
    },
    "architect": {
      "mode": "primary",
      "model": "opencode-go/kimi-k3",             // $15 tier — strongest open model, use sparingly
      "temperature": 0.1,
      "description": "Hard architecture/multi-file debugging. Short, targeted sessions.",
      "permission": { "edit": "ask", "bash": "ask" }
    },
    "research": {
      "mode": "subagent",
      "model": "opencode-go/glm-5.2",
      "description": "Deep-dive web research: search, read, synthesize with citations.",
      "permission": { "edit": "deny", "websearch": "allow", "webfetch": "allow" }
    }
  },

  // ---- Guardrails ----
  "permission": {
    "edit": "allow",
    "bash": {
      "*": "ask",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "ls*": "allow",
      "cat *": "allow",
      "grep *": "allow",
      "rg *": "allow",
      "python3 -m pytest*": "allow",
      "uv run*": "allow",
      "uvx *": "allow",
      "git push*": "ask",
      "rm -rf *": "deny"
    },
    "webfetch": "ask",
    "websearch": "allow",
    "external_directory": "deny"
  },

  // ---- Token hygiene ----
  // v1-native keys. On v2, `prune` is ignored (with a warning) and
  // `reserved` maps to `buffer` — a v2-only config can use natively:
  //   "compaction": { "auto": true, "keep": { "tokens": 15000 }, "buffer": 20000 }
  "compaction": {
    "auto": true,
    "prune": true,
    "reserved": 20000
  },
  "watcher": {
    "ignore": ["node_modules/**", "dist/**", ".git/**", "**/.venv/**",
               "**/__pycache__/**", "**/.pytest_cache/**"]
  },

  "formatter": {
    "ruff-format": { "command": ["uvx", "ruff", "format", "$FILE"], "extensions": [".py"] }
  },

  // LSP (`"lsp": true`) and the `server` block are v1-only capabilities:
  // v2 runs no language servers and ignores the server key. This config
  // omits both on purpose — lint/typecheck via AGENTS.md or skills is
  // cheaper and more predictable than LSP diagnostics on a dollar-quota
  // plan, and the web UI takes explicit port flags (§3).
}
```

Notes:

- **Don't set `"instructions": ["AGENTS.md"]`** — AGENTS.md is auto-loaded;
  listing it again duplicates it into every session's context (pure quota
  waste). Use `instructions` only for *additional* files.
- **Do not copy this into projects.** Global config covers every project;
  add a project `opencode.json` only for real overrides (e.g. pin a project
  to a specific model).
- `{env:VAR}` and `{file:path}` substitution works anywhere in the config.

### 4.2 Global personal rules — `~/.config/opencode/AGENTS.md`

Loaded automatically in **every** session, in every project. Keep it short —
it rides along in every context window you pay for. Put *personal* rules here
(code style you always want, "never touch X"), and *project* facts in each
project's own `AGENTS.md` (this folder's [AGENTS.md](AGENTS.md) is the
project-specific example).

### 4.3 Project files

- **`AGENTS.md`** (project root): auto-loaded when you work in that project.
  Commit it.
- **TUI/client settings**: v1 used `tui.json` (this folder's [tui.json](tui.json)
  is a valid *v1* file). **v2 replaces it with one global
  `~/.config/opencode/cli.json`** (schema `opencode.ai/v2/cli.json`; keys:
  `theme`, `session`, `tabs`, `keybinds`, `attention`, `diffs`, `plugins`)
  — which is already the only file in your `~/.config/opencode/`. There is
  no project-local client config in v2; port the settings you care about
  (`attention`, keybinds) into `cli.json`.
- **`.opencode/`** in a project: per-project `agents/`, `commands/`,
  `skills/`, `plugins/` (plural directory names).

## 5. Minimizing token usage (the quota playbook)

1. **Tier the models, keep the fat cap as default.** The docs' own estimate
   table puts `mimo-v2.6-flash` at ~30,100 requests per 5-hour window vs
   ~110 for `kimi-k3` — a **~270× spread**. Every token that *doesn't* go
   through `glm-5.3` / `kimi-k3` / `qwen3.8-max` ($15 caps, ~110–220
   req/5h) is headroom saved.
2. **Keep the context small.** Every session pays for the system prompt +
   tool schemas + AGENTS.md. Disable MCP servers globally and enable them
   per-agent (`tools: { "server*": false }` globally, `true` in the agent
   that needs them — same trick the old config used). Trim huge MCP servers
   with globs (`"github_*": false` for the tools you don't need).
3. **Compact and prune.** `compaction: { auto: true, prune: true }` keeps old
   tool outputs from piling up. `/compact` manually after big explorations.
4. **Let OpenCode use `small_model`** for titles/summaries — never point
   `small_model` at a $15-cap model.
5. **Sessions enable prompt caching.** OpenCode sends the session header
   natively — don't route through anything that strips it (LiteLLM needs
   explicit header forwarding, see §7).
6. **Exploit the windows.** One fully-used 5-hour window burns 20% of the
   monthly cap — that's **40% of the weekly allowance in a single morning**
   — so pace marathons across windows. For DeepSeek models, shift bulk work
   off-peak (peak = 01:00–04:00 & 06:00–10:00 UTC Mon–Fri at 2× the
   off-peak price; nights and weekends are off-peak).
7. **Free models are a safety net.** After a cap, free models keep working —
   good enough for brainstorming and small asks while a window resets.
8. **Watch the needle.** Console for the big picture;
   `curl -H "Authorization: Bearer $OPENCODE_API_KEY"
   https://opencode.ai/zen/go/v1/usage` for rolling + monthly percentages
   (community monitors like `pi-quota-monitoring` build on this endpoint).
9. **Three v2-specific gotchas**: keep `warming` **off** (warm-up requests
   "consume tokens, incur costs, count against rate limits" — pure loss on
   a flat plan); **reuse sessions** (`-c`, session tabs) because the stable
   session header is what earns prompt-cache discounts — new sessions
   re-pay cold context; and check real spend with `opencode stats --cost`.

## 6. Optimizing for agentic programming

- **Subagents for the expensive stuff.** `subagent_depth: 2` lets build
  delegate to research/review subagents that run with their own (tiered)
  models and their own context windows — the parent's context stays small.
- **Commands encode workflows.** Add to global config so every project has
  them:

  ```jsonc
  "command": {
    "plan-feature": {
      "template": "Acting as the architect agent, produce a short implementation plan (files to touch, risks, test strategy) for: $ARGUMENTS. Do not write code yet.",
      "description": "Implementation plan with the architect agent",
      "agent": "architect"
    },
    "research": {
      "template": "Delegate to the research subagent: investigate \"$ARGUMENTS\" using web search and page fetches. Return a structured brief with sources and a confidence assessment.",
      "description": "Deep web research via the research subagent",
      "agent": "build",
      "subtask": true
    }
  }
  ```

- **Permissions as guardrails, not brakes.** The `bash` pattern map above
  keeps read-only ops instant, asks before anything mutating, and hard-denies
  `rm -rf`. `external_directory: "deny"` stops cross-project wandering.
- **TUI muscle memory:** Tab switches agents (build → plan → architect),
  `/models` picks models on the fly, `ctrl+x` is the keybind leader, `/undo`
  and `/redo` revert via git checkpoints.
- **Formatters over token-burn.** Let `ruff-format` (or your language's
  equivalent) fix style mechanically instead of asking the model to.

## 7. Optional: LiteLLM as a governance layer (read the trade-offs first)

**Honest verdict for a solo Go-only user: you probably don't need this.**
Go already meters in dollars, enforces its own 5h/week/month windows, and
shows spend in the Console. A local LiteLLM proxy adds: latency, a
double-metering layer whose budgets don't map to Go's caps, and — worst — it
can **break prompt caching** across the hop, which makes you *burn quota
faster*, plus it must forward the `x-opencode-session` header or risk abuse
flagging.

**LiteLLM advantages / disadvantages in this setup:**

- ✅ Hard per-key budgets and virtual keys (a runaway agent hits *your*
  wall, not Go's window), unified request logs (Langfuse), scoped keys for
  scripts/teammates, config-level fallbacks/retries, provider-agnostic
  switching later.
- ❌ An extra network hop that can **break prompt caching** (the mechanism
  that stretches your quota), double-metering whose budgets don't map to
  Go's dollar caps, mandatory `x-opencode-session`/user-agent forwarding,
  and a Docker + Postgres footprint to maintain.

It earns its keep only if you want: hard per-project spend stops (virtual
keys with `max_budget`), scoped keys for scripts/teammates, or one log
pipeline. If so, front **Go itself** (not Anthropic/OpenAI — you're Go-only):

```yaml
# litellm config — LiteLLM >= 1.102.0, pin a real tag
model_list:
  - model_name: mimo-v2.6-flash
    litellm_params:
      model: openai/mimo-v2.6-flash
      api_base: https://opencode.ai/zen/go/v1
      api_key: os.environ/OPENCODE_API_KEY
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL   # Postgres REQUIRED for virtual keys/budgets
```

- Pin the image: `ghcr.io/berriai/litellm:v1.102.0` (the old
  `:main-stable` tag scheme is gone since 1.84.0).
- `allow_user_auth` is **deprecated** — remove it.
- Redis is only needed for response caching/multi-worker; Postgres only for
  virtual keys/budgets/spend — run stateless (no DB) if you just want
  proxying.
- **Forward the session header and user-agent** or Go may flag the traffic.
- Then point OpenCode's custom provider at `http://localhost:4000/v1` with a
  generated virtual key. Treat LiteLLM budgets as a *runaway guardrail*, not
  a mirror of Go billing.

## 8. Optional: Pydantic + LangGraph MCP servers (fixed)

The two MCP servers in this folder (`server.py`, `mcp_server.py` +
`graph.py`) still work, **but the dependency pins don't**: `mcp[cli]>=1.6.0`
now resolves to MCP SDK 2.x, which **removed** `mcp.server.fastmcp`
(verified: 2.2.0 → `ModuleNotFoundError`). Pin to the 1.x line in both PEP
723 blocks:

```python
# dependencies = [
#   "mcp[cli]>=1.30,<2",
#   ...
# ]
```

Other findings from the audit (September 2026):

- **LangGraph 1.x is API-compatible** with these files
  (`StateGraph`/`START`/`END`, Pydantic v2 state, `compile()`, `ainvoke` —
  verified that Pydantic-state graphs return a dict, so
  `CodeReviewResult(**result_state)` works). Current: langgraph 1.2.12,
  langchain-openai 1.6.4, pydantic 2.13.5.
- `server.py`'s `run_tests` executes pytest with the MCP server's *ephemeral*
  environment — fine for plain pytest, but a project needing its own deps
  will show false import failures. Prefer the built-in Bash tool for
  dependency-heavy suites.
- `query_metrics` returns **fabricated placeholder data (42.0)** — keep it
  disabled until you wire a real backend; a model will otherwise happily
  quote fake metrics.
- The LangGraph review pipeline makes **3 LLM calls per review**; the
  single-call reviewer suggestion in §6 does the same job for ~⅓ the tokens.
- These servers run from **this central folder** via absolute paths, so any
  project can use them without copying files:

  ```jsonc
  "mcp": {
    "pydantic-tools": {
      "type": "local",
      "command": ["uv", "run", "/home/ahsan/Git/common/opencode-go/server.py"],
      "enabled": false,
      "timeout": 15000
    },
    "langgraph-agent": {
      "type": "local",
      "command": ["uv", "run", "/home/ahsan/Git/common/opencode-go/mcp_server.py"],
      "enabled": false,
      "timeout": 30000,
      "environment": {
        "LITELLM_BASE_URL": "{env:LITELLM_BASE_URL}",
        "LITELLM_API_KEY": "{env:LITELLM_API_KEY}",
        "LITELLM_MODEL": "{env:LANGGRAPH_MODEL}"
      }
    }
  }
  ```

  (If you dropped LiteLLM per §7, the LangGraph server can point
  `LITELLM_BASE_URL` at `https://opencode.ai/zen/go` with your Go key
  instead — it's just an OpenAI-compatible client.)

### Are Pydantic and LangGraph worth it here? (advantages / disadvantages)

**Pydantic — typed MCP tools via FastMCP:**

- ✅ Tool inputs/outputs become precise JSON Schemas; malformed calls fail
  fast with validation errors; results arrive structured instead of prose
  the model has to reinterpret. The same servers are reusable from
  PydanticAI agents (§8.1).
- ❌ PEP 723 pins need maintenance (the `mcp` 2.x breakage above), tool
  schemas permanently cost context tokens unless gated per-agent, and a
  stub tool returning fake data (like `query_metrics` does) is worse than
  no tool at all.

**LangGraph — the plan → analyze → summarize graph:**

- ✅ Deterministic, inspectable multi-step flow with typed state; the same
  graph runs locally or deploys to LangGraph Platform, where the Agent
  Server serves it to OpenCode natively over MCP (§8.1).
- ❌ Three LLM calls per review where one strong-model prompt does the same
  job (~3× the quota), more moving parts than a plain subagent prompt, and
  framework churn to track (langgraph 0.6 → 1.x).

Rule of thumb: keep them if you value the structure and validation; if
you're optimizing purely for quota, a single-call reviewer subagent on
`glm-5.2` (§6) is the leaner equivalent.

### 8.1 First-party Pydantic & LangGraph integrations for OpenCode

Before reaching for the custom stdio servers above, know what both
ecosystems ship natively — you may not need any custom code:

**LangGraph — a deployed graph *is* an MCP server.** The LangGraph Agent
Server behind LangSmith Deployments exposes every deployed graph as an MCP
tool at a streamable-HTTP `/mcp` endpoint (`https://<deployment>.us.langgraph.app/mcp`;
`langgraph dev` serves the same locally on `http://localhost:8124/mcp`).
OpenCode connects directly — no `mcp_server.py` wrapper needed:

```jsonc
"mcp": {
  "langgraph-cloud": {
    "type": "remote",
    "url": "{env:LANGGRAPH_DEPLOYMENT_URL}/mcp",
    "enabled": false,
    "headers": { "x-api-key": "{env:LANGSMITH_API_KEY}" }
  }
}
```

Caveats: each graph surfaces as **one** tool (tools inside the graph aren't
individually exposed), and auth is your LangSmith API key. The reverse
direction — a LangGraph agent consuming MCP servers as tools — is what
[`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters)
is for.

**PydanticAI — MCP in both directions** ([docs](https://pydantic.dev/docs/ai/mcp/overview/)).
PydanticAI agents *consume* MCP servers via the `MCP` capability
(`pydantic_ai.capabilities`), the lower-level `MCPToolset`
(`pydantic_ai.mcp`), or `MCPServerTool` for provider-native MCP — so a
PydanticAI side-agent can reuse the exact same MCP servers you register in
OpenCode. *Serving* side: PydanticAI officially supports agents inside MCP
servers, and the standard way to expose one to OpenCode is a
[FastMCP](https://gofastmcp.com) server wrapping the agent's tools with
`@mcp.tool` — precisely the pattern this folder's `server.py` /
`mcp_server.py` follow (Pydantic models in, Pydantic models out). Known
limitation: MCP **tools only** — servers exposing just resources aren't
usable from agents ([pydantic-ai#1783](https://github.com/pydantic/pydantic-ai)).

## 9. Deep research setup for professional scientists

**Built-in web search works with Go.** OpenCode v2's `websearch` tool uses
Exa/Parallel and works out of the box **when you're on the OpenCode/Go
provider** — no API key, just allow it (`"websearch": "allow"`, as in §4).
Provider-native search *through* the gateway is not supported (upstream
declined), so for heavier retrieval add MCP servers:

```jsonc
"mcp": {
  "paper-search": {                       // arXiv + PubMed + Europe PMC +
    "type": "local",                      // bioRxiv + medRxiv + OpenAlex, one server
    "command": ["uvx", "paper-search-mcp"],
    "enabled": false
  },
  "tavily": {                             // agent-first web search w/ deep-research tool
    "type": "remote",
    "url": "https://mcp.tavily.com/mcp/?tavilyApiKey={env:TAVILY_API_KEY}",
    "enabled": false
  },
  "brave": {                              // independent index, generous free tier
    "type": "local",
    "command": ["npx", "-y", "@brave/brave-search-mcp-server"],
    "enabled": false,
    "environment": { "BRAVE_API_KEY": "{env:BRAVE_API_KEY}" }
  }
}
```

Enable per-agent (`tools: { "paper-search*": true, "tavily*": true }` on the
`research` subagent) so the schemas don't tax everyday sessions.

**Which model for search-heavy work — without overspending?** The search
*backend* (Exa/Parallel/Tavily) is model-independent, and the built-in
`websearch` tool costs nothing extra (hosted, no key) — the spend is model
tokens, and search agents re-read context constantly, so **cached-read
pricing dominates** (flash-class models charge ~$0.003–0.06/1M cached
tokens; premium ones $0.25–0.50). On 2026 open-weight agentic-search
benchmarks (BrowseComp et al.), **Kimi K3 leads** (~91%), with GLM-5.x close
behind; DeepSeek V4's agentic-search numbers are less documented. A
cost-tiered ladder that follows the §2 cap table:

- `glm-5.3-flash` — high-volume search-and-read passes (6,320 req/5h, $60 cap)
- `glm-5.2` — default research/synthesis model (880 req/5h, $60 cap)
- `mimo-v2.6-flash` — bulk cheap reading and note-taking (30,100 req/5h)
- `kimi-k3` — final hard synthesis only (110 req/5h, $15 cap — burns fast)
- DeepSeek V4 Flash off-peak — bulk batch summarization at half price

**Open Notebook** (open-source NotebookLM alternative,
[github.com/lfnovo/open-notebook](https://github.com/lfnovo/open-notebook))
for literature: docker-compose (SurrealDB + `lfnovo/open_notebook:v1-latest`,
UI on :8502, API on :5055; set `OPEN_NOTEBOOK_ENCRYPTION_KEY`), supports any
OpenAI-compatible endpoint for its chat/embedding models, and ships an MCP
server:

```jsonc
"mcp": {
  "open-notebook": {
    "type": "local",
    "command": ["uvx", "open-notebook-mcp"],
    "enabled": false,
    "environment": { "OPEN_NOTEBOOK_URL": "http://localhost:5055" }
  }
}
```

→ gives agents tools for notebooks, sources, notes, chat sessions, and
vector/text search over your saved literature. The pattern for a research
session: `paper-search`/Tavily to find, `webfetch` to read, Open Notebook to
persist and chat with the corpus, and the `research` subagent to synthesize.

## 10. IDE and GUI integration (and completions)

- **VS Code/Cursor/etc.:** the OpenCode extension embeds the **terminal** —
  that's its design (Ctrl+Esc to open, selection/tab auto-shared, `@File`
  refs). Fine as a launcher; not a native panel.
- **JetBrains:** no official plugin — connect via **ACP** (`opencode acp`)
  in `acp.json`, then pick OpenCode in the AI Chat agent selector.
- **Zed:** first-class via ACP (`agent_servers` entry or the ACP Registry) —
  the best "native panel" experience today. (ACP lacks `/undo`//`redo`.)
- **Neovim:** Avante.nvim or CodeCompanion.nvim over ACP.
- **Inline code completion is not an OpenCode feature** — it's agent-only.
  Your options, including the Copilot route (note the two directions:
  OpenCode *using your Copilot-plan models* via GitHub login is a stock
  feature — §1; here it's the reverse, *Copilot Chat using your Go key*):
  - **GitHub Copilot Chat + Go (BYOK)**: Copilot's "Manage Models" flow
    accepts **any OpenAI-compatible provider** — add
    `https://opencode.ai/zen/go/v1` as the base URL with your Go API key and
    Go models appear in Copilot Chat and agent mode. Two hard caveats:
    first, BYOK covers **chat/agent features only** — Copilot's inline
    ghost-text completions always run on GitHub's own models (BYOK for
    completions is an open feature request from May 2026, not shipped as of
    Sep 2026); second, Go's docs list Copilot Chat under *Known Problematic
    Clients* — the `x-opencode-session` header request
    ([microsoft/vscode#334186](https://github.com/microsoft/vscode/issues/334186))
    was still open, stale, and unshipped as of Sep 23, 2026, so expect
    errors until VS Code ships it.
  - **Zed edit predictions** against an OpenAI-compatible FIM endpoint:

    ```json
    {
      "edit_predictions": {
        "provider": "open_ai_compatible_api",
        "open_ai_compatible_api": {
          "api_url": "http://localhost:8080/v1/completions",
          "model": "your-fim-model",
          "prompt_format": "deepseek_coder",
          "max_output_tokens": 512
        }
      }
    }
    ```

  - **Continue** in VS Code for chat + autocomplete against any
    OpenAI-compatible endpoint;
  - or a self-hosted **Tabby** server / llama.cpp-served FIM model
    (Qwen2.5-Coder class) if you want completions fully local.
  Note the Go API serves **chat**-style traffic; inline FIM completions
  want a small local model or a completion-oriented provider regardless.

## 11. NanoClaw integration

[NanoClaw](https://github.com/nanocoai/nanoclaw) is a lightweight,
container-per-session personal AI agent you message from chat apps
(WhatsApp/Telegram/Discord/…). It's a **companion, not a replacement** for
OpenCode: always-on assistant on your phone, OpenCode as the heavy coding/
research terminal.

- Requires Node 22+, pnpm 10+, Docker; `bash nanoclaw.sh` after clone.
- Model wiring: its native runtime is the Claude Agent SDK, so any
  **Anthropic-compatible** endpoint works via `ANTHROPIC_BASE_URL` +
  `ANTHROPIC_AUTH_TOKEN` — point it at Go's Anthropic-compatible endpoint
  (base such that `<base>/v1/messages` resolves to
  `https://opencode.ai/zen/go/v1/messages`). Alternatively use its
  `/add-opencode` runtime skill, which speaks OpenAI-compatible providers.
- It ships a `.mcp.json`, so MCP servers can be added to its agents too.
- **Caution:** Go is designed for coding-agent traffic and monitored for
  abuse — keep NanoClaw's volume modest and coding-adjacent, and remember
  every NanoClaw message burns the same per-model caps.

## 12. Productivity tools (MCP)

Global wiring, enable per-agent as needed; remote servers keep the config
clean:

| Tool | Server | How |
|---|---|---|
| GitHub | official | remote `https://api.githubcopilot.com/mcp/` (OAuth) |
| Notion | official | remote `https://mcp.notion.com/mcp` |
| Linear | official | remote `https://mcp.linear.app/mcp` |
| Google Calendar | official Google Workspace MCP | remote `https://calendarmcp.googleapis.com/mcp/v1` (streamable HTTP; OAuth setup per [Google's guide](https://developers.google.com/workspace/calendar/api/guides/configure-mcp-server)) |
| Obsidian | `MarkusPfundstein/mcp-obsidian` | local, needs the Obsidian Local REST API plugin |

Trim tool schemas with globs (`"github_*": false` for what you don't use) —
big servers can eat a meaningful chunk of context.

### Creating documents like Claude's artifacts

OpenCode has no claude.ai-style artifact pane, but it can *produce real
document files* the same way Claude's web UI does under the hood — by
running code — and OpenCode v2's native **Agent Skills** make it repeatable:

1. Drop a document skill into `~/.config/opencode/skills/<name>/SKILL.md`
   (per-project alternative: `.opencode/skills/`; the Claude-compatible
   `~/.claude/skills/` also works). Anthropic's open-source
   [anthropics/skills](https://github.com/anthropics/skills) repo ships
   ready-made **docx / pptx / xlsx / pdf** skills in exactly that format
   ([skills docs](https://opencode.ai/docs/skills), updated Sep 22, 2026).
2. Ask for the document; the agent loads the skill via its `skill` tool,
   runs the Python toolchain (python-docx, python-pptx, openpyxl, …), and
   writes real files into your workspace.
3. Consume the results anywhere: open them with your normal apps, commit
   them, or share/export the session from OpenCode Web/Desktop
   (`opencode pair`).

Gate document skills with permission patterns (`"skill": "ask"` or
`internal-*`-style rules) so sessions only generate files when you ask.
Only skill names/descriptions load into context upfront — full skill
content is pulled on demand, so a big skills folder doesn't tax everyday
token usage.

## 13. What lives in this folder

```
AGENTS.md            example project-level rules (auto-loaded per project; keep per-project)
tui.json             v1 TUI settings (v2 uses ~/.config/opencode/cli.json — see §4.3)
server.py            pydantic-tools MCP server (pin mcp>=1.30,<2 before use)
mcp_server.py        langgraph-agent MCP server (same pin)
graph.py             LangGraph plan→analyze→summarize review workflow
config.yaml          LiteLLM config (optional layer — rework per §7 if used)
docker-compose.yml   LiteLLM + Postgres + Redis (optional layer)
.env.example         env vars for the optional layers
.gitignore           keeps .env, caches, and test artifacts out of git
.zcodeignore         auto-synced mirror of .gitignore for the ZCode workspace
```

The old README described a `litellm/` + `.opencode/mcp/` layout that doesn't
match this flattened folder (and `docker-compose.yml`'s `env_file: ../.env`
only worked from a subdirectory) — that's part of why the setup now prefers
global config + absolute paths from this one central location.

## 15. Verification log (2026-09-23)

Every claim below was **executed**, not desk-checked, against OpenCode
v2.0.14 and the live schemas:

- **opencode.jsonc loads in real v2.0.14** (`opencode debug config`) and all
  five custom agents register (`opencode debug agents`: architect / build /
  plan as primary, code-review / project-ops as subagents, each with its
  configured model). JSON-Schema check against `opencode.ai/config.json`:
  one flag — `agent.architect.model = "litellm/claude-sonnet-4-5"` is not in
  the schema's model catalog (custom providers aren't catalogued; it still
  loads at runtime). Every `opencode-go/*` ID used anywhere in this README —
  including all of §4's recommendations — enum-validates against the live
  Go catalog.
- **tui.json: valid** against `opencode.ai/tui.json` (`mouse`, `diff_style`,
  `attention` and their sub-keys all check out).
- **Python files compile** (`py_compile`), and **both MCP servers were
  boot-tested**: as pinned today they crash (`mcp` SDK 2.x removed
  `mcp.server.fastmcp` — reproduced with 2.2.0); after changing the pin to
  `mcp[cli]>=1.30,<2`, both import, initialize, and shut down cleanly —
  including the LangGraph stack on langgraph 1.2.12 / langchain-openai 1.6.4,
  confirming `graph.py`'s Pydantic-state graph compiles and `ainvoke` returns
  a dict (so `CodeReviewResult(**result_state)` is safe).
- **.gitignore exercised in a scratch git repo**: `.env`, `.env.local`,
  `report.json`, logs, caches, `.venv/`, editor dirs all ignored;
  `!.env.example` correctly un-ignored. **Gap: `.pytest-mcp-report.json`**
  (the file `server.py` writes into the project root) is *not* covered — add
  one line to `.gitignore`. `.zcodeignore` auto-mirrors this file, so the
  same gap applies there.
- **config.yaml / docker-compose.yml parse as YAML**, but `env_file: ../.env`
  resolves outside this folder (`~/Git/common/.env`, which doesn't exist),
  and the docker compose plugin isn't installed on this machine — the
  optional LiteLLM layer can't run as-is here regardless (see §7).
- **All config snippets in this README** (§4.1 global config, §6 command,
  §8.1, §9 MCP blocks) schema-validated after the §9 `open-notebook` snippet
  was corrected to sit inside an `"mcp"` object.

No project code files were modified — the audit findings are listed here so
fixes can be applied deliberately.

- **Re-verification pass (Sep 23, 2026)**, in response to a flagged error:
  §2's model/cap table was rebuilt **verbatim** from
  opencode.ai/docs/go#usage-limits (the earlier draft paraphrased it and
  carried two derived errors: the flash↔premium request spread is ~270×,
  not ~23×, and one fully-used 5-hour window is 40% of the weekly
  allowance, not "two resets"); DeepSeek peak hours (01:00–04:00 &
  06:00–10:00 UTC Mon–Fri, 2× price) and the DeepSeek V4.1 Flash 4× promo
  (ends Sep 27) were taken from the same table; the completions section was
  corrected to add **GitHub Copilot Chat BYOK** (OpenAI-compatible providers
  supported — chat/agent only, inline completions never route through BYOK)
  with Go's own "Known Problematic Clients" status and the still-open
  microsoft/vscode#334186; Zed's config key was fixed to
  `edit_predictions.provider: "open_ai_compatible_api"` (the previously
  stated `features.edit_prediction_provider` is wrong); Google's Calendar
  MCP endpoint was confirmed as `calendarmcp.googleapis.com/mcp/v1`; and
  the skills paths in §12 were verified against opencode.ai/docs/skills
  (page updated Sep 22, 2026).
- **Stock-features deep-dive (Sep 23, 2026)**: a full v1-vs-v2 research
  pass corrected four stale claims — §1 now states that **LSP is removed in
  v2** (config accepted and ignored; replaced by lint/typecheck commands)
  and **session sharing doesn't exist in v2 yet**; §3 no longer references
  v1's `opencode attach` (gone in v2; the shared background `service` +
  `opencode serve`/`pair` replaced it); §4.1 was rewritten with native v2
  keys (`experimental.subagent_depth`, `agents.title.model` instead of
  `small_model`, `compaction.keep/buffer` instead of `prune`/`reserved`,
  `lsp`/`server` removed with rationale). New in §1.1: multi-session
  mechanics (background service, session tabs, background subagents,
  worktrees, snapshots), Copilot-login billing (GitHub AI Credits since
  Jun 2026, legacy-plan drain bug #48330), ChatGPT-login details (Codex
  OAuth, own 5-hour windows, Zen-key leak bug #49847 when Go is also
  configured), credential storage (v2: `credential` table in
  `opencode.db`, not `auth.json` — note that `.env.example`'s auth.json
  comment is v1-era), and Models.dev/local-model auto-discovery. Also
  recorded: `opencode.ai/config.json` is the **v1** config schema (no v2
  replacement is published — `/v2/config.json` is 404; the v2 client schema
  is `/v2/cli.json`), so the schema-validations in this log were performed
  against the v1 schema; the stronger check is that the v2.0.14 binary
  itself loads the config and registers every agent (verified above).
  The rewritten §4.1 snippet was then live-tested on v2.0.14: all agents
  register — including a `title` override of a built-in — and
  `compaction.keep/buffer` plus `experimental.subagent_depth` round-trip
  through `opencode debug config`. (An initial apparent failure to register
  agents turned out to be a background-service warm-up artifact, not a
  config problem: a brand-new project's custom agents are absent from
  `opencode debug agents` until the service has seen the project, and the
  list comes back empty immediately after `opencode service restart`.)
- **v1-vs-v2 release-channel audit (Sep 23, 2026)**: confirmed via the
  GitHub API that **v2 has no releases at all** (tags only, latest
  v2.0.14) while every GitHub release — 37 assets each, including all 20
  desktop installers — attaches to v1.18.x tags (latest v1.18.32, Sep 21).
  Added §1.2 with the recommendation (**v1 as the daily driver, v2
  side-by-side, re-evaluate monthly** + concrete switch criteria), and
  made §4.1 dual-line compatible: back to v1-native `small_model` (v2 maps
  it to the title agent), top-level `subagent_depth` (v2: dropped silently,
  with the verified `experimental.subagent_depth` alternative documented
  inline), and v1 compaction keys (v2 ignores `prune` with a warning and
  maps `reserved` → `buffer`). §3 now installs both lines (v1:
  `opencode-bin` / `opencode.ai/install` / npm `opencode-ai`). The v1 side
  of §4.1 is schema-verified (validated against `opencode.ai/config.json`
  earlier in this log); the v2 side was live-verified on v2.0.14.
- **Env-var cross-reference (Sep 23, 2026)**: every variable referenced by
  `opencode.jsonc` (`{env:…}`), `graph.py` (`os.environ`), `config.yaml`
  (`os.environ/…`), and `docker-compose.yml` was diffed against
  `.env.example`. Findings: `graph.py` reads `LITELLM_API_KEY` /
  `LITELLM_MODEL`, which `.env.example` doesn't document — `opencode.jsonc`'s
  MCP `environment` block bridges them from `LITELLM_VIRTUAL_KEY` /
  `LANGGRAPH_MODEL`, so the stack works under OpenCode, but running the
  server manually with only `.env` exported relies on `graph.py`'s
  hardcoded fallback. `DATABASE_URL` / `REDIS_HOST` / `REDIS_PORT` are
  consumed by LiteLLM but not documented — `docker-compose.yml` injects all
  three itself, so only non-compose runs need them. `AWS_*` keys are
  documented but nothing consumes them (no Bedrock model in `config.yaml`).
  `AGENTS.md`'s claims (subagent names, MCP tool names, default model ID,
  permission behavior) all match the actual config.
- **Official feature-list coverage (Sep 23, 2026)**: OpenCode's published
  feature list (LSP, multi-session, share links, GitHub Copilot login,
  ChatGPT Plus/Pro login, Models.dev providers, editor surfaces) is now
  mapped in §1, including the quota implication that Go's per-model windows
  are account-level and therefore shared by parallel sessions.

## 14. Sources (fetched September 2026)

- OpenCode v2 docs: [docs](https://opencode.ai/v2/docs/), [config](https://opencode.ai/docs/config),
  [rules/AGENTS.md](https://opencode.ai/docs/rules), [agents](https://opencode.ai/docs/agents),
  [permissions](https://opencode.ai/docs/permissions), [MCP](https://opencode.ai/docs/mcp-servers),
  [tools](https://opencode.ai/docs/tools), [IDE](https://opencode.ai/docs/ide),
  [ACP](https://opencode.ai/docs/acp), [web](https://opencode.ai/docs/web),
  [TUI](https://opencode.ai/docs/tui)
- Config schema: https://opencode.ai/config.json · TUI schema: https://opencode.ai/tui.json
- OpenCode Go: [docs/go](https://opencode.ai/docs/go) (limits, endpoints, clients) ·
  [docs/zen](https://opencode.ai/docs/zen) · [Console](https://opencode.ai/console) ·
  [changelog](https://opencode.ai/changelog)
- LiteLLM: [proxy configs](https://docs.litellm.ai/docs/proxy/configs) ·
  [virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys) ·
  [release cycle](https://docs.litellm.ai/docs/proxy/release_cycle)
- Integrations: [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) ·
  [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook) ·
  [open-notebook-mcp](https://github.com/Epochal-dev/open-notebook-mcp) ·
  [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) ·
  [Tavily MCP](https://mcp.tavily.com) ·
  [BrowseComp leaderboard](https://leaderboard.steel.dev)
- Completions & skills: [VS Code BYOK docs](https://code.visualstudio.com/docs/copilot/custom-models) ·
  [BYOK announcement](https://code.visualstudio.com) ·
  [microsoft/vscode#334186](https://github.com/microsoft/vscode/issues/334186) ·
  [Zed edit predictions](https://zed.dev/docs/ai/edit-prediction) ·
  [Tabby](https://github.com/TabbyML/tabby) ·
  [anthropics/skills](https://github.com/anthropics/skills) ·
  [Google Calendar MCP reference](https://developers.google.com/workspace/calendar/api/v3/reference/mcp)
