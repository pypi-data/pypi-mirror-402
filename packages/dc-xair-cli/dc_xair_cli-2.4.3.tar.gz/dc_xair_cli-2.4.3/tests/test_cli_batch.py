"""Tests for batch command (Phase 5)."""

from click.testing import CliRunner

from xair.main import cli


class TestBatchCommand:
    """Tests for xair batch command."""

    def test_batch_command_exists(self):
        """batch command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "batch" in result.output

    def test_batch_help(self):
        """batch command has help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "--help"])
        assert result.exit_code == 0
        assert "stdin" in result.output.lower() or "file" in result.output.lower()

    def test_batch_has_file_option(self):
        """batch command accepts --file option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "--help"])
        assert "--file" in result.output or "-f" in result.output

    def test_batch_has_continue_on_error(self):
        """batch command accepts --continue-on-error option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "--help"])
        assert "--continue-on-error" in result.output
