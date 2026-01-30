import pytest
from unittest.mock import patch, MagicMock
from dockit.commands.restart import restart, start, stop, rm


@patch("dockit.commands.restart.Docker")
@patch("dockit.commands.restart.print_success")
def test_restart_container(mock_print_success, mock_docker_class):
    """Test restart command"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    restart(container="web")
    
    mock_docker.restart_container.assert_called_once_with("web")
    mock_print_success.assert_called_once()


@patch("dockit.commands.restart.Docker")
@patch("dockit.commands.restart.print_success")
def test_start_container(mock_print_success, mock_docker_class):
    """Test start command"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    start(container="web")
    
    mock_docker.start_container.assert_called_once_with("web")
    mock_print_success.assert_called_once()


@patch("dockit.commands.restart.Docker")
@patch("dockit.commands.restart.print_success")
def test_stop_container(mock_print_success, mock_docker_class):
    """Test stop command"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    stop(container="web")
    
    mock_docker.stop_container.assert_called_once_with("web")
    mock_print_success.assert_called_once()


@patch("dockit.commands.restart.Docker")
@patch("dockit.commands.restart.print_success")
def test_rm_container(mock_print_success, mock_docker_class):
    """Test rm command"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    rm(container="web", force=False)
    
    mock_docker.remove_container.assert_called_once_with("web", force=False)
    mock_print_success.assert_called_once()


@patch("dockit.commands.restart.Docker")
@patch("dockit.commands.restart.print_success")
def test_rm_container_force(mock_print_success, mock_docker_class):
    """Test rm command with force flag"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    
    rm(container="web", force=True)
    
    mock_docker.remove_container.assert_called_once_with("web", force=True)
