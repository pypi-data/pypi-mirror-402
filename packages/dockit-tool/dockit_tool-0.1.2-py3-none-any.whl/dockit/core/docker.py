from typing import List, Dict, Any, Optional
from .detect import detect_docker_engine
from .utils import run_command
from .errors import ContainerNotFoundError, CommandExecutionError
import json


class Docker:
    def __init__(self):
        self.cmd = detect_docker_engine()
    
    def list_containers(self, all: bool = False) -> List[Dict[str, str]]:
        """List containers and return structured data"""
        cmd = [self.cmd, "ps", "--format=json"]
        if all:
            cmd.insert(2, "-a")
        
        _, stdout, _ = run_command(cmd)
        if not stdout.strip():
            return []
        
        try:
            # Docker outputs JSON objects, one per line in some versions
            # Try parsing as array first
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Fall back to line-by-line parsing
            containers = []
            for line in stdout.strip().split("\n"):
                if line:
                    containers.append(json.loads(line))
            return containers
    
    def get_container_by_name(self, name: str, all: bool = False) -> Optional[Dict[str, Any]]:
        """Get container info by name"""
        containers = self.list_containers(all=all)
        for container in containers:
            if container.get("Names") == name:
                return container
        return None
    
    def resolve_container_id(self, name: str, all: bool = False) -> str:
        """Resolve container name to ID, raise error if not found"""
        container = self.get_container_by_name(name, all=all)
        if not container:
            raise ContainerNotFoundError(f"Container '{name}' not found")
        return container["ID"]
    
    def get_logs(
        self,
        container: str,
        follow: bool = False,
        since: Optional[str] = None,
        grep: Optional[str] = None,
    ) -> str:
        """Get container logs"""
        container_id = self.resolve_container_id(container, all=True)
        cmd = [self.cmd, "logs"]
        
        if follow:
            cmd.append("-f")
        if since:
            cmd.extend(["--since", since])
        
        cmd.append(container_id)
        
        _, stdout, stderr = run_command(cmd, check=False)
        output = stdout + stderr
        
        if grep:
            output = "\n".join(
                line for line in output.split("\n") if grep.lower() in line.lower()
            )
        
        return output
    
    def execute_shell(self, container: str) -> None:
        """Execute interactive shell in container"""
        container_id = self.resolve_container_id(container)
        
        # Try bash first, fall back to sh
        for shell in ["/bin/bash", "/bin/sh"]:
            try:
                run_command([self.cmd, "exec", "-it", container_id, shell])
                return
            except CommandExecutionError:
                continue
        
        raise CommandExecutionError(
            f"Could not open shell in container '{container}'"
        )
    
    def restart_container(self, container: str) -> None:
        """Restart a container"""
        container_id = self.resolve_container_id(container)
        run_command([self.cmd, "restart", container_id])
    
    def start_container(self, container: str) -> None:
        """Start a container"""
        container_id = self.resolve_container_id(container, all=True)
        run_command([self.cmd, "start", container_id])
    
    def stop_container(self, container: str) -> None:
        """Stop a container"""
        container_id = self.resolve_container_id(container)
        run_command([self.cmd, "stop", container_id])
    
    def remove_container(self, container: str, force: bool = False) -> None:
        """Remove a container"""
        container_id = self.resolve_container_id(container, all=True)
        cmd = [self.cmd, "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        run_command(cmd)
    
    def clean_system(self, all: bool = False, dry_run: bool = False) -> None:
        """Clean up Docker system"""
        cmd = [self.cmd, "system", "prune", "-f"]
        if all:
            cmd.append("-a")
        if dry_run:
            # Just show what would be removed without actually removing
            _, stdout, _ = run_command([self.cmd, "system", "prune", "--dry-run"], check=False)
            return
        
        run_command(cmd)
