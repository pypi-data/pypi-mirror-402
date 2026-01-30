"""Tests for CLI interface."""

import pytest
from unittest.mock import patch, MagicMock
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


def test_providers_command_shows_helpful_messages():
    """Test providers command shows helpful messages in different scenarios.
    
    Note: Full testing of all scenarios (no AI installed, no API key, with provider)
    requires manual testing. See tests/test_providers_manual.md for instructions.
    
    This test verifies that the command runs successfully and provides
    helpful output in at least one of the expected states.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ['providers'])
    
    # The command should always succeed
    assert result.exit_code == 0
    
    # Check that the output contains one of the expected states
    output = result.output
    
    # Should show one of these states:
    # 1. No AI features installed
    # 2. No API key configured  
    # 3. Active provider configured
    
    has_no_ai = '❌ AI features not installed' in output and 'pip install icon-gen-ai[ai]' in output
    has_no_key = '⚠ No API key configured' in output
    has_active = '✓ Active provider:' in output
    
    # At least one condition should be true
    assert has_no_ai or has_no_key or has_active, f"Unexpected output: {output}"
    
    # If showing error states, should include helpful instructions
    if has_no_ai or has_no_key:
        assert 'OPENAI_API_KEY' in output or 'ANTHROPIC_API_KEY' in output or 'HF_TOKEN' in output
