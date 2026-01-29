"""System commands (info, status, discover, meters)."""

import json
import sys

import click

from xair.constants import EXIT_NOT_FOUND
from xair.context import pass_context
from xair.discover import discover_mixers
from xair.utils import level_bar


@click.command()
@pass_context
def info(ctx):
    """Show mixer model, IP, and firmware info."""
    ctx.connect()
    try:
        info_data = ctx.mixer.info_response
        data = {
            "ip": info_data[0] if len(info_data) > 0 else ctx.ip,
            "name": info_data[1] if len(info_data) > 1 else "Unknown",
            "model": info_data[2] if len(info_data) > 2 else ctx.model,
            "version": info_data[3] if len(info_data) > 3 else "Unknown",
        }
        ctx.output(data, f"{data['model']} @ {data['ip']} (v{data['version']})")
    finally:
        ctx.disconnect()


@click.command()
@click.option("--timeout", type=float, default=3.0, help="Discovery timeout in seconds")
@pass_context
def discover(ctx, timeout):
    """Find XAir/MR mixers on the network.

    Sends UDP broadcast to discover mixers. Results show IP, model, and name.

    \b
    EXAMPLES:
        xair discover              # Find mixers (3 second timeout)
        xair discover --timeout 5  # Wait longer for responses
    """
    mixers = discover_mixers(timeout=timeout)

    if not mixers:
        click.echo("No mixers found", err=True)
        click.echo("\nTips:", err=True)
        click.echo(
            "  - Make sure the mixer is on and connected to the network", err=True
        )
        click.echo("  - Try a longer timeout: xair discover --timeout 10", err=True)
        click.echo(
            "  - Specify IP directly if you know it: xair --ip 192.168.1.50 info",
            err=True,
        )
        sys.exit(EXIT_NOT_FOUND)

    if ctx.json_output:
        click.echo(json.dumps({"mixers": mixers}))
    elif ctx.plain_output:
        for m in mixers:
            click.echo(f"ip={m['ip']}")
            click.echo(f"model={m['model']}")
            click.echo(f"name={m['name']}")
    else:
        for m in mixers:
            click.echo(f'{m["ip"]:15s}  {m["model"]:5s}  "{m["name"]}"')

        # Show next steps if not quiet
        if not ctx.quiet and mixers:
            click.echo("\nNext steps:", err=True)
            click.echo(
                f"  xair config init --ip {mixers[0]['ip']} --model {mixers[0]['model']}",
                err=True,
            )
            click.echo(f"  xair --ip {mixers[0]['ip']} info", err=True)


@click.command()
@pass_context
def status(ctx):
    """Show mixer overview with channel names and levels."""
    ctx.connect()
    try:
        channels = []
        for i, strip in enumerate(ctx.mixer.strip):
            name = strip.config.name or f"Ch {i + 1}"
            fader = strip.mix.fader
            muted = not strip.mix.on
            channels.append(
                {
                    "channel": i + 1,
                    "name": name,
                    "fader": fader,
                    "muted": muted,
                }
            )

        if ctx.json_output:
            click.echo(json.dumps({"channels": channels}))
        else:
            info_data = ctx.mixer.info_response
            model = info_data[2] if len(info_data) > 2 else ctx.model
            ip = info_data[0] if len(info_data) > 0 else ctx.ip
            click.echo(f"{model} @ {ip}")
            click.echo("-" * 40)
            for ch in channels:
                mute_str = " (muted)" if ch["muted"] else ""
                bar = level_bar(ch["fader"])
                click.echo(
                    f"CH {ch['channel']:02d} [{ch['name'][:8]:8s}] {bar} {ch['fader']:+.1f} dB{mute_str}"
                )
    finally:
        ctx.disconnect()


@click.command("meters")
@click.option("--watch", is_flag=True, help="Continuously update (Ctrl-C to stop)")
@pass_context
def meters_cmd(ctx, watch):
    """Show channel levels.

    Note: Meters require continuous polling and may not be accurate
    for brief snapshots.
    """
    ctx.connect()
    try:
        if watch:
            click.echo("Press Ctrl-C to stop")
            import time

            try:
                while True:
                    _show_meters(ctx)
                    time.sleep(0.1)
                    click.clear()
            except KeyboardInterrupt:
                pass
        else:
            _show_meters(ctx)
    finally:
        ctx.disconnect()


def _show_meters(ctx):
    """Display current meter levels."""
    for i, strip in enumerate(ctx.mixer.strip):
        name = strip.config.name or f"Ch {i + 1}"
        fader = strip.mix.fader
        muted = not strip.mix.on
        mute_str = " M" if muted else "  "
        bar = level_bar(fader, 20)
        click.echo(f"{i + 1:2d} {name[:8]:8s} {bar} {fader:+6.1f}{mute_str}")
