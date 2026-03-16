"""
core/graph.py
─────────────────────────────────────────────────────────────
The Brain — wires all agents into a directed graph.

Flows:
  Standard:  START → router → specialist → END
  Research:  START → router → search_enricher → strategist → END

Think of it like a train network:
  - router          = central station (reads the destination)
  - search_enricher = a layover where the cargo gets enriched
  - specialist agents = final destinations
  - state           = the cargo travelling every stop

Adding a new agent = add a node + add a branch in route_task().
That's it. No other files need to change.
"""

from __future__ import annotations
import logging

from langgraph.graph import StateGraph, START, END

from core.state import GGState
from agents.router_agent import router_agent
from agents.search_enricher import search_enricher_agent
from agents.strategist import strategist_agent
from agents.prompt_engineer import prompt_engineer_agent
from agents.coder import coder_agent

logger = logging.getLogger(__name__)


# ── Routing logic (pure function — easy to unit test) ─────────────────

def route_after_router(state: GGState) -> str:
    """
    First branch: immediately after the router.
    Decides whether we need enrichment before the specialist.
    """
    routes = {
        "strategy":        "strategist",
        "prompt_engineer": "prompt_engineer",
        "code":            "coder",
        "search":          "search_enricher",  # ← goes to enricher first
        "unknown":         END,
    }
    destination = routes.get(state.task_type, END)
    logger.info("[Graph] router → %s", destination)
    return destination


# ── Build the graph ───────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(GGState)

    # ── Nodes ─────────────────────────────────────────────────────────
    builder.add_node("router",          router_agent)
    builder.add_node("search_enricher", search_enricher_agent)
    builder.add_node("strategist",      strategist_agent)
    builder.add_node("prompt_engineer", prompt_engineer_agent)
    builder.add_node("coder",           coder_agent)

    # ── Edges ─────────────────────────────────────────────────────────
    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "strategist":      "strategist",
            "prompt_engineer": "prompt_engineer",
            "coder":           "coder",
            "search_enricher": "search_enricher",
            END:               END,
        },
    )

    # search_enricher always hands off to strategist to write the report
    builder.add_edge("search_enricher", "strategist")

    # Specialist agents all terminate
    builder.add_edge("strategist",      END)
    builder.add_edge("prompt_engineer", END)
    builder.add_edge("coder",           END)

    return builder.compile()


# ── Singleton — import this in main.py and tests ──────────────────────
graph = build_graph()
