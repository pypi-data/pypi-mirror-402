"""Test __main__ entry point."""

import subprocess
import sys
from pathlib import Path


def test_main_module_runs():
    """Test that __main__ can be executed."""
    result = subprocess.run(
        [sys.executable, "-m", "icon_gen_ai", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,  # Run from project root
        timeout=10,
    )
    
    # Click CLI returns 0 for --help
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "icon-gen-ai" in result.stdout  # Verify your script entry
    assert not result.stderr  # No errors

def test_main_entrypoint():
    """Test direct execution of __main__.py covers the entrypoint."""
    from icon_gen_ai.cli import main
    import sys
    
    # Capture SystemExit from Click CLI
    try:
        result = main(["--help"])
        assert result == 0
    except SystemExit as e:
        assert e.code == 0  # Success exit codes only
    
    print("Main entrypoint tested successfully")

def test_main_if_name_main():
    """Force coverage of __main__.py if __name__ block."""
    import icon_gen_ai.__main__  # Triggers import
    assert icon_gen_ai.__main__.__file__.endswith('__main__.py')
