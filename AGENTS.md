# Agent instructions

## Model routing

- Routine edits, grep/search, running tests, small refactors: default
  (`opencode-go/deepseek-v4-flash`) is intentional. Don't ask to switch
  models for these.
- Architecture decisions, multi-file refactors, or anything you're not
  confident about: hand off to the `architect` agent (or tell the user to
  switch with Tab) rather than guessing on a cheap model.

## Tool usage

- For "review my changes" / "review this diff" style requests, delegate to
  the `code-review` subagent. It runs a LangGraph plan -> analyze ->
  summarize workflow through the `langgraph-agent` MCP tool and returns a
  structured verdict (`approve` / `request_changes` / `needs_discussion`)
  plus findings. Don't try to review large diffs yourself line-by-line if
  this subagent is available.
- For running the test suite or querying service metrics, delegate to the
  `project-ops` subagent. It uses the `pydantic-tools` MCP server, whose
  inputs and outputs are schema-validated -- trust its structured result
  over free-text guesses about pass/fail counts.
- Never fabricate test results, metrics values, or review verdicts. If a
  tool call fails, say so and show the error.

## Safety

- Destructive shell commands (`rm -rf`, force-pushes, dropping databases)
  are denied or require explicit approval by permission config. Don't try
  to route around that by chaining commands.
- Don't write secrets (API keys, tokens) into source files. All credentials
  in this project are supplied via environment variables (see `.env.example`).
