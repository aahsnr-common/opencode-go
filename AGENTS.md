# Agent instructions

## Model routing

- Routine edits, grep/search, running tests, small refactors: the default
  (`opencode-go/mimo-v2.6-flash`) is intentional — it draws on one of Go's
  largest per-model usage buckets. Don't ask to switch models for these.
- Architecture decisions, multi-file refactors, or anything you're not
  confident about: hand off to the `architect` agent (`opencode-go/kimi-k3`,
  a $15-cap model — use short, targeted sessions), or tell the user to switch
  with Shift+Tab / `/agents`.
- Long research: delegate to the `research` subagent (`opencode-go/glm-5.2`).

## Tool usage

- For "review my changes" / "review this diff" requests, delegate to the
  `code-review` subagent. It runs a LangGraph plan -> analyze -> summarize
  workflow through the `langgraph-agent` MCP tool and returns a structured
  verdict (`approve` / `request_changes` / `needs_discussion`) plus findings.
  (Requires the `langgraph-agent` MCP server, which ships disabled — enable it
  per project first.) Don't review large diffs yourself line-by-line if this
  subagent is available.
- For running the test suite or querying service metrics, delegate to the
  `project-ops` subagent. It uses the `pydantic-tools` MCP server, whose
  inputs and outputs are schema-validated — trust its structured result over
  free-text guesses about pass/fail counts. Note its `query_metrics` tool
  returns placeholder data until a real backend is wired in.
- Never fabricate test results, metrics values, or review verdicts. If a tool
  call fails, say so and show the error.

## Safety

- Shell commands ask by default; `rm -rf *` is hard-denied by the global
  permissions array (OpenCode v2 `permissions`, not v1 `permission`). Using
  the `subagent` tool is the supported way to parallelize; don't try to route
  around permission rules by chaining commands.
- Reads of `.env` files and access outside the project ask for approval by
  default — leave those defaults in place.
- Don't write secrets (API keys, tokens) into source files. All credentials
  are supplied via environment variables (see `.env.example`) or via
  `/connect` for providers (stored in OpenCode's credential table).
