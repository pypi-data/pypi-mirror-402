"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from icon_gen_ai.cli import cli


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Generate icons from Iconify' in result.output


def test_cli_basic_generation():
    """Test basic icon generation via CLI."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['generate', 'mdi:github', '--size', '64'])
        assert result.exit_code == 0
        # Check that it saved the file
        assert 'Saved to output/mdi_github.svg' in result.output
