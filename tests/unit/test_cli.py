"""
Tests for the Health Analytics CLI.

These tests verify:
- Command parsing and dispatch
- Help output
- Error handling
- Configuration commands
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Path to the CLI script
CLI_PATH = Path(__file__).parent.parent.parent / "health"


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    @pytest.mark.unit
    def test_cli_exists(self):
        """CLI script should exist."""
        assert CLI_PATH.exists()

    @pytest.mark.unit
    def test_cli_is_executable(self):
        """CLI script should be executable."""
        import os
        assert os.access(CLI_PATH, os.X_OK)


class TestCLIHelp:
    """Tests for CLI help output."""

    @pytest.mark.unit
    def test_no_args_shows_help(self):
        """Should show help when no arguments provided."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            capture_output=True,
            text=True
        )
        assert 'usage:' in result.stdout.lower() or result.returncode != 0

    @pytest.mark.unit
    def test_help_flag(self):
        """Should show help with --help flag."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Health Analytics CLI' in result.stdout

    @pytest.mark.unit
    def test_command_help(self):
        """Should show command-specific help."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'dashboard', '--help'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert '--port' in result.stdout


class TestConfigCommand:
    """Tests for config command."""

    @pytest.mark.unit
    def test_config_shows_paths(self):
        """Config command should show all paths."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'config'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Health Analytics Configuration' in result.stdout
        assert 'Project Root' in result.stdout
        assert 'Health Data' in result.stdout
        assert 'Dashboard' in result.stdout

    @pytest.mark.unit
    def test_config_shows_validation(self):
        """Config command should show validation status."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'config'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Validation' in result.stdout


class TestStatusCommand:
    """Tests for status command."""

    @pytest.mark.unit
    def test_status_shows_overview(self):
        """Status command should show system overview."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'status'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Health Analytics Status' in result.stdout
        assert 'Configuration' in result.stdout
        assert 'Data Status' in result.stdout
        assert 'Dashboard Status' in result.stdout

    @pytest.mark.unit
    def test_status_shows_file_count(self):
        """Status command should show file count."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'status'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Files found' in result.stdout


class TestArgumentParsing:
    """Tests for argument parsing."""

    @pytest.mark.unit
    def test_dashboard_default_port(self):
        """Dashboard should default to port 8080."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'dashboard', '--help'],
            capture_output=True,
            text=True
        )
        assert 'default: 8080' in result.stdout

    @pytest.mark.unit
    def test_generate_accepts_days(self):
        """Generate should accept --days argument."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'generate', '--help'],
            capture_output=True,
            text=True
        )
        assert '--days' in result.stdout

    @pytest.mark.unit
    def test_analyze_requires_date(self):
        """Analyze command should require date argument."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'analyze'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'arguments' in result.stderr.lower()


class TestUnknownCommand:
    """Tests for unknown command handling."""

    @pytest.mark.unit
    def test_unknown_command_fails(self):
        """Unknown commands should fail gracefully."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), 'unknown_command'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0


class TestCommandsAvailable:
    """Tests that all expected commands are available."""

    @pytest.mark.unit
    @pytest.mark.parametrize("command", [
        'dashboard',
        'generate',
        'daily',
        'analyze',
        'weekly',
        'explore',
        'deep',
        'config',
        'status',
    ])
    def test_command_exists(self, command):
        """All documented commands should exist."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), command, '--help'],
            capture_output=True,
            text=True
        )
        # Should either succeed or fail with missing required args
        # but not with "unknown command"
        assert 'invalid choice' not in result.stderr.lower()
