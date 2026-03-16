"""
core/state.py
─────────────────────────────────────────────────────────────
The single source of truth for the GG AI Factory.

Every agent reads from GGState. Every agent writes to GGState.
Nothing passes between nodes except this dict.

Rule: if a field isn't in here, it doesn't exist in the system.
"""

from __future__ import annotations
from typing import List, Optional
from typing_extensions import TypedDict


class GGState(TypedDict, total=False):
    """
    total=False → all keys are optional at construction time.
    LangGraph builds state incrementally — each node adds its fields.
    If total=True, Python would demand ALL keys up front. That breaks
    the pattern where router sets task_type and strategist sets final_output.
    """

    # ── INPUT ─────────────────────────────────────────────────────────
    user_input: str             # Raw task string from the user
    session_id: str             # Short UUID for this run (used in filenames)
    output_format: str          # "markdown" | "html" | "pdf" | "json"

    # ── ROUTING (written by router_agent) ─────────────────────────────
    task_type: str              # What the router classified this as
                                # e.g. "strategy", "offer", "html", "audit", "unknown"
    routing_reason: str         # Why the router chose this route (for logging)
    agent_trail: List[str]      # Breadcrumb trail e.g. ["router", "strategist"]
    current_agent: str          # Which agent is currently executing

    # ── AGENT OUTPUTS (each agent writes to its own key) ──────────────
    business_strategy: Optional[str]    # Output of strategist agent
    grand_slam_offer: Optional[str]     # Output of offer_builder agent
    html_output: Optional[str]          # Output of html_coder agent
    audit_output: Optional[str]         # Output of google_business_audit agent
    final_output: Optional[str]         # The assembled final result for the user

    # ── CONVERSATION HISTORY ──────────────────────────────────────────
    messages: List[dict]        # Full LangChain message history
                                # Format: [{"role": "user", "content": "..."}]

    # ── META / ERROR TRACKING ─────────────────────────────────────────
    errors: List[str]           # Any errors caught during execution
    has_errors: bool            # Quick flag — avoids iterating errors list
    iteration_count: int        # Guard against infinite loops in the graph