import pytest
from unittest.mock import patch, MagicMock
from dockit.commands.shell import shell


@patch("dockit.commands.shell.Docker")
def test_shell_opens_container_shell(mock_docker_class):
    """Test shell command opens shell in container"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    shell(container="web")
    
    mock_docker.execute_shell.assert_called_once_with("web")


@patch("dockit.commands.shell.Docker")
@patch("dockit.commands.shell.print_error")
def test_shell_container_not_found(mock_print_error, mock_docker_class):
    """Test shell command when container not found"""
    import typer
    
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.execute_shell.side_effect = Exception("Container not found")
    
    with pytest.raises(typer.Exit):
        shell(container="nonexistent")
    
    mock_print_error.assert_called_once()
