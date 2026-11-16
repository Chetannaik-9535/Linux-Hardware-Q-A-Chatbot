"""Command Line Interface (CLI) for the Linux Hardware Q&A Assistant."""

from __future__ import annotations

import argparse
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from hw_assistant import __version__
from hw_assistant.config import settings
from hw_assistant.inspectors.system import SystemSummaryInspector
from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.orchestration.engine import HardwareAssistantEngine
from hw_assistant.orchestration.providers.claude import ClaudeProvider
from hw_assistant.orchestration.providers.mock import MockProvider
from hw_assistant.orchestration.providers.ollama import OllamaProvider
from hw_assistant.security.executor import SafeCommandExecutor

console = Console()


def print_banner() -> None:
    """Display startup banner and active mode."""
    banner = f"""[bold cyan]Linux Hardware Q&A Assistant[/bold cyan] [dim]v{__version__}[/dim]
[dim]Verified on-device hardware inspection via safe LLM tool-calling[/dim]"""
    console.print(Panel(banner, border_style="cyan"))


def display_system_summary(executor: SafeCommandExecutor) -> None:
    """Print structured hardware summary table to console."""
    summary = SystemSummaryInspector(executor).inspect()

    table = Table(title=f"Hardware Summary: {summary.hostname}", border_style="cyan")
    table.add_column("Subsystem", style="bold yellow", width=18)
    table.add_column("Details", style="white")

    table.add_row("OS & Kernel", f"{summary.os_name} (Kernel {summary.kernel_release})")
    if summary.motherboard:
        table.add_row(
            "Motherboard",
            f"{summary.motherboard.manufacturer or 'OEM'} {summary.motherboard.product_name or 'Board'} "
            f"(BIOS {summary.motherboard.bios_version or 'N/A'})",
        )
    if summary.cpu:
        table.add_row(
            "CPU",
            f"{summary.cpu.model} ({summary.cpu.cores} Cores, {summary.cpu.threads} Threads)",
        )
    if summary.memory:
        table.add_row(
            "Memory (RAM)",
            f"{summary.memory.total_gb:.1f} GB Total | {summary.memory.available_gb:.1f} GB Available "
            f"({summary.memory.utilization_percent}% Used)",
        )
    if summary.memory_topology:
        table.add_row("RAM Topology", summary.memory_topology.upgrade_assessment)
    if summary.storage:
        disk_str = f"{summary.storage.total_disks} Disks ({summary.storage.nvme_count} NVMe, {summary.storage.sata_count} SATA)"
        table.add_row("Storage", disk_str)
    if summary.gpus:
        gpu_str = ", ".join(f"{g.vendor} {g.model} ({g.vram_mb or 'Shared'} MB)" for g in summary.gpus)
        table.add_row("Graphics (GPU)", gpu_str)

    console.print(table)


def run_interactive(engine: HardwareAssistantEngine) -> None:
    """Run interactive chat REPL loop."""
    print_banner()
    console.print("[dim]Type your question and press Enter. Type 'exit' or 'quit' to leave.[/dim]\n")

    session_id = None

    while True:
        try:
            query = console.input("[bold green]User > [/bold green]").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Exiting Hardware Assistant. Goodbye![/yellow]")
                break
            if query.lower() == "summary":
                display_system_summary(engine.executor)
                continue

            with console.status("[cyan]Inspecting Linux system utilities...[/cyan]"):
                response = engine.ask(query=query, session_id=session_id)
                session_id = response.session_id

            # Print tool execution traces
            if response.tool_traces:
                trace_lines = []
                for t in response.tool_traces:
                    status_icon = "✓" if t.success else "✗"
                    color = "green" if t.success else "red"
                    trace_lines.append(
                        f"[{color}]{status_icon}[/{color}] [bold]{t.tool_name}[/bold] ({t.execution_time_ms:.1f}ms)"
                    )
                console.print(Panel(" | ".join(trace_lines), title="Tool Execution Trace", border_style="blue"))

            # Print assistant Markdown response
            console.print("\n[bold cyan]Assistant:[/bold cyan]")
            console.print(Markdown(response.message))
            console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break


def main() -> None:
    """CLI entry point parsing flags and dispatching execution."""
    parser = argparse.ArgumentParser(description="Linux Hardware Q&A Assistant CLI")
    parser.add_argument("--query", "-q", type=str, help="Single question to answer directly")
    parser.add_argument("--summary", "-s", action="store_true", help="Print hardware summary and exit")
    parser.add_argument(
        "--provider",
        choices=["mock", "claude", "ollama"],
        default=settings.llm_provider,
        help="LLM provider backend (default: mock)",
    )
    parser.add_argument(
        "--profile",
        choices=["thinkpad_x1", "dell_xps", "gaming_desktop", "acer_budget"],
        default=settings.mock_profile,
        help="Simulated hardware profile if running on non-Linux or in mock mode",
    )

    args = parser.parse_args()

    # Initialize executor and provider
    executor = SafeCommandExecutor(mock_profile=args.profile)
    dispatcher = ToolDispatcher(executor=executor)

    if args.provider == "claude":
        provider = ClaudeProvider()
    elif args.provider == "ollama":
        provider = OllamaProvider()
    else:
        provider = MockProvider()

    engine = HardwareAssistantEngine(
        provider=provider,
        dispatcher=dispatcher,
        executor=executor,
    )

    if args.summary:
        display_system_summary(executor)
        sys.exit(0)

    if args.query:
        response = engine.ask(query=args.query)
        if response.tool_traces:
            for t in response.tool_traces:
                console.print(f"[dim]Tool called: {t.tool_name} ({t.execution_time_ms:.1f}ms)[/dim]")
        console.print(Markdown(response.message))
        sys.exit(0)

    run_interactive(engine)


if __name__ == "__main__":
    main()

