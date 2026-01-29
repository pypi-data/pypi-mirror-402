from typing import Optional

from rich import print

from datazone.cli.execution.log import log
from datazone.service_callers.datazone import DatazoneServiceCaller


def run(
    extract_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    transform_selection: Optional[str] = None,
) -> None:
    """
    Start execution.
    Args:
        extract_id: Extract id
        pipeline_id: Pipeline id
        transform_selection (str): specific transform name to run
    """
    if not any([extract_id, pipeline_id]):
        print("[bold red]You should pass extract id or pipeline id![/bold red]")
        return

    if extract_id is not None:
        response_data = DatazoneServiceCaller.run_execution_extract(extract_id=extract_id)
    else:
        response_data = DatazoneServiceCaller.run_execution_pipeline(
            pipeline_id=pipeline_id,  # type: ignore
            transform_selection=transform_selection,
        )

    _id = response_data.get("id")
    if _id is None:
        error_message = response_data.get("message", "Run execution error!")
        print(f"[bold red]{error_message}[/bold red]")
        return

    print("[bold blue]Execution has created... :tada: [/bold blue]")

    log(execution_id=_id)
