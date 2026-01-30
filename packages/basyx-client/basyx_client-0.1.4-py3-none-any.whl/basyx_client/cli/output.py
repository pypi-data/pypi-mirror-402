"""Output formatting utilities for the CLI."""

from __future__ import annotations

import json
from collections.abc import Callable
from enum import Enum
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

# Global output format setting
_output_format: OutputFormat = None  # type: ignore


class OutputFormat(str, Enum):
    """Output format options."""

    json = "json"
    yaml = "yaml"
    table = "table"


def set_output_format(fmt: OutputFormat) -> None:
    """Set the global output format."""
    global _output_format
    _output_format = fmt


def get_output_format() -> OutputFormat:
    """Get the current output format."""
    return _output_format or OutputFormat.table


def format_output(
    data: Any,
    columns: list[tuple[str, str]] | None = None,
    title: str | None = None,
    extract_fn: Callable[[Any], dict[str, Any]] | None = None,
) -> None:
    """Format and print output based on the current format setting.

    Args:
        data: The data to output. Can be a single item, list, or dict.
        columns: For table format, list of (key, header) tuples.
        title: Table title for table format.
        extract_fn: Function to extract display dict from complex objects.
    """
    fmt = get_output_format()

    if fmt == OutputFormat.json:
        _output_json(data, extract_fn)
    elif fmt == OutputFormat.yaml:
        _output_yaml(data, extract_fn)
    else:
        _output_table(data, columns, title, extract_fn)


def _serialize_for_output(data: Any, extract_fn: Callable[[Any], dict[str, Any]] | None) -> Any:
    """Convert data to serializable format."""
    if extract_fn and data is not None:
        if isinstance(data, (list, tuple)):
            return [extract_fn(item) for item in data]
        return extract_fn(data)

    # Handle BaSyx model objects by checking for common attributes
    if hasattr(data, "id") or hasattr(data, "id_short"):
        return _model_to_dict(data)

    if isinstance(data, (list, tuple)):
        return [_serialize_for_output(item, None) for item in data]

    return data


def _model_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a BaSyx model object to a dictionary."""
    result: dict[str, Any] = {}

    # Common attributes for all AAS models
    common_attrs = [
        "id",
        "id_short",
        "semantic_id",
        "description",
        "administration",
        "kind",
        "value",
        "value_type",
        "model_type",
        "category",
        "asset_information",
    ]

    for attr in common_attrs:
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if val is not None:
                if hasattr(val, "__dict__"):
                    result[attr] = _model_to_dict(val)
                elif isinstance(val, (list, tuple, set)):
                    result[attr] = [_model_to_dict(v) if hasattr(v, "__dict__") else v for v in val]
                else:
                    result[attr] = val

    # Handle submodel elements
    if hasattr(obj, "submodel_element"):
        elements = getattr(obj, "submodel_element")
        if elements:
            result["submodel_element"] = [_model_to_dict(e) for e in elements]

    return result


def _output_json(data: Any, extract_fn: Callable[[Any], dict[str, Any]] | None) -> None:
    """Output data as JSON."""
    serialized = _serialize_for_output(data, extract_fn)
    console.print(json.dumps(serialized, indent=2, default=str))


def _output_yaml(data: Any, extract_fn: Callable[[Any], dict[str, Any]] | None) -> None:
    """Output data as YAML."""
    serialized = _serialize_for_output(data, extract_fn)
    console.print(yaml.safe_dump(serialized, default_flow_style=False, allow_unicode=True))


def _output_table(
    data: Any,
    columns: list[tuple[str, str]] | None,
    title: str | None,
    extract_fn: Callable[[Any], dict[str, Any]] | None,
) -> None:
    """Output data as a rich table."""
    if data is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Handle single item vs list
    if not isinstance(data, (list, tuple)):
        data = [data]

    if not data:
        console.print("[yellow]No results[/yellow]")
        return

    # Convert to dicts for display
    items = []
    for item in data:
        if extract_fn:
            items.append(extract_fn(item))
        elif isinstance(item, dict):
            items.append(item)
        else:
            items.append(_model_to_dict(item))

    # Auto-detect columns if not provided
    if not columns and items:
        # Use keys from first item
        first = items[0]
        columns = [(k, k.replace("_", " ").title()) for k in first.keys()]

    table = Table(title=title)
    for _, header in columns or []:
        table.add_column(header)

    for item in items:
        row = []
        for key, _ in columns or []:
            val = item.get(key, "")
            # Truncate long values
            val_str = str(val) if val is not None else ""
            if len(val_str) > 60:
                val_str = val_str[:57] + "..."
            row.append(val_str)
        table.add_row(*row)

    console.print(table)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ {message}[/blue]")


def print_verbose(ctx: Any, message: str) -> None:
    """Print a message only if verbose mode is enabled."""
    if ctx.obj.get("verbose"):
        console.print(f"[dim]{message}[/dim]")
