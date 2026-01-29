"""PandaDoc CLI - main entry point."""

from __future__ import annotations

import logging
import os
import sys

import typer

from pandadoc_cli import __version__
from pandadoc_cli.commands import config as config_cmd
from pandadoc_cli.commands import contact as contact_cmd
from pandadoc_cli.commands import copper as copper_cmd
from pandadoc_cli.commands import doc as doc_cmd
from pandadoc_cli.output import (
    OutputContext,
    OutputFormat,
    print_error,
    set_output_context,
)

# Create the main app
app = typer.Typer(
    name="pandadoc",
    help="Manage PandaDoc documents with Copper CRM integration.",
    no_args_is_help=True,
    add_completion=True,
)

# Register command groups
app.add_typer(doc_cmd.app, name="doc", help="Manage documents.")
app.add_typer(contact_cmd.app, name="contact", help="Manage contacts.")
app.add_typer(copper_cmd.app, name="copper", help="Copper CRM integration.")
app.add_typer(config_cmd.app, name="config", help="Manage configuration.")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"pandadoc {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug output.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON.",
    ),
    plain_output: bool = typer.Option(
        False,
        "--plain",
        help="Output as tab-separated values.",
    ),
    no_input: bool = typer.Option(
        False,
        "--no-input",
        help="Disable interactive prompts.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output.",
    ),
) -> None:
    """PandaDoc CLI - Document management with Copper CRM integration."""
    _ = version  # Used by callback

    if json_output and plain_output:
        print_error("--json and --plain are mutually exclusive.")
        raise typer.Exit(2)

    # Determine output format
    output_format = OutputFormat.DEFAULT
    if json_output:
        output_format = OutputFormat.JSON
    elif plain_output:
        output_format = OutputFormat.PLAIN

    # Check NO_COLOR env var
    if os.environ.get("NO_COLOR"):
        no_color = True
    if os.environ.get("TERM") == "dumb":
        no_color = True

    # Set global output context
    output_ctx = OutputContext(
        format=output_format,
        quiet=quiet,
        no_color=no_color,
    )
    set_output_context(output_ctx)
    ctx_obj: dict[str, bool] = {
        "no_input": no_input,
        "stdin_is_tty": sys.stdin.isatty(),
    }
    ctx.obj = ctx_obj

    # Configure verbose logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s: %(message)s",
            stream=sys.stderr,
        )


def run() -> None:
    """Run the CLI application."""
    try:
        app()
    except typer.Exit:
        raise
    except typer.Abort:
        raise
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    run()
