import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(view_id: str):
    delete_confirm = typer.confirm(
        f"Are you sure you want to delete the view with id: {view_id}?",
    )
    if not delete_confirm:
        return

    CrudServiceCaller(entity_name="view").delete_entity(entity_id=view_id)

    print("View has deleted successfully :fire:")
