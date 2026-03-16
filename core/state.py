"""
core/state.py
─────────────────────────────────────────────────────────────
The State is the "shared whiteboard" every agent reads from
and writes to as the task flows through the graph.

Think of it like a baton in a relay race — each runner (agent)
picks it up, adds their contribution, and passes it forward.
"""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


# ── Task types the router can classify ───────────────────────────────
TASK_TYPES = {
    "strategy":         "Write a proposal / strategy / offer",
    "prompt_engineer":  "Optimise or build a prompt for another AI",
    "code":             "Generate HTML/CSS/JS boilerplate",
    "search":           "Research a topic and summarise",
    "unknown":          "Cannot classify — escalate to human",
}


class GGState(BaseModel):
    """
    Everything the system remembers about a single run.

    Layers:
      1. INPUT   — what the user sent us
      2. ROUTING — where the router decided to send it
      3. CONTEXT — data collected along the way (search results, etc.)
      4. OUTPUT  — the final deliverable
      5. META    — bookkeeping (retries, errors, audit trail)
    """

    # ── 1. INPUT ──────────────────────────────────────────────────────
    user_input: str = Field(..., description="Raw request from the user")
    session_id: str = Field(default="", description="Unique run identifier")

    # ── 2. ROUTING ────────────────────────────────────────────────────
    task_type: str = Field(
        default="unknown",
        description=f"One of: {list(TASK_TYPES.keys())}",
    )
    routing_reason: str = Field(
        default="",
        description="Why the router chose this task_type (for debugging)",
    )

    # ── 3. CONTEXT ────────────────────────────────────────────────────
    search_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Results gathered by the web_search tool",
    )
    enriched_context: str = Field(
        default="",
        description="Processed / summarised context ready for downstream agents",
    )

    # ── 4. OUTPUT ─────────────────────────────────────────────────────
    draft_output: str = Field(
        default="",
        description="First pass from the specialist agent",
    )
    final_output: str = Field(
        default="",
        description="Polished, user-facing deliverable",
    )
    output_format: str = Field(
        default="markdown",
        description="markdown | html | pdf | json",
    )

    # ── 5. META ───────────────────────────────────────────────────────
    errors: list[str] = Field(default_factory=list)
    agent_trail: list[str] = Field(
        default_factory=list,
        description="Which agents ran, in order — full audit trail",
    )
    retry_count: int = Field(default=0)

    # ── Helpers ───────────────────────────────────────────────────────
    def log_agent(self, name: str) -> None:
        """Call at the start of every agent to record execution order."""
        self.agent_trail.append(name)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
