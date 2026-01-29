"""Configuration commands."""

from __future__ import annotations

from typing import Annotated

import typer

from pandadoc_cli.config import Config, get_config
from pandadoc_cli.output import (
    get_output_context,
    print_error,
    print_json,
    print_success,
)
from pandadoc_cli.prompts import confirm_optional, confirm_or_abort, prompt_value

app = typer.Typer(no_args_is_help=True)


@app.command("init")
def init_config(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing config"),
    ] = False,
) -> None:
    """Interactive configuration setup."""
    config_path = Config.user_config_path()

    if config_path.exists() and not force:
        confirm_or_abort(
            f"Config already exists at {config_path}. Overwrite?",
            force=False,
            action="Overwrite configuration",
        )

    config = Config()

    # PandaDoc API key
    typer.echo("\n--- PandaDoc Configuration ---")
    pandadoc_key = prompt_value(
        "PandaDoc API Key",
        hide_input=True,
        hint=(
            "Interactive setup requires a TTY. Use "
            "'pandadoc config set pandadoc.api_key <value>' or set PANDADOC_API_KEY."
        ),
    )
    config.pandadoc_api_key = pandadoc_key

    # Copper CRM (optional)
    typer.echo("\n--- Copper CRM Configuration (optional) ---")
    setup_copper = confirm_optional(
        "Configure Copper CRM integration?",
        default=True,
        hint=(
            "Interactive setup requires a TTY. Use "
            "'pandadoc config set copper.api_key <value>' and "
            "'pandadoc config set copper.user_email <value>'."
        ),
    )

    if setup_copper:
        copper_key = prompt_value(
            "Copper API Key",
            hide_input=True,
            hint=(
                "Interactive setup requires a TTY. Use "
                "'pandadoc config set copper.api_key <value>'."
            ),
        )
        copper_email = prompt_value(
            "Copper User Email",
            hide_input=False,
            hint=(
                "Interactive setup requires a TTY. Use "
                "'pandadoc config set copper.user_email <value>'."
            ),
        )
        config.copper.api_key = copper_key
        config.copper.user_email = copper_email

    # Save configuration
    config.save()
    print_success(f"Configuration saved to {config_path}")

    typer.echo("\nNext steps:")
    typer.echo("  1. Set up field mappings: pandadoc copper mapping set 'Field=path'")
    typer.echo("  2. List available Copper fields: pandadoc copper fields")
    typer.echo("  3. Create a document: pandadoc copper pull <opp-id> --template <id>")


@app.command("show")
def show_config() -> None:
    """Show current configuration."""
    config = get_config()
    ctx = get_output_context()

    pandadoc_data = {
        "api_key": _mask_key(config.pandadoc_api_key),
        "configured": bool(config.pandadoc_api_key),
    }
    copper_data = {
        "api_key": _mask_key(config.copper.api_key),
        "user_email": config.copper.user_email or "(not set)",
        "configured": bool(config.copper.api_key and config.copper.user_email),
    }
    config_paths = [str(p) for p in Config._config_paths() if p.exists()]
    data = {
        "pandadoc": pandadoc_data,
        "copper": copper_data,
        "mapping": config.mapping,
        "config_paths": config_paths,
    }

    if ctx.is_json:
        print_json(data)
    else:
        typer.echo("--- PandaDoc ---")
        typer.echo(f"  API Key: {pandadoc_data['api_key']}")
        typer.echo(f"  Configured: {pandadoc_data['configured']}")

        typer.echo("\n--- Copper CRM ---")
        typer.echo(f"  API Key: {copper_data['api_key']}")
        typer.echo(f"  User Email: {copper_data['user_email']}")
        typer.echo(f"  Configured: {copper_data['configured']}")

        typer.echo("\n--- Field Mappings ---")
        mappings = {k: v for k, v in config.mapping.items() if not k.startswith("_")}
        if mappings:
            for k, v in mappings.items():
                typer.echo(f"  {k} -> {v}")
        else:
            typer.echo("  (none)")

        typer.echo("\n--- Config Files ---")
        for path in config_paths:
            typer.echo(f"  {path}")


@app.command("set")
def set_config(
    key: Annotated[str, typer.Argument(help="Config key (e.g., pandadoc.api_key)")],
    value: Annotated[str, typer.Argument(help="Value to set")],
) -> None:
    """Set a configuration value."""
    config = get_config()

    parts = key.split(".")
    if len(parts) == 1:
        print_error(f"Invalid key: {key}. Use format: section.key")
        raise typer.Exit(2)

    section, field = parts[0], ".".join(parts[1:])

    if section == "pandadoc":
        if field == "api_key":
            config.pandadoc_api_key = value
        else:
            print_error(f"Unknown pandadoc field: {field}")
            raise typer.Exit(2)
    elif section == "copper":
        if field == "api_key":
            config.copper.api_key = value
        elif field == "user_email":
            config.copper.user_email = value
        else:
            print_error(f"Unknown copper field: {field}")
            raise typer.Exit(2)
    elif section == "mapping":
        config.mapping[field] = value
    else:
        print_error(f"Unknown section: {section}")
        raise typer.Exit(2)

    config.save()
    print_success(f"Set {key}")


@app.command("unset")
def unset_config(
    key: Annotated[str, typer.Argument(help="Config key to remove")],
) -> None:
    """Remove a configuration value."""
    config = get_config()

    parts = key.split(".")
    if len(parts) < 2:
        print_error(f"Invalid key: {key}. Use format: section.key")
        raise typer.Exit(2)

    section, field = parts[0], ".".join(parts[1:])

    if section == "pandadoc":
        if field == "api_key":
            config.pandadoc_api_key = ""
        else:
            print_error(f"Unknown pandadoc field: {field}")
            raise typer.Exit(2)
    elif section == "copper":
        if field == "api_key":
            config.copper.api_key = ""
        elif field == "user_email":
            config.copper.user_email = ""
        else:
            print_error(f"Unknown copper field: {field}")
            raise typer.Exit(2)
    elif section == "mapping":
        if field in config.mapping:
            del config.mapping[field]
        else:
            print_error(f"Mapping not found: {field}")
            raise typer.Exit(4)
    else:
        print_error(f"Unknown section: {section}")
        raise typer.Exit(2)

    config.save()
    print_success(f"Unset {key}")


def _mask_key(key: str) -> str:
    """Mask an API key for display."""
    if not key:
        return "(not set)"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
