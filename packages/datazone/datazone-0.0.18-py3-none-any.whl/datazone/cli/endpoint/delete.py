import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(endpoint_id: str):
    delete_confirm = typer.confirm(
        f"Are you sure you want to delete the endpoint with id: {endpoint_id}?",
    )
    if not delete_confirm:
        return

    CrudServiceCaller(entity_name="endpoint").delete_entity(entity_id=endpoint_id)

    print("Endpoint has deleted successfully :fire:")
