import questionary
import typer
from rich import print

from bson import ObjectId

from datazone.service_callers.crud import CrudServiceCaller


def create():
    name = typer.prompt("Endpoint Name", type=str)
    query = typer.prompt("SQL Query", type=str)
    project_id = typer.prompt("Project ID", type=str)
    if not ObjectId.is_valid(project_id):
        print(
            "[bold red]Invalid Project ID. It must be a 24-char hex ObjectId.[/bold red]",
        )
        return

    add_filters = questionary.confirm(
        "Do you want to add filters?", default=False,
    ).unsafe_ask()

    filters = []
    if add_filters:
        print(
            "[bold yellow]Note: Filters will be added as empty list. You can update them later.[/bold yellow]",
        )

    payload = {
        "name": name,
        "query": query,
        "project": project_id,
        "filters": filters,
    }

    CrudServiceCaller(entity_name="endpoint").create_entity(
        payload=payload,
    )

    print("[bold green]Endpoint has created successfully [/bold green] :tada:")
