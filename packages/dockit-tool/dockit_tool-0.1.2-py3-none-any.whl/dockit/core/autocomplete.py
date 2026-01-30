from typing import List, Optional
from .docker import Docker
from .compose import Compose
from .errors import DockitError


def get_container_names() -> List[str]:
    """Get list of all container names for autocomplete"""
    try:
        docker = Docker()
        containers = docker.list_containers(all=True)
        return [c.get("Names", "") for c in containers if c.get("Names")]
    except Exception:
        return []


def get_running_container_names() -> List[str]:
    """Get list of running container names for autocomplete"""
    try:
        docker = Docker()
        containers = docker.list_containers(all=False)
        return [c.get("Names", "") for c in containers if c.get("Names")]
    except Exception:
        return []


def get_images() -> List[str]:
    """Get list of image names for autocomplete"""
    try:
        docker = Docker()
        _, stdout, _ = docker.list_containers(all=False)
        # This would need actual implementation via docker images
        return []
    except Exception:
        return []


def get_networks() -> List[str]:
    """Get list of network names for autocomplete"""
    try:
        docker = Docker()
        # This would need actual implementation via docker network ls
        return []
    except Exception:
        return []


def get_volumes() -> List[str]:
    """Get list of volume names for autocomplete"""
    try:
        docker = Docker()
        # This would need actual implementation via docker volume ls
        return []
    except Exception:
        return []
