"""
agents/search_enricher.py
─────────────────────────────────────────────────────────────
The Research Assistant — sits between the router and the strategist
when the task_type is "search".

Pipeline for search tasks:
  router → search_enricher → strategist → END
              ↑
           (this file)

It does two things:
  1. Calls the web_search tool to gather raw results
  2. Asks Claude to synthesise them into a clean context block
     that the strategist can consume without noise

Think of it as a librarian who fetches books AND highlights
the relevant pages before handing them to the analyst.
"""

from __future__ import annotations
import os
import logging

from anthropic import Anthropic
from core.state import GGState
from tools.web_search import search, format_results_as_context

logger = logging.getLogger(__name__)

# ── Synthesis prompt (inline — short enough not to need its own file) ──
_SYNTHESIS_SYSTEM = """\
You are a research analyst. You receive raw web search results and
distil them into a concise, factual context block (max 600 words).

Rules:
- Bullet points only — no prose paragraphs
- Lead each bullet with the source domain in brackets: [source.com]
- Drop any result that is clearly irrelevant or low quality
- End with a "Key Takeaways" section (3-5 bullets)
- Do NOT include URLs in the body — only in the source tag
"""


def search_enricher_agent(state: GGState) -> GGState:
    """
    LangGraph node: fetches web results and synthesises them into
    state.enriched_context so the next agent gets clean input.

    Reads:   state.user_input
    Writes:  state.search_results, state.enriched_context
    """
    state.log_agent("search_enricher_agent")
    logger.info("[SearchEnricher] Searching for: %s", state.user_input[:80])

    # ── Step 1: Fetch raw results ──────────────────────────────────────
    results = search(state.user_input, max_results=6)
    state.search_results = results

    if not results:
        logger.warning("[SearchEnricher] No results — passing empty context downstream")
        state.enriched_context = "No web search results were found for this query."
        return state

    raw_context = format_results_as_context(results)
    logger.info("[SearchEnricher] Got %d results, synthesising...", len(results))

    # ── Step 2: Synthesise with Claude ────────────────────────────────
    client = Anthropic()
    model = os.getenv("ENRICHER_MODEL", "claude-haiku-4-5")  # fast + cheap for this step

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=_SYNTHESIS_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Research query: {state.user_input}\n\n"
                        f"Raw search results:\n{raw_context}"
                    ),
                }
            ],
        )
        state.enriched_context = response.content[0].text
        logger.info("[SearchEnricher] Synthesis complete.")

    except Exception as e:
        logger.error("[SearchEnricher] Synthesis error: %s", e)
        # Fallback: use raw results rather than crashing
        state.enriched_context = raw_context
        state.add_error(f"SearchEnricher synthesis error: {e}")

    return state
