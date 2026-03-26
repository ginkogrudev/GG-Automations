"""
api.py — FastAPI server for GG AI Factory.
Wraps the LangGraph system behind a REST API.
"""

from __future__ import annotations

import asyncio
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
OUTPUT_DIR = pathlib.Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(title="GG AI Factory", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
STATIC = pathlib.Path(__file__).parent / "index.html"


class RunRequest(BaseModel):
    task: str
    output_format: str = "markdown"


# ── Helpers ──────────────────────────────────────────────────────────

def _verify_key(key: str | None) -> None:
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return FileResponse(STATIC, media_type="text/html")


@app.post("/run")
async def run_task(
    body: RunRequest,
    x_api_key: str | None = Header(None),
):
    _verify_key(x_api_key)

    from main import run  # lazy import — keeps module load fast

    result = await asyncio.to_thread(run, body.task, body.output_format)

    if result is None:
        raise HTTPException(status_code=500, detail="Graph execution failed")

    # Auto-save HTML output
    if body.output_format == "html" and result.get("final_output"):
        path = OUTPUT_DIR / f"{result['session_id']}.html"
        path.write_text(result["final_output"], encoding="utf-8")

    return {
        "session_id": result.get("session_id", ""),
        "task_type": result.get("task_type", ""),
        "agent_trail": result.get("agent_trail", []),
        "output": result.get("final_output", ""),
        "output_format": result.get("output_format", body.output_format),
        "errors": result.get("errors", []),
    }


@app.get("/output/{session_id}")
async def get_output(session_id: str):
    """Download a previously saved output file."""
    path = OUTPUT_DIR / f"{session_id}.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    return FileResponse(path, filename=f"{session_id}.html")
