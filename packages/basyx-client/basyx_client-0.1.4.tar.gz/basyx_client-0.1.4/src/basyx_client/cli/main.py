"""Main CLI entry point using Typer."""

from __future__ import annotations

import typer

from basyx_client.cli.commands import (
    aasx,
    concepts,
    discovery,
    elements,
    registry,
    shells,
    submodels,
)
from basyx_client.cli.config import (
    ConfigManager,
    config_app,
)
from basyx_client.cli.output import OutputFormat, set_output_format

app = typer.Typer(
    name="basyx",
    help="CLI for interacting with AAS Part 2 API servers (BaSyx, AASX Server, etc.)",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from basyx_client import __version__

        typer.echo(f"basyx-client {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    url: str | None = typer.Option(
        None,
        "--url",
        "-u",
        envvar="BASYX_URL",
        help="Server URL (overrides profile)",
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        envvar="BASYX_PROFILE",
        help="Config profile to use",
    ),
    token: str | None = typer.Option(
        None,
        "--token",
        "-t",
        envvar="BASYX_TOKEN",
        help="Bearer token for authentication",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.table,
        "--format",
        "-f",
        help="Output format",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """BaSyx client CLI for AAS Part 2 API operations."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["url"] = url
    ctx.obj["profile"] = profile
    ctx.obj["token"] = token
    set_output_format(output_format)

    # Load config manager
    config_mgr = ConfigManager()
    ctx.obj["config"] = config_mgr


# Register command groups
app.add_typer(config_app, name="config", help="Manage CLI configuration")

app.add_typer(shells.app, name="shells", help="AAS shell operations")
app.add_typer(submodels.app, name="submodels", help="Submodel operations")
app.add_typer(elements.app, name="elements", help="Submodel element operations")
app.add_typer(registry.app, name="registry", help="Registry operations")
app.add_typer(aasx.app, name="aasx", help="AASX package operations")
app.add_typer(discovery.app, name="discovery", help="Discovery service operations")
app.add_typer(concepts.app, name="concepts", help="Concept description operations")


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
