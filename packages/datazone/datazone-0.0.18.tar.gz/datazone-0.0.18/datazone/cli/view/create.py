import questionary
import typer
from rich import print

from bson import ObjectId

from datazone.service_callers.crud import CrudServiceCaller


def create():
    view_type = questionary.select(
        "Select view type...",
        choices=["MATERIALIZED", "NON_MATERIALIZED"],
    ).unsafe_ask()

    source_type = questionary.select(
        "Select source type...",
        choices=["REPLICATE", "QUERY"],
    ).unsafe_ask()

    dataset_id = None
    query = None

    if source_type == "REPLICATE":
        dataset_id = typer.prompt("Dataset ID", type=str)
        if not ObjectId.is_valid(dataset_id):
            print("[bold red]Invalid Dataset ID. It must be a 24-char hex ObjectId.[/bold red]")
            return
    else:
        query = typer.prompt("Query", type=str)

    project_id = typer.prompt("Project ID", type=str)
    if not ObjectId.is_valid(project_id):
        print("[bold red]Invalid Project ID. It must be a 24-char hex ObjectId.[/bold red]")
        return

    name = typer.prompt("View Name", type=str)

    payload = {
        "name": name,
        "project": project_id,
        "type": view_type,
        "source_type": source_type,
    }
    if dataset_id:
        payload["dataset"] = dataset_id
    if query:
        payload["query"] = query

    CrudServiceCaller(entity_name="view").create_entity(
        payload=payload,
    )

    print("[bold green]View has created successfully [/bold green] :tada:")
