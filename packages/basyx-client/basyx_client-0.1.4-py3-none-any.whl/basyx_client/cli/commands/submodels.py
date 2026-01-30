"""Submodel commands."""

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

app = typer.Typer(help="Submodel operations")


def _extract_submodel_summary(sm: object) -> dict[str, str]:
    """Extract summary info from a submodel."""
    result: dict[str, str] = {}
    if hasattr(sm, "id"):
        result["id"] = str(getattr(sm, "id", ""))
    if hasattr(sm, "id_short"):
        result["id_short"] = str(getattr(sm, "id_short", ""))
    if hasattr(sm, "semantic_id"):
        sem_id = getattr(sm, "semantic_id")
        if sem_id and hasattr(sem_id, "key") and sem_id.key:
            result["semantic_id"] = str(getattr(sem_id.key[0], "value", ""))
    # Count elements
    if hasattr(sm, "submodel_element"):
        elements = getattr(sm, "submodel_element", None)
        result["element_count"] = str(len(elements) if elements else 0)
    return result


@app.command("list")
def list_submodels(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    semantic_id: str | None = typer.Option(
        None, "--semantic-id", "-s", help="Filter by semantic ID"
    ),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all submodels."""
    print_verbose(ctx, "Fetching submodels...")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                submodels = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.submodels.list(
                            limit=page_limit,
                            cursor=page_cursor,
                            semantic_id=semantic_id,
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.submodels.list(limit=limit, cursor=cursor, semantic_id=semantic_id)
                submodels = result.items

            format_output(
                submodels,
                columns=[
                    ("id", "ID"),
                    ("id_short", "ID Short"),
                    ("semantic_id", "Semantic ID"),
                    ("element_count", "Elements"),
                ],
                title="Submodels",
                extract_fn=_extract_submodel_summary,
            )
        except Exception as e:
            print_error(f"Failed to list submodels: {e}")
            raise typer.Exit(1)


@app.command("get")
def get_submodel(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    level: str = typer.Option("deep", "--level", help="Content level (deep/core)"),
) -> None:
    """Get a specific submodel by ID."""
    print_verbose(ctx, f"Fetching submodel: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            sm = client.submodels.get(submodel_id, level=level)
            format_output(sm, title="Submodel")
        except Exception as e:
            print_error(f"Failed to get submodel: {e}")
            raise typer.Exit(1)


@app.command("create")
def create_submodel(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="JSON file containing submodel definition",
        exists=True,
        readable=True,
    ),
) -> None:
    """Create a new submodel from a JSON file."""
    print_verbose(ctx, f"Creating submodel from: {file}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)
            sm = client.submodels.create(data)
            print_success(f"Created submodel: {getattr(sm, 'id', 'unknown')}")
            format_output(sm, extract_fn=_extract_submodel_summary)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create submodel: {e}")
            raise typer.Exit(1)


@app.command("delete")
def delete_submodel(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a submodel."""
    if not force:
        confirm = typer.confirm(f"Delete submodel '{submodel_id}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting submodel: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.submodels.delete(submodel_id)
            print_success(f"Deleted submodel: {submodel_id}")
        except Exception as e:
            print_error(f"Failed to delete submodel: {e}")
            raise typer.Exit(1)


@app.command("value")
def get_submodel_value(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
) -> None:
    """Get the $value serialization of a submodel."""
    print_verbose(ctx, f"Fetching submodel value: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            value = client.submodels.get_value(submodel_id)
            format_output(value, title="Submodel Value")
        except Exception as e:
            print_error(f"Failed to get submodel value: {e}")
            raise typer.Exit(1)
