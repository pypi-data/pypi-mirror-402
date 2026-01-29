import typer

from datazone.cli.app.list import list_func


app = typer.Typer()
app.command(name="list")(list_func)
