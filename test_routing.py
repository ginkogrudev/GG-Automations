"""
tests/test_routing.py
─────────────────────────────────────────────────────────────
Tests for the routing logic in core/graph.py.

The routing function is a pure function — it takes a state and
returns a string. No mocking, no API keys, ultra-fast.

Run with: pytest tests/test_routing.py -v
"""

import pytest
from core.state import GGState
from core.graph import route_after_router
from langgraph.graph import END


@pytest.mark.parametrize("task_type, expected_node", [
    ("strategy",        "strategist"),
    ("prompt_engineer", "prompt_engineer"),
    ("code",            "coder"),
    ("search",          "search_enricher"),
    ("unknown",         END),
    ("garbage_value",   END),  # anything unknown → END (safe default)
])
def test_route_after_router(task_type, expected_node):
    state = GGState(user_input="test", task_type=task_type)
    result = route_after_router(state)
    assert result == expected_node, (
        f"task_type='{task_type}' should route to '{expected_node}', got '{result}'"
    )


def test_search_routes_to_enricher_not_strategist():
    """Regression: search must go through enrichment, not skip it."""
    state = GGState(user_input="What are the latest AI trends?", task_type="search")
    assert route_after_router(state) == "search_enricher"
    assert route_after_router(state) != "strategist"
