import pytest
from unittest.mock import patch, MagicMock
from dockit.commands.ps import ps


@patch("dockit.commands.ps.Docker")
@patch("dockit.commands.ps.print_table")
def test_ps_lists_containers(mock_print_table, mock_docker_class):
    """Test ps command lists containers"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.list_containers.return_value = [
        {
            "Names": "web",
            "State": "running",
            "RunningFor": "2 hours",
            "Ports": "0.0.0.0:80->80/tcp",
            "Image": "nginx:latest",
        }
    ]
    
    ps(all=False)
    
    mock_docker.list_containers.assert_called_once_with(all=False)
    mock_print_table.assert_called_once()


@patch("dockit.commands.ps.Docker")
@patch("dockit.commands.ps.print_error")
def test_ps_no_containers(mock_print_error, mock_docker_class):
    """Test ps command with no containers"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.list_containers.return_value = []
    
    ps(all=False)
    
    mock_print_error.assert_called_once()


@patch("dockit.commands.ps.Docker")
@patch("dockit.commands.ps.print_table")
def test_ps_all_containers(mock_print_table, mock_docker_class):
    """Test ps command with --all flag"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.list_containers.return_value = []
    
    ps(all=True)
    
    mock_docker.list_containers.assert_called_once_with(all=True)
