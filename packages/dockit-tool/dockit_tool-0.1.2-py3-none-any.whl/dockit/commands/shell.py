import typer
from ..core import Docker, print_error, get_running_container_names

app = typer.Typer()


@app.command()
def shell(
    container: str = typer.Argument(..., help="Container name"),
):
    """Open shell in container"""
    try:
        docker = Docker()
        docker.execute_shell(container)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
