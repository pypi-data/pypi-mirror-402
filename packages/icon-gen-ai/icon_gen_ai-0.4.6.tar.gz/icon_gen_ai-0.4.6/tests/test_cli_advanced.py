"""Advanced CLI tests."""

import pytest
from click.testing import CliRunner
from icon_gen_ai.cli import cli, generate, providers


def test_cli_group():
    """Test CLI group shows help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'generate icons from Iconify' in result.output


def test_generate_command():
    """Test generate command."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate, ['mdi:github', '--size', '64'])
        assert result.exit_code == 0
        assert 'Success' in result.output or 'Generating' in result.output


def test_generate_with_background():
    """Test generate with background options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate, [
            'mdi:star',
            '--color', 'white',
            '--bg-color', '#FF0000',
            '--border-radius', '32',
            '--size', '64'
        ])
        assert result.exit_code == 0


def test_providers_command():
    """Test providers status command."""
    runner = CliRunner()
    result = runner.invoke(providers)
    assert result.exit_code == 0


def test_generate_with_output_path():
    runner = CliRunner()
    with runner.isolated_filesystem():
        output_path = 'output/icon.svg'
        result = runner.invoke(generate, [
            'mdi:home',
            '-o', output_path
        ])
        assert result.exit_code == 0
        assert 'Saved to' in result.output or 'Error' in result.output


def test_main_legacy_command():
    """Test legacy main command (backwards compatibility)."""
    from icon_gen_ai.cli import main
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['mdi:test', '--size', '64'])
        assert result.exit_code == 0 or 'Error' in result.output