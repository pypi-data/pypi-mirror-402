import typer
from ..core import Docker, print_error, print_success, get_running_container_names

app = typer.Typer()


@app.command()
def restart(
    container: str = typer.Argument(..., help="Container name"),
):
    """Restart a container"""
    try:
        docker = Docker()
        docker.restart_container(container)
        print_success(f"Container '{container}' restarted")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def start(
    container: str = typer.Argument(..., help="Container name"),
):
    """Start a container"""
    try:
        docker = Docker()
        docker.start_container(container)
        print_success(f"Container '{container}' started")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def stop(
    container: str = typer.Argument(..., help="Container name"),
):
    """Stop a container"""
    try:
        docker = Docker()
        docker.stop_container(container)
        print_success(f"Container '{container}' stopped")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def rm(
    container: str = typer.Argument(..., help="Container name"),
    force: bool = typer.Option(False, "-f", "--force", help="Force removal"),
):
    """Remove a container"""
    try:
        docker = Docker()
        docker.remove_container(container, force=force)
        print_success(f"Container '{container}' removed")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
