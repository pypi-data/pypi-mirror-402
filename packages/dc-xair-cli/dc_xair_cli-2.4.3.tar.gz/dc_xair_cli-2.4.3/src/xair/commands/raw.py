"""Raw OSC command."""

import json

import click

from xair.context import pass_context


@click.command("raw")
@click.argument("path")
@click.argument("value", required=False)
@pass_context
def raw_cmd(ctx, path, value):
    """Send raw OSC command.

    \b
    EXAMPLES:
        xair raw /ch/01/mix/fader           # Query value
        xair raw /ch/01/mix/fader 0.75      # Set value (0-1 normalized)
    """
    ctx.connect()
    try:
        if value is None:
            result = ctx.mixer.query(path)
            if ctx.json_output:
                click.echo(json.dumps({"path": path, "value": result}))
            else:
                click.echo(f"{path} = {result}")
        else:
            try:
                if "." in value:
                    parsed_value = float(value)
                else:
                    parsed_value = int(value)
            except ValueError:
                parsed_value = value

            ctx.mixer.send(path, parsed_value)
            if not ctx.quiet:
                click.echo(f"Sent: {path} {parsed_value}")
    finally:
        ctx.disconnect()
