"""Output formatting for PandaDoc CLI."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    """Output format options."""

    DEFAULT = "default"
    JSON = "json"
    PLAIN = "plain"


@dataclass
class OutputContext:
    """Output configuration context."""

    format: OutputFormat = OutputFormat.DEFAULT
    quiet: bool = False
    no_color: bool = False

    @property
    def console(self) -> Console:
        """Get a Rich console configured for this context."""
        return Console(
            force_terminal=not self.no_color and sys.stdout.isatty(),
            no_color=self.no_color,
        )

    @property
    def is_json(self) -> bool:
        """Return True if JSON output is requested."""
        return self.format == OutputFormat.JSON

    @property
    def is_plain(self) -> bool:
        """Return True if plain output is requested."""
        return self.format == OutputFormat.PLAIN


# Global output context
_output_ctx: OutputContext | None = None


def get_output_context() -> OutputContext:
    """Get the current output context."""
    global _output_ctx
    if _output_ctx is None:
        _output_ctx = OutputContext()
    return _output_ctx


def set_output_context(ctx: OutputContext) -> None:
    """Set the current output context."""
    global _output_ctx
    _output_ctx = ctx


def _emit_json(data: Any, stream: Any) -> None:
    """Write JSON to the provided stream."""
    stream.write(f"{json.dumps(data, indent=2, default=str)}\n")


def print_json(data: Any) -> None:
    """Print data as JSON."""
    _emit_json(data, sys.stdout)


def print_plain(rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    """Print data as tab-separated values."""
    if not rows:
        return

    if columns is None:
        columns = list(rows[0].keys())

    # Header
    print("\t".join(columns))

    # Rows
    for row in rows:
        values = [str(row.get(col, "")) for col in columns]
        print("\t".join(values))


def print_table(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]] | None = None,
    title: str | None = None,
) -> None:
    """Print data as a Rich table."""
    ctx = get_output_context()

    if ctx.quiet:
        return

    if ctx.is_json:
        print_json(rows)
        return

    if ctx.is_plain:
        col_keys = [c[0] for c in columns] if columns else None
        print_plain(rows, col_keys)
        return

    if not rows:
        ctx.console.print("[dim]No results[/dim]")
        return

    if columns is None:
        columns = [(k, k.replace("_", " ").title()) for k in rows[0]]

    table = Table(title=title)
    for _key, header in columns:
        table.add_column(header)

    for row in rows:
        values = [str(row.get(key, "")) for key, _ in columns]
        table.add_row(*values)

    ctx.console.print(table)


def print_success(message: str) -> None:
    """Print a success message."""
    ctx = get_output_context()
    if ctx.quiet:
        return
    if ctx.is_json:
        print_json({"success": True, "message": message})
        return
    ctx.console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    ctx = get_output_context()
    if ctx.is_json:
        _emit_json({"success": False, "error": message}, sys.stderr)
        return
    Console(stderr=True, no_color=ctx.no_color).print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message to stderr."""
    ctx = get_output_context()
    if ctx.quiet or ctx.is_json:
        return
    Console(stderr=True, no_color=ctx.no_color).print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    ctx = get_output_context()
    if ctx.quiet or ctx.is_json:
        return
    ctx.console.print(f"[dim]{message}[/dim]")


def print_id(id_value: str) -> None:
    """Print just an ID (for scripting)."""
    ctx = get_output_context()
    if ctx.is_json:
        print_json({"id": id_value})
    else:
        print(id_value)
