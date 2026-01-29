import typer

from datazone.cli.execution.run import run
from datazone.cli.execution.log import log
from datazone.cli.execution.list import list_func

app = typer.Typer()
app.command()(run)
app.command()(log)
app.command(name="list")(list_func)
