from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
import json


console = Console()


def print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Print a formatted table using rich"""
    table = Table(show_header=True, header_style="bold magenta")
    
    for header in headers:
        table.add_column(header)
    
    for row in rows:
        table.add_row(*row)
    
    console.print(table)


def print_json(data: Dict[str, Any]) -> None:
    """Print data as JSON"""
    console.print(json.dumps(data, indent=2))


def print_error(message: str) -> None:
    """Print error message"""
    console.print(f"[red]Error: {message}[/red]")


def print_success(message: str) -> None:
    """Print success message"""
    console.print(f"[green]✓ {message}[/green]")


def print_info(message: str) -> None:
    """Print info message"""
    console.print(f"[blue]ℹ {message}[/blue]")


def print_warning(message: str) -> None:
    """Print warning message"""
    console.print(f"[yellow]⚠ {message}[/yellow]")
