import pytest
from unittest.mock import patch, MagicMock
from dockit.core.detect import (
    detect_docker_engine,
    detect_compose,
    detect_swarm_mode,
)
from dockit.core.errors import DockerNotFoundError, ComposeNotFoundError


def test_detect_docker_engine_docker():
    """Test detection of docker engine"""
    with patch("dockit.core.detect.command_exists") as mock_exists:
        mock_exists.side_effect = lambda x: x == "docker"
        assert detect_docker_engine() == "docker"


def test_detect_docker_engine_podman():
    """Test detection of podman engine"""
    with patch("dockit.core.detect.command_exists") as mock_exists:
        mock_exists.side_effect = lambda x: x == "podman"
        assert detect_docker_engine() == "podman"


def test_detect_docker_engine_not_found():
    """Test error when docker/podman not found"""
    with patch("dockit.core.detect.command_exists", return_value=False):
        with pytest.raises(DockerNotFoundError):
            detect_docker_engine()


def test_detect_compose_v2():
    """Test detection of docker compose v2"""
    with patch("dockit.core.detect.detect_docker_engine", return_value="docker"):
        with patch("dockit.core.detect.run_command") as mock_run:
            mock_run.return_value = (0, "Docker Compose version 2.0.0", "")
            cmd, version = detect_compose()
            assert cmd == "docker compose"
            assert version == 2


def test_detect_compose_v1():
    """Test detection of docker-compose v1"""
    with patch("dockit.core.detect.detect_docker_engine", return_value="docker"):
        with patch("dockit.core.detect.run_command") as mock_run:
            mock_run.side_effect = Exception("v2 not found")
            with patch("dockit.core.detect.command_exists") as mock_exists:
                mock_exists.return_value = True
                cmd, version = detect_compose()
                assert cmd == "docker-compose"
                assert version == 1


def test_detect_compose_not_found():
    """Test error when compose not found"""
    with patch("dockit.core.detect.detect_docker_engine", return_value="docker"):
        with patch("dockit.core.detect.run_command") as mock_run:
            mock_run.side_effect = Exception("v2 not found")
            with patch("dockit.core.detect.command_exists", return_value=False):
                with pytest.raises(ComposeNotFoundError):
                    detect_compose()


def test_detect_swarm_mode_active():
    """Test detection of active swarm mode"""
    with patch("dockit.core.detect.detect_docker_engine", return_value="docker"):
        with patch("dockit.core.detect.run_command") as mock_run:
            mock_run.return_value = (0, "active", "")
            assert detect_swarm_mode() is True


def test_detect_swarm_mode_inactive():
    """Test detection of inactive swarm mode"""
    with patch("dockit.core.detect.detect_docker_engine", return_value="docker"):
        with patch("dockit.core.detect.run_command") as mock_run:
            mock_run.return_value = (0, "stopped", "")
            assert detect_swarm_mode() is False
