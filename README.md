# OpenCode v2 + OpenCode Go — Ultimate Setup Guide (v2.0.14)

A single, opinionated setup for running **OpenCode v2** (verified against **2.0.14**,
September 2026) on an **OpenCode Go** subscription ($10/mo) — tuned to stretch the
quota, with agent/permission guardrails, optional validated MCP tooling
(Pydantic + LangGraph), deep-research plumbing, IDE/GUI integration and
productivity MCP servers.

Everything here is **v2-only**; the LiteLLM governance layer that used to live in
this folder has been removed (Go already meters in dollars, and a self-hosted
proxy adds latency and risks breaking prompt caching). **Coming from v1?** Jump to
**§4 — Migrating from v1 to v2**; v1 and v2 are no longer installed side by side.

> OpenCode moves fast. Model lists, caps and config keys change. The pages under
> <https://opencode.ai/v2/docs> and <https://opencode.ai/docs/go> are authoritative;
> re-check them and `/models` before trusting exact IDs or caps.

---

## 1. What OpenCode v2 gives you (stock, verified on 2.0.14)

- **Client/server with a shared background service.** One server per user owns
  sessions, config, credentials, permissions and tool execution; TUI, desktop and
  web are clients of it. The database is
  `~/.local/share/opencode/opencode.db` (SQLite; `opencode debug paths db` prints)
  the live path). Diagnostics: `opencode service status|restart|stop|start`,
  `opencode api get /api/info`, logs in `~/.local/share/opencode/log/opencode.log`.
- **Multi-session & session tabs.** `opencode` opens the full TUI;
  `opencode run "..."` is the scriptable one-shot; `opencode mini` is the minimal
  interface. In the TUI: **Ctrl+X** is the leader, `Ctrl+X N` = new session,
  `Ctrl+X L` (or `/sessions`) = session list, `Ctrl+O` = recent sessions/projects,
  `Ctrl+Tab`/`Ctrl+Shift+Tab` = switch tabs, `Ctrl+X W` = close tab,
  `Ctrl+Shift+T` = reopen last closed tab.
- **Background subagents.** The `subagent` tool accepts `background: true`
  ("returns immediately and notifies the parent when the child finishes");
  children run with fresh context and their own model/permissions. **Default
  nesting depth is one.**
- **Git worktrees are first-class.** `Ctrl+M` in the dialog moves a session into a
  fresh worktree; set the parent directory with
  `"worktree": { "directory": "../worktrees" }`. }`
- **Snapshots / checkpoints.** Before each model step OpenCode snapshots the step's
  files (git-backed, best effort). `/undo` (`Ctrl+X U`) stages a rollback and puts
  the prompt back in the composer; `/redo` (`Ctrl+X R`) cancels a staged rollback.
  Filesystem restore needs a git repository; `"snapshots": false` disables capture.
  Snapshots are a convenience — not a backup, and shell side effects aren't undone.
- **Agents.** Built-ins include `build`, `plan`, `general`, `explore` plus internal
  `title`/`summary`/`compaction` agents. Custom agents are Markdown
  (`~/.config/opencode/agents/<name>.md`, `.opencode/agents/<name>.md`) or JSON
  under `agents`. Modes: `primary`, `subagent`, `all`. Per-agent options:
  `description`, `mode`, `model` (`provider/model#variant`), `system`,
  `permissions`, `steps`, `hidden`, `color`, `disabled` — **do not use the legacy
  v1 top-level `temperature`/`tools`/`permission`/`maxSteps` fields in new v2
  agent entries.**
- **Permissions.** v2 uses an ordered `permissions` array of
  `{ "action", "resource", "effect" }` (`allow`/`ask`/`deny`), **last matching rule
  wins**. Actions include `read`, `edit`, `glob`, `grep`, `shell`, `subagent`,
  `skill`, `question`, `webfetch`, `websearch`, `external_directory`, `execute`
  (Code Mode), and `<server>_<tool>` for MCP. The shipped base policy allows
  everything, except: external-directory access asks, `*.env`/`*.env.*` reads ask
  (`*.env.example` is allowed). Approvals can be once or "always" (saved per
  project; saved approvals never override a configured `deny`). `experimental.policies`
  can hard-deny after all rules (`provider.use`, `permission`) and Console-managed
  workspace policies override local config.
- **Commands.** `commands` in config or `.opencode/commands/*.md`; `$ARGUMENTS` and
  `$1`/`$2` positions; shell blocks with `` !`cmd` ``; `subagent: true` runs a
  command in a background child session (`subtask` is a deprecated alias;
  `subagent` wins).
- **Skills.** `.opencode/skills/<id>/SKILL.md` (or flat `<id>.md`); also discovered
  from `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills`, and the
  project `.claude/skills`/`.agents/skills`. Only ID/name/description are listed to
  the model per step; the body loads on demand via the `skill` tool. Gate with the
  `skill` permission action (e.g. deny `internal-*`).
- **MCP servers** (`mcp.servers`). Local (`command`) or remote (`url`); servers
  connect automatically, `"disabled": true` keeps one configured but off; per-server
  `timeout` is `{ startup, catalog, execution }`; tools are named
  `<server>_<tool>`. Code Mode is the default (tools grouped, nested calls still
  permission-checked; `"codemode": false` exposes them as ordinary tools).
  Manage with `opencode mcp add|list|auth|logout` or `/mcps`.
- **Websearch.** Four providers — **Exa, Firecrawl, Parallel, Tavily** — each needs
  `/connect` or its own API key (`EXA_API_KEY`, `FIRECRAWL_API_KEY`,
  `PARALLEL_API_KEY`, `TAVILY_API_KEY`). Pin one with
  `"websearch": { "provider": "tavily" }` (or `"random"`); `"websearch": false`
  removes the tool. **Not included with Go.**
- **Formatters.** Disabled by default; `"formatter": true` enables built-ins
  (ruff, prettier, gofmt, …) when their executables/config exist. Custom entries
  need `command` (array) + `extensions`.
- **Compaction.** Checkpoint-based; `"compaction": { "auto": true, "keep": { "tokens": 15000 }, "buffer": 20000 }`.
  Manual compaction runs at the next safe step boundary (`/compact`, or
  `POST /api/session/<id>/compact`).
- **Warming.** Off by default; if enabled it sends real model requests
  ("can consume tokens, incur costs, count against rate limits"). On a flat Go plan,
  keep it **off**.
- **Providers & models.** Catalog comes from **Models.dev** and is fetched live.
  Select with `/models` (`Ctrl+X M`, `F2` cycles recent), per-session selection
  overrides the default; variants use `#variant`
  (e.g. `openai/gpt-5.2#high`). Ollama / LM Studio / vLLM are auto-discovered.
  Custom OpenAI-compatible endpoints use
  `providers.<id>.package: "@opencode/ai/providers/openai-compatible"` + `settings.baseURL`.
- **Clients.** TUI, **Desktop v2** (macOS/Windows/Linux), browser UI
  (`opencode pair`), extensions for VS Code / Cursor / Zed / Windsurf / VSCodium.
- **Not in v2 (yet):**
  - **Session sharing**: "OpenCode V2 does not support session sharing yet." The
    `share` field is accepted and inert.
  - **LSP**: v2 runs no language servers and exposes no LSP diagnostics. Declare
    lint/typecheck commands in `AGENTS.md` (or a skill) and let the agent run them.
  - **`CLAUDE.md` fallback**: v2 discovers **only `AGENTS.md`**.
  - **`instructions` config entries**: accepted but **not loaded** — use AGENTS.md.

### 1.1 Subscription logins and extra providers (the quota overflow plan)

Multiple providers coexist (Go + Copilot + ChatGPT + local models); each keeps its
**own quota**, so a dormant subscription is a genuine overflow pool next to Go.

- **GitHub Copilot login** (official partnership, Jan 2026): Copilot
  Pro/Pro+/Business/Enterprise work via **device OAuth** — `/connect` → GitHub
  Copilot → enter the code at `github.com/verified-device`-style flow → `/models`.
  The model list is fetched live from your account (only tool-calling models
  appear). Billing hits your **Copilot plan**, not Go. ⚠️ **Known v2 bug**:
  [anomalyco/opencode#48330](https://github.com/anomalyco/opencode/issues/48330)
  (open, Sep 10 2026) — legacy *per-request* Copilot plans can drain an entire
  1,500-request month in one session.
- **ChatGPT Plus/Pro login**: implemented as **Codex-style browser OAuth**
  (`/connect` → OpenAI → "ChatGPT Plus/Pro"); you get the Codex-transport GPT family
  (`gpt-5.6-luna/sol/terra`, `gpt-6-astra`) and usage counts against the ChatGPT
  plan's **Codex allowance — its own 5-hour/weekly windows**, shared across Codex
  surfaces. ⚠️ **Known v2 bug**:
  [#49847](https://github.com/anomalyco/opencode/issues/49847) (open, Sep 18 2026) —
  when a Zen/Go credential is also configured, ChatGPT-OAuth requests can be sent
  with the **Zen API key** and fail with "API keys are not supported by this
  endpoint." Workaround: `opencode auth switch` between credentials, or wait for
  the fix.
- **Credentials**: v2 stores them in the **`credential` table inside
  `~/.local/share/opencode/opencode.db`** and supports **multiple credentials per
  provider** with `opencode auth login` / `auth switch`. (v1's
  `~/.local/share/opencode/auth.json` and its one-credential-per-provider limit are
  gone.) Switching models is per-session via `/models` (session choice overrides
  the config default) or permanent via an agent's `model`.
- **Models.dev**: the provider/model catalog is open-source and OpenCode fetches it
  live, so **new providers and models appear without an OpenCode update**.
- **Local models are first-class**: running **Ollama** (`127.0.0.1:11434`),
  **LM Studio** (`:1234/v1`) or **vLLM** (`:8000/v1`) is auto-discovered and appears
  in `/models` with zero config (vLLM discovers tools support via server flags, not
  from discovery). Local models cost nothing and touch no quota — the natural fourth
  tier when Go, Copilot and ChatGPT windows all run dry.
- **Policies replace v1's provider lists**: v1's `enabled_providers` /
  `disabled_providers` are gone in v2 — use `providers` plus
  `experimental.policies` (`provider.use`).

---

## 2. How OpenCode Go billing actually works (know this first)

From [opencode.ai/docs/go](https://opencode.ai/docs/go) and the v2 console docs (Sep 2026):

- **$10/month, one plan; one member per workspace.** Subscribe in the OpenCode
  console/Zen, copy the API key, `/connect` → **OpenCode Go**, then `/models`.
- **Limits are dollar values, per model** (each model has its own bucket):
  - **5-hour = 20%** of that model's monthly limit,
  - **weekly = 50%**,
  - **monthly = 100%**.
  A $60 model therefore allows $12 / 5 h, $30 / week, $60 / month. Requests are
  estimated from "typical coding-agent" token patterns, so cheaper models give far
  more requests per window. Buckets are **account-level per model** — N parallel
  sessions/subagents burn the same bucket N× faster.
- **Hit a cap?** Requests are blocked until the window resets ("Resets in …" is
  shown in the Console). Free models keep working, and the Console's **"Use
  balance"** option falls back to pay-as-you-go Zen credits.
- **Track usage:** Console → workspace usage (with per-model detail); **Usage API**
  for CSV exports (`GET https://opencode.ai/console/api/v1/usage/export`,
  service-account keys, `range=24h|7d|30d`); **Budgets API**
  (`/api/v1/budgets/members`) sets monthly caps per member.
- **Billing-dispute caveat:** issue
  [#46365](https://github.com/anomalyco/opencode/issues/46365) (open, Aug 31 2026)
  reports the Console's *global* monthly usage hitting 100% while the sum of
  per-model usage was ~$24.5 — i.e. the effective ceiling looked lower than the sum
  of documented per-model caps. Watch your Console early in a month before relying
  on the full bucket.

- **Estimates (per the docs table, Sep 2026)** — these move; the docs are
  authoritative. "req/5h" = docs' estimated requests per 5-hour window; caps are
  the per-model monthly dollar limits (those marked ✔ were confirmed against
  Console reports in Aug–Sep 2026; "—" = not independently re-verified):

  | Model group (as the docs group them) | Est. req / 5h | Monthly cap |
  |---|---|---|
  | Muse Spark 1.3 / 1.2 Contributor ⚠ trains on prompts, region-limited | 45,300 | ✔ $60 |
  | MiMo-V2.6-Flash, MiMo-V2.5 | 30,100 | ✔ $60 (V2.5) |
  | DeepSeek V4 Flash | 13,000 | ✔ $30 |
  | LongCat-2.0 | 11,400 | — |
  | DeepSeek V4.1 Flash | 6,500 (promo row lists 26,000 — check) | promo reported 4×, ends Sep 27, 2026 |
  | DeepSeek V4 Flash Vision Exp | 6,500 | ✔ $15 |
  | GLM-5.3-Flash | 6,320 | ✔ $30 (Aug) |
  | Qwen3.8 Flash | 5,400 | — |
  | Qwen3.7 Plus, Hy3 | 4,300 | — |
  | MiniMax M2.7 / M3 | 3,400 / 3,200 | — |
  | Qwen3.6 Plus | 3,300 | — |
  | MiMo-V2.5-Pro, MiMo-V2.6-Pro | 3,250 | — |
  | GPT 5.6 Luna (30-day abuse logs) | 2,050 | — |
  | Kimi K2.7 Code | 1,350 | ✔ $60 |
  | Hy4 preview | 1,350 | ✔ $30 |
  | Kimi K2.6 | 1,150 | — |
  | DeepSeek V4 Pro | 1,050 | ✔ $15 |
  | GLM-5.2, GLM-5.1 | 880 | ✔ $60 (5.2) |
  | GLM-5.3 | 220 | ✔ $15 |
  | Qwen3.7 Max | 170 | — |
  | Grok 4.7, Grok 4.6 (30-day logs, ZDR limits features) | 169 | — |
  | Qwen3.8 Max | 160 | — |
  | Kimi K3 | 110 | ✔ $15 |

- **Abuse monitoring / client requirements:** send coding-agent-style traffic,
  identify with your own user agent, and send a stable session ID in
  `x-opencode-session` per conversation (OpenCode does this natively; it's also what
  makes prompt caching and your quota go further). **The Go API is OpenAI-compatible**
  (`https://opencode.ai/zen/go/v1/chat/completions`) and several models also expose
  Anthropic-compatible `/v1/messages` or OpenAI `/v1/responses`; model IDs for config
  are `opencode-go/<model-id>` (e.g. `opencode-go/kimi-k3`). Go's docs list
  **GitHub Copilot Chat** under *Known problematic clients* (session header missing;
  VS Code issue [#334186](https://github.com/microsoft/vscode/issues/334186) still
  open) and validate Hermes, Claude Code, Codex, ZCode, Pi, jcode and Kilo Code CLI.
- **Privacy:** most models are 0-day retention / not trained on; **Grok 4.7/4.6 and
  GPT 5.6 Luna retain 30 days**; **Muse Spark Contributors train on your prompts**
  (and are region-limited); DeepSeek's ZDR agreement was valid through Sep 30, 2026.

**The lever that matters:** put flash-tier models on the big buckets and reserve the
$15-cap premium models for hard planning/review steps.

---

## 3. Install v2 (Fedora and Arch)

> **v1 must be removed first.** "OpenCode 1 and OpenCode 2 both use the `opencode`
> command and are no longer installed side by side by default. Remove a
> package-managed V1 installation before installing V2; the V2 curl installer
> replaces the V1 binary." Configuration and session-data locations are shared.

### Fedora

```bash
curl -fsSL https://opencode.ai/v2/install | bash
# or: npm install -g @opencode/cli
# or: bun install -g --trust @opencode/cli
# or: pnpm add -g --allow-build=@opencode/cli @opencode/cli
# or: yarn global add @opencode/cli
```

Standalone CLI binaries are also published for Linux glibc/musl (x64/ARM64) on the
download page. (Windows package managers are not supported; use the standalone
binary.)

### Arch Linux

```bash
# AUR — opencode-beta 2.0.14-1 (Sep 22, 2026), conflicts with opencode/opencode2
paru -S opencode-beta
# or: yay -S opencode-beta
# or via the Homebrew tap: brew install anomalyco/tap/opencode-v2
```

### Desktop (v2 is available)

- **Direct downloads** (<https://opencode.ai/download>): macOS (Apple silicon /
  Intel), Windows (x64 / ARM64), Linux `.deb` / `.rpm` / AppImage (x64 / ARM64).
- **Arch:** `paru -S opencode-desktop-bin` (**2.0.14-1**, builds the upstream
  `opencode-desktop-2.0.14-linux-*.deb`; conflicts with `opencode-desktop`).
- **Homebrew:** the `opencode-desktop` cask still tracked **1.18.32** at audit time
  (Sep 23, 2026) — prefer the download page or AUR until the cask catches up.

### Web UI (same config, password-protected)

```bash
opencode pair        # prints http://127.0.0.1:49374 + generated username/password
opencode service set hostname 0.0.0.0   # optional: expose on the LAN
opencode service set port 49374
opencode service set password "a-long-secret"
opencode service set cors https://app.example.com
opencode serve --hostname 0.0.0.0 --port 4096   # standalone foreground server
opencode --server http://127.0.0.1:4096         # attach a client
```

Docker images use versioned tags, e.g. `ghcr.io/anomalyco/opencode:2.0.0`.

---

## 4. Migrating from v1 to v2

The full guide is <https://opencode.ai/v2/docs/migrate-v1/>. The short version:

**Intentional breaking changes (only three):** plugins use a new API; the server API
and clients have new contracts (`@opencode/client`); terminal config moves from
layered `tui.json(c)` to one global `cli.json` (auto-migrated).

**Practical migration order:**

1. Keep your existing config and `.opencode/` files — v2 reads the same locations
   (`~/.config/opencode/opencode.json(c)`, `<project>/opencode.json(c)`,
   `<project>/.opencode/opencode.json(c)`) and normalizes supported v1 fields.
2. Start v2 and verify models, credentials, agents, permissions and MCP servers
   (`/models`, `/agents`, `/mcps`).
3. Port plugins — v1 plugin code does **not** run in v2.
4. Port integrations that call the server API.
5. When ready, convert config to the native v2 shape (optional, can be done
   incrementally). The recommended way is to ask OpenCode itself:
   *"Migrate my OpenCode configuration, including file-based definitions, from the
   V1 format to the native V2 format. Preserve its behavior and all unrelated
   settings."*
6. Keep a v1 copy while validating; don't point v1 at files you've converted to
   v2-only shapes.

**Field / file mapping (the ones that matter here):**

| v1 | v2 | Notes |
|---|---|---|
| `permission: { edit, bash: { "cmd*": "..." } }` | `permissions: [{ action, resource, effect }]` | `bash` → `shell`; `task` → `subagent`; ordered, **last match wins**; effects `allow`/`ask`/`deny`. |
| `agent: { name: {...} }` | `agents: { name: {...} }` | Legacy per-agent `temperature`, `tools`, `permission`, `disable`, `maxSteps` are discouraged; use `model`, `permissions`, `steps`, `mode`, `hidden`, `color`, `disabled`. |
| `command: {...}`, `subtask: true` | `commands: {...}`, `subagent: true` | `subtask` still accepted; `subagent` wins if both are set. |
| `autoupdate: true` | `update: "auto" \| "notify" \| "disable"` | Default `notify`. |
| `compaction: { auto, prune, reserved }` | `compaction: { auto, keep: { tokens }, buffer }` | v2 is checkpoint-based; tail-turn pruning is gone. |
| `lsp` | — | Not supported in v2; use lint/typecheck commands in AGENTS.md or a skill. |
| `share` | `share` | Accepted but inert: v2 doesn't support session sharing yet. |
| `server: { port }` | `opencode serve --port …` / `opencode service set port …` | No `server` config key. |
| `subagent_depth` | — | v2 nesting depth defaults to one; no config equivalent verified. |
| `small_model` | built-in `title`/`summary` agents | Override their model via `agents.title.model` / `agents.summary.model` (verify with `/agents`). |
| `instructions: [...]` | AGENTS.md only | v2 **accepts but does not load** `instructions` entries. |
| `tui.json(c)` (layered) | `~/.config/opencode/cli.json` | Auto-migrated on first v2 TUI start; **project-local client config is not migrated**. |
| `plugin: [pkg, [opts]]` | `plugins: [pkg, { package, options }]` | New plugin API; port entrypoints/hooks/tools. |
| `enabled_providers` / `disabled_providers` | `experimental.policies: [{action:"provider.use", resource, effect}]` | Policies never prompt and only tighten. |
| MCP `mcp: { name: {…, enabled: true} }` | `mcp: { servers: { name: {…, disabled: false} } }` | Server objects; `cwd`, `environment`, `timeout:{startup,catalog,execution}`, `protocol`, `codemode`. |
| `.opencode/agent\|command\|skill\|plugin/` | `.opencode/agents\|commands\|skills\|plugins/` | Singular forms still discovered for some types (`skill/`, `command/`, `plugin/`), but use plural for new files. |
| Server API v1 HTTP | `@opencode/client` + v2 API reference | Integrations must be ported. |

**Verify after migrating:** `opencode --version`, `opencode service status`,
`/models`, `/agents`, `/mcps`, and one real edit+shell task.

---

## 5. The lean global config — `~/.config/opencode/opencode.jsonc`

Config precedence (later wins): global → `OPENCODE_CONFIG` → project
`opencode.json(c)` → `.opencode/` configs → inline. Set defaults once here;
override per project only when genuinely needed. `{env:VAR}` and `{file:path}`
substitution work anywhere in the config.

This folder's [opencode.jsonc](opencode.jsonc) is this exact content, ready to
copy to `~/.config/opencode/`:

```jsonc
{
  // Global OpenCode v2 config. Copy to ~/.config/opencode/opencode.jsonc
  // (v2 also reads plain .json). Verified against OpenCode v2.0.14, Sep 2026.
  "$schema": "https://opencode.ai/config.json",

  // ---- Core -----------------------------------------------------------
  "model": "opencode-go/mimo-v2.6-flash",
  "default_agent": "build",
  "update": "notify",

  // ---- Agents (v2: "agents" — v1's "agent" + small_model are gone) ---
  "agents": {
    "plan": {
      "mode": "primary",
      "model": "opencode-go/glm-5.2",
      "description": "Read-only planning/analysis; the shipped plan agent denies edits."
    },
    "architect": {
      "mode": "primary",
      "model": "opencode-go/kimi-k3",
      "description": "Hard architecture + multi-file debugging; short, targeted sessions.",
      "permissions": [
        { "action": "edit", "resource": "*", "effect": "ask" },
        { "action": "shell", "resource": "*", "effect": "ask" }
      ]
    },
    "research": {
      "mode": "subagent",
      "model": "opencode-go/glm-5.2",
      "description": "Deep-dive web research: search, read, synthesize with citations.",
      "permissions": [
        { "action": "edit", "resource": "*", "effect": "deny" },
        { "action": "websearch", "resource": "*", "effect": "allow" },
        { "action": "webfetch", "resource": "*", "effect": "allow" }
      ]
    },
    // Built-in title/summary agents run on every session; keep them cheap.
    // (v2 replacement for v1's small_model — verify with /agents.)
    "title": { "model": "opencode-go/mimo-v2.6-flash" },
    "summary": { "model": "opencode-go/mimo-v2.6-flash" }
  },

  // ---- Permissions ----------------------------------------------------
  // Ordered rules; LAST match wins, so broad rules come first.
  // (v2 action for shell is "shell", not v1's "bash".)
  "permissions": [
    { "action": "shell", "resource": "*", "effect": "ask" },
    { "action": "shell", "resource": "git status *", "effect": "allow" },
    { "action": "shell", "resource": "git diff *", "effect": "allow" },
    { "action": "shell", "resource": "git log *", "effect": "allow" },
    { "action": "shell", "resource": "ls *", "effect": "allow" },
    { "action": "shell", "resource": "cat *", "effect": "allow" },
    { "action": "shell", "resource": "grep *", "effect": "allow" },
    { "action": "shell", "resource": "rg *", "effect": "allow" },
    { "action": "shell", "resource": "python3 -m pytest *", "effect": "allow" },
    { "action": "shell", "resource": "uv run *", "effect": "allow" },
    { "action": "shell", "resource": "uvx *", "effect": "allow" },
    { "action": "shell", "resource": "git push *", "effect": "ask" },
    { "action": "shell", "resource": "rm -rf *", "effect": "deny" },
    { "action": "websearch", "resource": "*", "effect": "ask" },
    { "action": "webfetch", "resource": "*", "effect": "ask" }
    // external_directory and *.env reads already default to "ask" in v2's
    // shipped base policy; they are intentionally left untouched.
  ],

  // ---- Commands ---------------------------------------------------------
  "commands": {
    "review": {
      "template": "Review the current working diff (`git diff`). Delegate to the code-review subagent (langgraph-agent MCP tool) and report its verdict and findings.",
      "description": "LangGraph-powered code review of the working diff",
      "agent": "build"
    },
    "test": {
      "template": "Use the project-ops subagent's run_tests tool to run the test suite for $ARGUMENTS and summarize any failures.",
      "description": "Run tests via the Pydantic-validated pytest MCP tool",
      "agent": "build"
    },
    "plan-feature": {
      "template": "Acting as the architect agent, produce a short implementation plan (files to touch, risks, test strategy) for: $ARGUMENTS. Do not write code yet.",
      "description": "Draft an implementation plan with the architect agent",
      "agent": "architect"
    },
    "research": {
      "template": "Delegate to the research subagent: investigate \"$ARGUMENTS\" using web search and page fetches. Return a structured brief with sources and a confidence assessment.",
      "description": "Deep web research via the research subagent",
      "agent": "build",
      "subagent": true
    }
  },

  // ---- MCP servers ------------------------------------------------------
  // v2 nests servers under mcp.servers and uses `disabled` (not `enabled`).
  // Servers connect automatically unless disabled. A project-level override
  // REPLACES the whole server object, so repeat every required field there.
  "mcp": {
    "servers": {
      "pydantic-tools": {
        "type": "local",
        "command": ["uv", "run", "/home/ahsan/Git/common/opencode-go/server.py"],
        "disabled": true,
        "timeout": { "startup": 15000 }
      },
      "langgraph-agent": {
        "type": "local",
        "command": ["uv", "run", "/home/ahsan/Git/common/opencode-go/mcp_server.py"],
        "disabled": true,
        "timeout": { "startup": 30000 },
        "environment": {
          "GRAPH_BASE_URL": "https://opencode.ai/zen/go/v1",
          "GRAPH_API_KEY": "{env:OPENCODE_GO_API_KEY}",
          "GRAPH_MODEL": "hy3"
        }
      }
    }
  },

  // ---- Token hygiene ----------------------------------------------------
  "compaction": {
    "auto": true,
    "keep": { "tokens": 15000 },
    "buffer": 20000
  },

  "formatter": true,
  "worktree": { "directory": "../worktrees" },

  // v2 websearch needs ONE provider connected (Exa/Firecrawl/Parallel/Tavily)
  // via /connect or its API key env var. "random" retries across providers.
  "websearch": { "provider": "random" },

  // Warming is off by default and sends billable requests when enabled.
  "warming": false

  // Removed vs the old v1-based config (see §4 for replacements):
  //   share, autoupdate, small_model, subagent_depth, lsp, server,
  //   instructions, permission{bash}, agent{}, command{}, mcp{<name>}, provider{}
}
```

Notes:

- **Do not** add `"instructions": ["AGENTS.md"]` — AGENTS.md is auto-loaded; v2
  ignores `instructions` entries anyway (they never reach the model).
- `share`, `lsp`, `server`, `autoupdate`, `small_model`, `subagent_depth` are v1
  concepts: omitted here on purpose (§4 says what replaces each).
- `watcher.ignore` still exists as a config section in the v2 docs; its exact shape
  was not re-verified in this audit — if your build warns, drop it (it's a
  nice-to-have, not load-bearing).
- `experimental.policies` is deliberately unused here; add it later if you want
  hard, prompt-less denials or want to force all traffic through approved
  providers, e.g.
  `"experimental": { "policies": [{ "action": "provider.use", "resource": "openai", "effect": "deny" }] }`.

### 5.1 CLI settings — `~/.config/opencode/cli.json` (replaces `tui.json`)

This folder's [cli.json](cli.json) is the same content:

```json
{
  "$schema": "https://opencode.ai/v2/cli.json",
  "mouse": true,
  "scroll": { "speed": 3 },
  "prompt": { "paste": "compact", "image_preview": false },
  "session": {
    "sidebar": "auto",
    "thinking": "hide",
    "tps": true,
    "markdown": "rendered"
  },
  "keybinds": { "leader": "ctrl+x" },
  "leader": { "timeout": 2000 }
}
```

Only `~/.config/opencode/cli.json` is read (or
`$XDG_CONFIG_HOME/opencode/cli.json`); there is **no project-local client config**.
Unknown settings are rejected, valid edits reload live, and `$schema` is added
automatically when v2 creates or migrates the file. `OPENCODE_CLI_CONFIG_CONTENT`
can override settings inline for one run. Full key list: `theme`, `animations`,
`cursor`, `mouse`, `scroll`, `prompt`, `session`, `tabs`, `diffs`, `alerts`,
`terminal`, `mini`, `keybinds`, `leader`, `plugins`, `debug`, `experimental`.

### 5.2 Project files

- **`AGENTS.md`** (project root, committed): auto-loaded; nested `AGENTS.md` files
  load as the agent explores that area. This folder's [AGENTS.md](AGENTS.md) is the
  example. Global personal rules go in `~/.config/opencode/AGENTS.md` — keep them
  short, since they ride along in every context window you pay for.
- **`.opencode/`** in a project: `agents/`, `commands/`, `skills/`, `plugins/`
  (plural directory names).

---

## 6. Token & quota playbook

1. **Tier the models; keep a big bucket as default.** `mimo-v2.6-flash`-class models
   provide ~30,000 est. requests per 5 h vs ~110 for `kimi-k3` — a ~275× spread.
   Every token that doesn't go through `glm-5.3` / `kimi-k3` / `qwen3.8-max`
   ($15 caps) is headroom saved.
2. **Keep context small.** Every session pays for the system prompt + tool schemas +
   AGENTS.md. Code Mode keeps MCP schemas out of context, so disable servers you
   don't need (`"disabled": true`) and gate skills with `permissions`.
3. **Compact and checkpoint.** `compaction.auto` on with `keep.tokens` tuned to
   taste; `/compact` after big explorations.
4. **Keep `title`/`summary` on a cheap model** (`agents.title.model` /
   `agents.summary.model`) — never a $15-cap model.
5. **Reuse sessions.** A stable `x-opencode-session` is what earns prompt-cache
   discounts; brand-new sessions re-pay cold context (`/sessions`, session tabs,
   `-c` for continue).
6. **Keep `warming` off** — warm-up requests are real, billable model calls.
7. **Exploit the windows.** One fully-used 5-hour window is 20% of a model's monthly
   bucket (= 40% of its weekly allowance), so pace marathons across windows.
8. **Watch the needle.** Console for the big picture (per-model detail + reset
   timers); Usage API CSV export for accounting; Budgets API if you share the
   workspace.
9. **Don't point an agent at the metered API as a proxy.** The LangGraph reviewer
   makes 3 LLM calls per review; a single-call reviewer subagent does the same job
   for ~⅓ the tokens. Use the MCP path only when you want the structured verdict.

---

## 7. Optimizing for agentic programming

- **Subagents for the expensive stuff.** `research` runs on its own (cheaper) model
  with its own context window; `build`'s context stays small. Nesting depth is 1 by
  default, so plan orchestration accordingly.
- **Commands encode workflows** (§5) so every project gets `/plan-feature`,
  `/review`, `/test`, `/research`.
- **Permissions as guardrails, not brakes.** The array in §5 keeps read-only git
  instant, asks before anything mutating, hard-denies `rm -rf`, and asks for web
  access globally (the `research` agent overrides that for itself).
- **Common `/` commands:** `/new`, `/sessions`, `/models`, `/agents`, `/undo`,
  `/redo`, `/editor`, `/compact`, `/connect`, `/mcps`, `/btw <question>`.
- **Keybind muscle memory:** leader `Ctrl+X`; `Ctrl+X N/L/M/A/U/R/E/W` = new
  session / sessions / models / agents / undo / redo / editor / close tab;
  `Shift+Tab` cycles agents; `F2` cycles recent models; `Ctrl+O` recent
  sessions+projects; `Ctrl+M` move session to worktree.
- **Formatters over token-burn.** `formatter: true` lets ruff/prettier fix style
  mechanically instead of paying a model to do it.

---

## 8. Optional: Pydantic + LangGraph MCP servers (this folder, no LiteLLM)

The LangGraph review pipeline (`graph.py` + `mcp_server.py`) and the
Pydantic-validated project-ops tools (`server.py`) still work — **with two fixes
applied in this revision**:

1. **Pin the MCP SDK to 1.x.** `pip install mcp` now resolves to **2.x**, which
   removed `mcp.server.fastmcp` (2.x uses `from mcp.server import MCPServer`).
   Both PEP 723 blocks now pin `"mcp[cli]>=1.30,<2"`; the 1.x branch (latest
   1.30.0, Sep 7 2026) still receives critical fixes and security patches.
2. **No LiteLLM hop.** `graph.py` now talks **directly to an OpenAI-compatible
   endpoint** (default: OpenCode Go) via `GRAPH_BASE_URL` / `GRAPH_API_KEY` /
   `GRAPH_MODEL`. Pick a model served on `/v1/chat/completions` (e.g. `hy3`,
   `hy4-preview` in the docs' endpoint table) — models served only on the
   Anthropic `/v1/messages` shape will not work through `ChatOpenAI`. Set
   `OPENCODE_GO_API_KEY` (the same key `/connect` stored).

Verified working in the audit: PEP 723 environments build; both servers import,
initialize and shut down; `graph.py`'s Pydantic-state graph compiles and `ainvoke`
returns a dict (so `CodeReviewResult(**result_state)` is safe) on langgraph 1.2.12 /
langchain-openai 1.6.4 / pydantic 2.x.

**Advantages / disadvantages:**

- ✅ **Pydantic tools**: precise JSON Schemas; malformed calls fail fast with
  validation errors; results arrive structured instead of prose. The same servers
  are reusable from PydanticAI agents.
- ✅ **LangGraph**: deterministic, inspectable multi-step flow with typed state; the
  same graph runs locally or deploys to LangGraph Platform.
- ❌ Extra moving parts and context cost: tool schemas permanently consume tokens
  unless gated per-agent (they ship `disabled: true` here on purpose).
- ❌ The reviewer costs **3 LLM calls per review** where one strong-model prompt does
  the same job (~3× the quota).
- ❌ `query_metrics` returns **fabricated placeholder data (42.0)** — keep it
  disabled until you wire a real backend; a model will otherwise happily quote fake
  metrics.
- ❌ `run_tests` executes pytest in the MCP server's *ephemeral* environment — fine
  for plain pytest, but a project needing its own deps will show false import
  failures. Prefer the built-in shell tool for dependency-heavy suites.

Rule of thumb: keep them if you value structure and validation; if you're optimizing
purely for quota, a single-call reviewer subagent on `glm-5.2` is the leaner
equivalent.

### 8.1 First-party Pydantic & LangGraph integrations (you may not need custom code)

**LangGraph — a deployed graph *is* an MCP server.** The LangGraph Agent Server
behind LangSmith Deployments exposes every deployed graph as an MCP tool at a
streamable-HTTP `/mcp` endpoint (`https://<deployment>.us.langgraph.app/mcp`;
`langgraph dev` serves the same locally at `http://localhost:8124/mcp`). OpenCode
connects directly — no wrapper script needed:

```jsonc
"mcp": {
  "servers": {
    "langgraph-cloud": {
      "type": "remote",
      "url": "{env:LANGGRAPH_DEPLOYMENT_URL}/mcp",
      "disabled": true,
      "headers": { "x-api-key": "{env:LANGSMITH_API_KEY}" }
    }
  }
}
```

Caveats: each graph surfaces as **one** tool (tools inside the graph aren't
individually exposed), and auth is your LangSmith API key. The reverse direction —
a LangGraph agent consuming MCP servers as tools — is what
[`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters)
is for.

**PydanticAI — MCP in both directions** ([docs](https://pydantic.dev/docs/ai/mcp/overview/)).
PydanticAI agents *consume* MCP servers via the `MCP` capability, the lower-level
`MCPToolset` (`pydantic_ai.mcp`), or `MCPServerTool` for provider-native MCP — so a
PydanticAI side-agent can reuse the exact same MCP servers you register in OpenCode.
On the *serving* side, the standard way to expose an agent to OpenCode is a
[FastMCP](https://gofastmcp.com) server wrapping the agent's tools with `@mcp.tool`
— precisely the pattern `server.py`/`mcp_server.py` follow (Pydantic models in,
Pydantic models out). Known limitation: MCP **tools only** — servers exposing just
resources aren't usable from agents.

---

## 9. Deep research setup for professional scientists

**Web search first.** v2's `websearch` tool needs a provider: connect **Exa**,
**Firecrawl**, **Parallel** or **Tavily** via `/connect`, or export the matching API
key. Pin one in config (`"websearch": { "provider": "parallel" }`) or leave
`"random"` so a 429 on one provider retries another. `"websearch": false` removes
the tool entirely.

**Paper search MCP** ([openags/paper-search-mcp](https://github.com/openags/paper-search-mcp), MIT):

```jsonc
"mcp": {
  "servers": {
    "paper-search": {
      "type": "local",
      "command": ["uvx", "paper-search-mcp"],
      "disabled": true
    }
  }
}
```

→ arXiv, PubMed/PMC, bioRxiv, medRxiv, Europe PMC, OpenAlex, Crossref, CORE,
OpenAIRE, dblp, Zenodo, HAL, SSRN, Semantic Scholar and more; optional API keys go
in `~/.config/paper-search-mcp/.env`.

**Literature notebooks.** [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook)
is an open-source NotebookLM alternative (docker-compose + SurrealDB, Next.js UI)
that speaks any OpenAI-compatible endpoint for chat/embeddings, and
[Epochal-dev/open-notebook-mcp](https://github.com/Epochal-dev/open-notebook-mcp)
exposes it to agents (39 tools: notebooks, sources, notes, search/ask, models, chat
sessions, settings; Python 3.12+, run from a clone with `uv`). Keep it disabled
until you actually need it.

**Which model for search-heavy work?** The search *backend* is model-independent;
the spend is model tokens, and search agents re-read context constantly, so
**cached-read pricing dominates**. A cost-tiered ladder following §2:

- `glm-5.3-flash` — high-volume search-and-read passes
- `mimo-v2.6-flash` — bulk cheap reading and note-taking
- `glm-5.2` — default research/synthesis model
- `kimi-k3` — final hard synthesis only (110 req/5h, $15 cap — burns fast)
- DeepSeek V4 Flash — paging through long documents

The pattern for a research session: `paper-search`/Tavily to find, `webfetch` to
read, Open Notebook to persist and chat with the corpus, and the `research` subagent
to synthesize.

---

## 10. IDE and GUI integration (and completions)

- **Extensions** ship for **VS Code, Cursor, Zed, Windsurf and VSCodium** (install
  links on <https://opencode.ai/download>). The VS Code-family extension embeds the
  OpenCode terminal rather than a native panel.
- **ACP for everything else.** `opencode acp` speaks Agent Client Protocol over
  stdin/stdout (protocol v1), starts a **private** server for that process (it does
  *not* join the shared background service), and can serve multiple sessions.
  Zed example (`~/.config/zed/settings.json`):

  ```json
  { "agent_servers": { "OpenCode": { "command": "opencode", "args": ["acp"] } } }
  ```

  Other ACP clients (JetBrains IDEs with ACP support, Neovim ACP plugins, …) use the
  same executable + `acp` argument with their own config format; if a GUI can't find
  `opencode`, set `command` to the absolute path from `which opencode`. ACP sessions
  support create/list/load/resume/fork/close/delete, model + effort + mode
  switching, and permission prompts. Sign in first with `opencode auth login`.
  (MCP over SSE and MCP over ACP are not supported by `opencode acp`.)
- **Inline completions are not an OpenCode feature** (it's an agent, not a
  completion engine). Options:
  - **Zed edit predictions** against an OpenAI-compatible FIM server (must implement
    `/v1/completions`):

    ```json
    {
      "edit_predictions": {
        "provider": "open_ai_compatible_api",
        "open_ai_compatible_api": {
          "api_url": "http://localhost:8080/v1/completions",
          "model": "zeta2.1",
          "prompt_format": "infer",
          "max_output_tokens": 512
        }
      }
    }
    ```

    `prompt_format` accepts `infer`, `zeta2` or `zeta2_1`; providers include Zeta
    (`zed`), GitHub Copilot, Mercury Coder, Codestral, `ollama` and
    `open_ai_compatible_api`.
  - **GitHub Copilot Chat + Go (BYOK)**: Copilot's "Manage Models" flow accepts
    OpenAI-compatible providers — add `https://opencode.ai/zen/go/v1` with your Go
    key and Go models appear in Copilot Chat/agent mode. Two hard caveats: BYOK
    covers **chat/agent features only** — Copilot's inline ghost-text completions
    always run on GitHub's own models; and Go's docs list **Copilot Chat as a known
    problematic client** until VS Code sends `x-opencode-session`
    ([microsoft/vscode#334186](https://github.com/microsoft/vscode/issues/334186),
    open since Sep 3, 2026 and stale/triage-needed since).
  - **Continue** in VS Code for chat + autocomplete against any OpenAI-compatible
    endpoint, or a self-hosted **Tabby**/llama.cpp-served FIM model (Qwen2.5-Coder
    class) for fully local completions.

  Note the Go API serves **chat**-style traffic; inline FIM completions want a small
  local model or a completion-oriented provider regardless.

---

## 11. NanoClaw integration

[NanoClaw](https://github.com/nanocoai/nanoclaw) is a lightweight,
container-per-session personal AI agent you message from WhatsApp, Telegram, Slack,
Discord, Gmail and other chat apps, built on Anthropic's Agent SDK. It's a
**companion, not a replacement** for OpenCode: always-on assistant on your phone,
OpenCode as the heavy coding/research terminal.

- Requires Node 22+, pnpm 10+, Docker; `bash nanoclaw.sh` after clone (it hands off
  to Claude Code to diagnose/resume if a step fails).
- Model wiring: its native runtime is Anthropic-SDK-compatible, so any
  **Anthropic-compatible** endpoint works via `ANTHROPIC_BASE_URL` +
  `ANTHROPIC_AUTH_TOKEN` — point it at Go's Anthropic-compatible endpoint (base such
  that `<base>/v1/messages` resolves to `https://opencode.ai/zen/go/v1/messages`).
  Alternatively use its `/add-opencode` runtime skill (OpenRouter, OpenAI, Google,
  DeepSeek, … via OpenCode config) or `/add-ollama-provider` for local models; both
  are configurable per agent group.
- It ships a `.mcp.json`, so MCP servers can be added to its agents too.
- **Caution:** Go is designed for coding-agent traffic and monitored for abuse —
  keep NanoClaw's volume modest and coding-adjacent, and remember every NanoClaw
  message burns the same per-model caps.

---

## 12. Productivity tools (MCP)

All endpoints verified Sep 2026. Wire them globally (or per project) and enable the
ones you need; remote servers keep the config clean:

| Tool | Server | How |
|---|---|---|
| GitHub | official remote | `https://api.githubcopilot.com/mcp/` (OAuth; `/readonly` and `/x/all` path variants, `X-MCP-Toolsets` / `X-MCP-Readonly` headers) |
| Notion | official remote | hosted by Notion, OAuth (see <https://developers.notion.com/docs/mcp>) |
| Linear | official remote | `https://mcp.linear.app/mcp` (OAuth; `…/mcp/readonly` for read-only; `/sse` is deprecated) |
| Google Calendar | official Google Workspace MCP | remote streamable HTTP — **Developer Preview** (requires Workspace Developer Preview Program + a Cloud project; enable `calendar-json.googleapis.com`) |
| Obsidian | `MarkusPfundstein/mcp-obsidian` | local; needs the Obsidian Local REST API plugin |

Trim tool schemas with Code Mode (default) or `permissions` denies — big servers can
eat a meaningful chunk of context.

### Creating documents like Claude's artifacts

OpenCode has no claude.ai-style artifact pane, but it can *produce real document
files* the same way Claude's web UI does under the hood — by running code — and v2's
native **Agent Skills** make it repeatable:

1. Drop a document skill into `~/.config/opencode/skills/<name>/SKILL.md`
   (per-project alternative: `.opencode/skills/`; the Claude-compatible
   `~/.claude/skills/` and `~/.agents/skills/` are also discovered). Anthropic's
   open-source [anthropics/skills](https://github.com/anthropics/skills) repo ships
   ready-made **docx / pptx / xlsx / pdf** skills in exactly that format.
2. Ask for the document; the agent lists the skill (name + description only) and
   loads its instructions via the `skill` tool, then runs the Python toolchain
   (python-docx, python-pptx, openpyxl, …) to write real files into your workspace.
3. Consume the results anywhere: open them with normal apps, commit them, or export
   the files from OpenCode Desktop/Web (`opencode pair`). Note that v2 has no
   session-sharing link yet (§1), so share the *artifacts*, not the session.

Gate document skills with the `skill` permission action (e.g. `internal-*` → `deny`)
so sessions only generate files when you ask. Only skill names/descriptions load into
context upfront, so a big skills folder doesn't tax everyday token usage.

---

## 13. What lives in this folder

```
README.md            this guide (v2-only, verified Sep 2026)
AGENTS.md            project-level agent rules (auto-loaded in this folder)
opencode.jsonc       the global config from §5 — copy to ~/.config/opencode/
cli.json             terminal settings from §5.1 — copy to ~/.config/opencode/
server.py            pydantic-tools MCP server (mcp>=1.30,<2 pin)
mcp_server.py        langgraph-agent MCP server (same pin)
graph.py             LangGraph plan→analyze→summarize review workflow
.env.example         env vars for the optional layers (no LiteLLM anymore)
.gitignore           keeps .env, caches, and test artifacts out of git
.zcodeignore         auto-synced mirror of .gitignore for the ZCode workspace
```

Removed in this revision: `config.yaml` and `docker-compose.yml` (the LiteLLM +
Postgres + Redis layer) and `tui.json` (v1 client config, replaced by `cli.json`).

---

## 14. Verification log (2026-09-23)

Verified against the live docs, repos and package indexes this pass:

- **v2 product surface** — from the docs under <https://opencode.ai/v2/docs>
  (intro, config, agents, models, permissions, tools, mcp-servers, skills, commands,
  compaction, formatters, snapshots, warming, websearch, instructions, policies,
  sharing, migrate-v1, troubleshooting, and the CLI pages for intro/TUI/Settings/
  Web/ACP/Keybinds): shared background service, `run`/`mini`, `pair`/`serve`/
  `--server`/`--standalone`, session tabs, worktrees, snapshots+undo/redo,
  `permissions` arrays (last match wins; `shell` not `bash`), `agents`/`commands`/
  `plugins` plurals, `mcp.servers` + `disabled`, Code Mode default, compaction
  `keep`/`buffer`, the four websearch providers, and the full `cli.json` key list.
  **Sharing** is verbatim "OpenCode V2 does not support session sharing yet."
- **Go** — $10/month; per-model dollar caps; 5 h = 20%, weekly = 50%, monthly = 100%;
  the usage-estimate table cross-checked against a community snapshot independently
  verified 2026-09-12 (5-hour figures matched exactly), and per-model caps
  spot-confirmed from a public Console report in issue #46365 (Aug 31, 2026);
  Usage/Budgets console APIs; the *Known problematic clients* list (GitHub Copilot
  Chat, Kimi Code, MiMo Code, DeepSeek Harness) and validated clients (Hermes,
  Claude Code, Codex, ZCode, Pi, jcode, Kilo Code CLI); privacy/retention table;
  `x-opencode-session` requirement; `opencode-go/<model-id>` config format.
- **Releases & installs** — AUR `opencode-beta` **2.0.14-1** (last updated
  2026-09-22, conflicts with `opencode`/`opencode2`); AUR `opencode-desktop-bin`
  **2.0.14-1** (2026-09-22, builds the upstream
  `opencode-desktop-2.0.14-linux-*.deb`); <https://opencode.ai/download> lists
  Desktop builds for macOS (Apple silicon/Intel), Windows (x64/ARM64) and Linux
  (.deb/.rpm/AppImage); the `opencode-desktop` **Homebrew cask still showed
  1.18.32**; GitHub releases still attach to the 1.18.x line (latest v1.18.32,
  Sep 21, 2026) while v2 ships via the docs' installers/`npm @opencode/cli`;
  v1/v2 are **no longer installed side by side**.
- **Open issues used as caveats** — #48330 (Copilot legacy-plan request drain,
  open), #49847 (ChatGPT-OAuth requests sent with the Zen key, open),
  #46365 (usage accounting discrepancy, open), microsoft/vscode#334186 (missing
  session header, open/stale).
- **Python stack** — `mcp` 2.2.0 is current and **removed `mcp.server.fastmcp`**;
  the 1.x branch lives on (1.30.0, Sep 7 2026) which is why the pins are
  `>=1.30,<2`. langgraph 1.2.12; langchain-openai 1.6.4; pydantic 2.x.
- **Ecosystem** — anthropics/skills (incl. docx/pptx/xlsx/pdf), nanocoai/nanoclaw
  (containers, chat apps, `/add-opencode`, Anthropic SDK + base-URL override),
  lfnovo/open-notebook + Epochal-dev/open-notebook-mcp (39 tools), openags/
  paper-search-mcp (MIT; arXiv/PubMed/bioRxiv/medRxiv/Europe PMC/OpenAlex…),
  GitHub remote MCP (`api.githubcopilot.com/mcp/`), Linear (`mcp.linear.app/mcp`),
  Notion (hosted remote MCP), Google Calendar MCP (Developer Preview), and Zed's
  edit-prediction keys (`provider`, `prompt_format`: `infer`/`zeta2`/`zeta2_1`).
- **Local files** — `graph.py`, `mcp_server.py`, `server.py` all pass
  `python3 -m py_compile`; `opencode.jsonc`/`cli.json` parse as JSON/JSONC; no file
  in this folder references LiteLLM anymore.

**Not independently re-verified this pass** (flagged inline where used): some
per-model Go caps and per-1M-token prices; the DeepSeek V4.1 Flash 4× promo and its
Sep 27, 2026 end date; the exact v2 `watcher` config shape; `agents.title`/`summary`
model overrides; and the Google Calendar MCP endpoint path. Treat the Go docs page
and `/models` as the source of truth for anything in that list.

---

## 15. Sources (fetched 2026-09-21 → 2026-09-23)

- **v2 docs:** <https://opencode.ai/v2/docs> · `/config` · `/agents` · `/models` ·
  `/permissions` · `/tools` · `/mcp-servers` · `/skills` · `/commands` ·
  `/compaction` · `/formatters` · `/snapshots` · `/warming` · `/websearch` ·
  `/instructions` · `/policies` · `/sharing` · `/migrate-v1` · `/troubleshooting` ·
  `/cli` · `/cli/tui` · `/cli/config` · `/cli/web` · `/cli/acp` · `/cli/keybinds`
- **Console / Go:** <https://opencode.ai/docs/go> ·
  <https://opencode.ai/v2/docs/console/go> ·
  <https://opencode.ai/v2/docs/console/usage> ·
  <https://opencode.ai/v2/docs/console/budgets> · <https://opencode.ai/console>
- **Schemas:** <https://opencode.ai/config.json> · <https://opencode.ai/v2/cli.json>
- **Download / packaging:** <https://opencode.ai/download> ·
  <https://github.com/anomalyco/opencode/releases> ·
  <https://aur.archlinux.org/packages/opencode-beta> ·
  <https://aur.archlinux.org/packages/opencode-desktop-bin> ·
  <https://formulae.brew.sh/cask/opencode-desktop>
- **Issues:** [#48330](https://github.com/anomalyco/opencode/issues/48330) ·
  [#49847](https://github.com/anomalyco/opencode/issues/49847) ·
  [#46365](https://github.com/anomalyco/opencode/issues/46365) ·
  [microsoft/vscode#334186](https://github.com/microsoft/vscode/issues/334186)
- **Package indexes:** <https://pypi.org/project/mcp/> ·
  <https://pypi.org/project/langgraph/> ·
  <https://pypi.org/project/langchain-openai/>
- **Integrations:** [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) ·
  [lfnovo/open-notebook](https://github.com/lfnovo/open-notebook) ·
  [Epochal-dev/open-notebook-mcp](https://github.com/Epochal-dev/open-notebook-mcp) ·
  [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) ·
  [anthropics/skills](https://github.com/anthropics/skills) ·
  [github/github-mcp-server](https://github.com/github/github-mcp-server) ·
  [Linear MCP](https://linear.app/docs/mcp) ·
  [Notion MCP](https://developers.notion.com/docs/mcp) ·
  [Google Calendar MCP](https://developers.google.com/workspace/calendar/api/guides/configure-mcp-server) ·
  [Zed edit predictions](https://zed.dev/docs/ai/edit-prediction) ·
  [Tabby](https://github.com/TabbyML/tabby)

