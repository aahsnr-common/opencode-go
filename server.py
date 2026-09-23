# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.30,<2",
#   "pydantic>=2.7",
#   "pytest>=8.0",
#   "pytest-json-report>=1.5",
# ]
# ///
"""
pydantic-tools MCP server.

Exposes strictly-typed project-ops tools to OpenCode over the Model Context
Protocol. Every tool's input and output is a Pydantic v2 model, so:

  - OpenCode's model gets a precise JSON Schema for each tool (generated
    automatically from the Pydantic model by FastMCP).
  - Malformed calls fail fast with a structured validation error instead of
    silently doing the wrong thing.
  - Results come back as validated, structured data -- not prose the model
    has to reinterpret.

NOTE: the MCP Python SDK 2.x removed `mcp.server.fastmcp`; this file targets
the maintained 1.x line (latest 1.30.0), hence the "<2" pin above.

Run directly with: uv run server.py
(the PEP 723 block above pins the ephemeral env's dependencies)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("pydantic-tools")


# ---------------------------------------------------------------------------
# run_tests
# ---------------------------------------------------------------------------
class RunTestsRequest(BaseModel):
    path: str = Field(default=".", description="Path or test node id to run, e.g. 'tests/' or 'tests/test_x.py::test_y'")
    marker: str | None = Field(default=None, description="Optional pytest -m marker expression")


class TestFailure(BaseModel):
    nodeid: str
    message: str


class RunTestsResult(BaseModel):
    ok: bool
    passed: int
    failed: int
    errors: int
    duration_seconds: float
    failures: list[TestFailure] = Field(default_factory=list)


@mcp.tool()
def run_tests(request: RunTestsRequest) -> RunTestsResult:
    """Run pytest with --json-report and return a structured, validated summary
    (pass/fail counts and per-test failure messages) instead of raw terminal output."""
    report_path = Path(".pytest-mcp-report.json")
    cmd = [
        "python3", "-m", "pytest", request.path,
        "--json-report", f"--json-report-file={report_path}",
        "-q",
    ]
    if request.marker:
        cmd += ["-m", request.marker]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if not report_path.exists():
        return RunTestsResult(
            ok=False, passed=0, failed=0, errors=1, duration_seconds=0.0,
            failures=[TestFailure(
                nodeid="pytest",
                message=(proc.stderr or proc.stdout or "pytest-json-report plugin not installed, or the run crashed")[:2000],
            )],
        )

    data = json.loads(report_path.read_text())
    summary = data.get("summary", {})
    failures = [
        TestFailure(
            nodeid=t["nodeid"],
            message=str(t.get("call", {}).get("longrepr", "failed"))[:2000],
        )
        for t in data.get("tests", [])
        if t.get("outcome") == "failed"
    ]
    report_path.unlink(missing_ok=True)

    failed = summary.get("failed", 0)
    errors = summary.get("error", 0)
    return RunTestsResult(
        ok=(failed == 0 and errors == 0),
        passed=summary.get("passed", 0),
        failed=failed,
        errors=errors,
        duration_seconds=data.get("duration", 0.0),
        failures=failures,
    )


# ---------------------------------------------------------------------------
# query_metrics
# ---------------------------------------------------------------------------
class QueryMetricsRequest(BaseModel):
    metric: Literal["latency_p95_ms", "error_rate", "requests_per_minute"]
    service: str = Field(..., description="Service name as registered in the metrics backend")
    window_minutes: int = Field(default=15, ge=1, le=1440)


class QueryMetricsResult(BaseModel):
    metric: str
    service: str
    window_minutes: int
    value: float
    unit: str


@mcp.tool()
def query_metrics(request: QueryMetricsRequest) -> QueryMetricsResult:
    """Query an internal metrics backend for a service. Replace the body with a
    real client (Prometheus/Datadog/etc.) -- this stub returns a deterministic
    placeholder so the tool is runnable out of the box, and MUST stay disabled
    in agents until it is wired to a real backend."""
    unit_map = {
        "latency_p95_ms": "ms",
        "error_rate": "%",
        "requests_per_minute": "rpm",
    }
    # TODO: replace with a real query, e.g. an httpx call to your Prometheus
    # HTTP API or Datadog API, still returning a QueryMetricsResult.
    placeholder_value = 42.0
    return QueryMetricsResult(
        metric=request.metric,
        service=request.service,
        window_minutes=request.window_minutes,
        value=placeholder_value,
        unit=unit_map[request.metric],
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
