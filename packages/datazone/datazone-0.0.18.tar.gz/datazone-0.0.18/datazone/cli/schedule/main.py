import typer

from datazone.cli.schedule.create import create
from datazone.cli.schedule.list import list_func
from datazone.cli.schedule.delete import delete

app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
