import typer

from datazone.cli.pipeline.create import create
from datazone.cli.pipeline.list import list_func
from datazone.cli.pipeline.delete import delete

app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
