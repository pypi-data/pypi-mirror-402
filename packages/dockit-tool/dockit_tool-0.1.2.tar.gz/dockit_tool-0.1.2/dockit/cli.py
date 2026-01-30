import typer
from typing import Optional
from .core import print_error, Docker, Compose, print_success, print_info
from .core.autocomplete import get_running_container_names

app = typer.Typer(
    help="A production-grade Docker wrapper CLI",
    no_args_is_help=True,
)


@app.command()
def ps(all: bool = typer.Option(False, "--all", "-a", help="Show all containers")):
    """List containers"""
    try:
        from .core import print_table
        docker = Docker()
        containers = docker.list_containers(all=all)
        
        if not containers:
            print_error("No containers found")
            return
        
        headers = ["NAME", "STATUS", "UPTIME", "PORTS", "IMAGE"]
        rows = []
        
        for c in containers:
            name = c.get("Names", "")
            status = c.get("State", "")
            uptime = c.get("RunningFor", "")
            ports = c.get("Ports", "")
            image = c.get("Image", "")
            
            rows.append([name, status, uptime, ports, image])
        
        print_table(headers, rows)
    
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def logs(
    container: str = typer.Argument(..., help="Container name"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since (e.g., 5m, 10s)"),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter logs by pattern"),
):
    """Get container logs"""
    try:
        docker = Docker()
        output = docker.get_logs(container, follow=follow, since=since, grep=grep)
        print(output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


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


@app.command()
def version():
    """Show dockit version"""
    print("dockit 0.1.0")


if __name__ == "__main__":
    app()
