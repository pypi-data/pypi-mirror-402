import typer
from typing import Optional
from ..core import Docker, print_table, print_error

app = typer.Typer()


@app.command()
def ps(all: bool = typer.Option(False, "--all", "-a", help="Show all containers")):
    """List containers"""
    try:
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
