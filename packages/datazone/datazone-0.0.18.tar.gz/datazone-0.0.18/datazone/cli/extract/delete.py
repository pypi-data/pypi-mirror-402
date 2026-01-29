import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(extract_id: str):
    delete_confirm = typer.confirm(
        f"Are you sure you want to delete the extract with id: {extract_id}?",
    )
    if not delete_confirm:
        return

    CrudServiceCaller(entity_name="extract").delete_entity(entity_id=extract_id)

    print("Extract has deleted successfully :fire:")
