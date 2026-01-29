"""Copper CRM integration commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from pandadoc_cli.api.copper import CopperClient, CopperError, CopperNotFoundError
from pandadoc_cli.api.pandadoc import PandaDocClient, PandaDocError
from pandadoc_cli.config import get_config
from pandadoc_cli.output import print_error, print_id, print_success, print_table

app = typer.Typer(no_args_is_help=True)

# In-memory storage for doc <-> opportunity links
_doc_links: dict[str, int] = {}


def _link_key(doc_id: str) -> str:
    return f"_link_{doc_id}"


def _get_doc_link(doc_id: str) -> int | None:
    """Get the Copper opportunity ID linked to a document."""
    if doc_id in _doc_links:
        return _doc_links[doc_id]

    config = get_config()
    value = config.mapping.get(_link_key(doc_id))
    if value is None:
        return None

    try:
        opp_id = int(value)
        _doc_links[doc_id] = opp_id  # Cache for future calls
        return opp_id
    except (TypeError, ValueError):
        return None


def _set_doc_link(doc_id: str, opp_id: int) -> None:
    """Link a document to a Copper opportunity."""
    _doc_links[doc_id] = opp_id

    config = get_config()
    config.mapping[_link_key(doc_id)] = str(opp_id)
    config.save()


def _clear_doc_link(doc_id: str) -> None:
    """Remove link between document and opportunity."""
    _doc_links.pop(doc_id, None)

    config = get_config()
    key = _link_key(doc_id)
    if key in config.mapping:
        del config.mapping[key]
        config.save()


@app.command("pull")
def pull_from_copper(
    opp_id: Annotated[int, typer.Argument(help="Copper opportunity ID")],
    template: Annotated[str, typer.Option("--template", "-t", help="Template ID")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Document name (default: opportunity name)"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without creating"),
    ] = False,
) -> None:
    """Create a document from Copper opportunity data."""
    try:
        config = get_config()
        copper = CopperClient()
        pandadoc = PandaDocClient()

        # Get opportunity data
        opp = copper.get_opportunity(opp_id)
        doc_name = name or f"Proposal - {opp.name}"

        # Apply field mapping
        fields: dict[str, Any] = {}
        for pandadoc_field, copper_path in config.mapping.items():
            if pandadoc_field.startswith("_"):
                continue  # Skip internal fields
            value = copper.resolve_field_value(opp, copper_path)
            if value is not None:
                fields[pandadoc_field] = {"value": str(value)}

        # Get recipient from primary contact
        recipients = []
        if opp.primary_contact_id:
            person = copper.get_person(opp.primary_contact_id)
            if person.email:
                recipients.append({"email": person.email})

        if dry_run:
            print_success(
                f"Would create document '{doc_name}' from opportunity '{opp.name}'"
            )
            print(f"  Template: {template}")
            if recipients:
                print(f"  Recipients: {', '.join(r['email'] for r in recipients)}")
            if fields:
                print("  Fields:")
                for k, v in fields.items():
                    print(f"    {k}: {v['value']}")
            return

        # Create document
        doc_id = pandadoc.create_document(
            template_id=template,
            name=doc_name,
            recipients=recipients,
            fields=fields if fields else None,
            metadata={"copper_opportunity_id": str(opp_id)},
        )

        # Auto-attach to opportunity
        _set_doc_link(doc_id, opp_id)

        print_success(f"Created document: {doc_id}")
        print_success(f"Linked to opportunity: {opp_id}")
        print_id(doc_id)

    except CopperNotFoundError:
        print_error(f"Opportunity not found: {opp_id}")
        raise typer.Exit(4) from None
    except CopperError as e:
        print_error(f"Copper error: {e}")
        raise typer.Exit(10) from e
    except PandaDocError as e:
        print_error(f"PandaDoc error: {e}")
        raise typer.Exit(1) from e


@app.command("sync")
def sync_to_copper(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without syncing"),
    ] = False,
) -> None:
    """Push document status to linked Copper opportunity."""
    try:
        opp_id = _get_doc_link(doc_id)
        if not opp_id:
            print_error(
                f"Document {doc_id} is not attached to a Copper opportunity. "
                f"Use: pandadoc copper attach {doc_id} <opp-id>"
            )
            raise typer.Exit(2)

        pandadoc = PandaDocClient()
        copper = CopperClient()

        # Get document status
        status = pandadoc.get_document_status(doc_id)
        doc = pandadoc.get_document(doc_id)
        doc_name = doc.get("name", "Unknown")

        if dry_run:
            print_success(
                f"Would sync document '{doc_name}' (status: {status}) to opportunity {opp_id}"
            )
            return

        # Update opportunity custom field
        config = get_config()
        status_field = config.mapping.get("_status_field", "Proposal Status")

        copper.update_opportunity(
            opp_id,
            custom_fields={status_field: status},
        )

        # Create activity log
        copper.create_activity(
            parent_type="opportunity",
            parent_id=opp_id,
            activity_type="note",
            details=f"PandaDoc: '{doc_name}' status updated to {status}",
        )

        print_success(f"Synced '{doc_name}' ({status}) to opportunity {opp_id}")

    except CopperError as e:
        print_error(f"Copper sync failed: {e}")
        raise typer.Exit(10) from e
    except PandaDocError as e:
        print_error(f"PandaDoc error: {e}")
        raise typer.Exit(1) from e


@app.command("attach")
def attach_to_opportunity(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
    opp_id: Annotated[int, typer.Argument(help="Copper opportunity ID")],
) -> None:
    """Link a document to a Copper opportunity."""
    try:
        # Verify both exist
        pandadoc = PandaDocClient()
        copper = CopperClient()

        pandadoc.get_document_status(doc_id)  # Raises if not found
        opp = copper.get_opportunity(opp_id)  # Raises if not found

        _set_doc_link(doc_id, opp_id)
        print_success(
            f"Linked document {doc_id} to opportunity '{opp.name}' ({opp_id})"
        )

    except CopperNotFoundError:
        print_error(f"Opportunity not found: {opp_id}")
        raise typer.Exit(4) from None
    except CopperError as e:
        print_error(f"Copper error: {e}")
        raise typer.Exit(10) from e
    except PandaDocError as e:
        print_error(f"PandaDoc error: {e}")
        raise typer.Exit(1) from e


@app.command("detach")
def detach_from_opportunity(
    doc_id: Annotated[str, typer.Argument(help="Document ID")],
) -> None:
    """Remove link between document and Copper opportunity."""
    opp_id = _get_doc_link(doc_id)
    if not opp_id:
        print_error(f"Document {doc_id} is not attached to any opportunity")
        raise typer.Exit(2)

    _clear_doc_link(doc_id)
    print_success(f"Unlinked document {doc_id} from opportunity {opp_id}")


@app.command("fields")
def list_copper_fields() -> None:
    """List available Copper field paths for mapping."""
    try:
        copper = CopperClient()
        fields = copper.get_available_fields()

        rows = [{"path": f} for f in fields]
        print_table(rows, [("path", "Field Path")])

    except CopperError as e:
        print_error(f"Copper error: {e}")
        raise typer.Exit(10) from e


# Mapping subcommands
mapping_app = typer.Typer(no_args_is_help=True, help="Manage field mappings.")
app.add_typer(mapping_app, name="mapping")


@mapping_app.command("show")
def show_mapping() -> None:
    """Show current field mappings."""
    config = get_config()

    mappings = {k: v for k, v in config.mapping.items() if not k.startswith("_")}
    if not mappings:
        print(
            "No mappings configured. Use 'pandadoc copper mapping set' to add mappings."
        )
        return

    rows = [{"pandadoc": k, "copper": v} for k, v in mappings.items()]
    print_table(rows, [("pandadoc", "PandaDoc Field"), ("copper", "Copper Path")])


@mapping_app.command("set")
def set_mapping(
    mapping: Annotated[
        str, typer.Argument(help="Mapping as 'PandaDoc Field=copper.path'")
    ],
) -> None:
    """Set a field mapping."""
    if "=" not in mapping:
        print_error("Invalid format. Use: 'PandaDoc Field=copper.path'")
        raise typer.Exit(2)

    pandadoc_field, copper_path = mapping.split("=", 1)
    pandadoc_field = pandadoc_field.strip()
    copper_path = copper_path.strip()

    config = get_config()
    config.mapping[pandadoc_field] = copper_path
    config.save()

    print_success(f"Set mapping: '{pandadoc_field}' -> '{copper_path}'")


@mapping_app.command("unset")
def unset_mapping(
    field: Annotated[str, typer.Argument(help="PandaDoc field name to remove")],
) -> None:
    """Remove a field mapping."""
    config = get_config()

    if field not in config.mapping:
        print_error(f"No mapping found for field: {field}")
        raise typer.Exit(4)

    del config.mapping[field]
    config.save()

    print_success(f"Removed mapping for: {field}")
