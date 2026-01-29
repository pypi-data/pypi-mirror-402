"""Helpers for safe interactive prompts."""

from __future__ import annotations

import sys

import typer
from click import get_current_context

from pandadoc_cli.output import print_error


def _cli_prompt_state() -> tuple[bool, bool]:
    """Return (no_input, stdin_is_tty) from the current CLI context."""
    ctx = get_current_context(silent=True)
    no_input = False
    stdin_is_tty = sys.stdin.isatty()

    if ctx and isinstance(ctx.obj, dict):
        no_input = bool(ctx.obj.get("no_input", False))
        stdin_is_tty = bool(ctx.obj.get("stdin_is_tty", stdin_is_tty))

    return no_input, stdin_is_tty


def confirm_or_abort(prompt: str, *, force: bool, action: str) -> None:
    """Confirm a destructive action or raise with a helpful error."""
    if force:
        return

    no_input, stdin_is_tty = _cli_prompt_state()
    if no_input or not stdin_is_tty:
        print_error(f"{action} requires confirmation. Re-run with --force.")
        raise typer.Exit(2)

    if not typer.confirm(prompt):
        raise typer.Abort()


def prompt_value(prompt: str, *, hide_input: bool = False, hint: str) -> str:
    """Prompt for a value or exit when prompts are disabled."""
    no_input, stdin_is_tty = _cli_prompt_state()
    if no_input or not stdin_is_tty:
        print_error(hint)
        raise typer.Exit(2)

    value: str = typer.prompt(prompt, hide_input=hide_input)
    return value


def confirm_optional(prompt: str, *, default: bool, hint: str) -> bool:
    """Confirm an optional choice or exit when prompts are disabled."""
    no_input, stdin_is_tty = _cli_prompt_state()
    if no_input or not stdin_is_tty:
        print_error(hint)
        raise typer.Exit(2)

    return typer.confirm(prompt, default=default)
