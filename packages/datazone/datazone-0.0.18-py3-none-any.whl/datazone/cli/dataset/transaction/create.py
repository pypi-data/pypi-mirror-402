import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def create(
    name: str = typer.Option(..., prompt=True),
    dataset_id: str = typer.Option(..., prompt=True),
):
    CrudServiceCaller(entity_name="view").create_entity(
        payload={
            "name": name,
            "dataset": dataset_id,
        },
    )

    print("[bold green]Dataset transaction has created successfully [/bold green] :tada:")
