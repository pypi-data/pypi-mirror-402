import typer

from datazone.cli.view.create import create
from datazone.cli.view.list import list_func
from datazone.cli.view.delete import delete


app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
