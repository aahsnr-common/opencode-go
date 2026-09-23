# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.6.0",
#   "pydantic>=2.7",
#   "langgraph>=0.6",
#   "langchain-openai>=0.3",
#   "langchain-core>=0.4",
# ]
# ///
"""
langgraph-agent MCP server.

Wraps the LangGraph plan -> analyze -> summarize workflow (graph.py) as a
single MCP tool, `run_code_review`. Input and output are Pydantic models,
so OpenCode's `code-review` subagent gets a typed JSON Schema for the tool
and a structured, validated result -- not a wall of text to reparse.

Run directly with: uv run mcp_server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from graph import ReviewState, compiled_graph

mcp = FastMCP("langgraph-agent")


class CodeReviewRequest(BaseModel):
    diff: str = Field(..., description="Unified diff, or a code snippet, to review")


class CodeReviewResult(BaseModel):
    plan: str
    findings: list[str]
    verdict: str
    summary: str


@mcp.tool()
async def run_code_review(request: CodeReviewRequest) -> CodeReviewResult:
    """Run the LangGraph code-review workflow (plan -> analyze -> summarize) on
    a diff and return a structured verdict (approve / request_changes /
    needs_discussion), the findings that led to it, and a short summary."""
    result_state = await compiled_graph.ainvoke(ReviewState(diff=request.diff))
    return CodeReviewResult(**result_state)


if __name__ == "__main__":
    mcp.run(transport="stdio")
