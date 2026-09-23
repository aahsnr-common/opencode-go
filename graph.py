"""
A small LangGraph workflow: plan -> analyze -> summarize.

State is a Pydantic model (langgraph supports Pydantic v2 state schemas
natively), and the LLM used at each node is an OpenAI-compatible client
pointed at the LiteLLM gateway rather than a provider SDK directly -- so
these calls get the same budgeting, fallback, and observability as every
other model call in the stack.

Imported by mcp_server.py; not meant to be run directly.
"""

from __future__ import annotations

import os
from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "sk-litellm-virtual-opencode")
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "claude-sonnet-4-5")

llm = ChatOpenAI(
    model=LITELLM_MODEL,
    base_url=f"{LITELLM_BASE_URL}/v1",
    api_key=LITELLM_API_KEY,
    temperature=0.1,
)


class ReviewState(BaseModel):
    diff: str
    plan: str = ""
    findings: list[str] = Field(default_factory=list)
    verdict: Literal["approve", "request_changes", "needs_discussion"] = "needs_discussion"
    summary: str = ""


def plan_node(state: ReviewState) -> dict:
    resp = llm.invoke(
        "You are a senior staff engineer. Outline a short review plan "
        "(3-5 bullet points: what to check and why) for the following diff:\n\n"
        f"{state.diff}"
    )
    return {"plan": resp.content}


def analyze_node(state: ReviewState) -> dict:
    resp = llm.invoke(
        f"Following this review plan:\n{state.plan}\n\n"
        "Review this diff and list concrete findings, one per line, covering "
        f"correctness, security, and style. Diff:\n\n{state.diff}"
    )
    findings = [
        line.lstrip("-* ").strip()
        for line in resp.content.splitlines()
        if line.strip()
    ]
    return {"findings": findings}


def summarize_node(state: ReviewState) -> dict:
    resp = llm.invoke(
        "Given these findings:\n"
        + "\n".join(f"- {f}" for f in state.findings)
        + "\n\nRespond with exactly one verdict word on the first line -- "
        "approve, request_changes, or needs_discussion -- followed by a "
        "two-sentence summary on the next line."
    )
    text = resp.content.strip()
    first_line = text.splitlines()[0].strip().lower() if text else ""
    verdict: Literal["approve", "request_changes", "needs_discussion"] = "needs_discussion"
    if "approve" in first_line:
        verdict = "approve"
    elif "request_changes" in first_line or "request changes" in first_line:
        verdict = "request_changes"
    return {"verdict": verdict, "summary": text}


_builder = StateGraph(ReviewState)
_builder.add_node("plan", plan_node)
_builder.add_node("analyze", analyze_node)
_builder.add_node("summarize", summarize_node)
_builder.add_edge(START, "plan")
_builder.add_edge("plan", "analyze")
_builder.add_edge("analyze", "summarize")
_builder.add_edge("summarize", END)

compiled_graph = _builder.compile()
