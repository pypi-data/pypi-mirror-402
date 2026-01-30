class DockitError(Exception):
    """Base exception for all dockit errors"""
    pass


class DockerNotFoundError(DockitError):
    """Docker engine not found"""
    pass


class ComposeNotFoundError(DockitError):
    """Docker Compose not found"""
    pass


class ContainerNotFoundError(DockitError):
    """Container not found"""
    pass


class CommandExecutionError(DockitError):
    """Command execution failed"""
    pass
