import typer
from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(pipeline_id: str):
    delete_confirm = typer.confirm(
        f"Are you sure you want to delete the pipeline with id: {pipeline_id}?",
    )
    if not delete_confirm:
        return

    CrudServiceCaller(entity_name="pipeline").delete_entity(entity_id=pipeline_id)

    print("Pipeline has deleted successfully :fire:")
