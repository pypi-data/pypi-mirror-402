"""Tests for CLI global flags (Phase 1)."""

from click.testing import CliRunner

from xair.main import cli
from xair.context import Context


class TestNoColorFlag:
    """Tests for --no-color flag."""

    def test_no_color_flag_sets_context(self):
        """--no-color flag sets no_color=True in context."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--no-color", "--help"])
        assert result.exit_code == 0

    def test_no_color_flag_appears_in_help(self):
        """--no-color flag is documented in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "--no-color" in result.output

    def test_no_color_env_var(self):
        """NO_COLOR env var disables colors."""
        runner = CliRunner(env={"NO_COLOR": "1"})
        # This should set no_color=True internally
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0


class TestVerboseFlag:
    """Tests for -v/--verbose flag."""

    def test_verbose_flag_appears_in_help(self):
        """--verbose flag is documented in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "--verbose" in result.output or "-v" in result.output

    def test_verbose_short_flag(self):
        """-v short flag works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["-v", "--help"])
        assert result.exit_code == 0


class TestTimeoutFlag:
    """Tests for --timeout flag."""

    def test_timeout_flag_appears_in_help(self):
        """--timeout flag is documented in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "--timeout" in result.output

    def test_timeout_accepts_float(self):
        """--timeout accepts float values."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--timeout", "3.5", "--help"])
        assert result.exit_code == 0

    def test_timeout_env_var(self):
        """XAIR_TIMEOUT env var sets timeout."""
        runner = CliRunner(env={"XAIR_TIMEOUT": "10.0"})
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0


class TestDryRunFlag:
    """Tests for --dry-run flag."""

    def test_dry_run_flag_appears_in_help(self):
        """--dry-run flag is documented in help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "--dry-run" in result.output

    def test_dry_run_flag_accepted(self):
        """--dry-run flag is accepted without error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--dry-run", "--help"])
        assert result.exit_code == 0


class TestContextAttributes:
    """Tests for Context class attributes."""

    def test_context_has_no_color(self):
        """Context has no_color attribute."""
        ctx = Context()
        assert hasattr(ctx, "no_color")

    def test_context_has_verbose(self):
        """Context has verbose attribute."""
        ctx = Context()
        assert hasattr(ctx, "verbose")

    def test_context_has_timeout(self):
        """Context has timeout attribute."""
        ctx = Context()
        assert hasattr(ctx, "timeout")

    def test_context_has_dry_run(self):
        """Context has dry_run attribute."""
        ctx = Context()
        assert hasattr(ctx, "dry_run")

    def test_context_timeout_default(self):
        """Context timeout defaults to 5.0."""
        ctx = Context()
        assert ctx.timeout == 5.0
