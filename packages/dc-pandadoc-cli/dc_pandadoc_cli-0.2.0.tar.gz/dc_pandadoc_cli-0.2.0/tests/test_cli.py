"""Tests for CLI argument parsing and command routing."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from pandadoc_cli.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_version_flag(self, runner: CliRunner) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "pandadoc" in result.output

    def test_help_flag(self, runner: CliRunner) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "PandaDoc" in result.output or "pandadoc" in result.output.lower()

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Test that no args shows help (Typer exits with 2)."""
        result = runner.invoke(app, [])
        # Typer with no_args_is_help exits with code 2
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output or "usage" in result.output.lower()

    def test_json_plain_are_mutually_exclusive(self, runner: CliRunner) -> None:
        """Test that --json and --plain cannot be combined."""
        result = runner.invoke(app, ["--json", "--plain", "doc", "list"])
        assert result.exit_code == 2
        stderr = result.stderr if result.stderr else result.output
        assert "mutually exclusive" in stderr.lower()


class TestNonInteractiveBehavior:
    """Test behavior when prompts are disabled."""

    def test_no_input_blocks_delete_confirmation(self, runner: CliRunner) -> None:
        """Test --no-input prevents confirmation prompts."""
        result = runner.invoke(app, ["--no-input", "doc", "delete", "doc_123"])
        assert result.exit_code == 2
        stderr = result.stderr if result.stderr else result.output
        assert "--force" in stderr


class TestDocFieldValidation:
    """Test field format validation."""

    def test_create_rejects_invalid_field_format(self, runner: CliRunner) -> None:
        """Ensure create fails fast on invalid --field format."""
        result = runner.invoke(
            app,
            ["doc", "create", "--template", "tpl_123", "--field", "bad"],
            env={"NO_COLOR": "1"},
        )
        assert result.exit_code == 2
        stderr = result.stderr if result.stderr else result.output
        assert "key=value" in stderr

    def test_update_rejects_invalid_field_format(self, runner: CliRunner) -> None:
        """Ensure update fails fast on invalid --field format."""
        result = runner.invoke(
            app,
            ["doc", "update", "doc_123", "--field", "bad"],
            env={"NO_COLOR": "1"},
        )
        assert result.exit_code == 2
        stderr = result.stderr if result.stderr else result.output
        assert "key=value" in stderr


class TestCommandGroups:
    """Test command groups exist and expose expected subcommands."""

    def test_doc_group_exists(self, runner: CliRunner) -> None:
        """Test doc command group exists with expected subcommands."""
        result = runner.invoke(app, ["doc", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        # Core document operations
        assert "list" in result.output
        assert "get" in result.output
        assert "create" in result.output
        assert "send" in result.output
        assert "status" in result.output

    def test_contact_group_exists(self, runner: CliRunner) -> None:
        """Test contact command group exists with expected subcommands."""
        result = runner.invoke(app, ["contact", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        # CRUD operations
        assert "list" in result.output
        assert "get" in result.output
        assert "create" in result.output
        assert "update" in result.output
        assert "delete" in result.output

    def test_copper_group_exists(self, runner: CliRunner) -> None:
        """Test copper command group exists with expected subcommands."""
        result = runner.invoke(app, ["copper", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        # Copper CRM integration commands
        assert "pull" in result.output
        assert "sync" in result.output
        assert "fields" in result.output
        assert "mapping" in result.output

    def test_config_group_exists(self, runner: CliRunner) -> None:
        """Test config command group exists with expected subcommands."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        # Configuration management
        assert "init" in result.output
        assert "show" in result.output
        assert "set" in result.output
        assert "unset" in result.output
