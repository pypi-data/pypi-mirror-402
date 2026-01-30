from typing import Optional
from .detect import detect_compose
from .utils import run_command, find_compose_file
from .errors import DockitError


class Compose:
    def __init__(self):
        self.cmd, self.version = detect_compose()
        self.compose_file = find_compose_file()
        
        if not self.compose_file:
            raise DockitError(
                "No compose.yaml or docker-compose.yml found in current directory"
            )
    
    def up(self, detach: bool = True, build: bool = False) -> None:
        """Start compose stack"""
        cmd = [self.cmd, "up"]
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        
        run_command(cmd)
    
    def down(self, volumes: bool = False) -> None:
        """Stop and remove compose stack"""
        cmd = [self.cmd, "down"]
        if volumes:
            cmd.append("-v")
        
        run_command(cmd)
    
    def restart(self, service: Optional[str] = None) -> None:
        """Restart compose service(s)"""
        cmd = [self.cmd, "restart"]
        if service:
            cmd.append(service)
        
        run_command(cmd)
    
    def logs(self, service: Optional[str] = None, follow: bool = False) -> str:
        """Get compose logs"""
        cmd = [self.cmd, "logs"]
        if follow:
            cmd.append("-f")
        if service:
            cmd.append(service)
        
        _, stdout, stderr = run_command(cmd, check=False)
        return stdout + stderr
    
    def ps(self) -> None:
        """List compose services"""
        cmd = [self.cmd, "ps"]
        run_command(cmd)
