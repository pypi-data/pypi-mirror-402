"""AAS shell commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from basyx_client.cli.config import get_client_from_context
from basyx_client.cli.output import (
    console,
    format_output,
    print_error,
    print_success,
    print_verbose,
)

app = typer.Typer(help="AAS shell operations")


def _extract_shell_summary(shell: object) -> dict[str, str]:
    """Extract summary info from an AAS shell."""
    result: dict[str, str] = {}
    if hasattr(shell, "id"):
        result["id"] = str(getattr(shell, "id", ""))
    if hasattr(shell, "id_short"):
        result["id_short"] = str(getattr(shell, "id_short", ""))
    if hasattr(shell, "asset_information"):
        asset_info = getattr(shell, "asset_information")
        if hasattr(asset_info, "global_asset_id"):
            result["global_asset_id"] = str(getattr(asset_info, "global_asset_id", ""))
    return result


@app.command("list")
def list_shells(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all AAS shells."""
    print_verbose(ctx, "Fetching AAS shells...")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                shells = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.shells.list(
                            limit=page_limit,
                            cursor=page_cursor,
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.shells.list(limit=limit, cursor=cursor)
                shells = result.items

            format_output(
                shells,
                columns=[
                    ("id", "ID"),
                    ("id_short", "ID Short"),
                    ("global_asset_id", "Global Asset ID"),
                ],
                title="AAS Shells",
                extract_fn=_extract_shell_summary,
            )
        except Exception as e:
            print_error(f"Failed to list shells: {e}")
            raise typer.Exit(1)


@app.command("get")
def get_shell(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
) -> None:
    """Get a specific AAS shell by ID."""
    print_verbose(ctx, f"Fetching AAS: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            shell = client.shells.get(aas_id)
            format_output(shell, title="AAS Shell")
        except Exception as e:
            print_error(f"Failed to get shell: {e}")
            raise typer.Exit(1)


@app.command("create")
def create_shell(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        help="JSON file containing AAS definition",
        exists=True,
        readable=True,
    ),
) -> None:
    """Create a new AAS shell from a JSON file."""
    print_verbose(ctx, f"Creating AAS from: {file}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)
            shell = client.shells.create(data)
            print_success(f"Created AAS: {getattr(shell, 'id', 'unknown')}")
            format_output(shell, extract_fn=_extract_shell_summary)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create shell: {e}")
            raise typer.Exit(1)


@app.command("delete")
def delete_shell(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an AAS shell."""
    if not force:
        confirm = typer.confirm(f"Delete AAS '{aas_id}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting AAS: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.shells.delete(aas_id)
            print_success(f"Deleted AAS: {aas_id}")
        except Exception as e:
            print_error(f"Failed to delete shell: {e}")
            raise typer.Exit(1)


@app.command("refs")
def get_submodel_refs(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
) -> None:
    """Get submodel references for an AAS shell."""
    print_verbose(ctx, f"Fetching submodel references for AAS: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            refs = client.shells.list_submodel_refs(aas_id)
            if refs is None or len(refs) == 0:
                console.print("[yellow]No submodel references found[/yellow]")
                return

            # Format references for display
            ref_data = []
            for ref in refs:
                keys = getattr(ref, "key", [])
                if keys:
                    first_key = keys[0]
                    ref_data.append(
                        {
                            "type": getattr(first_key, "type", ""),
                            "value": getattr(first_key, "value", ""),
                        }
                    )
            format_output(
                ref_data,
                columns=[("type", "Type"), ("value", "Value")],
                title="Submodel References",
            )
        except Exception as e:
            print_error(f"Failed to get submodel references: {e}")
            raise typer.Exit(1)


@app.command("asset-info")
def get_asset_info(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
) -> None:
    """Get asset information for an AAS shell."""
    print_verbose(ctx, f"Fetching asset info for AAS: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            info = client.shells.get_asset_info(aas_id)
            format_output(info, title="Asset Information")
        except Exception as e:
            print_error(f"Failed to get asset info: {e}")
            raise typer.Exit(1)
