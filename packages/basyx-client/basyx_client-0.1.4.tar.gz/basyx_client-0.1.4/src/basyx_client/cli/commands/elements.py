"""Submodel element commands."""

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

app = typer.Typer(help="Submodel element operations")


def _extract_element_summary(elem: object) -> dict[str, str]:
    """Extract summary info from a submodel element."""
    result: dict[str, str] = {}
    if hasattr(elem, "id_short"):
        result["id_short"] = str(getattr(elem, "id_short", ""))

    # Get model type
    model_type = type(elem).__name__
    result["type"] = model_type

    # Get value for Property, Range, etc.
    if hasattr(elem, "value"):
        val = getattr(elem, "value")
        if val is not None:
            result["value"] = str(val)[:50]  # Truncate long values
    if hasattr(elem, "value_type"):
        vt = getattr(elem, "value_type")
        if vt is not None:
            # Handle XSDataType enum
            result["value_type"] = str(vt).replace("XSDataType.", "")

    return result


@app.command("list")
def list_elements(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum number of results"),
    cursor: str | None = typer.Option(None, "--cursor", "-c", help="Pagination cursor"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages"),
) -> None:
    """List all elements in a submodel."""
    print_verbose(ctx, f"Fetching elements for submodel: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            if all_pages:
                from basyx_client.pagination import iterate_pages

                elements = list(
                    iterate_pages(
                        lambda page_limit, page_cursor: client.submodels.elements.list(
                            submodel_id,
                            limit=page_limit,
                            cursor=page_cursor,
                        ),
                        page_size=limit,
                    )
                )
            else:
                result = client.submodels.elements.list(submodel_id, limit=limit, cursor=cursor)
                elements = result.items

            format_output(
                elements,
                columns=[
                    ("id_short", "ID Short"),
                    ("type", "Type"),
                    ("value", "Value"),
                    ("value_type", "Value Type"),
                ],
                title="Submodel Elements",
                extract_fn=_extract_element_summary,
            )
        except Exception as e:
            print_error(f"Failed to list elements: {e}")
            raise typer.Exit(1)


@app.command("get")
def get_element(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    id_short_path: str = typer.Argument(
        ..., help="Element idShort path (e.g., Sensors.Temperature)"
    ),
) -> None:
    """Get a specific submodel element."""
    print_verbose(ctx, f"Fetching element: {submodel_id} / {id_short_path}")

    with get_client_from_context(ctx) as client:
        try:
            elem = client.submodels.elements.get(submodel_id, id_short_path)
            format_output(elem, title="Submodel Element")
        except Exception as e:
            print_error(f"Failed to get element: {e}")
            raise typer.Exit(1)


@app.command("get-value")
def get_element_value(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    id_short_path: str = typer.Argument(..., help="Element idShort path"),
) -> None:
    """Get the value of a submodel element."""
    print_verbose(ctx, f"Fetching element value: {submodel_id} / {id_short_path}")

    with get_client_from_context(ctx) as client:
        try:
            value = client.submodels.elements.get_value(submodel_id, id_short_path)
            format_output({"path": id_short_path, "value": value}, title="Element Value")
        except Exception as e:
            print_error(f"Failed to get element value: {e}")
            raise typer.Exit(1)


@app.command("set-value")
def set_element_value(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    id_short_path: str = typer.Argument(..., help="Element idShort path"),
    value: str = typer.Argument(..., help="New value (JSON or primitive)"),
) -> None:
    """Set the value of a submodel element."""
    print_verbose(ctx, f"Setting element value: {submodel_id} / {id_short_path}")

    # Try to parse as JSON, otherwise use as string
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    with get_client_from_context(ctx) as client:
        try:
            client.submodels.elements.set_value(submodel_id, id_short_path, parsed_value)
            print_success(f"Set value for {id_short_path}")
        except Exception as e:
            print_error(f"Failed to set element value: {e}")
            raise typer.Exit(1)


@app.command("create")
def create_element(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    file: Path = typer.Argument(
        ...,
        help="JSON file containing element definition",
        exists=True,
        readable=True,
    ),
    parent_path: str | None = typer.Option(
        None, "--parent", "-p", help="Parent element idShort path (for nested elements)"
    ),
) -> None:
    """Create a new submodel element from a JSON file."""
    print_verbose(ctx, f"Creating element in submodel: {submodel_id}")

    with get_client_from_context(ctx) as client:
        try:
            with open(file) as f:
                data = json.load(f)

            if parent_path:
                elem = client.submodels.elements.create(submodel_id, parent_path, data)
            else:
                elem = client.submodels.elements.create_root(submodel_id, data)

            print_success(f"Created element: {getattr(elem, 'id_short', 'unknown')}")
            format_output(elem, extract_fn=_extract_element_summary)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON file: {e}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to create element: {e}")
            raise typer.Exit(1)


@app.command("delete")
def delete_element(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    id_short_path: str = typer.Argument(..., help="Element idShort path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a submodel element."""
    if not force:
        confirm = typer.confirm(f"Delete element '{id_short_path}'?")
        if not confirm:
            print_error("Aborted")
            raise typer.Exit(0)

    print_verbose(ctx, f"Deleting element: {submodel_id} / {id_short_path}")

    with get_client_from_context(ctx) as client:
        try:
            client.submodels.elements.delete(submodel_id, id_short_path)
            print_success(f"Deleted element: {id_short_path}")
        except Exception as e:
            print_error(f"Failed to delete element: {e}")
            raise typer.Exit(1)


@app.command("invoke")
def invoke_operation(
    ctx: typer.Context,
    submodel_id: str = typer.Argument(..., help="Submodel identifier"),
    id_short_path: str = typer.Argument(..., help="Operation idShort path"),
    input_file: Path | None = typer.Option(
        None,
        "--input",
        "-i",
        help="JSON file with input arguments",
        exists=True,
        readable=True,
    ),
    async_mode: bool = typer.Option(False, "--async", help="Invoke asynchronously"),
    timeout: int | None = typer.Option(
        None, "--timeout", "-t", help="Operation timeout in seconds"
    ),
) -> None:
    """Invoke an operation submodel element."""
    print_verbose(ctx, f"Invoking operation: {submodel_id} / {id_short_path}")

    input_args: list = []
    inout_args: list = []

    if input_file:
        with open(input_file) as f:
            data = json.load(f)
            input_args = data.get("inputArguments", [])
            inout_args = data.get("inoutputArguments", [])

    with get_client_from_context(ctx) as client:
        try:
            if async_mode:
                handle_id = client.submodels.elements.invoke_async(
                    submodel_id,
                    id_short_path,
                    input_arguments=input_args,
                    inoutput_arguments=inout_args,
                )
                console.print(f"[blue]Operation started. Handle: {handle_id}[/blue]")
            else:
                result = client.submodels.elements.invoke(
                    submodel_id,
                    id_short_path,
                    input_arguments=input_args,
                    inoutput_arguments=inout_args,
                    timeout=timeout,
                )
                format_output(result, title="Operation Result")
        except Exception as e:
            print_error(f"Failed to invoke operation: {e}")
            raise typer.Exit(1)
