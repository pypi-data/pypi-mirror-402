"""Document commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from pandadoc_cli.api.pandadoc import (
    ConflictError,
    NotFoundError,
    PandaDocClient,
    PandaDocError,
)
from pandadoc_cli.output import (
    get_output_context,
    print_error,
    print_id,
    print_success,
    print_table,
)
from pandadoc_cli.prompts import confirm_or_abort

app = typer.Typer(no_args_is_help=True)


def _parse_field_values(fields: list[str] | None) -> dict[str, dict[str, str]]:
    """Parse key=value fields into PandaDoc payload format."""
    if not fields:
        return {}

    parsed: dict[str, dict[str, str]] = {}
    for item in fields:
        if "=" not in item:
            print_error("Invalid field format. Use --field key=value.")
            raise typer.Exit(2)
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            print_error("Invalid field format. Use --field key=value.")
            raise typer.Exit(2)
        parsed[key] = {"value": value.strip()}

    return parsed


@app.command("list")
def list_documents(
    status: Annotated[
        str | None,
        typer.Option(
            "--status", "-s", help="Filter by status (draft, sent, completed, etc.)"
        ),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option("--template", "-t", help="Filter by template ID"),
    ] = None,
) -> None:
    """List documents."""
    try:
        client = PandaDocClient()
        docs = client.list_documents(status=status, template_id=template)

        rows = [d.to_dict() for d in docs]
        columns = [
            ("id", "ID"),
            ("name", "Name"),
            ("status", "Status"),
            ("date_modified", "Modified"),
        ]
        print_table(rows, columns)
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("get")
def get_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
) -> None:
    """Get document details."""
    try:
        client = PandaDocClient()
        doc = client.get_document(doc_id)

        ctx = get_output_context()
        if ctx.is_json:
            from pandadoc_cli.output import print_json

            print_json(doc)
        else:
            # Print key details
            print(f"ID: {doc.get('id', 'N/A')}")
            print(f"Name: {doc.get('name', 'N/A')}")
            print(f"Status: {doc.get('status', 'N/A')}")
            print(f"Created: {doc.get('date_created', 'N/A')}")
            print(f"Modified: {doc.get('date_modified', 'N/A')}")
            if doc.get("recipients"):
                print("Recipients:")
                for r in doc["recipients"]:
                    print(f"  - {r.get('email', 'N/A')} ({r.get('role', 'N/A')})")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("create")
def create_document(
    template: Annotated[str, typer.Option("--template", "-t", help="Template ID")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Document name")
    ] = None,
    recipient: Annotated[
        list[str] | None,
        typer.Option("--recipient", "-r", help="Recipient email (repeatable)"),
    ] = None,
    field: Annotated[
        list[str] | None,
        typer.Option("--field", "-f", help="Field value as key=value (repeatable)"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without creating"),
    ] = False,
) -> None:
    """Create a document from a template."""
    # Parse recipients
    recipients = []
    if recipient:
        for email in recipient:
            recipients.append({"email": email})

    fields = _parse_field_values(field)

    doc_name = name or f"Document from {template}"

    if dry_run:
        print_success(f"Would create document '{doc_name}' from template '{template}'")
        if recipients:
            print(f"  Recipients: {', '.join(r['email'] for r in recipients)}")
        if fields:
            print(f"  Fields: {fields}")
        return

    try:
        client = PandaDocClient()
        doc_id = client.create_document(
            template_id=template,
            name=doc_name,
            recipients=recipients,
            fields=fields if fields else None,
        )
        print_success(f"Created document: {doc_id}")
        print_id(doc_id)
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("duplicate")
def duplicate_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID to duplicate")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New document name")
    ] = None,
) -> None:
    """Duplicate an existing document."""
    try:
        client = PandaDocClient()
        # Get original document details
        original = client.get_document(doc_id)
        new_name = name or f"Copy of {original.get('name', 'Document')}"

        # Create from same template if available
        template_id = original.get("template", {}).get("id")
        if not template_id:
            print_error("Cannot duplicate: document has no associated template")
            raise typer.Exit(1)

        new_doc_id = client.create_document(
            template_id=template_id,
            name=new_name,
            recipients=original.get("recipients", []),
        )
        print_success(f"Created duplicate: {new_doc_id}")
        print_id(new_doc_id)
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("update")
def update_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    field: Annotated[
        list[str] | None,
        typer.Option("--field", "-f", help="Field value as key=value (repeatable)"),
    ] = None,
) -> None:
    """Update document fields."""
    if not field:
        print_error("No fields specified. Use --field key=value")
        raise typer.Exit(2)

    fields = _parse_field_values(field)

    try:
        client = PandaDocClient()
        client.update_document(doc_id, fields)
        print_success(f"Updated document: {doc_id}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except ConflictError:
        print_error("Cannot update: document is not in draft status")
        raise typer.Exit(5) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("delete")
def delete_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete a document."""
    confirm_or_abort(f"Delete document {doc_id}?", force=force, action="Delete")

    try:
        client = PandaDocClient()
        client.delete_document(doc_id)
        print_success(f"Deleted document: {doc_id}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("send")
def send_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    subject: Annotated[
        str | None,
        typer.Option("--subject", "-s", help="Email subject"),
    ] = None,
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Email message"),
    ] = None,
    silent: Annotated[
        bool,
        typer.Option("--silent", help="Send without email notification"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without sending"),
    ] = False,
) -> None:
    """Send document for signature."""
    if dry_run:
        print_success(f"Would send document: {doc_id}")
        if subject:
            print(f"  Subject: {subject}")
        if message:
            print(f"  Message: {message}")
        return

    try:
        client = PandaDocClient()
        client.send_document(doc_id, subject=subject, message=message, silent=silent)
        print_success(f"Sent document: {doc_id}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except ConflictError:
        print_error("Cannot send: document is not in draft status")
        raise typer.Exit(5) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("remind")
def remind_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Reminder message"),
    ] = None,
) -> None:
    """Send a reminder for a document."""
    try:
        client = PandaDocClient()
        client.remind_document(doc_id, message=message)
        print_success(f"Sent reminder for: {doc_id}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("void")
def void_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    reason: Annotated[
        str | None,
        typer.Option("--reason", "-r", help="Reason for voiding"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without voiding"),
    ] = False,
) -> None:
    """Void a sent document."""
    if dry_run:
        print_success(f"Would void document: {doc_id}")
        if reason:
            print(f"  Reason: {reason}")
        return

    confirm_or_abort(
        f"Void document {doc_id}? This cannot be undone.",
        force=force,
        action="Void",
    )

    try:
        client = PandaDocClient()
        client.void_document(doc_id, reason=reason)
        print_success(f"Voided document: {doc_id}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except ConflictError:
        print_error("Cannot void: document is not in sent status")
        raise typer.Exit(5) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("download")
def download_document(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    format_: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (pdf, docx)"),
    ] = "pdf",
) -> None:
    """Download a document."""
    try:
        client = PandaDocClient()
        content = client.download_document(doc_id)

        output_path = output or Path(f"{doc_id}.{format_}")

        output_path.write_bytes(content)
        print_success(f"Downloaded to: {output_path}")
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("link")
def get_document_link(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
) -> None:
    """Get a shareable link for a document."""
    try:
        client = PandaDocClient()
        link = client.get_document_link(doc_id)
        print(link)
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e


@app.command("status")
def get_document_status(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
) -> None:
    """Get document status."""
    try:
        client = PandaDocClient()
        status = client.get_document_status(doc_id)

        ctx = get_output_context()
        if ctx.is_json:
            from pandadoc_cli.output import print_json

            print_json({"id": doc_id, "status": status})
        else:
            print(status)
    except NotFoundError:
        print_error(f"Document not found: {doc_id}")
        raise typer.Exit(4) from None
    except PandaDocError as e:
        print_error(str(e))
        raise typer.Exit(1) from e
