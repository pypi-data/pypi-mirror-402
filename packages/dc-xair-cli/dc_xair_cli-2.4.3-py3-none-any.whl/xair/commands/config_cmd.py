"""Configuration management commands."""

from pathlib import Path

import click

from xair.config import CONFIG_PATHS


@click.group()
def config():
    """Manage configuration."""
    pass


@config.command("show")
def config_show():
    """Show active configuration.

    Displays the loaded configuration file and its contents.
    """
    for path in CONFIG_PATHS:
        if path.exists():
            click.echo(f"Config loaded from: {path}")
            click.echo("-" * 40)
            with open(path) as f:
                click.echo(f.read())
            return

    click.echo("No config file found. Searched:")
    for path in CONFIG_PATHS:
        click.echo(f"  {path}")
    click.echo("\nCreate config: xair config init")


@config.command("init")
@click.option(
    "--path",
    type=click.Path(),
    help="Config file path (default: ~/.config/xair/config.toml)",
)
@click.option("--ip", help="Mixer IP address")
@click.option(
    "--model",
    type=click.Choice(["XR18", "XR16", "XR12", "MR18", "X32"]),
    help="Mixer model",
)
@click.option("-f", "--force", is_flag=True, help="Overwrite existing file")
def config_init(path, ip, model, force):
    """Create a configuration file (interactive or with flags).

    \b
    EXAMPLES:
        xair config init                         # Interactive prompts
        xair config init --ip 192.168.1.50       # Specify IP only
        xair config init --ip 192.168.1.50 --model XR18  # Full config
        xair config init --path ./xair.toml      # Custom location
    """
    # Interactive mode: prompt for missing values
    if not ip:
        ip = click.prompt("Mixer IP address", default="192.168.1.50")
    if not model:
        model = click.prompt(
            "Mixer model",
            type=click.Choice(["XR18", "XR16", "XR12", "MR18", "X32"]),
            default="XR18",
        )

    # Build config content
    config_content = f"""[connection]
ip = "{ip}"
model = "{model}"
"""

    # Determine path
    if path:
        config_path = Path(path).expanduser()
    else:
        config_path = Path("~/.config/xair/config.toml").expanduser()

    # Check if exists
    if config_path.exists() and not force:
        if not click.confirm(f"{config_path} exists. Overwrite?"):
            click.echo("Aborted.")
            raise click.Abort()

    # Write file
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_content)

    # Success feedback
    click.echo(f"✓ Config saved to {config_path}")
    click.echo("\nTest connection:")
    click.echo("  xair info")
