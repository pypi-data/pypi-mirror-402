import typer

from datazone.cli.profile.create import create
from datazone.cli.profile.delete import delete
from datazone.cli.profile.list import list_func
from datazone.cli.profile.set_default import setdefault

app = typer.Typer()
app.command(name="list")(list_func)
app.command()(create)
app.command()(delete)
app.command()(setdefault)
