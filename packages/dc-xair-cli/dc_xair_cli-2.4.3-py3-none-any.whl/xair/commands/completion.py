"""Shell completion generation."""

import click


@click.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion_cmd(shell):
    """Generate shell completion script.

    \b
    EXAMPLES:
        xair completion bash >> ~/.bashrc
        xair completion zsh >> ~/.zshrc
        xair completion fish > ~/.config/fish/completions/xair.fish
    """
    from click.shell_completion import get_completion_class

    # Import here to avoid circular import
    from xair.main import cli

    comp_cls = get_completion_class(shell)
    comp = comp_cls(cli, {}, "xair", "_XAIR_COMPLETE")
    click.echo(comp.source())
