"""
core/llm.py
─────────────────────────────────────────────────────────────
One function: call_llm()

It reads the model string from .env and automatically picks
the right provider — Gemini or Claude.

The story: think of this as a universal plug adapter.
Your agents don't care whether the socket is Gemini or Claude.
They just plug in via call_llm() and get text back.

Supported model prefixes:
  gemini-*  → Google Generative AI SDK
  claude-*  → Anthropic SDK
  anything else → raises ValueError so you know fast

Usage in any agent:
  from core.llm import call_llm
  text = call_llm(
      model=os.getenv("ROUTER_MODEL", "gemini-2.5-flash"),
      system="You are...",
      user="Do this...",
      max_tokens=256,
  )
"""

from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)


def call_llm(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 2048,
) -> str:
    """
    Call Claude or Gemini depending on the model string.
    Returns the text response as a plain string.
    Raises on hard errors — agents should catch and add to state.errors.
    """
    if model.startswith("gemini"):
        return _call_gemini(model, system, user, max_tokens)
    elif model.startswith("claude"):
        return _call_claude(model, system, user, max_tokens)
    else:
        raise ValueError(
            f"Unknown model prefix '{model}'. "
            "Use 'gemini-...' or 'claude-...' in your .env file."
        )


# ── Gemini ────────────────────────────────────────────────────────────

def _call_gemini(model: str, system: str, user: str, max_tokens: int) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai not installed. Run: pip install google-generativeai"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    genai.configure(api_key=api_key)

    gemini_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,
        ),
    )

    response = gemini_model.generate_content(user)
    text = response.text.strip()
    logger.debug("[LLM/Gemini] %s → %d chars", model, len(text))
    return text


# ── Claude ────────────────────────────────────────────────────────────

def _call_claude(model: str, system: str, user: str, max_tokens: int) -> str:
    from anthropic import Anthropic

    client = Anthropic()  # reads ANTHROPIC_API_KEY from env automatically
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = response.content[0].text
    logger.debug("[LLM/Claude] %s → %d chars", model, len(text))
    return text