import typer

from datazone.cli.project.create import create
from datazone.cli.project.deploy import deploy
from datazone.cli.project.summary import summary
from datazone.cli.project.list import list_func
from datazone.cli.project.clone import clone
from datazone.cli.project.pull import pull
from datazone.cli.project.activities import app as activities_app

app = typer.Typer()
app.command()(create)
app.command()(deploy)
app.command()(summary)
app.command(name="list")(list_func)
app.command()(clone)
app.command()(pull)
app.add_typer(activities_app, name="activities")
