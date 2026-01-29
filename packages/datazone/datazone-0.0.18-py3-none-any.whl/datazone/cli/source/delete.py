import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(source_id: str):
    delete_confirm = typer.confirm(
        f"Are you sure you want to delete the source with id: {source_id}?",
    )
    if not delete_confirm:
        return

    CrudServiceCaller(entity_name="source").delete_entity(entity_id=source_id)

    print("Source has deleted successfully :fire:")
