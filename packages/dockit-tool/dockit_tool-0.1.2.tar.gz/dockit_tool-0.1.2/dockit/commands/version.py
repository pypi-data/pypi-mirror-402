import typer

app = typer.Typer()


@app.command()
def version():
    """Show dockit version"""
    print("dockit 0.1.0")
