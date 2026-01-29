import typer
from rich import print

from datazone.models.common import JobType
from datazone.service_callers.crud import CrudServiceCaller


def create():
    payload = {}

    job_type: JobType = typer.prompt("Job Type", type=JobType, default=JobType.EXTRACT, show_choices=True)
    # TODO make following checks in backend
    if job_type == JobType.EXTRACT:
        extract_id = typer.prompt("Extract ID", type=str)
        CrudServiceCaller(entity_name="extract").get_entity_with_id(entity_id=extract_id)
        payload["extract"] = extract_id
    else:
        pipeline_id = typer.prompt("Pipeline ID", type=str)
        CrudServiceCaller(entity_name="pipeline").get_entity_with_id(entity_id=pipeline_id)
        payload["pipeline"] = pipeline_id

    payload["name"] = typer.prompt("Name", type=str)
    # TODO add cron expression validation. check cron-validator package
    payload["expression"] = typer.prompt("Schedule Expression", type=str)
    payload["is_active"] = typer.prompt("Is Active?", type=bool, default=True)

    CrudServiceCaller(entity_name="schedule").create_entity(payload=payload)

    print("Schedule has created successfully :tada:")
