"""
main.py
─────────────────────────────────────────────────────────────
Entry point for GG AI Factory.
Runs as a CLI REPL or takes a single --task argument.
"""

from __future__ import annotations
import argparse
import logging
import os
import sys
import uuid
from typing import cast

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

# Зареждаме променливите на средата преди всичко останало
load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Local imports ─────────────────────────────────────────────────────
try:
    from core.graph import graph
    from core.state import GGState
    from tools.doc_generator import save as save_doc
except ImportError as e:
    logger.critical(f"Грешка при импортиране на основни модули: {e}")
    sys.exit(1)

console = Console()

# КОМПИЛИРАМЕ ГРАФА ВЕДНЪЖ (Performance Optimization)
try:
    COMPILED_GRAPH = graph.compile()
except Exception as e:
    logger.critical(f"Неуспешно компилиране на LangGraph: {e}")
    sys.exit(1)


# ── Runner ────────────────────────────────────────────────────────────

def run(user_input: str, output_format: str = "markdown") -> GGState | None:
    """Execute a single task through the agent graph."""
    
    session_id = str(uuid.uuid4())[:8]

    # Инициализация на State-a (TypedDict)
    initial_state: GGState = {
        "user_input": user_input,
        "session_id": session_id,
        "output_format": output_format,
        "agent_trail": ["router"],
        "routing_reason": "",
        "task_type": "",
        "final_output": None,
        "messages": [],
        "errors": [],
        "iteration_count": 0,
        "has_errors": False,
    }

    console.print(
        Panel(
            f"[bold cyan]Session:[/] {session_id}\n"
            f"[bold cyan]Task:[/]    {user_input[:120]}",
            title="[bold]GG AI Factory - Task Initialization[/]",
            border_style="cyan",
        )
    )

    # 1. Защитаваме екзекуцията на графа (Fault Tolerance)
    try:
        with console.status("[bold green]GG AI Factory работи по офертата (Hormozi Style)...[/]"):
            final_state: GGState = cast(GGState, COMPILED_GRAPH.invoke(initial_state))
    except Exception as e:
        logger.error(f"Graph execution failed: {e}", exc_info=True)
        console.print(f"[bold red]Критична грешка при изпълнение на агентите:[/] {e}")
        return None

    # 2. Pretty output
    console.print()
    trail = " → ".join(final_state.get('agent_trail', ['router']))
    console.print(f"[dim]Route:[/] {trail}")
    
    if final_state.get("routing_reason", ""):
        console.print(f"[dim]Reason:[/] {final_state.get('routing_reason', '')}")
    console.print()

    # 3. Обработка на резултата
    final_output = final_state.get("final_output")
    if final_output:
        display_content = (
            Markdown(final_output) 
            if final_state.get("output_format") == "markdown" 
            else Text(final_output)
        )
        
        console.print(
            Panel(
                display_content,
                title="[bold green]Grand Slam Output[/]",
                border_style="green",
            )
        )
        
        # 4. Запазване на файла със защита
        try:
            saved_path = save_doc(
                content=final_output,
                filename=session_id,
                fmt=final_state.get("output_format", "markdown"),
            )
            console.print(f"\n[bold blue]🚀 Готово! Файлът е запазен тук:[/] [dim]{saved_path}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Грешка при запазване на документа:[/] {e}")

    elif final_state.get("task_type") == "unknown":
        console.print(
            "[yellow]⚠ Task type unknown — no specialist matched. "
            "Дай ми повече контекст. Какъв е бизнес резултатът, който търсиш?[/yellow]"
        )

    # 5. Отчитане на бизнес грешки (Ако агентите са върнали такива)
    if final_state.get("has_errors") and final_state.get("errors"):
        for err in final_state["errors"]:
            console.print(f"[red]Agent Error:[/] {err}")

    return final_state


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GG AI Factory CLI - Built for Scale")
    parser.add_argument("--task", type=str, help="Task to run (skips REPL)")
    parser.add_argument(
        "--output",
        type=str,
        default="markdown",
        choices=["markdown", "html", "pdf", "json"],
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    if args.task:
        run(args.task, args.output)
        return

    # ── Interactive REPL ──────────────────────────────────────────────
    console.print("\n[bold cyan]GG AI Factory[/] · Interactive Mode")
    console.print("[dim]Въведи своята задача. За изход напиши 'exit' или 'q'.[/dim]\n")

    while True:
        try:
            user_input = console.input("[bold yellow]GG > [/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Принудително спиране...[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            break

        run(user_input, args.output)
        console.print("\n" + "─" * 60 + "\n")

    console.print("[bold green]До скоро! Keep building.[/bold green]")


if __name__ == "__main__":
    main()