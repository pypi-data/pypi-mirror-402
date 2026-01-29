"""Contact commands."""

from __future__ import annotations

from typing import Annotated

import typer

from pandadoc_cli.api.pandadoc import NotFoundError, PandaDocClient, PandaDocError
from pandadoc_cli.output import print_error, print_id, print_success, print_table
from pandadoc_cli.prompts import confirm_or_abort

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_contacts(
    email: Annotated[
        str | None,
        typer.Option("--email", "-e", help="Filter by email"),
    ] = None,
) -> None:
    """List contacts."""
    try:
        client = PandaDocClient()
        contacts = client.list_contacts(email=email)

        rows = [c.to_dict() for c in contacts]
        columns = [
            ("id", "ID"),
            ("email", "Email"),
            ("first_name", "First Name"),
            ("last_name", "Last Name"),
            ("company", "Company"),
        ]
        print_table(rows, columns)
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("get")
def get_contact(
    contact_id: Annotated[str, typer.Argument(help="Contact ID")],
) -> None:
    """Get contact details."""
    try:
        client = PandaDocClient()
        contact = client.get_contact(contact_id)

        print(f"ID: {contact.id}")
        print(f"Email: {contact.email}")
        if contact.first_name:
            print(f"First Name: {contact.first_name}")
        if contact.last_name:
            print(f"Last Name: {contact.last_name}")
        if contact.company:
            print(f"Company: {contact.company}")
    except NotFoundError:
        print_error(f"Contact not found: {contact_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("create")
def create_contact(
    email: Annotated[str, typer.Option("--email", "-e", help="Email address")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Full name (parsed as first/last)"),
    ] = None,
    company: Annotated[
        str | None,
        typer.Option("--company", "-c", help="Company name"),
    ] = None,
) -> None:
    """Create a contact."""
    first_name = None
    last_name = None
    if name:
        parts = name.split(None, 1)
        first_name = parts[0] if parts else None
        last_name = parts[1] if len(parts) > 1 else None

    try:
        client = PandaDocClient()
        contact_id = client.create_contact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
        )
        print_success(f"Created contact: {contact_id}")
        print_id(contact_id)
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("update")
def update_contact(
    contact_id: Annotated[str, typer.Argument(help="Contact ID")],
    email: Annotated[
        str | None,
        typer.Option("--email", "-e", help="New email address"),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="New full name"),
    ] = None,
    company: Annotated[
        str | None,
        typer.Option("--company", "-c", help="New company name"),
    ] = None,
) -> None:
    """Update a contact."""
    first_name = None
    last_name = None
    if name:
        parts = name.split(None, 1)
        first_name = parts[0] if parts else None
        last_name = parts[1] if len(parts) > 1 else None

    try:
        client = PandaDocClient()
        client.update_contact(
            contact_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
        )
        print_success(f"Updated contact: {contact_id}")
    except NotFoundError:
        print_error(f"Contact not found: {contact_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("delete")
def delete_contact(
    contact_id: Annotated[str, typer.Argument(help="Contact ID")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete a contact."""
    confirm_or_abort(f"Delete contact {contact_id}?", force=force, action="Delete")

    try:
        client = PandaDocClient()
        client.delete_contact(contact_id)
        print_success(f"Deleted contact: {contact_id}")
    except NotFoundError:
        print_error(f"Contact not found: {contact_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e
