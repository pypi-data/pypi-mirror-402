"""Batch command execution."""

import shlex
import sys

import click

from xair.constants import EXIT_ERROR
from xair.context import pass_context
from xair.utils import parse_channel_spec
from xair.commands.channel import _channel_control


@click.command("batch")
@click.option(
    "-f",
    "--file",
    "input_file",
    type=click.File("r"),
    default="-",
    help="Command file (default: stdin)",
)
@click.option("--continue-on-error", is_flag=True, help="Continue after errors")
@pass_context
def batch_cmd(ctx, input_file, continue_on_error):
    """Execute commands from file or stdin.

    Each line is a command (same syntax as CLI). Lines starting with # are
    comments. Blank lines are ignored.

    \b
    EXAMPLES:
        echo "ch 1 mute on" | xair batch
        xair batch -f soundcheck.txt
        xair batch --continue-on-error < commands.txt
    """
    ctx.connect()
    try:
        for line_num, line in enumerate(input_file, 1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                args = shlex.split(line)
                if not args:
                    continue

                _execute_batch_line(ctx, args)

            except Exception as e:
                click.echo(f"Line {line_num}: {e}", err=True)
                if not continue_on_error:
                    sys.exit(EXIT_ERROR)
    finally:
        ctx.disconnect()


def _execute_batch_line(ctx, args: list):
    """Execute a single batch command line.

    Supports: ch, bus, lr, dca, fx, rtn, raw commands.
    Supports multi-channel specs (1-4, 1,3,5, all).
    """
    if not args:
        return

    cmd = args[0]
    cmd_args = args[1:]

    if cmd == "ch" and len(cmd_args) >= 1:
        channels = parse_channel_spec(cmd_args[0], len(ctx.mixer.strip))
        for channel in channels:
            _channel_control(ctx, "strip", channel, tuple(cmd_args[1:]))
    elif cmd == "bus" and len(cmd_args) >= 1:
        buses = parse_channel_spec(cmd_args[0], len(ctx.mixer.bus))
        for bus_num in buses:
            _channel_control(ctx, "bus", bus_num, tuple(cmd_args[1:]))
    elif cmd == "lr":
        _channel_control(ctx, "lr", None, tuple(cmd_args))
    elif cmd == "dca" and len(cmd_args) >= 1:
        dcas = parse_channel_spec(cmd_args[0], len(ctx.mixer.dca))
        for dca_num in dcas:
            _channel_control(ctx, "dca", dca_num, tuple(cmd_args[1:]))
    elif cmd == "fx" and len(cmd_args) >= 1:
        fxs = parse_channel_spec(cmd_args[0], len(ctx.mixer.fx))
        for fx_num in fxs:
            _channel_control(ctx, "fx", fx_num, tuple(cmd_args[1:]))
    elif cmd == "rtn" and len(cmd_args) >= 1:
        rtns = parse_channel_spec(cmd_args[0], len(ctx.mixer.fxreturn))
        for rtn_num in rtns:
            _channel_control(ctx, "fxreturn", rtn_num, tuple(cmd_args[1:]))
    elif cmd == "raw" and len(cmd_args) >= 1:
        path = cmd_args[0]
        value = cmd_args[1] if len(cmd_args) > 1 else None
        if value:
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            ctx.mixer.send(path, value)
        else:
            result = ctx.mixer.query(path)
            click.echo(f"{path} = {result}")
    else:
        raise click.ClickException(f"Unknown command: {cmd}")
