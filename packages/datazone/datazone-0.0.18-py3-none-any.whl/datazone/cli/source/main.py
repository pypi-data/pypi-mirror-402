import typer

from datazone.cli.source.create import create
from datazone.cli.source.list import list_func
from datazone.cli.source.delete import delete

app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
