from typing import Tuple, Optional
from .utils import command_exists, run_command
from .errors import DockerNotFoundError, ComposeNotFoundError


def detect_docker_engine() -> str:
    """Detect Docker engine and return command (docker or podman)"""
    if command_exists("docker"):
        return "docker"
    elif command_exists("podman"):
        return "podman"
    else:
        raise DockerNotFoundError("Docker or Podman not found. Please install Docker.")


def detect_compose() -> Tuple[str, int]:
    """
    Detect Docker Compose and return (command, version).
    Returns ("docker compose", 2) for v2 or ("docker-compose", 1) for v1.
    """
    docker_cmd = detect_docker_engine()
    
    # Try docker compose (v2)
    if docker_cmd == "docker":
        try:
            _, stdout, _ = run_command([docker_cmd, "compose", "version"], check=False)
            if "Docker Compose" in stdout:
                return "docker compose", 2
        except Exception:
            pass
    
    # Fall back to docker-compose (v1)
    if command_exists("docker-compose"):
        return "docker-compose", 1
    
    raise ComposeNotFoundError(
        "Docker Compose not found. Please install Docker Compose."
    )


def detect_swarm_mode() -> bool:
    """Check if Docker Swarm mode is enabled"""
    try:
        docker_cmd = detect_docker_engine()
        _, stdout, _ = run_command(
            [docker_cmd, "info", "--format={{.Swarm.LocalNodeState}}"],
            check=False,
        )
        return "active" in stdout.lower()
    except Exception:
        return False
