"""Tests for scene command improvements (Phase 4)."""

from click.testing import CliRunner

from xair.main import cli


class TestSceneSaveNameOption:
    """Tests for scene save --name option."""

    def test_scene_save_has_name_option(self):
        """scene save accepts --name option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scene", "save", "--help"])
        assert "--name" in result.output


class TestSceneShowCommand:
    """Tests for scene show command."""

    def test_scene_show_command_exists(self):
        """scene show command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scene", "--help"])
        assert "show" in result.output

    def test_scene_show_help(self):
        """scene show has help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scene", "show", "--help"])
        assert result.exit_code == 0


class TestSceneLoadForceOption:
    """Tests for scene load --force option."""

    def test_scene_load_has_force_option(self):
        """scene load accepts --force option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scene", "load", "--help"])
        assert "--force" in result.output or "-f" in result.output
