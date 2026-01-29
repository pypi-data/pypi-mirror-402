"""xair CLI - Control Behringer XAir/Midas MR mixers from the command line.

USAGE:
    xair [OPTIONS] COMMAND [ARGS]...

EXAMPLES:
    xair info                     # Show mixer info
    xair ch 1 fader -6            # Set channel 1 fader to -6 dB
    xair ch 1 mute on             # Mute channel 1
    xair bus 1 fader 0            # Set bus 1 to unity
    xair scene load 1             # Load scene 1
    xair status                   # Show mixer overview

Need help? Report issues at: https://github.com/dallascrilley/xair/issues
"""

import sys
from pathlib import Path

import click

from xair.config import load_config
from xair.constants import EXIT_ERROR, EXIT_USAGE
from xair.context import pass_context

# Import commands
from xair.commands.channel import bus_cmd, channel_cmd, dca_cmd, fx_cmd, lr_cmd, rtn_cmd
from xair.commands.scene import scene
from xair.commands.system import discover, info, meters_cmd, status
from xair.commands.batch import batch_cmd
from xair.commands.raw import raw_cmd
from xair.commands.config_cmd import config
from xair.commands.completion import completion_cmd


@click.group()
@click.option("--ip", envvar="XAIR_IP", help="Mixer IP address")
@click.option(
    "--model",
    envvar="XAIR_MODEL",
    default="XR18",
    type=click.Choice(["XR18", "XR16", "XR12", "MR18", "X32"]),
    help="Mixer model",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option(
    "--plain", "plain_output", is_flag=True, help="Output as plain key=value pairs"
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-essential output")
@click.option(
    "--no-color", is_flag=True, envvar="NO_COLOR", help="Disable colored output"
)
@click.option("-v", "--verbose", is_flag=True, help="Show debug information")
@click.option(
    "--timeout",
    type=float,
    default=5.0,
    envvar="XAIR_TIMEOUT",
    help="Connection timeout in seconds",
)
@click.option("--dry-run", is_flag=True, help="Preview commands without sending")
@click.option(
    "--config", "config_path", type=click.Path(exists=True), help="Config file path"
)
@click.version_option(version="2.4.1", prog_name="xair")
@pass_context
def cli(
    ctx,
    ip,
    model,
    json_output,
    plain_output,
    quiet,
    no_color,
    verbose,
    timeout,
    dry_run,
    config_path,
):
    """Control Behringer XAir/Midas MR mixers from the command line."""
    cfg = load_config(Path(config_path) if config_path else None)
    conn = cfg.get("connection", {})

    ctx.ip = ip or conn.get("ip")
    ctx.model = model or conn.get("model", "XR18")
    ctx.json_output = json_output
    ctx.plain_output = plain_output
    ctx.quiet = quiet
    ctx.no_color = no_color
    ctx.verbose = verbose
    ctx.timeout = timeout
    ctx.dry_run = dry_run


# Register commands
cli.add_command(info)
cli.add_command(discover)
cli.add_command(status)
cli.add_command(channel_cmd)
cli.add_command(bus_cmd)
cli.add_command(lr_cmd)
cli.add_command(dca_cmd)
cli.add_command(fx_cmd)
cli.add_command(rtn_cmd)
cli.add_command(scene)
cli.add_command(raw_cmd)
cli.add_command(meters_cmd)
cli.add_command(batch_cmd)
cli.add_command(config)
cli.add_command(completion_cmd)


def main():
    """Entry point for CLI."""
    try:
        cli(standalone_mode=False)
    except click.ClickException as e:
        e.show()
        sys.exit(EXIT_USAGE if "usage" in str(e).lower() else EXIT_ERROR)
    except click.Abort:
        sys.exit(130)


if __name__ == "__main__":
    main()
