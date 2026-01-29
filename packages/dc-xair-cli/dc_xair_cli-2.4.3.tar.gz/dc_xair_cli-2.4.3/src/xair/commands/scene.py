"""Scene management commands."""

import json
import sys

import click

from xair.context import pass_context


@click.group()
def scene():
    """Manage mixer scenes/snapshots."""
    pass


@scene.command("load")
@click.argument("scene_num", type=int)
@click.option("-f", "--force", is_flag=True, help="Skip confirmation prompt")
@pass_context
def scene_load(ctx, scene_num, force):
    """Load a scene (1-64).

    By default, prompts for confirmation when running interactively.
    Use --force to skip the confirmation.
    """
    if not 1 <= scene_num <= 64:
        raise click.ClickException("Scene number must be 1-64")

    if not force and sys.stdin.isatty() and not ctx.quiet:
        if not click.confirm(
            f"Load scene {scene_num}? This will overwrite current mixer state"
        ):
            raise click.Abort()

    ctx.connect()
    try:
        ctx.mixer.send("/-snap/load", scene_num - 1)
        if ctx.json_output:
            click.echo(json.dumps({"action": "load", "scene": scene_num}))
        elif not ctx.quiet:
            click.echo(f"Loaded scene {scene_num}")
    finally:
        ctx.disconnect()


@scene.command("save")
@click.argument("scene_num", type=int)
@click.option("--name", help="Scene name to save")
@pass_context
def scene_save(ctx, scene_num, name):
    """Save to a scene slot (1-64).

    Optionally set the scene name with --name.
    """
    if not 1 <= scene_num <= 64:
        raise click.ClickException("Scene number must be 1-64")

    ctx.connect()
    try:
        if name:
            ctx.mixer.send(f"/-snap/{scene_num - 1}/name", name)

        ctx.mixer.send("/-snap/save", scene_num - 1)
        if ctx.json_output:
            data = {"action": "save", "scene": scene_num}
            if name:
                data["name"] = name
            click.echo(json.dumps(data))
        elif not ctx.quiet:
            if name:
                click.echo(f'Saved to scene {scene_num} "{name}"')
            else:
                click.echo(f"Saved to scene {scene_num}")
    finally:
        ctx.disconnect()


@scene.command("show")
@click.argument("scene_num", type=int)
@pass_context
def scene_show(ctx, scene_num):
    """Show details for a scene (1-64)."""
    if not 1 <= scene_num <= 64:
        raise click.ClickException("Scene number must be 1-64")

    ctx.connect()
    try:
        name_response = ctx.mixer.query(f"/-snap/{scene_num - 1}/name")
        name = name_response[0] if name_response else ""

        data = {"slot": scene_num, "name": name}
        ctx.output(data, f'Scene {scene_num}: "{name}"')
    finally:
        ctx.disconnect()


@scene.command("list")
@pass_context
def scene_list(ctx):
    """List scene names."""
    ctx.connect()
    try:
        scenes = []
        for i in range(64):
            name_response = ctx.mixer.query(f"/-snap/{i}/name")
            name = name_response[0] if name_response else ""
            if name:  # Only include scenes with actual names
                scenes.append({"slot": i + 1, "name": name})

        if ctx.json_output:
            click.echo(json.dumps({"scenes": scenes}))
        else:
            if not scenes:
                click.echo("No named scenes found")
            else:
                for s in scenes[:20]:
                    click.echo(f"{s['slot']:2d}: {s['name']}")
    finally:
        ctx.disconnect()
