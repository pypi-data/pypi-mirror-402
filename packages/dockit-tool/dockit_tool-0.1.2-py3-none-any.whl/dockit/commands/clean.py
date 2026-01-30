import typer
from ..core import Docker, print_error, print_success, print_info

app = typer.Typer()


@app.command()
def clean(
    all: bool = typer.Option(False, "--all", "-a", help="Remove all unused resources"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be removed"),
):
    """Clean up Docker system"""
    try:
        docker = Docker()
        if dry_run:
            print_info("Would remove the following unused resources:")
        docker.clean_system(all=all, dry_run=dry_run)
        if not dry_run:
            print_success("Docker system cleaned")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
