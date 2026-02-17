# test_cli.py
import pytest
from unittest.mock import patch, MagicMock
import sys
from sentinal import cli

@pytest.fixture
def mock_core():
    """Fixture to mock the core module."""
    with patch('sentinal.cli.core', autospec=True) as mock:
        yield mock

def run_cli(*args):
    """Helper to run the CLI with specified arguments."""
    original_argv = sys.argv
    sys.argv = ['sentinal', *args]
    try:
        cli.main()
    finally:
        sys.argv = original_argv

def test_no_command(capsys):
    """Test that running with no command prints help."""
    with pytest.raises(SystemExit):
        run_cli()
    captured = capsys.readouterr()
    assert "usage: sentinal" in captured.err or "usage: sentinal" in captured.out


def test_health_command(mock_core: MagicMock):
    """Test the 'health' command."""
    run_cli('health')
    mock_core.health.assert_called_once_with(json_output=False, spark=False)

def test_health_command_with_args(mock_core: MagicMock):
    """Test the 'health' command with arguments."""
    run_cli('health', '--json', '--spark')
    mock_core.health.assert_called_once_with(json_output=True, spark=True)

def test_clean_command(mock_core: MagicMock):
    """Test the 'clean' command."""
    run_cli('clean')
    mock_core.clean.assert_called_once_with(force=False)

def test_clean_command_with_force(mock_core: MagicMock):
    """Test the 'clean' command with --force."""
    run_cli('clean', '--force')
    mock_core.clean.assert_called_once_with(force=True)

# Placeholder tests for other commands

def test_lint_command(mock_core: MagicMock):
    """Test the 'lint' command."""
    run_cli('lint', 'test.py')
    mock_core.lint.assert_called_once_with(file='test.py')

def test_kill_top_command(mock_core: MagicMock):
    """Test the 'kill-top' command."""
    run_cli('kill-top', '3')
    mock_core.kill_top.assert_called_once_with(num=3, force=False)

def test_audit_command(mock_core: MagicMock):
    """Test the 'audit' command."""
    run_cli('audit', '/tmp')
    mock_core.audit.assert_called_once_with(directory='/tmp')

def test_gpu_command(mock_core: MagicMock):
    """Test the 'gpu' command."""
    run_cli('gpu')
    mock_core.gpu.assert_called_once()

def test_metrics_command(mock_core: MagicMock):
    """Test the 'metrics' command."""
    run_cli('metrics', '9999')
    mock_core.metrics.assert_called_once_with(port=9999)

def test_ask_local_command(mock_coremock_core: MagicMock):
    """Test the 'ask-local' command."""
    run_cli('ask-local', 'why is the sky blue?')
    mock_core.ask_local.assert_called_once_with(question='why is the sky blue?')

def test_trace_io_command(mock_core: MagicMock):
    """Test the 'trace-io' command."""
    run_cli('trace-io', '60')
    mock_core.trace_io.assert_called_once_with(duration=60)

def test_index_tree_command(mock_core: MagicMock):
    """Test the 'index-tree' command."""
    run_cli('index-tree', '/home')
    mock_core.index_tree.assert_called_once_with(path='/home')

@patch('sentinal.cli.invoke_adk')
def test_adk_command(mock_invoke_adk: MagicMock):
    """Test the 'adk' command."""
    run_cli('adk', 'test message')
    mock_invoke_adk.assert_called_once_with('test message')
