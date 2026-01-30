"""Discovery service commands."""

from __future__ import annotations

import typer

from basyx_client.cli.config import get_client_from_context
from basyx_client.cli.output import (
    console,
    format_output,
    print_error,
    print_success,
    print_verbose,
)

app = typer.Typer(help="Discovery service operations")


@app.command("lookup")
def lookup(
    ctx: typer.Context,
    asset_id_type: str = typer.Argument(..., help="Asset ID type (e.g., globalAssetId)"),
    asset_id_value: str = typer.Argument(..., help="Asset ID value"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
) -> None:
    """Look up AAS IDs by asset ID.

    Examples:
        basyx discovery lookup globalAssetId "urn:example:asset:1"
        basyx discovery lookup serialNumber "SN-123456"
    """
    print_verbose(ctx, f"Looking up AAS for asset: {asset_id_type}={asset_id_value}")

    with get_client_from_context(ctx) as client:
        try:
            result = client.discovery.get_aas_ids_by_asset(
                [{"name": asset_id_type, "value": asset_id_value}],
                limit=limit,
                cursor=cursor,
            )

            aas_ids = result.items
            if not aas_ids:
                console.print("[yellow]No AAS found for this asset ID[/yellow]")
                return

            # Format as list of dicts for table output
            data = [{"aas_id": aas_id} for aas_id in aas_ids]
            format_output(
                data,
                columns=[("aas_id", "AAS ID")],
                title=f"AAS IDs for {asset_id_type}={asset_id_value}",
            )

            if result.has_more and result.cursor:
                console.print(f"[dim]More results available. Use --cursor {result.cursor}[/dim]")
        except Exception as e:
            print_error(f"Failed to lookup: {e}")
            raise typer.Exit(1)


@app.command("link")
def link(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
    asset_id_type: str = typer.Argument(..., help="Asset ID type"),
    asset_id_value: str = typer.Argument(..., help="Asset ID value"),
) -> None:
    """Link an asset ID to an AAS.

    Examples:
        basyx discovery link "urn:example:aas:1" globalAssetId "urn:example:asset:1"
    """
    print_verbose(ctx, f"Linking asset {asset_id_type}={asset_id_value} to AAS {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.discovery.link_aas_to_asset(
                aas_id=aas_id,
                asset_ids=[{"name": asset_id_type, "value": asset_id_value}],
            )
            print_success(f"Linked {asset_id_type}={asset_id_value} to AAS {aas_id}")
        except Exception as e:
            print_error(f"Failed to link: {e}")
            raise typer.Exit(1)


@app.command("unlink")
def unlink(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
    asset_id_type: str = typer.Argument(..., help="Asset ID type"),
    asset_id_value: str = typer.Argument(..., help="Asset ID value"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Unlink an asset ID from an AAS.

    Examples:
        basyx discovery unlink "urn:example:aas:1" globalAssetId "urn:example:asset:1"
    """
    if not force:
        confirm = typer.confirm(f"Unlink {asset_id_type}={asset_id_value} from AAS {aas_id}?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Unlinking asset {asset_id_type}={asset_id_value} from AAS {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            client.discovery.unlink_asset_from_aas(
                aas_id=aas_id,
                asset_id={"name": asset_id_type, "value": asset_id_value},
            )
            print_success(f"Unlinked {asset_id_type}={asset_id_value} from AAS {aas_id}")
        except Exception as e:
            print_error(f"Failed to unlink: {e}")
            raise typer.Exit(1)


@app.command("list-links")
def list_links(
    ctx: typer.Context,
    aas_id: str = typer.Argument(..., help="AAS identifier"),
) -> None:
    """List all asset IDs linked to an AAS."""
    print_verbose(ctx, f"Listing asset links for AAS: {aas_id}")

    with get_client_from_context(ctx) as client:
        try:
            links = client.discovery.get_asset_links(aas_id)
            if not links:
                console.print(f"[yellow]No asset IDs linked to AAS {aas_id}[/yellow]")
                return

            # Format links for display
            data = []
            for link in links:
                data.append(
                    {
                        "type": link.get("name", link.get("key", "")),
                        "value": link.get("value", ""),
                    }
                )

            format_output(
                data,
                columns=[("type", "Asset ID Type"), ("value", "Asset ID Value")],
                title=f"Asset Links for AAS {aas_id}",
            )
        except Exception as e:
            print_error(f"Failed to list links: {e}")
            raise typer.Exit(1)
