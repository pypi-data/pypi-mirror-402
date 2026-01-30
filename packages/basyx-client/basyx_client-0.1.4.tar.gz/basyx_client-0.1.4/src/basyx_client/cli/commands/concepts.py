"""Concept description commands."""

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

app = typer.Typer(help="Concept description operations")


def _extract_concept_summary(cd: object) -> dict[str, str]:
    """Extract summary from a concept description."""
    result: dict[str, str] = {}
    if hasattr(cd, "id"):
        result["id"] = str(getattr(cd, "id", ""))
    if hasattr(cd, "id_short"):
        result["id_short"] = str(getattr(cd, "id_short", ""))

    # Get preferred name from embedded data spec if available
    if hasattr(cd, "embedded_data_specifications"):
        specs = getattr(cd, "embedded_data_specifications", [])
        if specs:
            for spec in specs:
                content = getattr(spec, "data_specification_content", None)
                if content and hasattr(content, "preferred_name"):
                    names = getattr(content, "preferred_name", [])
                    if names:
                        # Get first name entry
                        first = next(iter(names), None)
                        if first:
                            result["preferred_name"] = str(getattr(first, "text", ""))
                            break

    return result


@app.command("list")
def list_concepts(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    id_short: str | None = typer.Option(None, "--id-short", help="Filter by idShort"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all concept descriptions."""
    print_verbose(ctx, "Fetching concept descriptions...")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                concepts = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.concept_descriptions.list(
                            limit=page_limit,
                            cursor=page_cursor,
                            id_short=id_short,
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.concept_descriptions.list(
                    limit=limit, cursor=cursor, id_short=id_short
                )
                concepts = result.items

            format_output(
                concepts,
                columns=[
                    ("id", "ID"),
                    ("id_short", "ID Short"),
                    ("preferred_name", "Preferred Name"),
                ],
                title="Concept Descriptions",
                extract_fn=_extract_concept_summary,
            )
        except Exception as e:
            print_error(f"Failed to list concept descriptions: {e}")
            raise typer.Exit(1)


@app.command("get")
def get_concept(
    ctx: typer.Context,
    concept_id: str = typer.Argument(..., help="Concept description identifier"),
) -> None:
    """Get a specific concept description by ID."""
    print_verbose(ctx, f"Fetching concept description: {concept_id}")

    with get_client_from_context(ctx) as client:
        try:
            cd = client.concept_descriptions.get(concept_id)
            format_output(cd, title="Concept Description")
        except Exception as e:
            print_error(f"Failed to get concept description: {e}")
            raise typer.Exit(1)


@app.command("create")
def create_concept(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="JSON file containing concept description definition",
        exists=True,
        readable=True,
    ),
) -> None:
    """Create a new concept description from a JSON file."""
    print_verbose(ctx, f"Creating concept description from: {file}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)
            cd = client.concept_descriptions.create(data)
            print_success(f"Created concept description: {getattr(cd, 'id', 'unknown')}")
            format_output(cd, extract_fn=_extract_concept_summary)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create concept description: {e}")
            raise typer.Exit(1)


@app.command("delete")
def delete_concept(
    ctx: typer.Context,
    concept_id: str = typer.Argument(..., help="Concept description identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a concept description."""
    if not force:
        confirm = typer.confirm(f"Delete concept description '{concept_id}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting concept description: {concept_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.concept_descriptions.delete(concept_id)
            print_success(f"Deleted concept description: {concept_id}")
        except Exception as e:
            print_error(f"Failed to delete concept description: {e}")
            raise typer.Exit(1)
