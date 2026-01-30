import pytest
from unittest.mock import patch, MagicMock
from dockit.core.autocomplete import (
    get_container_names,
    get_running_container_names,
    get_images,
    get_networks,
    get_volumes,
)


@patch("dockit.core.autocomplete.Docker")
def test_get_container_names(mock_docker_class):
    """Test getting all container names"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.list_containers.return_value = [
        {"Names": "web"},
        {"Names": "db"},
    ]
    
    names = get_container_names()
    
    assert names == ["web", "db"]
    mock_docker.list_containers.assert_called_once_with(all=True)


@patch("dockit.core.autocomplete.Docker")
def test_get_container_names_exception(mock_docker_class):
    """Test get_container_names returns empty list on exception"""
    mock_docker_class.side_effect = Exception("Docker not found")
    
    names = get_container_names()
    
    assert names == []


@patch("dockit.core.autocomplete.Docker")
def test_get_running_container_names(mock_docker_class):
    """Test getting running container names"""
    mock_docker = MagicMock()
    mock_docker_class.return_value = mock_docker
    mock_docker.list_containers.return_value = [
        {"Names": "web"},
    ]
    
    names = get_running_container_names()
    
    assert names == ["web"]
    mock_docker.list_containers.assert_called_once_with(all=False)


def test_get_images_returns_list():
    """Test get_images returns a list"""
    images = get_images()
    assert isinstance(images, list)


def test_get_networks_returns_list():
    """Test get_networks returns a list"""
    networks = get_networks()
    assert isinstance(networks, list)


def test_get_volumes_returns_list():
    """Test get_volumes returns a list"""
    volumes = get_volumes()
    assert isinstance(volumes, list)
