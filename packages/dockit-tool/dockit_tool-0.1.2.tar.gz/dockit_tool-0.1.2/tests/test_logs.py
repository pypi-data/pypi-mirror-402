import pytest
from unittest.mock import patch, MagicMock
from dockit.commands.logs import logs


@patch("dockit.commands.logs.Docker")
@patch("builtins.print")
def test_logs_get_container_logs(mock_print, mock_docker_class):
    """Test logs command retrieves container logs"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.get_logs.return_value = "log output"
    
    logs(container="web", follow=False, since=None, grep=None, json_output=False)
    
    mock_docker.get_logs.assert_called_once_with(
        "web", follow=False, since=None, grep=None
    )
    mock_print.assert_called_once_with("log output")


@patch("dockit.commands.logs.Docker")
@patch("builtins.print")
def test_logs_with_follow(mock_print, mock_docker_class):
    """Test logs command with follow flag"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.get_logs.return_value = "log output"
    
    logs(container="web", follow=True, since=None, grep=None, json_output=False)
    
    mock_docker.get_logs.assert_called_once_with(
        "web", follow=True, since=None, grep=None
    )


@patch("dockit.commands.logs.Docker")
@patch("builtins.print")
def test_logs_with_grep(mock_print, mock_docker_class):
    """Test logs command with grep filter"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.get_logs.return_value = "filtered log output"
    
    logs(container="web", follow=False, since=None, grep="error", json_output=False)
    
    mock_docker.get_logs.assert_called_once_with(
        "web", follow=False, since=None, grep="error"
    )
