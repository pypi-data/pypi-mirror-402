import typer
from ..core import Compose, print_error, print_success

app = typer.Typer()


@app.command()
def down(
    volumes: bool = typer.Option(False, "-v", "--volumes", help="Remove volumes"),
):
    """Stop and remove compose stack"""
    try:
        compose = Compose()
        compose.down(volumes=volumes)
        print_success("Compose stack stopped")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
