"""Tests for shell completion command (Phase 6)."""

from click.testing import CliRunner

from xair.main import cli


class TestCompletionCommand:
    """Tests for xair completion command."""

    def test_completion_command_exists(self):
        """completion command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "completion" in result.output

    def test_completion_help(self):
        """completion command has help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "--help"])
        assert result.exit_code == 0

    def test_completion_accepts_bash(self):
        """completion generates bash script."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "bash"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower() or "bash" in result.output.lower()

    def test_completion_accepts_zsh(self):
        """completion generates zsh script."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "zsh"])
        assert result.exit_code == 0

    def test_completion_accepts_fish(self):
        """completion generates fish script."""
        runner = CliRunner()
        result = runner.invoke(cli, ["completion", "fish"])
        assert result.exit_code == 0
