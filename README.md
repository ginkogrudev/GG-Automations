# GG AI Factory 🏭

> A Python multi-agent system for GG Solutions — built for separation of concerns,
> clean prompt management, and easy agent extension.

---

## Architecture at a glance

```
User request
     │
     ▼
 router_agent          ← classifies the intent
     │
     ├── "strategy"    → strategist_agent
     ├── "code"        → coder_agent
     ├── "prompt_eng"  → prompt_engineer_agent
     ├── "search"      → search_enricher → strategist_agent
     └── "unknown"     → END (escalate to human)
```

Every agent reads from and writes to a shared `GGState` object — the single
baton that flows through the entire pipeline.

---

## Project structure

```
gg_ai_factory/
│
├── core/
│   ├── state.py          # GGState — the shared memory object
│   └── graph.py          # LangGraph wiring — the ONLY place routing logic lives
│
├── agents/               # One file per agent — each does ONE thing
│   ├── router_agent.py   # Classifies input → task_type
│   ├── search_enricher.py# Fetches + synthesises web results
│   ├── strategist.py     # Writes proposals & strategies
│   ├── prompt_engineer.py# Builds & improves AI prompts
│   └── coder.py          # Generates HTML/CSS/JS
│
├── prompts/              # All prompt strings — separated from agent logic
│   ├── router.py
│   ├── strategist.py
│   ├── prompt_engineer.py
│   └── coder.py
│
├── tools/                # Reusable skills (not agent-specific)
│   ├── web_search.py     # Tavily search wrapper
│   └── doc_generator.py  # Save output as .md / .html / .pdf
│
├── tests/
│   ├── test_state.py
│   ├── test_routing.py
│   └── test_doc_generator.py
│
├── .env.example
├── requirements.txt
└── main.py               # CLI entry point
```

---

## Quick start

```bash
# 1. Clone & enter
cd gg_ai_factory

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (required)
# TAVILY_API_KEY is optional — only needed for "search" tasks

# 5. Run
python main.py --task "Write a proposal for a client who needs an AI chatbot on their website"

# Or interactive REPL
python main.py
```

---

## Running tests

```bash
# All tests (fast — no API calls needed)
pytest tests/ -v

# Single file
pytest tests/test_routing.py -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Adding a new agent

Three steps — nothing else changes.

**1. Create the prompt file** `prompts/my_agent.py`:
```python
SYSTEM_PROMPT = "You are a ..."
USER_PROMPT_TEMPLATE = "Task: {user_input}\nContext: {enriched_context}"
```

**2. Create the agent** `agents/my_agent.py`:
```python
from core.state import GGState
from prompts import my_agent as prompts

def my_agent(state: GGState) -> GGState:
    state.log_agent("my_agent")
    # call Claude, write to state.final_output
    return state
```

**3. Wire it in** `core/graph.py`:
```python
from agents.my_agent import my_agent
builder.add_node("my_agent", my_agent)
# add to route_after_router dict + add_edge to END
```

Done. ✅

---

## Swapping models per agent

Edit `.env` — no code changes needed:

```env
ROUTER_MODEL=claude-haiku-4-5        # fast + cheap for classification
STRATEGIST_MODEL=claude-opus-4-5     # best quality for writing
PROMPT_ENGINEER_MODEL=claude-sonnet-4-5
CODER_MODEL=claude-sonnet-4-5
ENRICHER_MODEL=claude-haiku-4-5      # fast for synthesis
```

---

## Key design principles

| Principle | How it's implemented |
|---|---|
| **Separation of concerns** | Agents never contain prompt strings |
| **Single source of truth** | `GGState` is the only shared object |
| **Routing isolation** | `route_after_router()` is a pure function — fully testable |
| **Graceful degradation** | Every agent catches exceptions and adds to `state.errors` |
| **Model flexibility** | Every agent reads its model from `.env` |

---

## Output

All outputs are saved automatically to `./output/` (configurable via `OUTPUT_DIR` in `.env`).

| Format | File | When |
|---|---|---|
| Markdown | `{session_id}.md` | strategy, prompt_engineer |
| HTML | `{session_id}.html` | coder, or `--output html` |
| PDF | `{session_id}.pdf` | `--output pdf` (requires weasyprint) |
