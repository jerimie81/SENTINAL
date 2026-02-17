from sentinal import cli
import sys
from io import StringIO

def test_main_no_args(capsys):
    """
    Test that running main() with no arguments prints help.
    """
    # To test argparse, we need to control sys.argv
    # However, a simple test is to check the output when no args are passed.
    # We expect it to print help and exit.
    try:
        # Mock sys.argv to simulate running with no command-line arguments
        original_argv = sys.argv
        sys.argv = ['sentinal']
        cli.main()
    except SystemExit as e:
        # Argparse's print_help() calls sys.exit()
        assert e.code == 0
    finally:
        sys.argv = original_argv
    
    captured = capsys.readouterr()
    assert "usage: sentinal" in captured.out or "usage: cli.py" in captured.out

def test_health_check_arg(capsys, monkeypatch):
    """
    Test that running with --health-check calls the core health_check function.
    """
    # Mock the core.health_check function to check if it's called
    class MockCore:
        health_check_called = False
        def health_check(self):
            self.health_check_called = True
            print("Mock health check!")

    mock_core = MockCore()
    monkeypatch.setattr(cli, 'core', mock_core)
    
    try:
        original_argv = sys.argv
        sys.argv = ['sentinal', '--health-check']
        cli.main()
    finally:
        sys.argv = original_argv

    assert mock_core.health_check_called is True
    captured = capsys.readouterr()
    assert "Performing health check..." in captured.out
    
