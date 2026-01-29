"""Tests for discover command (Phase 3)."""

from click.testing import CliRunner

from xair.main import cli


class TestDiscoverCommand:
    """Tests for xair discover command."""

    def test_discover_command_exists(self):
        """discover command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "discover" in result.output

    def test_discover_help(self):
        """discover command has help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", "--help"])
        assert result.exit_code == 0
        assert "Find" in result.output or "mixer" in result.output.lower()

    def test_discover_timeout_option(self):
        """discover command accepts --timeout option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", "--help"])
        assert "--timeout" in result.output


class TestDiscoverFunction:
    """Tests for discover_mixers function."""

    def test_discover_mixers_function_exists(self):
        """discover_mixers function is importable."""
        from xair.discover import discover_mixers

        assert callable(discover_mixers)

    def test_discover_mixers_returns_list(self):
        """discover_mixers returns a list."""
        from xair.discover import discover_mixers

        # With very short timeout, should return empty list (no real mixers)
        result = discover_mixers(timeout=0.1)
        assert isinstance(result, list)

    def test_discover_mixers_accepts_timeout(self):
        """discover_mixers accepts timeout parameter."""
        from xair.discover import discover_mixers

        # Should not raise
        result = discover_mixers(timeout=0.01)
        assert isinstance(result, list)
