import typer

from datazone.cli.dataset.transaction.create import create
from datazone.cli.dataset.transaction.list import list_func
from datazone.cli.dataset.transaction.delete import delete

app = typer.Typer()
app.command()(create)
app.command(name="list")(list_func)
app.command()(delete)
