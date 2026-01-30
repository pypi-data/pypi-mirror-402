import typer
from ..core import Compose, print_error, print_success

app = typer.Typer()


@app.command()
def up(
    build: bool = typer.Option(False, "--build", help="Build images before starting"),
):
    """Start compose stack"""
    try:
        compose = Compose()
        compose.up(detach=True, build=build)
        print_success("Compose stack started")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
