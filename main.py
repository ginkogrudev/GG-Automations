"""
main.py
─────────────────────────────────────────────────────────────
Entry point for GG AI Factory.
Runs as a CLI REPL or takes a single --task argument.

Usage:
  python main.py                          # interactive REPL
  python main.py --task "Write a proposal for a SaaS landing page"
  python main.py --task "..." --output pdf
"""

from __future__ import annotations
import argparse
import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

load_dotenv()

# ── Logging setup (before any local imports) ──────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Local imports (after env is loaded) ───────────────────────────────
from core.graph import graph
from core.state import GGState

console = Console()


# ── Runner ────────────────────────────────────────────────────────────

def run(user_input: str, output_format: str = "markdown") -> GGState:
    """Execute a single task through the agent graph."""

    initial_state = GGState(
        user_input=user_input,
        session_id=str(uuid.uuid4())[:8],
        output_format=output_format,
    )

    console.print(
        Panel(
            f"[bold cyan]Session:[/] {initial_state.session_id}\n"
            f"[bold cyan]Task:[/]    {user_input[:120]}",
            title="[bold]GG AI Factory[/]",
            border_style="cyan",
        )
    )

    final_state: GGState = graph.invoke(initial_state)

    # ── Pretty output ─────────────────────────────────────────────────
    console.print()
    console.print(f"[dim]Route:[/] router → {' → '.join(final_state.agent_trail[1:])}")
    console.print(f"[dim]Reason:[/] {final_state.routing_reason}")
    console.print()

    if final_state.final_output:
        console.print(
            Panel(
                Markdown(final_state.final_output)
                if final_state.output_format == "markdown"
                else Text(final_state.final_output),
                title="[bold green]Output[/]",
                border_style="green",
            )
        )
    elif final_state.task_type == "unknown":
        console.print(
            "[yellow]⚠  Task type unknown — no specialist matched. "
            "Please refine your request.[/yellow]"
        )

    if final_state.has_errors:
        for err in final_state.errors:
            console.print(f"[red]Error:[/] {err}")

    # Save output via doc_generator
    if final_state.final_output:
        from tools.doc_generator import save as save_doc
        saved_path = save_doc(
            content=final_state.final_output,
            filename=final_state.session_id,
            fmt=final_state.output_format,
        )
        console.print(f"\n[dim]Saved → {saved_path}[/dim]")

    return final_state


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GG AI Factory CLI")
    parser.add_argument("--task",   type=str, help="Task to run (skips REPL)")
    parser.add_argument(
        "--output",
        type=str,
        default="markdown",
        choices=["markdown", "html", "pdf", "json"],
        help="Output format",
    )
    args = parser.parse_args()

    if args.task:
        run(args.task, args.output)
        return

    # ── Interactive REPL ──────────────────────────────────────────────
    console.print("\n[bold cyan]GG AI Factory[/] · Interactive Mode")
    console.print("[dim]Type your task. Enter 'exit' to quit.[/dim]\n")

    while True:
        try:
            user_input = console.input("[bold]> [/]").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            break

        run(user_input)
        console.print("\n" + "─" * 60 + "\n")

    console.print("[dim]Bye.[/dim]")


if __name__ == "__main__":
    main()