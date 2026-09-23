# OpenCode v2 + OpenCode Go — Ultimate Setup Guide

A single, opinionated setup for running **OpenCode v2** on an **OpenCode Go**
subscription ($10/mo) — tuned to stretch the quota across all ~29 models Go
currently offers, with agent/permission guardrails, model choices for specific
work scenarios, deep-research plumbing, IDE/GUI integration and productivity MCP
servers.

Everything here is **v2-only**; the LiteLLM governance layer that used to live in
this folder has been removed (Go already meters in dollars, and a self-hosted
proxy adds latency and risks breaking prompt caching). The Pydantic/LangGraph MCP
servers that used to live in this folder have also been removed (see §12 for what
that means for this folder's file list) — they added real quota/context cost for
a job a single strong-model subagent does more cheaply (§6, §7). **Coming from
v1?** Jump to **§4 — Migrating from v1 to v2**; v1 and v2 are no longer installed
side by side.

> OpenCode moves fast. Model lists, caps and config keys change. The pages under
> <https://opencode.ai/v2/docs> and <https://opencode.ai/docs/go> are authoritative;
> re-check them and `/models` before trusting exact IDs or caps. This revision was
> audited against those pages on **2026-09-23** (see §13/§14); the Go docs page
> itself is stamped "Last updated: Sep 22, 2026."
>
> **Independent verification pass (2026-09-23):** a second, independent audit
> re-fetched `opencode.ai/v2/docs`, `opencode.ai/docs/go`, and `opencode.ai/go`
> directly and cross-checked the pricing table, request estimates, model list,
> and version numbers below. Full results are in the new **§15 — Independent
> audit findings** at the end of this file. Headline: the Go pricing table and
> request-count table check out almost line-for-line against the live docs; the
> flagged 2.0.6-vs-2.0.14 version gap is real and reproducible; but Anomaly's own
> marketing pages are inconsistent about a **"$5 first month"** promo (see §15.1)
> that this guide's headline price doesn't mention either way.

---

## 1. What OpenCode v2 gives you (stock; see §13 for a version-number caveat)

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
  Desktop and Web both let you attach/paste a screenshot into the composer — the
  CLI can too (`prompt.image_preview` in `cli.json`, §5.1, just toggles whether it
  previews the image inline). **That's a client-side attachment feature, separate
  from whether the selected model can actually read the image** — but "separate"
  doesn't mean "only one model can," which an earlier revision of this section
  wrongly implied (see the correction in §13). The model picker's capability icons
  (what you're hovering over if you're looking at `/models` or the console) come
  from the same Models.dev catalog OpenCode fetches live (§1), and by that catalog
  **several** Go models are tagged with image input, not just
  `deepseek-v4-flash-vision-exp` — GLM-5.3-Flash is a confirmed example. What the
  Go docs page (§2) actually documents is narrower: only
  `deepseek-v4-flash-vision-exp` gets an explicit per-image-token billing line,
  and there's a reported case
  ([lidge-jun/opencodex#4505](https://github.com/lidge-jun/opencodex/issues/4505))
  of the Go backend's own vision denylist overriding the catalog's declared image
  support for at least one other model (DeepSeek V4.1 Flash). So: the catalog tag
  is a reasonable first signal, not a guarantee — if a screenshot-heavy task
  matters, send a real test image on the model you intend to use and confirm it's
  actually read before relying on it, rather than trusting either "the icon says
  image" or last revision's "only one model does this" at face value.
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

- **Full lineup, fetched directly from <https://opencode.ai/docs/go/> on
  2026-09-23** (page stamped "Last updated: Sep 22, 2026") — every cap below is
  read straight off the docs' usage-limits table, not estimated or
  cross-referenced against a third party. "req/5h" is the docs' own estimated-
  request figure for that window:

  | Model | Est. req / 5h | Monthly cap | Notes |
  |---|---|---|---|
  | Muse Spark 1.3 / 1.2 Contributor | 45,300 | $60 | ⚠ trains on prompts, [region-limited](https://ai.developer.meta.com/legal/geographic-use-policy) |
  | MiMo-V2.6-Flash | 30,100 | $60 | |
  | MiMo-V2.5 | 30,100 | $60 | older sibling of V2.6-Flash, same price/limit |
  | LongCat-2.0 | 11,400 | $60 | |
  | DeepSeek V4.1 Flash | ~~6,500~~ **26,000** | ~~$15~~ **$60** | 4× promo, ends **Sep 27, 2026** — reverts to $15/6,500 after |
  | DeepSeek V4 Flash | 13,000 | $30 | |
  | DeepSeek V4 Flash Vision Exp | 6,500 | $15 | only model with documented per-image-token billing (§13) |
  | GLM-5.3-Flash | 6,320 | $60 | catalog-tagged for image input too — unverified on Go specifically, see §13 |
  | Qwen3.8 Flash | 5,400 | $30 | |
  | Qwen3.7 Plus | 4,300 | $60 | |
  | Hy3 | 4,300 | $60 | |
  | MiniMax M2.7 | 3,400 | $60 | |
  | MiniMax M3 | 3,200 | $60 | |
  | Qwen3.6 Plus | 3,300 | $60 | |
  | MiMo-V2.6-Pro | 3,250 | $15 | |
  | MiMo-V2.5-Pro | 3,250 | $15 | |
  | GPT 5.6 Luna | 2,050 | $15 | 30-day abuse-monitoring retention |
  | Kimi K2.7 Code | 1,350 | $60 | |
  | Hy4 preview | 1,350 | $30 | |
  | Kimi K2.6 | 1,150 | $60 | |
  | DeepSeek V4 Pro | 1,050 | $15 | |
  | GLM-5.2 | 880 | $60 | |
  | GLM-5.1 | 880 | $60 | |
  | GLM-5.3 | 220 | $15 | newest/strongest GLM, smallest bucket |
  | Qwen3.7 Max | 170 | $30 | |
  | Grok 4.7 | 169 | $15 | 30-day retention; ZDR disables Responses/Files/Batch |
  | Grok 4.6 | 169 | $15 | same caveats as 4.7 |
  | Qwen3.8 Max | 160 | $15 | |
  | Kimi K3 | 110 | $15 | flagship reasoning model, priciest bucket |

  Not in the usage/estimate tables but still live on the endpoints page — **not**
  the privacy page, where this guide's earlier wording was too broad (see §15.3):
  **MiniMax M2.5** (legacy sibling of M2.7, Anthropic-compatible endpoint) — the
  Go landing page counts **30 models** total where the table above accounts for
  29 rows (30 distinct models once the combined Muse Spark row is split), so
  treat M2.5 as a still-reachable legacy option rather than a headline pick.
  DeepSeek prices split into **Peak** (01:00–04:00 and 06:00–10:00 UTC, Mon–Fri)
  and **Off-Peak** (all other hours, including weekends) token rates; the request
  estimates above use typical mixed usage.

  **Independently reconfirmed 2026-09-23:** every req/5h figure and monthly cap
  spot-checked against a direct re-fetch of `opencode.ai/docs/go` matched
  exactly (Muse Spark 45,300 · GLM-5.3-Flash 6,320/$60 · DeepSeek V4.1 Flash
  promo 26,000/$60 ending Sep 27 · Kimi K3 110/$15 · Grok 4.7/4.6 169/$15 ·
  GPT 5.6 Luna 2,050/$15, etc. — see §15.3 for the full check). MiniMax M2.5's
  absence from the "current list of models" bullet and from the privacy table,
  while still present in the token-price and endpoints tables, was also
  reproduced independently.

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

**The lever that matters:** put flash-tier models on the big buckets ($60-cap,
thousands of req/5h) and reserve the $15-cap models (Kimi K3, GLM-5.3, Qwen3.8
Max, Grok 4.7/4.6, DeepSeek V4 Pro, GPT 5.6 Luna) for the handful of steps per
day that actually need frontier reasoning — hard architecture calls, security-
sensitive diffs, and final review gates. See §6/§7/§8 for how this maps onto
specific agents and workflows.

---

## 3. Install v2 (Fedora and Arch)

> **v1 must be removed first.** "OpenCode 1 and OpenCode 2 both use the `opencode`
> command and are no longer installed side by side by default. Remove a
> package-managed V1 installation before installing V2; the V2 curl installer
> replaces the V1 binary." Configuration and session-data locations are shared.
> **Note (independent audit, 2026-09-23):** a live re-fetch of
> `opencode.ai/v2/docs` confirms the installer still just calls the binary
> `opencode` (no separate `opencode2` command), consistent with this claim. Be
> aware some older cached/indexed copies of the same docs page (from earlier in
> the v2 beta) described a distinct `opencode2` binary that *could* run
> side-by-side with v1 — that appears to be a historical, now-superseded state
> of the docs rather than the current one. See §15.4.

### Fedora

```bash
curl -fsSL https://opencode.ai/v2/install | bash
# or: npm install -g @opencode/cli
# or: bun install -g --trust @opencode/cli
# or: pnpm add -g --allow-build=@opencode/cli @opencode/cli
# or: yarn global add @opencode/cli
```

Standalone CLI binaries are published for macOS, Windows and Linux (glibc/musl,
x64/ARM64) directly off the v2 docs intro page — as of this pass (2026-09-23) that
page's links resolve to build **2.0.6**, not 2.0.14 (see §13). Confirm your
installed version with `opencode --version` rather than trusting a specific
number in this guide. (Windows package managers are not supported; use the
standalone binary.)

### Arch Linux

```bash
paru -S opencode-beta
# or: yay -S opencode-beta
# or via the Homebrew tap: brew install anomalyco/tap/opencode-v2
```

`opencode-beta` conflicts with `opencode`/`opencode2`. This pass did **not**
re-open the AUR package page to confirm its current version pin — check
<https://aur.archlinux.org/packages/opencode-beta> directly before assuming any
specific build number.

### Desktop (v2 is available)

- **Direct downloads** (<https://opencode.ai/download>, refetched this pass):
  macOS (Apple Silicon / Intel), Windows (**x64 only** in this pass's fetch — no
  ARM64 link was present), Linux `.deb` / `.rpm` (**no AppImage link** was present
  in this pass's fetch, and no ARM64 variant for either package format). If you
  need Windows ARM64, a Linux AppImage, or ARM64 `.deb`/`.rpm`, check the download
  page yourself — an earlier draft of this guide claimed all of those existed and
  this pass could not confirm they still do.
- **Arch:** `paru -S opencode-desktop-bin` (conflicts with `opencode-desktop`) —
  version not re-verified this pass.
- **Homebrew:** `brew install --cask opencode-desktop` is listed directly on the
  download page now; whether the cask has caught up to the current stable Desktop
  build was not re-checked this pass.

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
  // Each agent's model is picked for its scenario, not just its price — see §6/§7
  // for the full reasoning behind every assignment below.
  "agents": {
    "plan": {
      "mode": "primary",
      "model": "opencode-go/glm-5.2",
      "description": "Read-only planning/analysis; the shipped plan agent denies edits. GLM-5.2 gives solid multi-step reasoning at a $60 monthly cap (880 req/5h) — cheap enough to plan freely, unlike the $15-cap models."
    },
    "architect": {
      "mode": "primary",
      "model": "opencode-go/kimi-k3",
      "description": "Hard architecture + multi-file debugging; short, targeted sessions only. Kimi K3 is Go's strongest reasoning model but sits on the smallest bucket (110 req/5h, $15 cap) — reserve it for the few sessions/day that actually need frontier-level tracing across files.",
      "permissions": [
        { "action": "edit", "resource": "*", "effect": "ask" },
        { "action": "shell", "resource": "*", "effect": "ask" }
      ]
    },
    "quickfix": {
      "mode": "primary",
      "model": "opencode-go/glm-5.3-flash",
      "description": "Everyday small edits, typo/lint fixes, boilerplate, one-file changes. GLM-5.3-Flash (6,320 req/5h, $60 cap) is a meaningfully stronger flash tier than mimo-v2.6-flash for a modest cost, so it's the pick when you want more than pure autocomplete-grade output but don't need architect-level reasoning."
    },
    "vision": {
      "mode": "subagent",
      "model": "opencode-go/deepseek-v4-flash-vision-exp",
      "description": "Screenshot/UI-diff debugging, reading diagrams or error dialogs pasted as images, OCR-style extraction from PDFs rendered to PNG. Deliberately kept on the one model Go documents per-image-token billing for (§2/§13) — not necessarily the only model on Go that *can* take an image (see §13), but the one whose image handling is actually documented, so it's the safe default until you've verified another route yourself. 6,500 req/5h on a $15 cap, so route it only actual image-bearing turns."
    },
    "longread": {
      "mode": "subagent",
      "model": "opencode-go/longcat-2.0",
      "description": "Paging through large logs, long AGENTS.md trees, big config dumps, or long documents before handing a distilled summary back to a reasoning model. 11,400 req/5h on a $60 cap — built for volume, not depth."
    },
    "research": {
      "mode": "subagent",
      "model": "opencode-go/glm-5.2",
      "description": "Deep-dive web research: search, read, synthesize with citations. See §8 for the full model ladder used across a research session (this is just the default/synthesis step).",
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
      "template": "Review the current working diff (`git diff`) for correctness, security and style. Report a clear verdict (approve/changes-requested) with specific findings.",
      "description": "Single-call code review of the working diff",
      "agent": "architect"
    },
    "test": {
      "template": "Run the test suite for $ARGUMENTS using the project's normal test command (check AGENTS.md / package.json / pyproject.toml if unsure) and summarize any failures.",
      "description": "Run tests via the built-in shell tool",
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
  // This revision ships with no local MCP servers by default — see §11 for the
  // productivity servers (GitHub, Notion, Linear, Google Calendar, Obsidian)
  // and §8 for the research-oriented ones (paper-search).
  "mcp": {
    "servers": {}
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

**Which file governs which client:** `opencode.jsonc` (§5) is read by the shared
background service (§1) — TUI, Desktop and Web are all clients of that one
service, so every model/agent/permission/MCP/compaction setting in it, including
every cost-minimization choice in §6/§7, applies identically no matter which
client you open. `cli.json` (§5.1) only affects the terminal client's own UI
(mouse, scroll, theme, paste behavior) — Desktop and Web have their own
UI-preference storage and aren't governed by it. There's no separate
"desktop.json"/"web.json" to maintain: nothing UI-only in Desktop/Web draws on
quota, so there's nothing cost-relevant to configure there beyond §5.

### 5.2 Project files

- **`AGENTS.md`** (project root, committed): auto-loaded; nested `AGENTS.md` files
  load as the agent explores that area. This folder's [AGENTS.md](AGENTS.md) (§5.3)
  is the example. Global personal rules go in `~/.config/opencode/AGENTS.md` — keep
  them short, since they ride along in every context window you pay for.
- **`.opencode/`** in a project: `agents/`, `commands/`, `skills/`, `plugins/`
  (plural directory names).

### 5.3 Project rules — `AGENTS.md`

Read by every client (TUI, Desktop, Web) via the shared server (§1) — there's
nothing client-specific to configure here. This folder's [AGENTS.md](AGENTS.md) is
this exact content:

```markdown
# AGENTS.md

Project-level agent rules for this repo — auto-loaded on every session
regardless of client (TUI/Desktop/Web) or which agent picks it up. Nested
AGENTS.md files in subfolders load as the agent explores that area; keep this
top-level file short, since it rides along in every context window you pay for.

## Stack & commands
- Install deps: `<fill in — e.g. npm ci / uv sync / bundle install>`
- Lint: `<fill in>` (formatter:true in opencode.jsonc already auto-fixes most
  style issues via ruff/prettier/gofmt — this is only for what it can't)
- Typecheck: `<fill in>`
- Test: `<fill in>` — also what `/test` (§5) runs by default

## Conventions
- Match existing file/module layout; don't introduce a new pattern for something
  the codebase already does one way.
- Prefer the smallest diff that correctly does the job.
- Don't add new dependencies without calling it out in the response.

## Cost-minimization reminders (see §6/§7 for the full playbook)
- Stay on the default `build` agent for normal work; it's on a big-bucket model.
- Escalate to `architect` only for genuinely hard multi-file/architecture work —
  it's the smallest bucket in the lineup.
- Route screenshots, diagrams or rendered PDF pages through the `vision`
  subagent explicitly; the default agent's model can't see images (see §1/§9).
- Long logs/configs/docs go through `longread` first, not straight into `build`.
```

### 5.4 Optional-layer secrets — `.env.example`

Only for the optional layers (websearch providers, non-OpenCode clients like
Continue, §9.1); OpenCode's own Go/Copilot/ChatGPT logins are handled by
`opencode auth login` / `/connect` and stored in its credential DB (§1.1), not in
any `.env` file. Copy to `.env` (already covered by [`.gitignore`](#12-what-lives-in-this-folder),
§12) and fill in only what you actually use — this folder's
[.env.example](.env.example) is this exact content:

```bash
# Copy to .env (already listed in .gitignore, §12) and fill in only what you use.
# OpenCode's own Go/Copilot/ChatGPT logins live in its credential DB (§1.1) —
# nothing below is required for OpenCode itself to run.

# ---- Websearch provider (opencode.jsonc: "websearch": { "provider": "random" }) ----
# Only ONE is required to make the websearch tool work at all; set more than one
# and "random" (§1/§8) will retry across them on a 429 instead of failing the turn.
EXA_API_KEY=
FIRECRAWL_API_KEY=
PARALLEL_API_KEY=
TAVILY_API_KEY=

# ---- Third-party OpenAI-compatible clients only (Continue, §9.1) ----
# OpenCode's own TUI/Desktop/Web clients authenticate via `/connect`, not this
# var. Set this only if you're pointing something outside OpenCode (Continue,
# a script, etc.) at https://opencode.ai/zen/go/v1 directly.
OPENCODE_GO_API_KEY=

# ---- paper-search-mcp (§8), optional per-source keys ----
# The server itself reads these from ~/.config/paper-search-mcp/.env, not this
# file — listed here only as a reminder of what exists.
# SEMANTIC_SCHOLAR_API_KEY=
# CORE_API_KEY=
```

---

## 6. Token & quota playbook

1. **Tier the models; keep a big bucket as default.** `mimo-v2.6-flash`-class models
   provide ~30,100 est. requests per 5 h vs ~110 for `kimi-k3` — a ~274× spread.
   The full $15-cap ("spend sparingly") tier per §2 is: `kimi-k3`, `glm-5.3`,
   `qwen3.8-max`, `grok-4.7`, `grok-4.6`, `deepseek-v4-pro`, `gpt-5.6-luna`,
   `deepseek-v4-flash-vision-exp`, `mimo-v2.6-pro`, `mimo-v2.5-pro`. Every token
   that doesn't need to go through one of those is headroom saved.
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
9. **Prefer single-call subagents over multi-step pipelines.** A multi-step
   review/analysis pipeline that makes 3 separate LLM calls burns ~3× the quota of
   one well-prompted subagent call that returns the same verdict in one shot
   (see `/review` in §5, which is intentionally a single call). Reach for a
   multi-step pipeline only when you need deterministic, inspectable state
   between steps — not by default.

---

## 7. Optimizing for agentic programming

- **Match the agent to the scenario, not just the price.** §5 now ships six
  agents, each tuned to a distinct kind of work instead of one-size-fits-all:
  - `build` (default, `mimo-v2.6-flash`) — the everyday driver for normal
    feature work; huge bucket (30,100 req/5h), 0-day retention, no training.
  - `quickfix` (`glm-5.3-flash`) — one-file edits, typos, boilerplate, lint
    fixes; noticeably sharper than pure flash tiers for a small cost step-up.
  - `plan` (`glm-5.2`, read-only) — scoping and design docs before code is
    touched; generous $60 cap means you can iterate on a plan freely.
  - `architect` (`kimi-k3`) — the one agent that should feel "expensive":
    tricky multi-file bugs, architecture decisions, anything where being wrong
    costs more than the $15-cap bucket it burns.
  - `vision` (`deepseek-v4-flash-vision-exp`) — the one model Go documents
    per-image-token billing for (§2/§13); invoke it specifically when a
    screenshot, diagram or rendered PDF page is part of the task, not for
    ordinary text turns. It's the safe default, not necessarily the *only*
    image-capable route on Go — `quickfix`'s own model (`glm-5.3-flash`) is
    catalog-tagged for image input too, per §13 — but that isn't independently
    verified as working through the Go backend specifically, so this guide
    still routes images through `vision` until someone confirms otherwise.
  - `longread` (`longcat-2.0`) — pre-digesting large logs/configs/docs into a
    short brief before handing that brief to a reasoning model, so the
    expensive model never has to read the raw firehose itself.
- **Subagents for the expensive stuff.** `research`, `vision` and `longread` all
  run on their own (task-appropriate) model with their own context window, so
  `build`'s context stays small. Nesting depth is 1 by default, so plan
  orchestration accordingly — a subagent can't itself spawn nested subagents.
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

## 8. Deep research setup for professional scientists

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
the spend is model tokens, and a research session re-reads the same growing
context on every turn, so **cached-read pricing and bucket size dominate far more
than raw model quality**. A five-stage ladder, mapped onto specific scenarios
within a session and the models from §2's full table:

1. **Fan-out search-and-read** (dozens of queries, skim-level triage of what's
   worth reading closely) — `glm-5.3-flash` (6,320 req/5h, $60 cap, $0.15/$0.50
   per 1M tokens). This is the highest-volume step in any research session, so it
   belongs on the cheapest capable model.
2. **Bulk note-taking and light summarization** of the pages that clear triage —
   `mimo-v2.6-flash` (30,100 req/5h, $60 cap). Same tier as the default `build`
   agent, so it shares headroom with everyday coding work without contention.
3. **Long-document paging** — full papers, long PDFs, or a dense spec that needs
   to be read start-to-finish rather than skimmed — `longcat-2.0` (11,400 req/5h,
   $60 cap) or, when the source is peak-hour DeepSeek pricing sensitive,
   `deepseek-v4-flash` (13,000 req/5h, $30 cap; note the Peak/Off-Peak split in
   §2). Route figures, plots or scanned/rendered pages through
   `deepseek-v4-flash-vision-exp` (6,500 req/5h, $15 cap) — it's the model Go
   documents image-token billing for (§2/§13), so it's the dependable choice for
   anything with a chart or a screenshot, even though it may not be the literal
   only model on Go whose underlying catalog entry accepts images (§13).
4. **Default synthesis** — turning triaged notes into a structured brief with
   citations — `glm-5.2` (880 req/5h, $60 cap). This is what the `research`
   subagent in §5 runs by default; the $60 cap means you can synthesize several
   briefs a day without worrying about the bucket.
5. **Final hard synthesis only** — reconciling conflicting sources, writing the
   one paragraph that has to be exactly right, or a literature-review-style pass
   across everything gathered — `kimi-k3` (110 req/5h, $15 cap). This is the most
   expensive step in the ladder by a wide margin, so route only the last,
   highest-stakes pass through it, and treat DeepSeek V4.1 Flash's 4× promo
   (§2, ends **Sep 27, 2026**) as a temporary reason to lean on it instead for
   mid-tier synthesis while it lasts.

The pattern for a full research session: `paper-search`/Tavily to find, `webfetch`
to read, the `longread` or `vision` subagent (§5/§7) to pre-digest anything long
or image-heavy, Open Notebook to persist and chat with the corpus, and the
`research` subagent to synthesize — escalating to `architect` (running `kimi-k3`)
only for the final pass.

---

## 9. IDE and GUI integration (and completions)

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

  ### 9.1 Continue + your Go API key (yes, but read this first)

  Because the Go endpoint is **OpenAI-compatible**
  (`https://opencode.ai/zen/go/v1`, §2), Continue's `openai`-provider block will
  talk to it with just a base URL and the key you copied from the Console —
  no OpenCode install required for that VS Code window. `~/.continue/config.yaml`:

  ```yaml
  name: opencode-go
  version: 0.0.1
  schema: v1
  models:
    - name: Go chat — GLM-5.3-Flash
      provider: openai
      model: glm-5.3-flash
      apiBase: https://opencode.ai/zen/go/v1
      apiKey: ${{ secrets.OPENCODE_GO_API_KEY }}
      roles: [chat, edit]
    - name: Go autocomplete — MiMo-V2.6-Flash (biggest bucket, §2)
      provider: openai
      model: mimo-v2.6-flash
      apiBase: https://opencode.ai/zen/go/v1
      apiKey: ${{ secrets.OPENCODE_GO_API_KEY }}
      roles: [autocomplete]
  ```

  Three things this setup does **not** give you, so it's a different trade-off from
  running OpenCode itself, not a strict subset:

  1. **No abuse-monitoring identification.** §2 says Go expects coding-agent
     traffic with a stable `x-opencode-session` header and a recognizable user
     agent — OpenCode's own clients send this natively; Continue doesn't, and Go's
     own docs already flag one non-native client (Copilot Chat, for the same
     missing-header reason, [vscode#334186](https://github.com/microsoft/vscode/issues/334186))
     as "known problematic." Continue isn't on that list, but it isn't on the
     *verified* list either (Hermes, Claude Code, Codex, ZCode, Pi, jcode, Kilo
     Code CLI, §2) — expect the same class of risk, not a guarantee either way.
  2. **Autocomplete quality is a real caveat, not a formality.** The line right
     above this section exists for a reason: Go serves chat-style traffic, and
     `roles: [autocomplete]` wants low-latency FIM completions. It'll work, but a
     completion-oriented provider or a local Tabby/llama.cpp model will likely
     feel snappier for that specific role.
  3. **You lose everything that isn't the raw model call** — agents, the
     permissions guardrails (§5), skills, subagents, `/review` and `/plan-feature`,
     compaction, worktrees. Continue only ever talks to the model; OpenCode's
     quota-stretching tricks in §6/§7 (agent-per-scenario routing, cached-session
     reuse, single-call subagents) don't apply because there's no OpenCode server
     in the loop at all.

  In short: it works as a way to spend the *same* Go dollars from a second client,
  but it's a separate, thinner integration — not an alternative front-end onto the
  same OpenCode session/agent/permission stack described in the rest of this guide.

---

## 10. NanoClaw integration

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

## 11. Productivity tools (MCP)

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

## 12. What lives in this folder

```
README.md            this guide (v2-only, verified Sep 2026)
AGENTS.md            project-level agent rules (§5.3, auto-loaded in this folder)
opencode.jsonc       the global config from §5 — copy to ~/.config/opencode/
cli.json             terminal settings from §5.1 — copy to ~/.config/opencode/
.env.example         env vars for the optional layers (§5.4: websearch keys, etc.)
.gitignore           keeps .env, caches, and test artifacts out of git
.zcodeignore         auto-synced mirror of .gitignore for the ZCode workspace
```

Removed in this revision: `config.yaml` and `docker-compose.yml` (the LiteLLM +
Postgres + Redis layer), `tui.json` (v1 client config, replaced by `cli.json`), and
`server.py` / `mcp_server.py` / `graph.py` — the Pydantic-validated project-ops
tools and LangGraph review pipeline. They still work if you want to reintroduce
them (pin `mcp[cli]>=1.30,<2` if you do — `pip install mcp` now resolves to 2.x,
which removed `mcp.server.fastmcp`), but this revision drops them: a single-call
`architect` subagent (§5, §7) gets the same reviewed-diff outcome for roughly a
third of the LLM calls, with no extra tool-schema context cost on every session.

---

## 13. Verification log (2026-09-23)

This revision was re-audited directly against the live pages (not against a prior
draft's claims) on **2026-09-23**:

- **Go model lineup and pricing** — fetched <https://opencode.ai/docs/go/> directly
  (page stamped "Last updated: Sep 22, 2026") and cross-checked against
  <https://opencode.ai/go>. The full 29-model "current list of models," every
  per-model monthly cap, every 5-hour request estimate, the Peak/Off-Peak
  DeepSeek split, and the privacy/retention table in §2 and §13 come straight off
  that page — this closes out gaps a previous pass had marked "—" (not
  independently verified) for models like LongCat-2.0, Qwen3.7/3.8 Flash/Max,
  MiniMax M2.7/M3, MiMo-Pro variants, GLM-5.2/5.1, Grok 4.7/4.6, Qwen3.7 Max and
  GPT 5.6 Luna. **MiniMax M2.5** appears only in the **Endpoints** table now (not
  in "current list of models," usage-limits, estimated-requests, *or* Privacy) —
  a same-day re-fetch during this revision found it had already dropped out of
  the Privacy table since an earlier pass noted it there, so treat it as legacy
  and don't rely on this guide's privacy claims for it specifically. The
  **DeepSeek V4.1 Flash 4× promo and its Sep 27, 2026 end date** are stated
  verbatim on the live pricing table, not a rumor.
- **"Only vision-capable model" claim — corrected, not just re-checked.** An
  earlier pass in this revision re-fetched the live Go docs and concluded
  `deepseek-v4-flash-vision-exp` was still the only vision-capable model in the
  lineup. **That was wrong**, caught by a reader's own screenshot of the model
  picker showing GLM-5.3-Flash's capability icons expanding, on hover, to
  include an image tag. Checking further: OpenCode's model picker/console draws
  its capability icons from the same live Models.dev catalog OpenCode itself
  fetches (§1) — it isn't the Go docs page. That catalog data (cross-checked via
  a third-party Models.dev-sourced listing, `pi.dev/models/opencode-go/*`) shows
  `opencode-go/glm-5.3-flash` declared with `"input": ["text", "image"]`, while
  e.g. `hy3` and `hy4-preview` are declared `"input": ["text"]` only — so image
  tagging in the catalog is real, model-specific data, not a UI default. What
  the Go docs page actually documents is narrower and shouldn't have been read
  as "the only model that takes images": it calls out per-image-token billing
  for `deepseek-v4-flash-vision-exp` specifically and says nothing about image
  billing for any other model, which is a documentation gap, not evidence of
  incapability elsewhere. Complicating this further, a reported issue
  ([lidge-jun/opencodex#4505](https://github.com/lidge-jun/opencodex/issues/4505))
  describes the Go backend maintaining its own `noVisionModels` denylist that
  overrides the catalog's declared image support for at least
  `deepseek-v4.1-flash` — so catalog-tagged image support and actual Go-backend
  image handling can diverge in the other direction too. Net effect: this guide
  no longer claims Vision Exp is the only image-capable model on Go (§1/§5/§7/§8
  corrected above), but it also doesn't claim GLM-5.3-Flash's image input is
  confirmed working through the Go endpoint specifically — that needs a real
  test send, not just a catalog icon or a docs page, before you'd rely on it for
  anything that has to work.
- **v2 product surface** — refetched <https://opencode.ai/v2/docs> directly: the
  intro page confirms the shared install flow (`curl .../v2/install`, `npm i -g
  @opencode/cli`, etc.), Desktop/Web/Docker instructions, and that OpenCode Go is
  presented as the recommended low-cost provider. The docs' left-nav (config,
  agents, models, skills, commands, plugins, providers, websearch, network,
  snapshots, compaction, formatters, references, attachments, tools, mcp-servers,
  permissions, policies, instructions, sharing, warming) matches what earlier
  passes described; **Sharing** and **Instructions** were not independently
  re-opened this pass — treat those two specific claims (no session sharing yet;
  `instructions` entries accepted but unloaded) as carried over, not re-verified.
- **⚠ Version discrepancy — worth running `opencode --version` yourself.** The
  live v2 docs intro page's CLI/Desktop download links currently resolve to build
  **2.0.6** (e.g. `.../files/bin/2.0.6/opencode-darwin-arm64.zip`), not 2.0.14.
  Separately, <https://opencode.ai/download> lists installers via `curl`,
  `npm`, `brew install anomalyco/tap/opencode-v2`, and `paru/yay -S opencode-beta`
  for the CLI, and `brew install --cask opencode-desktop` plus direct "stable"
  download links for Desktop — but that page's Desktop section only shows macOS
  (Apple Silicon/Intel), Windows (x64), and Linux .deb/.rpm; it did **not** show a
  Windows ARM64 build or a Linux AppImage in this pass's fetch, where an earlier
  draft of this guide claimed both existed. Reconcile the "v2.0.14" figure (this
  revision's title no longer asserts a specific version number for that reason)
  against `opencode --version` and the AUR package pages before relying on it; the
  discrepancy could reflect a lagging CDN cache on the docs page, a beta/dev
  channel AUR build running ahead of the stable download page, or simply that both
  pages had moved on again by the time you're reading this.
  **Independently reconfirmed 2026-09-23:** a direct re-fetch of
  `opencode.ai/v2/docs` still resolves every CLI and Desktop binary link to
  build **2.0.6** — this is real and reproducible, not a one-off cache glitch.
  That same intro page, however, *does* list a full platform matrix straight
  from `/v2/docs` itself (macOS AS/Intel, Windows x64 **and** ARM64, Linux
  glibc/musl x64/ARM64, and Desktop builds including Linux **AppImage** for
  both x64 and ARM64) — so if `opencode.ai/download` is genuinely narrower, as
  this guide's fetch found, that's an inconsistency *between two of Anomaly's
  own pages*, not just a stale draft in this guide. Practical takeaway: for any
  platform `opencode.ai/download` seems to be missing, check
  `opencode.ai/v2/docs` before concluding the build doesn't exist. See §15.2.
- **Open issues used as caveats** — #48330 (Copilot legacy-plan request drain),
  #49847 (ChatGPT-OAuth requests sent with the Zen key), #46365 (usage accounting
  discrepancy), microsoft/vscode#334186 (missing session header) — these were
  **not** re-opened this pass; treat their "open"/"stale" status as of whenever
  they were last checked, not as of 2026-09-23.
- **Ecosystem** — anthropics/skills (incl. docx/pptx/xlsx/pdf), nanocoai/nanoclaw
  (containers, chat apps, `/add-opencode`, Anthropic SDK + base-URL override),
  lfnovo/open-notebook + Epochal-dev/open-notebook-mcp (39 tools), openags/
  paper-search-mcp (MIT; arXiv/PubMed/bioRxiv/medRxiv/Europe PMC/OpenAlex…),
  GitHub remote MCP (`api.githubcopilot.com/mcp/`), Linear (`mcp.linear.app/mcp`),
  Notion (hosted remote MCP), Google Calendar MCP (Developer Preview), and Zed's
  edit-prediction keys (`provider`, `prompt_format`: `infer`/`zeta2`/`zeta2_1`) —
  **not** re-opened this pass; carried over from the prior audit.

**Not independently re-verified this pass:** the exact v2 `watcher` config shape;
`agents.title`/`summary` model overrides; the Google Calendar MCP endpoint path;
and everything under "Ecosystem" and "Open issues" above. Treat the Go docs page
and `/models` as the source of truth for model IDs/caps, and <https://opencode.ai/v2/docs>
as the source of truth for product behavior, since both move fast.

**Removed in this revision:** the "Optional: Pydantic + LangGraph MCP servers"
section and its accompanying `server.py`/`mcp_server.py`/`graph.py` files (§12) —
per request, all Pydantic/LangGraph content has been stripped from this guide.

---

## 14. Sources (fetched 2026-09-23)

- **v2 docs:** <https://opencode.ai/v2/docs> (refetched directly this pass) ·
  `/config` · `/agents` · `/models` · `/permissions` · `/tools` · `/mcp-servers` ·
  `/skills` · `/commands` · `/compaction` · `/formatters` · `/snapshots` ·
  `/warming` · `/websearch` · `/instructions` · `/policies` · `/sharing` ·
  `/migrate-v1` · `/troubleshooting` · `/cli` · `/cli/tui` · `/cli/config` ·
  `/cli/web` · `/cli/acp` · `/cli/keybinds` — only the intro page was refetched
  and read directly this pass; the sub-pages listed here were carried over from
  an earlier pass and were not individually re-opened.
- **Go:** <https://opencode.ai/docs/go/> and <https://opencode.ai/go> (both
  refetched directly this pass — this is the primary source for §2 and §13).
- **Console / Go (carried over, not re-opened this pass):**
  <https://opencode.ai/v2/docs/console/go> ·
  <https://opencode.ai/v2/docs/console/usage> ·
  <https://opencode.ai/v2/docs/console/budgets> · <https://opencode.ai/console>
- **Schemas (carried over):** <https://opencode.ai/config.json> ·
  <https://opencode.ai/v2/cli.json>
- **Download / packaging:** <https://opencode.ai/download> (refetched directly
  this pass — see the version-discrepancy note in §13) ·
  <https://github.com/anomalyco/opencode/releases> ·
  <https://aur.archlinux.org/packages/opencode-beta> ·
  <https://aur.archlinux.org/packages/opencode-desktop-bin> ·
  <https://formulae.brew.sh/cask/opencode-desktop> — the AUR/GitHub-releases/
  Homebrew-cask links were carried over, not re-opened, this pass.
- **Issues (carried over, not re-opened):**
  [#48330](https://github.com/anomalyco/opencode/issues/48330) ·
  [#49847](https://github.com/anomalyco/opencode/issues/49847) ·
  [#46365](https://github.com/anomalyco/opencode/issues/46365) ·
  [microsoft/vscode#334186](https://github.com/microsoft/vscode/issues/334186)
- **Integrations (carried over, not re-opened):**
  [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) ·
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

---

## 15. Independent audit findings (external pass, 2026-09-23)

This section documents a second, independent verification pass done from
outside this guide's own authorship — re-fetching Anomaly's live pages rather
than trusting this guide's earlier self-reported citations. It confirms most of
the guide's numbers, finds the guide's own flagged uncertainties are real, and
surfaces a couple of things worth tightening.

### 15.1 Pricing: a genuine inconsistency on Anomaly's own pages, not this guide

The two pages fetched live this pass disagree with each other:

- `opencode.ai/go` and `opencode.ai/v2/docs` (both re-fetched directly) state a
  flat **"$10/month"** with no introductory-price language — this is what this
  guide's headline `$10/mo` reflects.
- `opencode.ai/docs/go` (the detailed Go page, and several of its localized
  variants) states **"$5 for your first month, then $10/month."**

Since Anomaly's own landing page and detailed docs page don't agree, this
guide's flat "$10/mo" isn't wrong, but it also isn't the complete picture for a
first-time subscriber — worth a one-line mention that a first-month discount
may apply depending on which sign-up path is used.

### 15.2 Version numbers: confirmed real, not a one-off

Directly re-fetching `opencode.ai/v2/docs` reproduced the exact discrepancy
this guide flagged: every CLI and Desktop download link on that page currently
resolves to build **2.0.6**. This guide's decision to stop asserting "2.0.14"
in its own title is the right call — `opencode --version` remains the only
reliable source for the number actually running on a given machine.
Separately, that same intro page turned out to list a **fuller** platform
matrix (Windows ARM64, Linux AppImage for both x64/ARM64, ARM64 `.deb`/`.rpm`)
than this guide's fetch of `opencode.ai/download` found — see the note added at
§3.

### 15.3 Go model table: spot-checked and accurate

A line-by-line spot-check of roughly 15 rows in this guide's §2 pricing/request
table against a fresh fetch of `opencode.ai/docs/go` found **no numeric
discrepancies** — request-per-5-hour estimates, monthly caps, and the DeepSeek
V4.1 Flash promotional 4× figures (26,000 req/5h, $60 cap, ending Sep 27, 2026)
all matched exactly. The "current list of models" bullet on the live docs page
has **30** entries (this guide's 29-row table accounts for all of them once the
combined Muse Spark 1.3/1.2 row is split into two), and **MiniMax M2.5** is
confirmed present in the token-price and endpoints tables but genuinely absent
from both the "current list of models" bullet *and* the privacy table — this
guide's original wording ("still live on the endpoints/privacy pages") overstated
that slightly, since M2.5 isn't actually on the privacy page; corrected at §2.

### 15.4 v1/v2 coexistence: current docs support this guide, older cached copies don't

This guide's central framing — that v1 and v2 share the `opencode` command and
aren't installed side-by-side — matches a direct, live re-fetch of
`opencode.ai/v2/docs` today. However, an older indexed/cached snapshot of what
appears to be the same docs page (surfaced via general web search rather than a
direct fetch) described OpenCode 2 running as a separate `opencode2` binary
installable alongside v1. This is very likely just an artifact of the docs
having been rewritten as v2 moved from early beta toward its current state, but
it's a good illustration of why this guide is right to keep insisting on
re-checking the *live* pages rather than trusting any single snapshot — this
one included.

### 15.5 Citations spot-checked as genuine

`microsoft/vscode#334186`, cited by this guide as an open request for automatic
session-header support in GitHub Copilot Chat, is in fact cited for exactly
that purpose directly in Anomaly's own live `opencode.ai/docs/go` page (in its
"Known Problematic Clients" table) — this is a real, correctly-used citation,
not a fabricated one. The underlying repository `anomalyco/opencode` was
confirmed to be a real, actively developed project with a high commit/PR
volume consistent with this guide's "moves fast" framing.

### 15.6 Not independently re-verified in this pass

In the time available, this pass did **not** independently re-open: the
GitHub issue numbers cited for the Copilot request-drain, ChatGPT/Zen-key, and
usage-accounting bugs (`#48330`, `#49847`, `#46365`); the `lidge-jun/opencodex`
vision-denylist issue; the AUR package pages; the Console/budgets API
endpoints; or anything under this guide's own "Ecosystem" list. Treat those the
same way this guide already asks you to — as carried-over claims worth
re-checking yourself against the live source before relying on them, not as
newly confirmed by this pass.

