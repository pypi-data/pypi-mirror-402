import typer

from datazone.cli.endpoint.create import create
from datazone.cli.endpoint.list import list_func
from datazone.cli.endpoint.delete import delete


app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
