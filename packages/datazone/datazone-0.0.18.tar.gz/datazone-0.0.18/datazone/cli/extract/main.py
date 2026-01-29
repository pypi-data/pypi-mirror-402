import typer

from datazone.cli.extract.create import create
from datazone.cli.extract.list import list_func
from datazone.cli.extract.delete import delete
from datazone.cli.extract.execute import execute

app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
app.command()(execute)
