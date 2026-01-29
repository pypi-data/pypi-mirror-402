"""CLI context for shared state and output formatting."""

import json
import sys
from typing import Optional, TYPE_CHECKING

import click

import xair_api
from xair_api.errors import XAirRemoteConnectionTimeoutError, XAirRemoteError

from xair.constants import EXIT_CONNECTION, EXIT_TIMEOUT, EXIT_USAGE


if TYPE_CHECKING:
    from xair_api.xair import XAirRemote


class Context:
    """Shared context for CLI commands."""

    def __init__(self):
        self.ip: Optional[str] = None
        self.model: str = "XR18"
        self.json_output: bool = False
        self.plain_output: bool = False
        self.quiet: bool = False
        self.no_color: bool = False
        self.verbose: bool = False
        self.timeout: float = 5.0
        self.dry_run: bool = False
        self.mixer: Optional["XAirRemote"] = None

    def connect(self) -> None:
        """Connect to the mixer."""
        if self.dry_run:
            if self.verbose:
                click.echo("Dry-run mode: skipping connection", err=True)
            return

        if not self.ip:
            click.echo(
                "Error: No mixer IP specified. Use --ip, XAIR_IP env var, or config file.",
                err=True,
            )
            click.echo("\nTry one of:", err=True)
            click.echo(
                "  xair discover              # Find mixers on network", err=True
            )
            click.echo("  xair config init           # Create config file", err=True)
            click.echo("  xair --ip 192.168.1.50 info  # Specify IP directly", err=True)
            sys.exit(EXIT_USAGE)

        try:
            # Show progress message before blocking network call
            if not self.quiet:
                click.echo(f"Connecting to {self.model} at {self.ip}...", err=True)

            self.mixer = xair_api.connect(self.model, ip=self.ip)
            self.mixer.__enter__()

            if self.verbose:
                click.echo("✓ Connected", err=True)
        except XAirRemoteConnectionTimeoutError as e:
            click.echo(f"Error: Connection timeout: {e.ip}:{e.port}", err=True)
            click.echo("\nIs the mixer on and connected to the network?", err=True)
            click.echo("Try: xair discover --timeout 10", err=True)
            sys.exit(EXIT_TIMEOUT)
        except XAirRemoteError as e:
            click.echo(f"Error: Connection failed: {e}", err=True)
            click.echo("\nCheck mixer IP and network connection.", err=True)
            sys.exit(EXIT_CONNECTION)

    def disconnect(self) -> None:
        """Disconnect from the mixer."""
        if self.mixer:
            self.mixer.__exit__(None, None, None)

    def output(
        self, data: dict[str, object], human_format: Optional[str] = None
    ) -> None:
        """Output data in JSON, plain, or human-readable format."""
        if self.json_output:
            click.echo(json.dumps(data))
        elif self.plain_output:
            for key, value in data.items():
                if key != "unit":  # Skip metadata in plain mode
                    click.echo(f"{key}={value}")
        elif human_format:
            click.echo(human_format)
        else:
            for key, value in data.items():
                click.echo(f"{key}: {value}")

    def success(
        self, label: str, old_value=None, new_value=None, unit: str = ""
    ) -> None:
        """Show success feedback for state changes (human-readable only)."""
        if self.quiet or self.json_output or self.plain_output:
            return

        checkmark = "✓" if not self.no_color else "[OK]"

        if old_value is not None and new_value is not None:
            # Show transition: old → new
            unit_str = f" {unit}" if unit else ""
            click.echo(
                f"{checkmark} {label}: {old_value}{unit_str} → {new_value}{unit_str}",
                err=True,
            )
        elif new_value is not None:
            # Show new value only
            unit_str = f" {unit}" if unit else ""
            click.echo(f"{checkmark} {label}: {new_value}{unit_str}", err=True)
        else:
            # Generic success
            click.echo(f"{checkmark} {label}", err=True)


pass_context = click.make_pass_decorator(Context, ensure=True)
