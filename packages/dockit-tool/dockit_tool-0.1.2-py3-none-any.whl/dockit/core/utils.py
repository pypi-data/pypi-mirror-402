import subprocess
from typing import Tuple, Optional
from pathlib import Path


def run_command(cmd: list, check: bool = True) -> Tuple[int, str, str]:
    """Execute a shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Command not found: {cmd[0]}") from e


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    try:
        subprocess.run(
            ["which", cmd],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def find_compose_file() -> Optional[Path]:
    """Find docker-compose.yml or compose.yaml in current directory"""
    for name in ["compose.yaml", "docker-compose.yml"]:
        path = Path(name)
        if path.exists():
            return path
    return None
