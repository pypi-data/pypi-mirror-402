"""Registry commands for AAS and Submodel descriptors."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from basyx_client.cli.config import get_client_from_context
from basyx_client.cli.output import (
    format_output,
    print_error,
    print_success,
    print_verbose,
)

app = typer.Typer(help="Registry operations")

# AAS Registry subcommand
shells_app = typer.Typer(help="AAS shell registry operations")
app.add_typer(shells_app, name="shells")

# Submodel Registry subcommand
submodels_app = typer.Typer(help="Submodel registry operations")
app.add_typer(submodels_app, name="submodels")


def _extract_aas_descriptor(desc: dict) -> dict[str, str]:
    """Extract summary from an AAS descriptor."""
    return {
        "id": desc.get("id", ""),
        "id_short": desc.get("idShort", ""),
        "endpoints": str(len(desc.get("endpoints", []))),
    }


def _extract_sm_descriptor(desc: dict) -> dict[str, str]:
    """Extract summary from a submodel descriptor."""
    return {
        "id": desc.get("id", ""),
        "id_short": desc.get("idShort", ""),
        "semantic_id": _get_semantic_id(desc),
        "endpoints": str(len(desc.get("endpoints", []))),
    }


def _get_semantic_id(desc: dict) -> str:
    """Extract semantic ID from a descriptor."""
    sem_id = desc.get("semanticId", {})
    keys = sem_id.get("keys", [])
    if keys:
        return keys[0].get("value", "")
    return ""


# ==================== AAS Registry Commands ====================


@shells_app.command("list")
def list_aas_descriptors(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all AAS descriptors in the registry."""
    print_verbose(ctx, "Fetching AAS descriptors...")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                descriptors = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.aas_registry.list(
                            limit=page_limit, cursor=page_cursor
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.aas_registry.list(limit=limit, cursor=cursor)
                descriptors = result.items

            format_output(
                descriptors,
                columns=[
                    ("id", "ID"),
                    ("id_short", "ID Short"),
                    ("endpoints", "Endpoints"),
                ],
                title="AAS Descriptors",
                extract_fn=_extract_aas_descriptor,
            )
        except Exception as e:
            print_error(f"Failed to list AAS descriptors: {e}")
            raise typer.Exit(1)


@shells_app.command("get")
def get_aas_descriptor(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
) -> None:
    """Get a specific AAS descriptor."""
    print_verbose(ctx, f"Fetching AAS descriptor: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            desc = client.aas_registry.get(aas_id)
            format_output(desc, title="AAS Descriptor")
        except Exception as e:
            print_error(f"Failed to get AAS descriptor: {e}")
            raise typer.Exit(1)


@shells_app.command("create")
def create_aas_descriptor(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="JSON file containing AAS descriptor",
        exists=True,
        readable=True,
    ),
) -> None:
    """Create a new AAS descriptor in the registry."""
    print_verbose(ctx, f"Creating AAS descriptor from: {file}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)
            desc = client.aas_registry.create(data)
            print_success(f"Created AAS descriptor: {desc.get('id', 'unknown')}")
            format_output(desc, extract_fn=_extract_aas_descriptor)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create AAS descriptor: {e}")
            raise typer.Exit(1)


@shells_app.command("delete")
def delete_aas_descriptor(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an AAS descriptor from the registry."""
    if not force:
        confirm = typer.confirm(f"Delete AAS descriptor '{aas_id}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting AAS descriptor: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.aas_registry.delete(aas_id)
            print_success(f"Deleted AAS descriptor: {aas_id}")
        except Exception as e:
            print_error(f"Failed to delete AAS descriptor: {e}")
            raise typer.Exit(1)


# ==================== Submodel Registry Commands ====================


@submodels_app.command("list")
def list_sm_descriptors(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all submodel descriptors in the registry."""
    print_verbose(ctx, "Fetching submodel descriptors...")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                descriptors = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.submodel_registry.list(
                            limit=page_limit, cursor=page_cursor
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.submodel_registry.list(limit=limit, cursor=cursor)
                descriptors = result.items

            format_output(
                descriptors,
                columns=[
                    ("id", "ID"),
                    ("id_short", "ID Short"),
                    ("semantic_id", "Semantic ID"),
                    ("endpoints", "Endpoints"),
                ],
                title="Submodel Descriptors",
                extract_fn=_extract_sm_descriptor,
            )
        except Exception as e:
            print_error(f"Failed to list submodel descriptors: {e}")
            raise typer.Exit(1)


@submodels_app.command("get")
def get_sm_descriptor(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
) -> None:
    """Get a specific submodel descriptor."""
    print_verbose(ctx, f"Fetching submodel descriptor: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            desc = client.submodel_registry.get(submodel_id)
            format_output(desc, title="Submodel Descriptor")
        except Exception as e:
            print_error(f"Failed to get submodel descriptor: {e}")
            raise typer.Exit(1)


@submodels_app.command("create")
def create_sm_descriptor(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="JSON file containing submodel descriptor",
        exists=True,
        readable=True,
    ),
) -> None:
    """Create a new submodel descriptor in the registry."""
    print_verbose(ctx, f"Creating submodel descriptor from: {file}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)
            desc = client.submodel_registry.create(data)
            print_success(f"Created submodel descriptor: {desc.get('id', 'unknown')}")
            format_output(desc, extract_fn=_extract_sm_descriptor)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create submodel descriptor: {e}")
            raise typer.Exit(1)


@submodels_app.command("delete")
def delete_sm_descriptor(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a submodel descriptor from the registry."""
    if not force:
        confirm = typer.confirm(f"Delete submodel descriptor '{submodel_id}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting submodel descriptor: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.submodel_registry.delete(submodel_id)
            print_success(f"Deleted submodel descriptor: {submodel_id}")
        except Exception as e:
            print_error(f"Failed to delete submodel descriptor: {e}")
            raise typer.Exit(1)
