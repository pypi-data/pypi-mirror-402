import typer
from typing import Optional
from ..core import Docker, print_error, get_running_container_names

app = typer.Typer()


@app.command()
def logs(
    container: str = typer.Argument(..., help="Container name"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since (e.g., 5m, 10s)"),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter logs by pattern"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get container logs"""
    try:
        docker = Docker()
        output = docker.get_logs(container, follow=follow, since=since, grep=grep)
        print(output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
