"""Configuration management for the CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from basyx_client import AASClient
from basyx_client.auth import BearerAuth

console = Console()

CONFIG_DIR = Path.home() / ".basyx"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "default_profile": "local",
    "profiles": {
        "local": {
            "url": "http://localhost:8081",
        }
    },
}


class ConfigManager:
    """Manages CLI configuration from ~/.basyx/config.yaml."""

    def __init__(self) -> None:
        self._config: dict[str, Any] | None = None

    @property
    def config(self) -> dict[str, Any]:
        """Lazy load configuration."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            return DEFAULT_CONFIG.copy()

        try:
            with open(CONFIG_FILE) as f:
                loaded = yaml.safe_load(f) or {}
                # Merge with defaults
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                return merged
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
            return DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def get_profile(self, name: str | None = None) -> dict[str, Any]:
        """Get a profile by name, or the default profile."""
        profile_name = name or self.config.get("default_profile", "local")
        profiles = self.config.get("profiles", {})
        if profile_name not in profiles:
            if profile_name != "local":
                console.print(
                    f"[yellow]Profile '{profile_name}' not found, using defaults[/yellow]"
                )
            return {"url": "http://localhost:8081"}
        return profiles[profile_name]

    def set_value(self, key: str, value: str) -> None:
        """Set a configuration value using dot notation."""
        parts = key.split(".")
        current = self.config

        # Navigate to the parent of the target key
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Handle type conversion for known keys
        final_key = parts[-1]
        if final_key in ("timeout", "port"):
            value = int(value)  # type: ignore
        elif value.lower() in ("true", "false"):
            value = value.lower() == "true"  # type: ignore

        current[final_key] = value
        self.save()

    def get_value(self, key: str) -> Any:
        """Get a configuration value using dot notation."""
        parts = key.split(".")
        current = self.config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


def get_client_from_context(ctx: typer.Context) -> AASClient:
    """Create an AASClient from the CLI context."""
    config_mgr: ConfigManager = ctx.obj["config"]
    profile = config_mgr.get_profile(ctx.obj.get("profile"))

    # URL priority: --url flag > env var > profile
    url = ctx.obj.get("url") or profile.get("url")
    if not url:
        console.print("[red]Error: No URL specified. Use --url or configure a profile.[/red]")
        raise typer.Exit(1)

    # Authentication priority: --token flag > env var > profile
    auth: httpx.Auth | None = None
    token = ctx.obj.get("token")
    if token:
        auth = BearerAuth(token)
    elif "auth" in profile:
        auth_config = profile["auth"]
        auth_type = auth_config.get("type", "bearer")
        if auth_type == "bearer":
            # Token can come from env var specified in config
            token_env = auth_config.get("token_env")
            if token_env:
                env_token = os.environ.get(token_env)
                if env_token:
                    auth = BearerAuth(env_token)
            elif "token" in auth_config:
                auth = BearerAuth(auth_config["token"])
        elif auth_type == "oauth2":
            try:
                from basyx_client.auth import OAuth2ClientCredentials

                # Get client secret from env if specified
                client_secret = auth_config.get("client_secret")
                secret_env = auth_config.get("client_secret_env")
                if secret_env:
                    client_secret = os.environ.get(secret_env, client_secret)

                auth = OAuth2ClientCredentials(
                    token_url=auth_config["token_url"],
                    client_id=auth_config["client_id"],
                    client_secret=client_secret or "",
                    scope=auth_config.get("scope"),
                )
            except ImportError:
                console.print(
                    "[yellow]OAuth2 support requires authlib. "
                    "Install with: pip install basyx-client[oauth][/yellow]"
                )

    # Timeout from profile
    timeout = profile.get("timeout", 30.0)

    return AASClient(base_url=url, auth=auth, timeout=timeout)


# Config CLI commands
config_app = typer.Typer(help="Manage CLI configuration")


@config_app.command("show")
def config_show(
    ctx: typer.Context,
    profile: str | None = typer.Argument(None, help="Profile name to show"),
) -> None:
    """Show current configuration or a specific profile."""
    config_mgr: ConfigManager = ctx.obj["config"]

    if profile:
        prof = config_mgr.get_profile(profile)
        console.print(f"[bold]Profile: {profile}[/bold]")
        console.print(yaml.safe_dump(prof, default_flow_style=False))
    else:
        console.print(f"[bold]Config file:[/bold] {CONFIG_FILE}")
        console.print(yaml.safe_dump(config_mgr.config, default_flow_style=False))


@config_app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key (dot notation)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value.

    Examples:
        basyx config set default_profile production
        basyx config set profiles.production.url https://aas.company.com
        basyx config set profiles.production.timeout 60
    """
    config_mgr: ConfigManager = ctx.obj["config"]
    config_mgr.set_value(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@config_app.command("get")
def config_get(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key (dot notation)"),
) -> None:
    """Get a configuration value."""
    config_mgr: ConfigManager = ctx.obj["config"]
    value = config_mgr.get_value(key)
    if value is None:
        console.print(f"[yellow]Key '{key}' not found[/yellow]")
        raise typer.Exit(1)
    console.print(value)


@config_app.command("profiles")
def config_profiles(ctx: typer.Context) -> None:
    """List all configured profiles."""
    config_mgr: ConfigManager = ctx.obj["config"]
    default = config_mgr.config.get("default_profile", "local")
    profiles = config_mgr.config.get("profiles", {})

    table = Table(title="Configured Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Auth", style="yellow")
    table.add_column("Default", style="magenta")

    for name, profile in profiles.items():
        url = profile.get("url", "-")
        auth = profile.get("auth", {}).get("type", "-")
        is_default = "✓" if name == default else ""
        table.add_row(name, url, auth, is_default)

    console.print(table)


@config_app.command("init")
def config_init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
) -> None:
    """Initialize configuration file with defaults."""
    if CONFIG_FILE.exists() and not force:
        console.print(f"[yellow]Config file already exists: {CONFIG_FILE}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f, default_flow_style=False)
    console.print(f"[green]Created config file: {CONFIG_FILE}[/green]")
